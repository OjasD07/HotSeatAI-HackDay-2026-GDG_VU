"""
HotSeat AI — Bulletproof Dual-Engine Gemma 4 Router & JSON Extractor
=====================================================================

Provides:
  • Gemma4Router     – waterfall cloud cascade (Gemini API) + local Ollama fallback
  • extract_json_safely – 3-layer resilient JSON parser that never lets a 500 escape

Multimodal ordering rule
------------------------
Gemma 4 requires **image parts BEFORE text prompts** in the `contents` array:
    contents=[types.Part.from_bytes(data=image_bytes, mime_type=…), prompt]

Copyright 2026  HotSeat AI Contributors
SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import urllib.error
import urllib.request
from typing import Any, Optional

from google import genai
from google.genai import types

# ─── Logging ────────────────────────────────────────────────────────────────
logger = logging.getLogger("hotseat.engine")

# ─── Constants ──────────────────────────────────────────────────────────────
_CLOUD_CASCADE: list[str] = [
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
    "gemma-3-27b-it",
]

_DEFAULT_TEMPERATURE: float = 0.4
_DEFAULT_OLLAMA_URL: str = "http://localhost:11434/api/chat"
_DEFAULT_OLLAMA_MODEL: str = "gemma4"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  3-Layer Safe JSON Extractor
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def extract_json_safely(raw_text: str, fallback_dict: dict) -> dict:
    """Parse JSON from potentially messy LLM output using a 3-layer strategy.

    Layer 1 – Strip ``<thought>…</thought>`` reasoning blocks.
    Layer 2 – Strip markdown code fences (````json`` / `````).
    Layer 3 – Locate the first ``{`` / last ``}`` and attempt ``json.loads()``.

    If all three layers fail, *fallback_dict* is returned with the raw text
    injected under the ``"_raw"`` key so the caller always gets a ``dict``
    and the server **never** throws a 500 error.

    Parameters
    ----------
    raw_text:
        The raw string returned by the LLM (may contain markdown, XML tags, etc.).
    fallback_dict:
        A dict to return when parsing fails.  A ``"_raw"`` key is appended
        containing the original ``raw_text`` for debugging.

    Returns
    -------
    dict
        Parsed JSON object, or *fallback_dict* augmented with ``"_raw"``.
    """
    if not raw_text or not raw_text.strip():
        return {**fallback_dict, "_raw": raw_text}

    # Layer 1: strip <thought>…</thought> blocks
    cleaned = re.sub(r"<thought>.*?</thought>", "", raw_text, flags=re.DOTALL)

    # Layer 2: strip markdown code fences
    cleaned = cleaned.replace("```json", "").replace("```", "")

    # Layer 3: locate outermost braces and parse
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace : last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            logger.warning("JSON decode failed after all 3 cleaning layers.")

    # Fallback: return the safety dict + raw text for debugging
    return {**fallback_dict, "_raw": raw_text}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Gemma 4 Dual-Engine Router
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Gemma4Router:
    """Route inference requests through a waterfall of Gemma 4 model endpoints.

    Supported providers
    -------------------
    ``"gemini_api"``
        Cloud-hosted models via the Google GenAI SDK.  Cascades through
        ``gemma-4-26b-a4b-it → gemma-4-31b-it → gemma-3-27b-it``.

    ``"ollama"``
        Locally-hosted open-weight model via the Ollama REST API.
        Falls back to ``gemini_api`` if the local server is unreachable
        **and** a ``GEMINI_API_KEY`` is available.

    Parameters
    ----------
    api_key:
        Optional Gemini API key.  If *None*, the router reads
        ``GEMINI_API_KEY`` from the environment.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key: Optional[str] = api_key or os.environ.get("GEMINI_API_KEY")

    # ── public interface ────────────────────────────────────────────────────
    async def generate(
        self,
        prompt: str,
        image_bytes: Optional[bytes] = None,
        mime_type: str = "image/png",
        fallback_dict: Optional[dict] = None,
        provider: str = "ollama",
        api_key_override: Optional[str] = None,
    ) -> dict[str, Any]:
        """Generate a JSON response from Gemma 4.

        Parameters
        ----------
        prompt:
            The text prompt to send to the model.
        image_bytes:
            Optional raw bytes of an image (slide screenshot, chart, etc.).
        mime_type:
            MIME type of the supplied image (default ``"image/png"``).
        fallback_dict:
            Safety dict returned when all parsing fails.
        provider:
            ``"ollama"`` (default) or ``"gemini_api"``.
        api_key_override:
            An optional per-request API key (e.g. from a request header)
            that takes precedence over the instance / env key.

        Returns
        -------
        dict
            Always a ``dict`` — never raises to the caller.
            Contains an ``"engine_used"`` key noting which model produced the
            response.
        """
        if fallback_dict is None:
            fallback_dict = {}

        effective_key = api_key_override or self._api_key

        if provider == "gemini_api":
            return await self._cloud_cascade(
                prompt, image_bytes, mime_type, fallback_dict, effective_key
            )

        if provider == "ollama":
            return await self._ollama(
                prompt, image_bytes, mime_type, fallback_dict, effective_key
            )

        # Unknown provider — surface the error in data, don't crash
        return {
            **fallback_dict,
            "error": f"Unknown provider '{provider}'",
            "engine_used": "none",
        }

    # ── Gemini API cloud cascade ────────────────────────────────────────────
    async def _cloud_cascade(
        self,
        prompt: str,
        image_bytes: Optional[bytes],
        mime_type: str,
        fallback_dict: dict,
        api_key: Optional[str],
    ) -> dict[str, Any]:
        """Waterfall through cloud-hosted Gemma models.

        For each model in ``_CLOUD_CASCADE``:
          1. Try with ``response_mime_type="application/json"`` for native JSON.
          2. If the endpoint rejects ``response_mime_type``, retry without it
             and parse the output through ``extract_json_safely()``.
        """
        if not api_key:
            return {
                **fallback_dict,
                "error": "GEMINI_API_KEY is not set and no key was provided.",
                "engine_used": "none",
            }

        client = genai.Client(api_key=api_key)

        # Build contents — images BEFORE text (Gemma 4 multimodal rule)
        contents: list[Any] = []
        if image_bytes:
            contents.append(
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            )
        contents.append(prompt)

        last_error: Optional[Exception] = None

        for model_id in _CLOUD_CASCADE:
            # ── Attempt 1: structured JSON mode ─────────────────────────────
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=_DEFAULT_TEMPERATURE,
                        response_mime_type="application/json",
                    ),
                )
                raw = response.text or ""
                result = extract_json_safely(raw, fallback_dict)
                result["engine_used"] = f"gemini_api/{model_id} (json_mode)"
                logger.info("Cloud cascade succeeded: %s (json_mode)", model_id)
                return result

            except Exception as exc_json:
                logger.warning(
                    "Model %s rejected json_mode (%s). Retrying plain.",
                    model_id,
                    exc_json,
                )

                # ── Attempt 2: plain text → extract_json_safely ─────────────
                try:
                    response = client.models.generate_content(
                        model=model_id,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            temperature=_DEFAULT_TEMPERATURE,
                        ),
                    )
                    raw = response.text or ""
                    result = extract_json_safely(raw, fallback_dict)
                    result["engine_used"] = f"gemini_api/{model_id} (plain)"
                    logger.info("Cloud cascade succeeded: %s (plain)", model_id)
                    return result

                except Exception as exc_plain:
                    last_error = exc_plain
                    logger.warning(
                        "Model %s failed entirely: %s — trying next model.",
                        model_id,
                        exc_plain,
                    )

        # All models exhausted
        return {
            **fallback_dict,
            "error": f"All cloud models failed. Last error: {last_error}",
            "engine_used": "none",
        }

    # ── Local Ollama fallback ───────────────────────────────────────────────
    async def _ollama(
        self,
        prompt: str,
        image_bytes: Optional[bytes],
        mime_type: str,
        fallback_dict: dict,
        api_key: Optional[str],
    ) -> dict[str, Any]:
        """Call a local Ollama instance and fall back to cloud if unreachable.

        The request is sent as a synchronous ``urllib.request`` call wrapped
        in the async method so we avoid adding ``httpx`` / ``aiohttp`` as a
        dependency.  For a hackathon-scale app this is perfectly adequate.
        """
        ollama_url = os.environ.get("OLLAMA_URL", _DEFAULT_OLLAMA_URL)
        ollama_model = os.environ.get("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)

        # Build the Ollama chat payload
        message: dict[str, Any] = {"role": "user", "content": prompt}
        if image_bytes:
            message["images"] = [base64.b64encode(image_bytes).decode("ascii")]

        payload = json.dumps(
            {
                "model": ollama_model,
                "messages": [message],
                "stream": False,
                "format": "json",
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            ollama_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            # Ollama wraps the response in message.content
            raw = body.get("message", {}).get("content", "")
            result = extract_json_safely(raw, fallback_dict)
            result["engine_used"] = f"ollama/{ollama_model}"
            logger.info("Ollama succeeded: %s", ollama_model)
            return result

        except (urllib.error.URLError, OSError, ConnectionError) as exc:
            logger.warning("Ollama unreachable (%s). Checking cloud fallback.", exc)

            if api_key:
                logger.info(
                    "GEMINI_API_KEY present — falling back to gemini_api cascade."
                )
                result = await self._cloud_cascade(
                    prompt, image_bytes, mime_type, fallback_dict, api_key
                )
                # Annotate the fallback in engine_used
                original_engine = result.get("engine_used", "unknown")
                result["engine_used"] = (
                    f"{original_engine} (fallback from ollama — {exc})"
                )
                return result

            return {
                **fallback_dict,
                "error": (
                    f"Ollama unreachable at {ollama_url} and no GEMINI_API_KEY "
                    f"available for cloud fallback. ({exc})"
                ),
                "engine_used": "none",
            }

        except Exception as exc:
            logger.exception("Unexpected error calling Ollama: %s", exc)
            return {
                **fallback_dict,
                "error": f"Ollama call failed unexpectedly: {exc}",
                "engine_used": "none",
            }

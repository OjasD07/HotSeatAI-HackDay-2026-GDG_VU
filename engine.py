"""
HotSeat AI — Gemma 4 Multimodal Inference Engine & JSON Extractor
=================================================================

Provides:
  • Gemma4Router        – live Gemma 4 multimodal inference via Google GenAI SDK
                          ("gemma-4-26b-a4b-it" → "gemma-4-31b-it") + local Ollama
  • extract_json_safely – 3-layer JSON extractor (strips <thought> blocks & fences)
                          with zero hardcoded fake responses

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
import time
import urllib.error
import urllib.request
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv(override=True)

from google import genai
from google.genai import types

# ─── Logging ────────────────────────────────────────────────────────────────
logger = logging.getLogger("hotseat.engine")

# ─── Constants ──────────────────────────────────────────────────────────────
_CLOUD_CASCADE: list[str] = [
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
]

_DEFAULT_TEMPERATURE: float = 0.3
_DEFAULT_OLLAMA_URL: str = "http://127.0.0.1:11434/api/chat"
_DEFAULT_OLLAMA_MODEL: str = "gemma4:12b"
_DEFAULT_OLLAMA_KEEP_ALIVE: str = "30m"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  3-Layer JSON Extractor (Zero Canned Fallbacks)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def extract_json_safely(raw_text: str) -> dict[str, Any]:
    """Parse a JSON object from Gemma 4 output using a 3-layer cleaning pipeline.

    Layer 1 – Strip ``<thought>…</thought>`` reasoning blocks.
    Layer 2 – Strip markdown code fences (````json`` / `````).
    Layer 3 – Locate outermost ``{`` … ``}`` and parse with ``json.loads()``.

    Raises a ``ValueError`` if the model output does not contain a valid JSON
    object. Never returns hardcoded or pre-written fake responses.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Gemma 4 returned an empty response.")

    # Layer 1: strip <thought>…</thought> reasoning blocks
    cleaned = re.sub(r"<thought>.*?</thought>", "", raw_text, flags=re.DOTALL)

    # Layer 2: strip markdown code fences
    cleaned = cleaned.replace("```json", "").replace("```JSON", "").replace("```", "").strip()

    # Layer 3: locate outermost braces and parse
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
        raise ValueError(
            f"Gemma 4 response did not contain a JSON object. Raw output: {cleaned[:300]}"
        )

    candidate = cleaned[first_brace : last_brace + 1]
    try:
        parsed = json.loads(candidate)
        if not isinstance(parsed, dict):
            raise ValueError("Parsed JSON root is not an object.")
        return parsed
    except json.JSONDecodeError:
        # Attempt lightweight trailing-comma cleanup before raising
        repaired = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            parsed = json.loads(repaired)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as exc:
            logger.error("JSON decode failed after cleaning: %s | raw=%s", exc, candidate[:400])
            raise ValueError(f"Failed to parse JSON from Gemma 4 output: {exc}") from exc

    raise ValueError("Failed to parse JSON object from Gemma 4 output.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Gemma 4 Dual-Engine Multimodal Router
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Gemma4Router:
    """Route multimodal and text diligence prompts to live Gemma 4 endpoints.

    Supported providers
    -------------------
    ``"gemini_api"``
        Cloud-hosted Gemma 4 models via the Google GenAI SDK.
        Defaults to ``gemma-4-26b-a4b-it`` and cascades to ``gemma-4-31b-it``.

    ``"ollama"``
        Locally-hosted open-weight Gemma 4 model via the Ollama REST API.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key: Optional[str] = api_key or os.environ.get("GEMINI_API_KEY")

    async def generate(
        self,
        prompt: str,
        image_bytes: Optional[bytes] = None,
        mime_type: str = "image/jpeg",
        provider: str = "gemini_api",
        api_key_override: Optional[str] = None,
        ollama_model_override: Optional[str] = None,
    ) -> dict[str, Any]:
        """Run live inference against Gemma 4 and return the parsed JSON dict.

        Reads the API key from ``api_key_override`` first, then
        ``os.environ.get("GEMINI_API_KEY")``. Raises a ``RuntimeError`` if
        no key is found when using ``gemini_api`` or if inference fails.
        """
        load_dotenv(override=True)

        active_api_key = (
            api_key_override.strip()
            if api_key_override and api_key_override.strip()
            else (os.environ.get("GEMINI_API_KEY") or self._api_key or "").strip()
        )

        if provider == "gemini_api":
            if not active_api_key:
                raise RuntimeError("GEMINI_API_KEY is missing in .env")
            return await self._cloud_cascade(
                prompt=prompt,
                image_bytes=image_bytes,
                mime_type=mime_type,
                active_api_key=active_api_key,
            )

        if provider == "ollama":
            return await self._ollama(
                prompt=prompt,
                image_bytes=image_bytes,
                mime_type=mime_type,
                active_api_key=active_api_key,
                ollama_model_override=ollama_model_override,
            )

        raise ValueError(f"Unsupported inference provider: '{provider}'")

    # ── Gemini API cloud cascade ────────────────────────────────────────────
    async def _cloud_cascade(
        self,
        prompt: str,
        image_bytes: Optional[bytes],
        mime_type: str,
        active_api_key: str,
    ) -> dict[str, Any]:
        """Call Gemma 4 directly via ``google-genai`` without unsupported config flags."""
        if not active_api_key:
            raise RuntimeError("GEMINI_API_KEY is missing in .env")

        client = genai.Client(api_key=active_api_key)

        contents: list[Any] = []
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
        contents.append(prompt)

        # Build cascade list: default "gemma-4-26b-a4b-it", cascade to "gemma-4-31b-it"
        env_primary = os.environ.get("GEMMA_MODEL_ID", "gemma-4-26b-a4b-it").strip()
        env_fallbacks = os.environ.get("GEMMA_FALLBACK_MODELS", "").strip()

        cascade: list[str] = []
        if env_primary:
            cascade.append(env_primary)
        if env_fallbacks:
            for m in env_fallbacks.split(","):
                m_clean = m.strip()
                if m_clean and m_clean not in cascade:
                    cascade.append(m_clean)
        for default_m in _CLOUD_CASCADE:
            if default_m not in cascade:
                cascade.append(default_m)

        last_error: Optional[Exception] = None

        for model_id in cascade:
            try:
                start_t = time.time()
                # Call Gemma 4 directly without unsupported config parameters that trigger 400 errors
                response = client.models.generate_content(
                    model=model_id,  # Default: "gemma-4-26b-a4b-it", cascade to "gemma-4-31b-it"
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=_DEFAULT_TEMPERATURE,
                    ),
                )
                latency_ms = int((time.time() - start_t) * 1000)

                raw_text = response.text or ""
                result = extract_json_safely(raw_text)
                result["engine_used"] = f"gemini_api/{model_id}"
                result["model_id"] = model_id
                result["latency_ms"] = latency_ms

                logger.info(
                    "Gemma 4 cloud inference succeeded: model=%s latency=%dms",
                    model_id,
                    latency_ms,
                )
                return result

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Model %s failed (%s) — cascading to next Gemma 4 model.",
                    model_id,
                    exc,
                )

        raise RuntimeError(f"Gemma 4 inference failed across cascade {cascade}: {last_error}")

    # ── Local Ollama inference ──────────────────────────────────────────────
    async def _ollama(
        self,
        prompt: str,
        image_bytes: Optional[bytes],
        mime_type: str,
        active_api_key: str,
        ollama_model_override: Optional[str] = None,
    ) -> dict[str, Any]:
        """Call local Ollama instance and optionally cascade to Gemini API if unreachable."""
        ollama_url = os.environ.get("OLLAMA_URL", _DEFAULT_OLLAMA_URL)
        ollama_model = (
            ollama_model_override.strip()
            if ollama_model_override and ollama_model_override.strip()
            else os.environ.get("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)
        )
        keep_alive = os.environ.get("OLLAMA_KEEP_ALIVE", _DEFAULT_OLLAMA_KEEP_ALIVE)

        message: dict[str, Any] = {"role": "user", "content": prompt}
        if image_bytes:
            message["images"] = [base64.b64encode(image_bytes).decode("ascii")]

        payload = json.dumps(
            {
                "model": ollama_model,
                "messages": [message],
                "stream": False,
                "format": "json",
                "keep_alive": keep_alive,
                "options": {"temperature": _DEFAULT_TEMPERATURE},
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            ollama_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            start_t = time.time()
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            latency_ms = int((time.time() - start_t) * 1000)

            raw_text = body.get("message", {}).get("content", "")
            result = extract_json_safely(raw_text)
            result["engine_used"] = f"ollama/{ollama_model}"
            result["model_id"] = ollama_model
            result["latency_ms"] = latency_ms

            logger.info("Ollama inference succeeded: model=%s latency=%dms", ollama_model, latency_ms)
            return result

        except (urllib.error.URLError, OSError, ConnectionError) as exc:
            logger.warning("Local Ollama unreachable at %s (%s).", ollama_url, exc)
            if active_api_key:
                logger.info("Falling back from unreachable Ollama to Gemini API Gemma 4 cascade.")
                result = await self._cloud_cascade(
                    prompt=prompt,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                    active_api_key=active_api_key,
                )
                result["engine_used"] = f"{result['engine_used']} (ollama-fallback)"
                return result
            raise RuntimeError(
                f"Local Ollama server is unreachable at {ollama_url} and GEMINI_API_KEY is missing in .env."
            ) from exc

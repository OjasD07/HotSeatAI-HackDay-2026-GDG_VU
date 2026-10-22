"""
HotSeat AI — Gemma 4 Multimodal Inference Engine & Connection Diagnostics
=========================================================================

Supported Providers (Strictly Isolated — No Silent Cross-Provider Fallbacks)
----------------------------------------------------------------------------
  • "gemini_api" – Google GenAI SDK ("gemma-4-26b-a4b-it" → "gemma-4-31b-it")
  • "ollama"     – Local Ollama REST API (http://127.0.0.1:11434/api/chat)
  • "lmstudio"   – Local LM Studio OpenAI-compatible API (http://127.0.0.1:1234/v1/chat/completions)

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
_DEFAULT_OLLAMA_TAGS_URL: str = "http://127.0.0.1:11434/api/tags"
_DEFAULT_OLLAMA_MODEL: str = "gemma4:12b"
_DEFAULT_OLLAMA_KEEP_ALIVE: str = "30m"

_DEFAULT_LMSTUDIO_URL: str = "http://127.0.0.1:1234/v1/chat/completions"
_DEFAULT_LMSTUDIO_MODELS_URL: str = "http://127.0.0.1:1234/v1/models"
_DEFAULT_LMSTUDIO_MODEL: str = "gemma-4-12b-it"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  3-Layer JSON Extractor (Zero Canned Fallbacks)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def extract_json_safely(raw_text: str) -> dict[str, Any]:
    """Parse a JSON object from model output using a 3-layer cleaning pipeline.

    Layer 1 – Strip ``<thought>…</thought>`` reasoning blocks.
    Layer 2 – Strip markdown code fences (````json`` / `````).
    Layer 3 – Locate outermost ``{`` … ``}`` and parse with ``json.loads()``.

    Raises a ``ValueError`` if the model output does not contain a valid JSON
    object. Never returns hardcoded or pre-written fake responses.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Model returned an empty response.")

    # Layer 1: strip <thought>…</thought> reasoning blocks
    cleaned = re.sub(r"<thought>.*?</thought>", "", raw_text, flags=re.DOTALL)

    # Layer 2: strip markdown code fences
    cleaned = cleaned.replace("```json", "").replace("```JSON", "").replace("```", "").strip()

    # Layer 3: locate outermost braces and parse
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
        raise ValueError(
            f"Model response did not contain a JSON object. Raw output: {cleaned[:300]}"
        )

    candidate = cleaned[first_brace : last_brace + 1]
    try:
        parsed = json.loads(candidate)
        if not isinstance(parsed, dict):
            raise ValueError("Parsed JSON root is not an object.")
        return parsed
    except json.JSONDecodeError:
        repaired = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            parsed = json.loads(repaired)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as exc:
            logger.error("JSON decode failed after cleaning: %s | raw=%s", exc, candidate[:400])
            raise ValueError(f"Failed to parse JSON from model output: {exc}") from exc

    raise ValueError("Failed to parse JSON object from model output.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Gemma 4 Multi-Provider Router (Gemini API, Ollama, LM Studio)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Gemma4Router:
    """Route multimodal and text diligence prompts to live Gemma 4 endpoints.

    Each provider is strictly isolated:
      • ``"gemini_api"`` → Google Gemini API (Gemma 4 cloud cascade)
      • ``"ollama"``     → Local Ollama server ONLY (never falls back to Gemini API)
      • ``"lmstudio"``   → Local LM Studio server ONLY (never falls back to Gemini API)
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key: Optional[str] = api_key or os.environ.get("GEMINI_API_KEY")

    def _resolve_api_key(self, api_key_override: Optional[str] = None) -> str:
        load_dotenv(override=True)
        return (
            api_key_override.strip()
            if api_key_override and api_key_override.strip()
            else (os.environ.get("GEMINI_API_KEY") or self._api_key or "").strip()
        )

    async def generate(
        self,
        prompt: str,
        image_bytes: Optional[bytes] = None,
        mime_type: str = "image/jpeg",
        provider: str = "gemini_api",
        api_key_override: Optional[str] = None,
        ollama_model_override: Optional[str] = None,
    ) -> dict[str, Any]:
        """Run live inference against the selected provider and return parsed JSON."""
        active_api_key = self._resolve_api_key(api_key_override)

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
                ollama_model_override=ollama_model_override,
            )

        if provider == "lmstudio":
            return await self._lmstudio(
                prompt=prompt,
                image_bytes=image_bytes,
                mime_type=mime_type,
                model_override=ollama_model_override,
            )

        raise ValueError(f"Unsupported inference provider: '{provider}'")

    # ── Provider Connection & Latency Probe ─────────────────────────────────
    async def ping_provider(
        self,
        provider: str,
        api_key_override: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> dict[str, Any]:
        """Test connectivity and measure exact round-trip latency (ms) for a provider."""
        if provider == "gemini_api":
            active_api_key = self._resolve_api_key(api_key_override)
            if not active_api_key:
                return {
                    "provider": "gemini_api",
                    "ok": False,
                    "model_id": os.environ.get("GEMMA_MODEL_ID", "gemma-4-26b-a4b-it"),
                    "latency_ms": None,
                    "error": "GEMINI_API_KEY is missing in .env and no override key was provided.",
                }
            model_id = os.environ.get("GEMMA_MODEL_ID", "gemma-4-26b-a4b-it").strip() or "gemma-4-26b-a4b-it"
            try:
                client = genai.Client(api_key=active_api_key)
                start_t = time.time()
                response = client.models.generate_content(
                    model=model_id,
                    contents='Respond only with {"ok": true}',
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        max_output_tokens=16,
                    ),
                )
                latency_ms = int((time.time() - start_t) * 1000)
                _ = response.text
                return {
                    "provider": "gemini_api",
                    "ok": True,
                    "model_id": model_id,
                    "latency_ms": latency_ms,
                    "error": None,
                }
            except Exception as exc:
                return {
                    "provider": "gemini_api",
                    "ok": False,
                    "model_id": model_id,
                    "latency_ms": None,
                    "error": f"Gemini API connection error: {exc}",
                }

        if provider == "ollama":
            ollama_url = os.environ.get("OLLAMA_URL", _DEFAULT_OLLAMA_URL)
            base_host = ollama_url.split("/api/")[0] if "/api/" in ollama_url else "http://127.0.0.1:11434"
            tags_url = f"{base_host}/api/tags"
            ollama_model = (
                model_override.strip()
                if model_override and model_override.strip()
                else os.environ.get("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)
            )
            try:
                start_t = time.time()
                req = urllib.request.Request(tags_url, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                latency_ms = int((time.time() - start_t) * 1000)
                models = [m.get("name", "") for m in data.get("models", []) if isinstance(m, dict)]
                return {
                    "provider": "ollama",
                    "ok": True,
                    "model_id": ollama_model,
                    "available_models": models,
                    "endpoint": ollama_url,
                    "latency_ms": latency_ms,
                    "error": None,
                }
            except Exception as exc:
                return {
                    "provider": "ollama",
                    "ok": False,
                    "model_id": ollama_model,
                    "endpoint": ollama_url,
                    "latency_ms": None,
                    "error": f"Ollama unreachable at {ollama_url}: {exc}",
                }

        if provider == "lmstudio":
            lmstudio_url = os.environ.get("LMSTUDIO_URL", _DEFAULT_LMSTUDIO_URL)
            base_host = lmstudio_url.split("/v1/")[0] if "/v1/" in lmstudio_url else "http://127.0.0.1:1234"
            models_url = f"{base_host}/v1/models"
            lmstudio_model = (
                model_override.strip()
                if model_override and model_override.strip()
                else os.environ.get("LMSTUDIO_MODEL", _DEFAULT_LMSTUDIO_MODEL)
            )
            try:
                start_t = time.time()
                req = urllib.request.Request(models_url, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                latency_ms = int((time.time() - start_t) * 1000)
                models = [m.get("id", "") for m in data.get("data", []) if isinstance(m, dict)]
                active_model = models[0] if models and not model_override else lmstudio_model
                return {
                    "provider": "lmstudio",
                    "ok": True,
                    "model_id": active_model,
                    "available_models": models,
                    "endpoint": lmstudio_url,
                    "latency_ms": latency_ms,
                    "error": None,
                }
            except Exception as exc:
                return {
                    "provider": "lmstudio",
                    "ok": False,
                    "model_id": lmstudio_model,
                    "endpoint": lmstudio_url,
                    "latency_ms": None,
                    "error": f"LM Studio unreachable at {lmstudio_url}: {exc}",
                }

        return {
            "provider": provider,
            "ok": False,
            "model_id": "unknown",
            "latency_ms": None,
            "error": f"Unknown provider '{provider}'",
        }

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

        raise RuntimeError(f"Gemini API connection/inference failed across {cascade}: {last_error}")

    # ── Local Ollama inference (NO cloud fallback) ──────────────────────────
    async def _ollama(
        self,
        prompt: str,
        image_bytes: Optional[bytes],
        mime_type: str,
        ollama_model_override: Optional[str] = None,
    ) -> dict[str, Any]:
        """Call local Ollama instance directly. Never falls back to Gemini API."""
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

        except urllib.error.HTTPError as exc:
            err_body = ""
            try:
                err_body = exc.read().decode("utf-8")[:300]
            except Exception:
                pass
            raise RuntimeError(
                f"Ollama HTTP {exc.code} error at {ollama_url} (model '{ollama_model}'): {err_body or exc.reason}"
            ) from exc
        except (urllib.error.URLError, OSError, ConnectionError) as exc:
            raise RuntimeError(
                f"Cannot connect to local Ollama at {ollama_url} (model '{ollama_model}'): {exc}. "
                "Ensure 'ollama serve' is running locally."
            ) from exc

    # ── Local LM Studio inference (OpenAI-compatible /v1/chat/completions) ──
    async def _lmstudio(
        self,
        prompt: str,
        image_bytes: Optional[bytes],
        mime_type: str,
        model_override: Optional[str] = None,
    ) -> dict[str, Any]:
        """Call local LM Studio server directly. Never falls back to Gemini API."""
        lmstudio_url = os.environ.get("LMSTUDIO_URL", _DEFAULT_LMSTUDIO_URL)
        lmstudio_model = (
            model_override.strip()
            if model_override and model_override.strip()
            else os.environ.get("LMSTUDIO_MODEL", _DEFAULT_LMSTUDIO_MODEL)
        )

        if image_bytes:
            b64_img = base64.b64encode(image_bytes).decode("ascii")
            content: Any = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{b64_img}"},
                },
                {"type": "text", "text": prompt},
            ]
        else:
            content = prompt

        payload = json.dumps(
            {
                "model": lmstudio_model,
                "messages": [{"role": "user", "content": content}],
                "temperature": _DEFAULT_TEMPERATURE,
                "stream": False,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            lmstudio_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            start_t = time.time()
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            latency_ms = int((time.time() - start_t) * 1000)

            choices = body.get("choices", [])
            raw_text = (
                choices[0].get("message", {}).get("content", "")
                if choices and isinstance(choices[0], dict)
                else ""
            )
            used_model = body.get("model") or lmstudio_model
            result = extract_json_safely(raw_text)
            result["engine_used"] = f"lmstudio/{used_model}"
            result["model_id"] = used_model
            result["latency_ms"] = latency_ms

            logger.info("LM Studio inference succeeded: model=%s latency=%dms", used_model, latency_ms)
            return result

        except urllib.error.HTTPError as exc:
            err_body = ""
            try:
                err_body = exc.read().decode("utf-8")[:300]
            except Exception:
                pass
            raise RuntimeError(
                f"LM Studio HTTP {exc.code} error at {lmstudio_url} (model '{lmstudio_model}'): {err_body or exc.reason}"
            ) from exc
        except (urllib.error.URLError, OSError, ConnectionError) as exc:
            raise RuntimeError(
                f"Cannot connect to local LM Studio server at {lmstudio_url} (model '{lmstudio_model}'): {exc}. "
                "Ensure LM Studio Local Server is running on port 1234."
            ) from exc

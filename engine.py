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

import asyncio
import base64
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from copy import deepcopy
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

# ─── Gemma payload / timeout bounds ─────────────────────────────────────────
# Keep the final `contents` payload bounded and leave enough of the Cloudflare
# 100s gateway window for the fallback model to run after a primary failure.
_MAX_GEMMA_HISTORY_TURNS: int = 10
_GEMMA_TOTAL_BUDGET_SECONDS: float = 92.0
_GEMMA_REQUEST_TIMEOUT_SECONDS: float = 70.0
_GEMMA_MIN_ATTEMPT_SECONDS: float = 8.0
_GEMMA_RETRY_DELAY_SECONDS: float = 0.35
_GEMMA_FAST_RETRY_THRESHOLD_SECONDS: float = 15.0

_DEFAULT_OLLAMA_HOST: str = "http://127.0.0.1:11434"
_DEFAULT_OLLAMA_URL: str = "http://127.0.0.1:11434/api/chat"
_DEFAULT_OLLAMA_TAGS_URL: str = "http://127.0.0.1:11434/api/tags"
_DEFAULT_OLLAMA_MODEL: str = "gemma4:12b"
_DEFAULT_OLLAMA_KEEP_ALIVE: str = "30m"

_DEFAULT_LMSTUDIO_URL: str = "http://127.0.0.1:1234/v1/chat/completions"
_DEFAULT_LMSTUDIO_MODELS_URL: str = "http://127.0.0.1:1234/v1/models"
_DEFAULT_LMSTUDIO_MODEL: str = "gemma-4-12b-it"


def _clean_env(key: str, default: str = "") -> str:
    """Read an environment variable with quote-stripping and `or default` fallback."""
    raw = os.environ.get(key) or default
    cleaned = str(raw).strip().strip("\"'").strip()
    return cleaned or default


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Gemma 4 Conversation Sanitizer (Gemini `v1beta` `contents` contract)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Gemma endpoints on the Generative Language API accept only `user` and `model`
# roles, reject top-level `systemInstruction`, and reject `tools` / `toolConfig`
# / `responseMimeType`. The helpers below convert any dialogue history into a
# strictly alternating `user` → `model` sequence before every request.
_GEMMA_SYSTEM_ROLES = {"system", "developer"}
_GEMMA_FORBIDDEN_CONFIG_KEYS = {
    "system_instruction",
    "systemInstruction",
    "tools",
    "tool_config",
    "toolConfig",
    "response_mime_type",
    "responseMimeType",
    "response_schema",
    "responseSchema",
}
_TRANSIENT_GEMMA_MARKERS = (
    "internal error",
    "internal",
    "unavailable",
    "overloaded",
    "deadline exceeded",
    "timed out",
    "timeout",
    "try again",
    "http 500",
    "http 502",
    "http 503",
    "http 504",
)


def _is_transient_gemma_error(exc: BaseException) -> bool:
    """Detect transient Gemini 5xx/overload failures worth a single retry."""
    text = str(exc).lower()
    return any(marker in text for marker in _TRANSIENT_GEMMA_MARKERS)


def _has_valid_image_payload(image_bytes: Any) -> bool:
    """Return True only for a non-empty, actually attachable image payload."""
    if image_bytes is None:
        return False
    if isinstance(image_bytes, str):
        return bool(image_bytes.strip())
    if isinstance(image_bytes, (bytes, bytearray, memoryview)):
        return len(image_bytes) > 0
    if isinstance(image_bytes, (list, tuple, dict)):
        return bool(image_bytes)
    return False


def _normalise_inline_data(inline: Any) -> Optional[dict[str, Any]]:
    """Return a valid inline-data part, or ``None`` for empty/malformed payloads.

    This is the single guard that prevents null, empty, or malformed image
    objects from ever reaching the Gemini request body.
    """
    if inline is None:
        return None

    if isinstance(inline, dict):
        data = inline.get("data")
        mime_type = inline.get("mime_type") or inline.get("mimeType")
    else:
        data = getattr(inline, "data", None)
        mime_type = getattr(inline, "mime_type", None) or getattr(
            inline, "mimeType", None
        )

    if isinstance(data, str):
        if not data.strip():
            return None
    elif isinstance(data, (bytes, bytearray, memoryview)):
        if len(data) == 0:
            return None
        data = bytes(data)
    else:
        return None

    mime = str(mime_type or "image/jpeg").strip()
    if not mime.lower().startswith("image/"):
        mime = "image/jpeg"
    return {"mime_type": mime, "data": data}


def _normalise_gemma_role(role: Any) -> str:
    """Map every provider role to the only two roles Gemma accepts."""
    value = str(role or "").strip().lower()
    if value in {"assistant", "model"}:
        return "model"
    return "user"


def _is_failed_gemma_turn(message: Any) -> bool:
    """Return True for error/empty structural turns that must never be replayed."""
    if not isinstance(message, dict):
        return False
    if message.get("error"):
        return True
    if message.get("failed") is True:
        return True
    if message.get("ok") is False:
        return True
    role = str(message.get("role") or "").strip().lower()
    return role in {"error", "tool", "function"}


def _extract_gemma_parts(
    message: Any, include_media: bool = True
) -> list[dict[str, Any]]:
    """Extract text/inline-data parts from OpenAI, Gemini, or SDK message shapes.

    ``include_media`` is set to ``False`` for historical turns so a base64 slide
    image is only ever attached to the current (final) user turn.
    """
    if message is None:
        return []

    if isinstance(message, str):
        text = message.strip()
        return [{"text": text}] if text else []

    if isinstance(message, dict):
        raw_parts = message.get("parts")
        if raw_parts is None:
            raw_parts = message.get("content")
        if raw_parts is None:
            raw_parts = message.get("text")
    elif isinstance(message, types.Content):
        raw_parts = list(message.parts or [])
    else:
        raw_parts = getattr(message, "parts", None)
        if raw_parts is None:
            raw_parts = getattr(message, "content", None)
        if raw_parts is None:
            raw_parts = [message]

    if raw_parts is None:
        return []
    if isinstance(raw_parts, (str, bytes)) or not isinstance(raw_parts, (list, tuple)):
        raw_parts = [raw_parts]

    parts: list[dict[str, Any]] = []
    for item in raw_parts:
        if item is None:
            continue
        if isinstance(item, str):
            text = item.strip()
            if text:
                parts.append({"text": text})
            continue
        if isinstance(item, dict):
            text = item.get("text")
            if text is not None and str(text).strip():
                parts.append({"text": str(text).strip()})
            if include_media:
                inline = _normalise_inline_data(
                    item.get("inline_data") or item.get("inlineData")
                )
                if inline is not None:
                    parts.append({"inline_data": inline})
            continue

        # google.genai.types.Part and compatible SDK objects
        text = getattr(item, "text", None)
        if text is not None and str(text).strip():
            parts.append({"text": str(text).strip()})
        if include_media:
            inline = _normalise_inline_data(getattr(item, "inline_data", None))
            if inline is not None:
                parts.append({"inline_data": inline})

    return parts


def _merge_gemma_parts(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge adjacent turns while keeping multimodal parts before text parts."""
    combined = [part for group in groups for part in group]
    media = [part for part in combined if part.get("inline_data")]
    others = [
        part for part in combined if not part.get("inline_data") and not part.get("text")
    ]
    texts = [
        str(part["text"]).strip()
        for part in combined
        if part.get("text") and str(part["text"]).strip()
    ]
    merged: list[dict[str, Any]] = []
    merged.extend(media)
    merged.extend(others)
    if texts:
        merged.append({"text": "\n\n".join(texts)})
    return merged


def _sanitize_gemini_contents(
    messages: Optional[list[Any]] = None,
    system_prompt: str = "",
    include_media: bool = False,
) -> list[dict[str, Any]]:
    """Normalise any message history into Gemma's strict `user`/`model` schema.

    * Deep-clones the incoming history so the live ``SESSION_STATE`` record is
      never mutated while folding or merging turns.
    * Remaps ``assistant`` → ``model``.
    * Folds ``system`` / ``developer`` messages into the first ``user`` turn.
    * Drops failed, error, empty, tool, and function turns.
    * Merges consecutive turns that resolve to the same role.
    * Caps history to the most recent ``_MAX_GEMMA_HISTORY_TURNS`` turns.
    * Guarantees the sanitized sequence starts with a ``user`` turn.

    ``include_media`` defaults to ``False`` so inline image data from earlier
    turns is stripped; only the caller's current user turn may carry a slide
    image. The caller appends the current user turn, which guarantees the final
    payload also ends with the latest ``user`` turn.
    """
    turns: list[dict[str, Any]] = []
    system_chunks: list[str] = []

    if messages is None:
        message_list: list[Any] = []
    elif isinstance(messages, (str, dict)) or not isinstance(
        messages, (list, tuple)
    ):
        message_list = [messages]
    else:
        message_list = list(messages)

    # Never mutate the caller's live session history.
    try:
        message_list = deepcopy(message_list)
    except Exception:  # pragma: no cover - exotic SDK objects
        message_list = list(message_list)

    if system_prompt and str(system_prompt).strip():
        system_chunks.append(str(system_prompt).strip())

    for message in message_list:
        if _is_failed_gemma_turn(message):
            continue

        role_raw = (
            message.get("role")
            if isinstance(message, dict)
            else getattr(message, "role", "user")
        )
        role_key = str(role_raw or "user").strip().lower()

        if role_key in _GEMMA_SYSTEM_ROLES:
            system_text = "\n\n".join(
                str(part["text"]).strip()
                for part in _extract_gemma_parts(message, include_media=include_media)
                if part.get("text")
            ).strip()
            if system_text:
                system_chunks.append(system_text)
            continue

        parts = _extract_gemma_parts(message, include_media=include_media)
        if not parts:
            continue

        role = _normalise_gemma_role(role_raw)
        if turns and turns[-1]["role"] == role:
            turns[-1]["parts"] = _merge_gemma_parts(turns[-1]["parts"], parts)
        else:
            turns.append({"role": role, "parts": parts})

    # Bounded sliding window of the most recent valid turns. Drop a leading
    # `model` turn so the payload still starts with `user`.
    if len(turns) > _MAX_GEMMA_HISTORY_TURNS:
        turns = turns[-_MAX_GEMMA_HISTORY_TURNS:]
    while turns and turns[0]["role"] != "user":
        turns.pop(0)

    system_text = "\n\n".join(chunk for chunk in system_chunks if chunk).strip()
    if system_text:
        first_user = next((turn for turn in turns if turn["role"] == "user"), None)
        if first_user is not None:
            first_user["parts"] = _merge_gemma_parts(
                [{"text": system_text}], first_user["parts"]
            )
        else:
            turns.insert(0, {"role": "user", "parts": [{"text": system_text}]})

    # Gemma requires the first conversational turn to be `user`.
    if turns and turns[0]["role"] != "user":
        turns.insert(
            0,
            {
                "role": "user",
                "parts": [
                    {
                        "text": system_text
                        or "Continue the institutional diligence session from the prior context."
                    }
                ],
            },
        )

    return turns


def _build_gemma_contents(
    history: Optional[list[Any]],
    prompt: str,
    image_bytes: Optional[bytes],
    mime_type: str,
) -> list[dict[str, Any]]:
    """Build a sanitized multi-turn payload ending with the current user turn.

    Historical turns are stripped of inline media and capped to the most recent
    valid turns. Only the current turn may carry the slide image, and only when
    the payload is genuinely non-empty (Turn 0 text-only chat stays text-only).
    """
    turns = _sanitize_gemini_contents(history, include_media=False)

    current_parts: list[dict[str, Any]] = []
    image_payload = (
        _normalise_inline_data({"mime_type": mime_type, "data": image_bytes})
        if _has_valid_image_payload(image_bytes)
        else None
    )
    if image_payload is not None:
        current_parts.append({"inline_data": image_payload})
    if prompt and str(prompt).strip():
        current_parts.append({"text": str(prompt)})

    if current_parts:
        if turns and turns[-1]["role"] == "user":
            turns[-1]["parts"] = _merge_gemma_parts(turns[-1]["parts"], current_parts)
        else:
            turns.append({"role": "user", "parts": current_parts})

    # Keep the full request bounded even after appending the current turn.
    if len(turns) > _MAX_GEMMA_HISTORY_TURNS:
        turns = turns[-_MAX_GEMMA_HISTORY_TURNS:]
    while turns and turns[0]["role"] != "user":
        turns.pop(0)

    # Defensive: historical turns can never carry media (only the final turn).
    for turn in turns[:-1]:
        turn["parts"] = [part for part in turn["parts"] if not part.get("inline_data")]

    if turns and turns[0]["role"] != "user":
        turns.insert(
            0,
            {
                "role": "user",
                "parts": [
                    {"text": "Continue the institutional diligence session from the prior context."}
                ],
            },
        )
    if turns and turns[-1]["role"] != "user":
        turns.append(
            {
                "role": "user",
                "parts": [
                    {"text": "Provide your next diligence inquiry based on the record above."}
                ],
            }
        )

    return turns


def _to_genai_contents(turns: list[dict[str, Any]]) -> list[types.Content]:
    """Convert sanitized turn dictionaries into typed `google-genai` contents."""
    contents: list[types.Content] = []
    for turn in turns:
        parts: list[types.Part] = []
        for part in turn.get("parts", []):
            if "inline_data" in part:
                inline = _normalise_inline_data(part.get("inline_data"))
                if inline is None:
                    continue
                data = inline["data"]
                if isinstance(data, str):
                    try:
                        data = base64.b64decode(data)
                    except Exception:
                        data = b""
                if data:
                    parts.append(
                        types.Part.from_bytes(
                            data=data,
                            mime_type=inline["mime_type"],
                        )
                    )
                continue
            if part.get("text"):
                parts.append(types.Part(text=str(part["text"])))
        if parts:
            contents.append(types.Content(role=turn["role"], parts=parts))
    return contents


def _session_history_to_messages(history: Optional[list[Any]]) -> list[dict[str, Any]]:
    """Convert stored session turn records into sanitizer-ready chat messages."""
    messages: list[dict[str, Any]] = []
    for turn in history or []:
        if not isinstance(turn, dict):
            continue
        user_message = str(turn.get("user_message") or "").strip()
        vc_response = str(turn.get("vc_spoken_response") or "").strip()
        if user_message:
            messages.append({"role": "user", "content": user_message})
        if vc_response:
            messages.append({"role": "assistant", "content": vc_response})
    return messages


def _gemma_generation_config(
    overrides: Optional[dict[str, Any]] = None,
) -> types.GenerateContentConfig:
    """Build a Gemma-safe generation config.

    Gemma endpoints reject `systemInstruction`, `tools`, `toolConfig`, and
    `responseMimeType`; any such keys supplied by a caller are removed here.
    """
    safe = dict(overrides or {})
    for key in list(safe):
        if key in _GEMMA_FORBIDDEN_CONFIG_KEYS:
            safe.pop(key, None)
    safe.setdefault("temperature", _DEFAULT_TEMPERATURE)
    return types.GenerateContentConfig(**safe)


def _gemma_timeout_config(attempt_timeout: float) -> types.GenerateContentConfig:
    """Build a Gemma config with SDK retries disabled and a hard HTTP timeout.

    The per-request bounds only apply the ``http_options`` override when the
    installed ``google-genai`` version exposes it; the surrounding
    ``asyncio.wait_for`` remains the authoritative outer bound.
    """
    http_options_cls = getattr(types, "HttpOptions", None)
    retry_options_cls = getattr(types, "HttpRetryOptions", None)
    if http_options_cls is not None:
        http_kwargs: dict[str, Any] = {"timeout": int(attempt_timeout * 1000)}
        if retry_options_cls is not None:
            http_kwargs["retry_options"] = retry_options_cls(attempts=1)
        try:
            return _gemma_generation_config(
                {"http_options": http_options_cls(**http_kwargs)}
            )
        except Exception:  # pragma: no cover - older SDK without http_options
            logger.debug("google-genai version does not accept http_options.")
    return _gemma_generation_config()


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
        self._api_key: Optional[str] = api_key or _clean_env("GEMINI_API_KEY", "")

    def _resolve_api_key(self, api_key_override: Optional[str] = None) -> str:
        load_dotenv(override=True)
        override_clean = str(api_key_override or "").strip().strip("\"'").strip()
        return override_clean or _clean_env("GEMINI_API_KEY", "") or (self._api_key or "").strip()

    async def generate(
        self,
        prompt: str,
        image_bytes: Optional[bytes] = None,
        mime_type: str = "image/jpeg",
        provider: str = "gemini_api",
        api_key_override: Optional[str] = None,
        ollama_model_override: Optional[str] = None,
        history: Optional[list[Any]] = None,
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
                history=history,
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
            model_id = _clean_env("GEMMA_MODEL_ID", "gemma-4-26b-a4b-it")
            if not active_api_key:
                return {
                    "provider": "gemini_api",
                    "ok": False,
                    "model_id": model_id,
                    "latency_ms": None,
                    "error": "GEMINI_API_KEY is missing in .env and no override key was provided.",
                }
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
            ollama_host = _clean_env("OLLAMA_HOST", _DEFAULT_OLLAMA_HOST)
            ollama_url = _clean_env("OLLAMA_URL", f"{ollama_host.rstrip('/')}/api/chat")
            base_host = ollama_url.split("/api/")[0] if "/api/" in ollama_url else ollama_host.rstrip("/")
            tags_url = f"{base_host}/api/tags"
            ollama_model = (
                model_override.strip()
                if model_override and model_override.strip()
                else _clean_env("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)
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
            lmstudio_url = _clean_env("LMSTUDIO_URL", _DEFAULT_LMSTUDIO_URL)
            base_host = lmstudio_url.split("/v1/")[0] if "/v1/" in lmstudio_url else "http://127.0.0.1:1234"
            models_url = f"{base_host}/v1/models"
            lmstudio_model = (
                model_override.strip()
                if model_override and model_override.strip()
                else _clean_env("LMSTUDIO_MODEL", _DEFAULT_LMSTUDIO_MODEL)
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
        history: Optional[list[Any]] = None,
    ) -> dict[str, Any]:
        """Call Gemma 4 directly via ``google-genai`` without unsupported config flags.

        Multi-turn history is sanitized to Gemma's strict ``user``/``model``
        contract before the current multimodal user turn is appended.
        """
        if not active_api_key:
            raise RuntimeError("GEMINI_API_KEY is missing in .env")

        client = genai.Client(api_key=active_api_key)

        history_messages = _session_history_to_messages(history)
        sanitized_turns = _build_gemma_contents(
            history_messages,
            prompt,
            image_bytes,
            mime_type,
        )
        contents = _to_genai_contents(sanitized_turns)

        env_primary = _clean_env("GEMMA_MODEL_ID", "gemma-4-26b-a4b-it")
        env_fallbacks = (
            _clean_env("GEMMA_FALLBACK_MODELS", "")
            or _clean_env("GEMMA_FALLBACK_MODEL", "")
            or "gemma-4-26b-a4b-it,gemma-4-31b-it,gemma-3-27b-it"
        )

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
        deadline = time.monotonic() + _GEMMA_TOTAL_BUDGET_SECONDS

        for model_id in cascade:
            for attempt in range(2):
                remaining = deadline - time.monotonic()
                if remaining < _GEMMA_MIN_ATTEMPT_SECONDS:
                    logger.warning(
                        "Gemma timeout budget exhausted before %s attempt %d; stopping cascade.",
                        model_id,
                        attempt + 1,
                    )
                    break

                # Leave at least a minimum window for the fallback model.
                attempt_timeout = min(
                    _GEMMA_REQUEST_TIMEOUT_SECONDS,
                    max(
                        _GEMMA_MIN_ATTEMPT_SECONDS,
                        remaining - _GEMMA_MIN_ATTEMPT_SECONDS,
                    ),
                )
                attempt_started = time.monotonic()

                try:
                    # Gemma rejects systemInstruction, tools, toolConfig, and
                    # responseMimeType; the timeout config strips them all,
                    # disables SDK retries, and applies a hard HTTP timeout.
                    config = _gemma_timeout_config(attempt_timeout)
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            client.models.generate_content,
                            model=model_id,  # Default: "gemma-4-26b-a4b-it", cascade to "gemma-4-31b-it"
                            contents=contents,
                            config=config,
                        ),
                        timeout=attempt_timeout,
                    )
                    latency_ms = int((time.monotonic() - attempt_started) * 1000)

                    raw_text = response.text or ""
                    result = extract_json_safely(raw_text)
                    result["engine_used"] = f"gemini_api/{model_id}"
                    result["model_id"] = model_id
                    result["latency_ms"] = latency_ms

                    logger.info(
                        "Gemma 4 cloud inference succeeded: model=%s latency=%dms turns=%d",
                        model_id,
                        latency_ms,
                        len(contents),
                    )
                    return result

                except Exception as exc:
                    elapsed = time.monotonic() - attempt_started
                    if isinstance(exc, asyncio.TimeoutError):
                        exc = TimeoutError(
                            f"Gemma request timed out after {elapsed * 1000:.0f}ms "
                            f"(limit {attempt_timeout * 1000:.0f}ms)"
                        )
                    last_error = exc

                    # Retry only fast 5xx/INTERNAL failures. A slow timeout has
                    # already consumed the window the fallback model needs.
                    if (
                        attempt == 0
                        and elapsed <= _GEMMA_FAST_RETRY_THRESHOLD_SECONDS
                        and _is_transient_gemma_error(exc)
                        and deadline - time.monotonic() >= _GEMMA_MIN_ATTEMPT_SECONDS
                    ):
                        logger.warning(
                            "Transient Gemma failure on %s (%s); retrying once in %.0fms.",
                            model_id,
                            exc,
                            _GEMMA_RETRY_DELAY_SECONDS * 1000,
                        )
                        await asyncio.sleep(_GEMMA_RETRY_DELAY_SECONDS)
                        continue

                    logger.warning(
                        "Model %s failed (%s) — cascading to next Gemma 4 model.",
                        model_id,
                        exc,
                    )
                    break

        raise RuntimeError(
            f"Gemini API connection/inference failed across {cascade}: {last_error}"
        )

    # ── Local Ollama inference (NO cloud fallback) ──────────────────────────
    async def _ollama(
        self,
        prompt: str,
        image_bytes: Optional[bytes],
        mime_type: str,
        ollama_model_override: Optional[str] = None,
    ) -> dict[str, Any]:
        """Call local Ollama instance directly. Never falls back to Gemini API."""
        ollama_host = _clean_env("OLLAMA_HOST", _DEFAULT_OLLAMA_HOST)
        ollama_url = _clean_env("OLLAMA_URL", f"{ollama_host.rstrip('/')}/api/chat")
        ollama_model = (
            ollama_model_override.strip()
            if ollama_model_override and ollama_model_override.strip()
            else _clean_env("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)
        )
        keep_alive = _clean_env("OLLAMA_KEEP_ALIVE", _DEFAULT_OLLAMA_KEEP_ALIVE)

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
        lmstudio_url = _clean_env("LMSTUDIO_URL", _DEFAULT_LMSTUDIO_URL)
        lmstudio_model = (
            model_override.strip()
            if model_override and model_override.strip()
            else _clean_env("LMSTUDIO_MODEL", _DEFAULT_LMSTUDIO_MODEL)
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

"""
HotSeat AI — Institutional Venture Capital Diligence Backend
============================================================

Endpoints
---------
GET  /health           → service health probe
GET  /api/state        → current session snapshot
POST /api/reset        → reset session to clean institutional state
POST /api/interrogate  → live Gemma 4 multimodal pitch-deck interrogation turn
GET  /api/skill        → compile & return SKILL.md from live session learnings
POST /api/skill        → compile, write to disk, & return SKILL.md
POST /api/verdict      → live Investment Committee memorandum & term-sheet verdict

Copyright 2026  HotSeat AI Contributors
SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv(override=True)

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from engine import Gemma4Router

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-22s  %(levelname)-5s  %(message)s",
)
logger = logging.getLogger("hotseat.app")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Institutional Committee Personas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERSONAS: dict[str, dict[str, str]] = {
    "sand_hill_vc": {
        "title": "Managing Partner (Venture & Growth)",
        "instructions": (
            "Focus on thesis consistency, market sizing methodology, distribution velocity, "
            "structural defensibility, and venture-scale capital efficiency."
        ),
    },
    "ruthless_cfo": {
        "title": "Chief Financial Officer (Unit Economics & Audit)",
        "instructions": (
            "Focus on unit economics, gross and contribution margins, CAC payback, "
            "burn multiple, working capital cycles, and cross-slide financial reconciliation."
        ),
    },
    "enterprise_buyer": {
        "title": "Enterprise Procurement Lead (Security & ROI)",
        "instructions": (
            "Focus on enterprise deployment readiness, regulatory compliance, security architecture, "
            "switching costs, and auditable customer ROI."
        ),
    },
    "demo_day_judge": {
        "title": "Technical Diligence Partner (Architecture & Defensibility)",
        "instructions": (
            "Focus on proprietary technical architecture, clinical or engineering validation, "
            "scalability bottlenecks, and unit compute/production costs."
        ),
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  In-Memory Session State (Zero Pre-Seeded Claims)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_INITIAL_STATE: dict[str, Any] = {
    "conviction_score": 50,
    "discrepancy_count": 0,
    "evasion_strikes": 0,
    "detected_industry": "—",
    "business_model": "—",
    "last_vc_question": "",
    "claim_ledger": [],
    "history": [],
    "skill_rules": [],
    "contradictions_logged": [],
}

SESSION_STATE: dict[str, Any] = deepcopy(_INITIAL_STATE)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FastAPI Application
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app = FastAPI(
    title="HotSeat AI — Institutional Venture Diligence Terminal",
    version="1.0.0",
    description=(
        "Multimodal Venture Capital pitch-deck diligence engine, cross-slide "
        "contradiction auditor, and self-improving SKILL.md guardrail compiler "
        "powered by live Gemma 4 inference."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = Gemma4Router()
_MAX_LEDGER_IN_PROMPT = 25

_SKILL_DIR = Path(".claude/skills/pitch-defense")
_SKILL_PATH = _SKILL_DIR / "SKILL.md"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Prompt Builders (100% Dynamic — Zero Canned Responses)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _build_interrogation_prompt(
    persona_key: str,
    slide_number: int,
    user_message: str,
    last_vc_question: str,
    claim_ledger: list[dict],
    has_image: bool,
    evasion_hint: bool,
) -> str:
    """Build the live multimodal institutional diligence prompt for Gemma 4."""
    recent_claims = claim_ledger[-_MAX_LEDGER_IN_PROMPT:]
    claim_ledger_json = json.dumps(recent_claims, indent=2) if recent_claims else "[]"

    prompt = f"""You are a Senior Managing Partner at an institutional Venture Capital firm conducting formal due diligence on a startup pitch.
Maintain a composed, analytical, professional, and rigorous tone at all times. Never use slang, internet memes, "roast" language, or casual insults.

INPUTS PROVIDED TO YOU:
1. Attached Slide Image: The presentation slide currently displayed on screen by the founder.
2. Founder's Verbal/Written Statement: "{user_message}"
3. Prior Session Claim Ledger (from earlier slides/turns in this session only): {claim_ledger_json}
4. Previous Inquiry Asked by Partner: "{last_vc_question}"

YOUR ANALYTICAL MANDATE:
1. INSPECT THE SLIDE IMAGE DIRECTLY: Read the exact title, sector, metrics, charts, and claims shown visually on the attached slide image.
2. CROSS-CHECK VISUAL SLIDE VS. FOUNDER STATEMENT:
   - Does the founder's statement ("{user_message}") contradict the visual slide currently on screen? (For example, if the slide on screen visually depicts a Healthcare/MedTech product, and the founder states "We are a finance company", immediately flag `contradiction_detected: true` and formally ask the founder to explain why their verbal statement contradicts the sector and product shown on their slide).
   - Does the current slide or statement contradict an earlier entry in the Prior Session Claim Ledger?
   - If `last_vc_question` was asked, did the founder provide a substantive, direct answer, or did they evade the question?
3. FORMULATE AN INSTITUTIONAL DILIGENCE INQUIRY:
   - Address the founder formally and respectfully in 2 to 3 concise sentences (under 55 words).
   - Cite the exact figures, terminology, or visual elements from their slide and contrast them with their statement.
   - Probe unit economics, market sizing methodology, regulatory pathways, distribution economics, or thesis consistency.

Return ONLY a valid JSON object with this exact structure:
{{
  "detected_industry": "Inferred strictly from current slide & statement",
  "business_model": "Inferred strictly from current slide & statement",
  "visual_claims_extracted": ["Exact metric or claim read from the slide image"],
  "evaluation": {{
    "answered_previous_question": true,
    "evasion_detected": false,
    "contradiction_detected": false,
    "contradiction_detail": "Formal explanation of the discrepancy between the visual slide, current statement, or prior slide (empty string if none)",
    "conviction_delta": 5,
    "inquiry_category": "THESIS INCONSISTENCY | UNIT ECONOMICS DILIGENCE | MARKET & GTM VALIDATION | REGULATORY & MOAT REVIEW | UNANSWERED INQUIRY"
  }},
  "vc_spoken_response": "Formal, executive 2-3 sentence question to the founder.",
  "new_skill_guardrail": "Formal due-diligence checklist item to append to SKILL.md"
}}"""

    return prompt


def _build_verdict_prompt() -> str:
    """Build the Investment Committee memorandum prompt from live session history."""
    score = SESSION_STATE["conviction_score"]
    industry = SESSION_STATE["detected_industry"]
    biz_model = SESSION_STATE["business_model"]
    strikes = SESSION_STATE["discrepancy_count"]
    ledger = SESSION_STATE["claim_ledger"][-_MAX_LEDGER_IN_PROMPT:]
    history = SESSION_STATE["history"]
    contradictions = SESSION_STATE["contradictions_logged"]

    if score >= 68:
        decision_band = "PROCEED TO TERM SHEET"
    elif score >= 45:
        decision_band = "ADVANCE TO SECOND-STAGE DILIGENCE"
    else:
        decision_band = "DECLINE TO ADVANCE"

    history_json = json.dumps(history, indent=2) if history else "[]"
    ledger_json = json.dumps(ledger, indent=2) if ledger else "[]"
    contradictions_json = json.dumps(contradictions, indent=2) if contradictions else "[]"

    prompt = f"""You are the Voting Investment Committee of a Tier-1 institutional venture capital firm.
Maintain a composed, analytical, professional, and rigorous tone at all times.

Synthesize a formal Investment Committee Evaluation Memorandum from the live diligence record below. Base every score, strength, risk, and revision item strictly on the actual claims and interrogation transcript recorded in this session.

SESSION DILIGENCE RECORD:
- Sector / Vertical: {industry}
- Business Model: {biz_model}
- Final Conviction Index: {score}/100
- Unresolved Discrepancy Flags: {strikes}
- Policy Decision Band: {decision_band}
- Logged Material Discrepancies:
{contradictions_json}
- Verified Session Claim Ledger:
{ledger_json}
- Diligence Transcript:
{history_json}

Return ONLY a single valid JSON object (no markdown fences, no commentary outside the JSON) with these exact keys:
1. "decision": Must be "{decision_band}" (one of "PROCEED TO TERM SHEET", "ADVANCE TO SECOND-STAGE DILIGENCE", or "DECLINE TO ADVANCE").
2. "headline_offer_or_reason": A formal 1-sentence executive summary of the IC decision citing specific metrics or findings from the session.
3. "scores": An object with 4 integer keys (each 0 to 100):
   - "market_timing"
   - "unit_economics"
   - "defensibility_moat"
   - "founder_conviction"
4. "biggest_strength": 1 formal sentence citing the most compelling quantitative or strategic evidence established during the session.
5. "fatal_flaw": 1 formal sentence citing the most critical discrepancy, unit-economics vulnerability, or unanswered diligence risk from the session.
6. "mandatory_deck_fixes": Array of 3 specific, actionable deck revisions required prior to advancing."""

    return prompt


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Self-Improving Agent Skill Compiler  (/api/skill)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _compile_skill_md() -> str:
    """Compile live session diligence findings into a spec-compliant SKILL.md."""
    industry = SESSION_STATE["detected_industry"]
    biz_model = SESSION_STATE["business_model"]
    score = SESSION_STATE["conviction_score"]
    contradictions = SESSION_STATE["contradictions_logged"]
    rules = SESSION_STATE["skill_rules"]

    frontmatter = (
        "---\n"
        "name: hotseat-pitch-defense\n"
        "description: >\n"
        "  Audit pitch decks, financial projections, and founder narratives for cross-slide\n"
        "  contradictions, unit economics flaws, and investor objections before live VC pitches.\n"
        "license: Apache-2.0\n"
        "metadata:\n"
        "  engine: Gemma 4 Multimodal Harness\n"
        f'  detected_industry: "{industry}"\n'
        f'  business_model: "{biz_model}"\n'
        f'  conviction_score: "{score}/100"\n'
        "---\n"
    )

    section1_lines = ["## 1. Material Cross-Slide Contradictions & Audit Flags\n"]
    if contradictions:
        for i, c in enumerate(contradictions, 1):
            section1_lines.append(f"{i}. {c}")
    else:
        section1_lines.append(
            "_No material cross-slide contradictions logged in the active diligence session._"
        )
    section1 = "\n".join(section1_lines)

    section2_lines = [
        "## 2. Synthesized Institutional Diligence Guardrails (Gemma 4 Live Loop)\n"
    ]
    if rules:
        for i, rule in enumerate(rules, 1):
            section2_lines.append(f"{i}. {rule}")
    else:
        section2_lines.append(
            "_No session guardrails synthesized yet. Submit a slide or founder defense to compile live rules._"
        )
    section2 = "\n".join(section2_lines)

    checklist_items = [
        "Reconcile top-down TAM/SAM/SOM figures against bottom-up customer count and pricing assumptions.",
        "Cross-audit customer acquisition cost (CAC), payback period, and gross margin across marketing and financial slides.",
        "Verify that headcount, R&D milestones, and capital deployment schedules align with stated burn rate and runway.",
        "Confirm that channel partner, distributor, or payment processing fees are reflected in net contribution margins.",
    ]
    for rule in rules[:6]:
        checklist_items.append(f"[Session Rule] {rule}")

    section3_lines = ["## 3. Pre-Committee Verification Protocol\n"]
    for item in checklist_items:
        section3_lines.append(f"- [ ] {item}")
    section3 = "\n".join(section3_lines)

    return "\n".join(
        [
            frontmatter,
            f"# Institutional Pitch-Defense Skill — {industry}\n",
            f"> **Active IC Conviction Index: {score}/100** | **Model: {biz_model}**\n",
            section1,
            "",
            section2,
            "",
            section3,
            "",
        ]
    )


def _persist_skill_md() -> str:
    """Compile and persist SKILL.md to `.claude/skills/pitch-defense/SKILL.md`."""
    skill_md = _compile_skill_md()
    try:
        _SKILL_DIR.mkdir(parents=True, exist_ok=True)
        _SKILL_PATH.write_text(skill_md, encoding="utf-8")
    except Exception as exc:
        logger.warning("Could not persist SKILL.md to disk: %s", exc)
    return skill_md


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Endpoints
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.get("/health")
async def health_check() -> JSONResponse:
    """Service health probe."""
    return JSONResponse(content={"status": "ok", "engine": "gemma-4-multimodal"})


@app.get("/api/ping")
async def get_ping(provider: str = "all") -> JSONResponse:
    """Probe connectivity and round-trip latency for Gemini API, Ollama, and LM Studio."""
    if provider == "all":
        gemini_status = await router.ping_provider("gemini_api")
        ollama_status = await router.ping_provider("ollama")
        lmstudio_status = await router.ping_provider("lmstudio")
        return JSONResponse(
            content={
                "providers": {
                    "gemini_api": gemini_status,
                    "ollama": ollama_status,
                    "lmstudio": lmstudio_status,
                }
            }
        )
    single = await router.ping_provider(provider)
    return JSONResponse(content=single)


@app.post("/api/ping")
async def post_ping(
    provider: str = Form("all"),
    api_key: str = Form(""),
    ollama_model: str = Form(""),
) -> JSONResponse:
    """Probe connectivity and latency with optional runtime overrides from the UI."""
    key_override = api_key if api_key else None
    model_override = ollama_model if ollama_model else None

    if provider == "all":
        gemini_status = await router.ping_provider("gemini_api", api_key_override=key_override)
        ollama_status = await router.ping_provider("ollama", model_override=model_override)
        lmstudio_status = await router.ping_provider("lmstudio", model_override=model_override)
        return JSONResponse(
            content={
                "providers": {
                    "gemini_api": gemini_status,
                    "ollama": ollama_status,
                    "lmstudio": lmstudio_status,
                }
            }
        )

    single = await router.ping_provider(
        provider,
        api_key_override=key_override,
        model_override=model_override,
    )
    return JSONResponse(content=single)


@app.get("/api/state")
async def get_state() -> JSONResponse:
    """Return the current session state snapshot."""
    return JSONResponse(content=SESSION_STATE)


@app.post("/api/reset")
async def reset_state() -> JSONResponse:
    """Reset session state and synchronize SKILL.md."""
    global SESSION_STATE
    SESSION_STATE = deepcopy(_INITIAL_STATE)
    _persist_skill_md()
    logger.info("Institutional diligence session reset to clean state.")
    return JSONResponse(content={"status": "reset", "session": SESSION_STATE})


@app.post("/api/interrogate")
async def interrogate(
    slide_image: Optional[UploadFile] = File(None),
    slide_number: int = Form(1),
    user_message: str = Form(""),
    persona: str = Form("sand_hill_vc"),
    provider: str = Form("gemini_api"),
    api_key: str = Form(""),
    ollama_model: str = Form(""),
) -> JSONResponse:
    """Execute a live multimodal interrogation turn via Gemma 4."""
    global SESSION_STATE

    image_bytes: Optional[bytes] = None
    mime_type: str = "image/jpeg"
    if slide_image and slide_image.filename:
        raw_bytes = await slide_image.read()
        if raw_bytes:
            image_bytes = raw_bytes
            mime_type = slide_image.content_type or "image/jpeg"

    clean_message = user_message.strip()
    if not image_bytes and not clean_message:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Please upload a pitch-deck slide or enter a verbal defense statement.",
                "detail": "Both slide_image and user_message were empty.",
            },
        )

    last_q = SESSION_STATE.get("last_vc_question", "")
    word_count = len(clean_message.split()) if clean_message else 0
    evasion_hint = bool(last_q and clean_message and word_count < 4 and not image_bytes)

    prompt = _build_interrogation_prompt(
        persona_key=persona,
        slide_number=slide_number,
        user_message=clean_message,
        last_vc_question=last_q,
        claim_ledger=SESSION_STATE["claim_ledger"],
        has_image=image_bytes is not None,
        evasion_hint=evasion_hint,
    )

    try:
        result = await router.generate(
            prompt=prompt,
            image_bytes=image_bytes,
            mime_type=mime_type,
            provider=provider,
            api_key_override=api_key if api_key else None,
            ollama_model_override=ollama_model if ollama_model else None,
        )
    except Exception as exc:
        logger.error("Live Gemma 4 interrogation failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "detail": str(exc)},
        )

    # Extract dynamic fields directly from live Gemma 4 response
    raw_eval = result.get("evaluation") if isinstance(result.get("evaluation"), dict) else {}

    raw_claims = (
        result.get("visual_claims_extracted")
        if "visual_claims_extracted" in result
        else result.get("visual_claims")
    )
    visual_claims: list[str] = (
        [str(c).strip() for c in raw_claims if str(c).strip()]
        if isinstance(raw_claims, list)
        else []
    )

    detected_industry = str(result.get("detected_industry") or "").strip()
    business_model = str(result.get("business_model") or "").strip()

    answered_previous_question = bool(
        raw_eval.get("answered_previous_question", result.get("answered_previous_question", True))
    )
    contradiction_detected = bool(
        raw_eval.get("contradiction_detected", result.get("contradiction_detected", False))
    )
    contradiction_detail = str(
        raw_eval.get("contradiction_detail") or result.get("contradiction_detail") or ""
    ).strip()
    evasion_detected = bool(
        raw_eval.get("evasion_detected", result.get("evasion_detected", evasion_hint))
    )

    inquiry_category = str(
        raw_eval.get("inquiry_category")
        or result.get("inquiry_category")
        or raw_eval.get("attack_vector_badge")
        or result.get("attack_vector_badge")
        or ""
    ).strip()
    if not inquiry_category:
        inquiry_category = (
            "THESIS INCONSISTENCY"
            if contradiction_detected
            else (
                "UNANSWERED INQUIRY"
                if evasion_detected
                else "UNIT ECONOMICS DILIGENCE"
            )
        )
    attack_vector_badge = inquiry_category

    vc_spoken_response = str(result.get("vc_spoken_response") or "").strip()
    if not vc_spoken_response:
        return JSONResponse(
            status_code=502,
            content={
                "error": "Gemma 4 returned an incomplete JSON payload without 'vc_spoken_response'.",
                "detail": json.dumps(result)[:400],
            },
        )

    try:
        raw_delta = int(
            raw_eval.get(
                "conviction_delta",
                result.get("conviction_delta", 0),
            )
        )
    except (TypeError, ValueError):
        raw_delta = 0
    conviction_delta = _clamp(raw_delta, -20, 15)

    new_skill_guardrail = str(result.get("new_skill_guardrail") or "").strip()
    model_id = str(result.get("model_id", "gemma-4-26b-a4b-it"))
    engine_used = str(result.get("engine_used", f"gemini_api/{model_id}"))
    latency_ms = int(result.get("latency_ms", 0))

    # ── Update SESSION_STATE ────────────────────────────────────────────────
    for claim_text in visual_claims:
        entry = {"slide": slide_number, "source": "Visual Slide", "claim": claim_text}
        if entry not in SESSION_STATE["claim_ledger"]:
            SESSION_STATE["claim_ledger"].append(entry)

    if clean_message:
        SESSION_STATE["claim_ledger"].append(
            {
                "slide": slide_number,
                "source": "Verbal Defense",
                "claim": clean_message,
            }
        )

    SESSION_STATE["conviction_score"] = _clamp(
        SESSION_STATE["conviction_score"] + conviction_delta, 0, 100
    )

    if evasion_detected or contradiction_detected:
        SESSION_STATE["discrepancy_count"] += 1
        SESSION_STATE["evasion_strikes"] = SESSION_STATE["discrepancy_count"]

    if contradiction_detected and contradiction_detail:
        if contradiction_detail not in SESSION_STATE["contradictions_logged"]:
            SESSION_STATE["contradictions_logged"].append(contradiction_detail)

    if detected_industry:
        SESSION_STATE["detected_industry"] = detected_industry
    if business_model:
        SESSION_STATE["business_model"] = business_model

    SESSION_STATE["last_vc_question"] = vc_spoken_response

    if new_skill_guardrail and new_skill_guardrail not in SESSION_STATE["skill_rules"]:
        SESSION_STATE["skill_rules"].append(new_skill_guardrail)

    turn_record: dict[str, Any] = {
        "turn": len(SESSION_STATE["history"]) + 1,
        "slide_number": slide_number,
        "persona": persona,
        "user_message": clean_message,
        "vc_spoken_response": vc_spoken_response,
        "conviction_delta": conviction_delta,
        "evasion_detected": evasion_detected,
        "contradiction_detected": contradiction_detected,
        "contradiction_detail": contradiction_detail,
        "inquiry_category": inquiry_category,
        "attack_vector_badge": attack_vector_badge,
        "model_id": model_id,
        "engine_used": engine_used,
        "latency_ms": latency_ms,
    }
    SESSION_STATE["history"].append(turn_record)

    # Persist updated SKILL.md to disk
    _persist_skill_md()

    evaluation: dict[str, Any] = {
        "answered_previous_question": answered_previous_question,
        "evasion_detected": evasion_detected,
        "contradiction_detected": contradiction_detected,
        "contradiction_detail": contradiction_detail,
        "conviction_delta": conviction_delta,
        "inquiry_category": inquiry_category,
        "attack_vector_badge": attack_vector_badge,
        "vc_spoken_response": vc_spoken_response,
        "model_id": model_id,
        "latency_ms": latency_ms,
    }

    payload: dict[str, Any] = {
        "turn": turn_record,
        "evaluation": evaluation,
        "visual_claims_extracted": visual_claims,
        "visual_claims": visual_claims,
        "detected_industry": SESSION_STATE["detected_industry"],
        "business_model": SESSION_STATE["business_model"],
        "contradiction_detected": contradiction_detected,
        "contradiction_detail": contradiction_detail,
        "evasion_detected": evasion_detected,
        "inquiry_category": inquiry_category,
        "attack_vector_badge": attack_vector_badge,
        "vc_spoken_response": vc_spoken_response,
        "conviction_delta": conviction_delta,
        "new_skill_guardrail": new_skill_guardrail,
        "model_id": model_id,
        "engine_used": engine_used,
        "latency_ms": latency_ms,
        "session": SESSION_STATE,
    }

    logger.info(
        "Turn %d complete | persona=%s | Δconv=%+d | score=%d | latency=%dms | engine=%s",
        turn_record["turn"],
        persona,
        conviction_delta,
        SESSION_STATE["conviction_score"],
        latency_ms,
        engine_used,
    )

    return JSONResponse(content=payload)


@app.get("/api/skill")
async def get_skill() -> PlainTextResponse:
    """Compile and return the SKILL.md content."""
    skill_md = _compile_skill_md()
    return PlainTextResponse(content=skill_md, media_type="text/markdown")


@app.post("/api/skill")
async def post_skill() -> JSONResponse:
    """Compile SKILL.md, write it to disk, and return the content."""
    skill_md = _persist_skill_md()
    return JSONResponse(
        content={
            "status": "written",
            "path": str(_SKILL_PATH),
            "size_bytes": len(skill_md),
            "skill_md": skill_md,
        }
    )


@app.post("/api/verdict")
async def verdict(
    provider: str = Form("gemini_api"),
    api_key: str = Form(""),
    ollama_model: str = Form(""),
) -> JSONResponse:
    """Generate a live Investment Committee memorandum via Gemma 4."""
    if not SESSION_STATE["history"] and not SESSION_STATE["claim_ledger"]:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Cannot generate an Investment Committee Verdict before conducting at least one diligence turn.",
                "detail": "Session history and claim ledger are empty.",
            },
        )

    prompt = _build_verdict_prompt()

    try:
        result = await router.generate(
            prompt=prompt,
            image_bytes=None,
            provider=provider,
            api_key_override=api_key if api_key else None,
            ollama_model_override=ollama_model if ollama_model else None,
        )
    except Exception as exc:
        logger.error("Live Gemma 4 verdict generation failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "detail": str(exc)},
        )

    score = SESSION_STATE["conviction_score"]
    if score >= 68:
        band_decision = "PROCEED TO TERM SHEET"
    elif score >= 45:
        band_decision = "ADVANCE TO SECOND-STAGE DILIGENCE"
    else:
        band_decision = "DECLINE TO ADVANCE"

    raw_scores = result.get("scores") if isinstance(result.get("scores"), dict) else {}
    scores = {
        "market_timing": _clamp(int(raw_scores.get("market_timing", score)), 0, 100),
        "unit_economics": _clamp(int(raw_scores.get("unit_economics", score)), 0, 100),
        "defensibility_moat": _clamp(int(raw_scores.get("defensibility_moat", score)), 0, 100),
        "founder_conviction": _clamp(int(raw_scores.get("founder_conviction", score)), 0, 100),
    }

    raw_fixes = result.get("mandatory_deck_fixes")
    mandatory_deck_fixes = (
        [str(item).strip() for item in raw_fixes if str(item).strip()]
        if isinstance(raw_fixes, list)
        else []
    )

    model_id = str(result.get("model_id", "gemma-4-26b-a4b-it"))
    memo: dict[str, Any] = {
        "decision": str(result.get("decision") or band_decision).strip(),
        "headline_offer_or_reason": str(result.get("headline_offer_or_reason") or "").strip(),
        "scores": scores,
        "biggest_strength": str(result.get("biggest_strength") or "").strip(),
        "fatal_flaw": str(result.get("fatal_flaw") or "").strip(),
        "mandatory_deck_fixes": mandatory_deck_fixes,
        "model_id": model_id,
        "engine_used": str(result.get("engine_used", f"gemini_api/{model_id}")),
        "latency_ms": int(result.get("latency_ms", 0)),
        "session": SESSION_STATE,
    }

    logger.info(
        "Verdict generated | decision=%s | score=%d | latency=%dms | engine=%s",
        memo["decision"],
        SESSION_STATE["conviction_score"],
        memo["latency_ms"],
        memo["engine_used"],
    )

    return JSONResponse(content=memo)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _clamp(value: int, lo: int, hi: int) -> int:
    """Clamp *value* between *lo* and *hi* inclusive."""
    return max(lo, min(hi, value))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Static Files Mount  (MUST be last — catch-all for the SPA frontend)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Path("static").mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Dev Server Entry Point
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == "__main__":
    import os
    import uvicorn

    host = (os.environ.get("HOST") or "0.0.0.0").strip().strip("\"'") or "0.0.0.0"
    port = int((os.environ.get("PORT") or "8000").strip().strip("\"'") or "8000")
    uvicorn.run("app:app", host=host, port=port, reload=True)

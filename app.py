"""
HotSeat AI — Core Stateful FastAPI Backend
============================================

Endpoints
---------
GET  /api/state        → current session snapshot
POST /api/reset        → reset session to defaults
POST /api/interrogate  → multimodal pitch-deck interrogation turn
GET  /api/skill        → compile & return SKILL.md from session learnings
POST /api/skill        → compile, write to disk, & return SKILL.md
POST /api/verdict      → IC term-sheet / pass generator

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
#  Interrogator Personas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERSONAS: dict[str, dict[str, str]] = {
    "sand_hill_vc": {
        "title": "Sand Hill Tier-1 VC",
        "instructions": (
            "You are a legendary Sand Hill Road Tier-1 VC partner. "
            "You focus relentlessly on monopoly moat, TAM sanity, "
            "founder-market fit, distribution velocity, and 10x return math. "
            "You adapt your analysis to ANY industry — SaaS, Biotech, D2C Food, "
            "FinTech, Hardware, Climate, Retail, Logistics, or anything else. "
            "Never assume the startup is a software company unless the slide "
            "explicitly says so."
        ),
    },
    "ruthless_cfo": {
        "title": "Ruthless PE / CFO Auditor",
        "instructions": (
            "You are a ruthless PE-background CFO auditor. "
            "You are obsessed with unit economics, CAC/LTV ratios, gross margins, "
            "distributor cuts, working capital cycles, and burn rate. "
            "You demand concrete numbers and flag any financial claim that lacks "
            "supporting evidence or contradicts earlier slides."
        ),
    },
    "enterprise_buyer": {
        "title": "Skeptical Enterprise Buyer",
        "instructions": (
            "You are a skeptical VP of Procurement at a Fortune-500 enterprise. "
            "You probe switching costs, compliance and regulatory hurdles, "
            "operational SLAs, workflow friction, integration complexity, "
            "and ROI payback period. You need to justify this purchase to your "
            "board — vague promises will not cut it."
        ),
    },
    "demo_day_judge": {
        "title": "Hackathon / Demo-Day Judge",
        "instructions": (
            "You are a seasoned hackathon and demo-day judge. "
            "You probe what is real versus mocked, edge-case failure modes, "
            "latency under load, real-world scalability, and whether the demo "
            "reflects a repeatable product or a one-off script. "
            "You appreciate honesty about limitations over hand-waving."
        ),
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  In-Memory Session State
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_INITIAL_STATE: dict[str, Any] = {
    "conviction_score": 50,
    "evasion_strikes": 0,
    "detected_industry": "Detecting from pitch...",
    "business_model": "Analyzing...",
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
    title="HotSeat AI",
    version="0.1.0",
    description=(
        "Industry-agnostic, multimodal Venture Capital pitch-deck interrogator, "
        "cross-slide contradiction detector, and self-improving Agent Skill compiler "
        "powered by Gemma 4."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared router instance
router = Gemma4Router()

# ─── Claim-ledger cap (keeps prompt size bounded → latency < 2.5 s) ────────
_MAX_LEDGER_IN_PROMPT = 20


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Prompt Builder
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
    """Build the Universal 5-Step Cognitive VC prompt for Gemma 4."""

    persona = PERSONAS.get(persona_key, PERSONAS["sand_hill_vc"])
    persona_block = persona["instructions"]

    # Limit claim ledger to the most recent entries
    recent_claims = claim_ledger[-_MAX_LEDGER_IN_PROMPT:]
    ledger_json = json.dumps(recent_claims, indent=2) if recent_claims else "[]"

    evasion_clause = ""
    if evasion_hint:
        evasion_clause = (
            "\n⚠️ EVASION ALERT: The founder's response to your last question "
            f'("{last_vc_question}") was suspiciously short or empty. '
            "Call out this non-answer directly and re-ask the question with "
            "even more pressure. Set evasion_detected to true.\n"
        )

    image_instruction = (
        "An image of pitch-deck slide #{slide_number} is attached above. "
        "Analyse it visually to extract claims."
    ).format(slide_number=slide_number) if has_image else (
        "No slide image was provided for this turn. "
        "Focus entirely on probing the founder's verbal statements and "
        "cross-referencing against the existing claim_ledger."
    )

    prompt = f"""SYSTEM ROLE: {persona_block}

CONTEXT:
- Current slide number: {slide_number}
- Founder's verbal statement: "{user_message}"
- Your previous question to the founder: "{last_vc_question}"
- Existing claim_ledger (prior slides + verbal claims):
{ledger_json}
{evasion_clause}
{image_instruction}

You MUST respond with a single JSON object (no markdown, no commentary outside the JSON). Follow these 5 cognitive steps IN ORDER, embedding each result as a key in the JSON:

STEP 1 — "visual_claims": Extract up to 4 concrete quantitative or strategic claims visible on the uploaded slide image. Each claim is a string. If there is no image or the slide contains no numbers/metrics, set this to an empty list and pivot your questioning to probe their verbal business model instead.

STEP 2 — "detected_industry" and "business_model": Dynamically infer the startup's industry and business model from the slide content and verbal statements. NEVER default to "SaaS" or "Software" unless the pitch explicitly states it. Examples: "Biotech / Contract Research", "D2C Packaged Food / Subscription", "FinTech / Neo-Banking", "Hardware / IoT SaaS Hybrid", "Climate / Carbon Credits Marketplace", "Retail / Franchise Model".

STEP 3 — "contradiction_detected" (boolean) and "contradiction_detail" (string): Compare the current slide's claims and the founder's verbal statement against the claim_ledger. If any numbers, timelines, market sizes, or strategic claims conflict with earlier entries, set contradiction_detected to true and describe the specific conflict. Also set "evasion_detected" (boolean) to true if the founder dodged or gave a non-substantive answer to your previous question ("{last_vc_question}").

STEP 4 — "vc_spoken_response": Your interrogation response. Strictly 2-3 punchy sentences, maximum 50 words, first-person voice. Reference EXACT numbers or claims from their slide or verbal statement. Be sharp and specific. Do NOT be generic.

STEP 5 — "simulated_strong_reply": A concrete 2-sentence data-backed founder answer to this exact question (what a GREAT founder would say). "simulated_evasive_reply": A 1-sentence buzzword dodge (what a weak founder would say to evade).

ALSO INCLUDE these keys:
- "conviction_delta": integer from -20 to +15 representing how this turn changes investor conviction. Negative = founder lost credibility. Positive = founder was compelling.
- "new_skill_guardrail": A single sentence describing a reusable interrogation rule learned from this turn (for compiling into SKILL.md). Example: "Always cross-check TAM figures against the stated serviceable market on the previous slide."

Respond ONLY with the JSON object. No other text."""

    return prompt


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Endpoints
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.get("/api/state")
async def get_state() -> JSONResponse:
    """Return the current session state snapshot."""
    return JSONResponse(content=SESSION_STATE)


@app.post("/api/reset")
async def reset_state() -> JSONResponse:
    """Reset session to factory defaults."""
    global SESSION_STATE
    SESSION_STATE = deepcopy(_INITIAL_STATE)
    logger.info("Session state reset to initial values.")
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
    """Run one interrogation turn against the uploaded slide / verbal answer.

    The endpoint:
      1. Checks for evasion (short / empty replies to prior questions).
      2. Builds the 5-step cognitive VC prompt.
      3. Routes through ``Gemma4Router`` (cloud cascade or local Ollama).
      4. Updates ``SESSION_STATE`` (claim ledger, conviction, strikes, etc.).
      5. Returns the full turn payload plus the updated session.
    """
    global SESSION_STATE

    # ── Read image bytes (if provided) ──────────────────────────────────────
    image_bytes: Optional[bytes] = None
    mime_type: str = "image/png"
    if slide_image and slide_image.filename:
        image_bytes = await slide_image.read()
        mime_type = slide_image.content_type or "image/png"

    # ── Evasion pre-check ───────────────────────────────────────────────────
    last_q = SESSION_STATE.get("last_vc_question", "")
    word_count = len(user_message.strip().split()) if user_message.strip() else 0
    evasion_hint = bool(last_q and word_count < 3 and not image_bytes)

    # ── Build prompt ────────────────────────────────────────────────────────
    prompt = _build_interrogation_prompt(
        persona_key=persona,
        slide_number=slide_number,
        user_message=user_message,
        last_vc_question=last_q,
        claim_ledger=SESSION_STATE["claim_ledger"],
        has_image=image_bytes is not None,
        evasion_hint=evasion_hint,
    )

    # ── Fallback dict (guarantees 200 even if model output is garbage) ─────
    fallback = {
        "visual_claims": [],
        "detected_industry": SESSION_STATE["detected_industry"],
        "business_model": SESSION_STATE["business_model"],
        "contradiction_detected": False,
        "contradiction_detail": "",
        "evasion_detected": evasion_hint,
        "attack_vector_badge": "Unit Economics & Moat Diligence",
        "vc_spoken_response": "I need a moment — could you repeat that?",
        "conviction_delta": 0,
        "simulated_strong_reply": "N/A",
        "simulated_evasive_reply": "N/A",
        "new_skill_guardrail": "",
    }

    # ── Call Gemma 4 via the router ─────────────────────────────────────────
    result = await router.generate(
        prompt=prompt,
        image_bytes=image_bytes,
        mime_type=mime_type,
        fallback_dict=fallback,
        provider=provider,
        api_key_override=api_key if api_key else None,
        ollama_model_override=ollama_model if ollama_model else None,
    )

    # ── Normalise model output (defensive — keys may be missing) ────────────
    visual_claims: list[str] = result.get("visual_claims", [])
    if not isinstance(visual_claims, list):
        visual_claims = []

    detected_industry: str = result.get(
        "detected_industry", SESSION_STATE["detected_industry"]
    )
    business_model: str = result.get(
        "business_model", SESSION_STATE["business_model"]
    )
    contradiction_detected: bool = bool(result.get("contradiction_detected", False))
    contradiction_detail: str = result.get("contradiction_detail", "")
    evasion_detected: bool = bool(result.get("evasion_detected", evasion_hint))
    attack_vector_badge: str = result.get(
        "attack_vector_badge",
        (
            "Cross-Slide Contradiction Audit"
            if contradiction_detected
            else (
                "Founder Evasion Callout"
                if evasion_detected
                else "Unit Economics & Moat Diligence"
            )
        ),
    )
    vc_spoken_response: str = result.get(
        "vc_spoken_response", fallback["vc_spoken_response"]
    )
    conviction_delta: int = _clamp(
        int(result.get("conviction_delta", 0)), -20, 15
    )
    simulated_strong_reply: str = result.get("simulated_strong_reply", "N/A")
    simulated_evasive_reply: str = result.get("simulated_evasive_reply", "N/A")
    new_skill_guardrail: str = result.get("new_skill_guardrail", "")
    engine_used: str = result.get("engine_used", "unknown")

    # ━━━ Update SESSION_STATE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # — Append visual claims to claim_ledger
    for claim_text in visual_claims:
        SESSION_STATE["claim_ledger"].append(
            {"slide": slide_number, "source": "Visual Slide", "claim": str(claim_text)}
        )

    # — Append verbal statement as a ledger entry (if non-trivial)
    if user_message.strip():
        SESSION_STATE["claim_ledger"].append(
            {
                "slide": slide_number,
                "source": "Verbal Defense",
                "claim": user_message.strip(),
            }
        )

    # — Conviction score (clamped 0–100)
    SESSION_STATE["conviction_score"] = _clamp(
        SESSION_STATE["conviction_score"] + conviction_delta, 0, 100
    )

    # — Evasion / contradiction strikes
    if evasion_detected or contradiction_detected:
        SESSION_STATE["evasion_strikes"] += 1

    # — Log contradiction
    if contradiction_detected and contradiction_detail:
        SESSION_STATE["contradictions_logged"].append(contradiction_detail)

    # — Industry & business model (only update if the model provided a real value)
    if detected_industry and detected_industry != SESSION_STATE["detected_industry"]:
        SESSION_STATE["detected_industry"] = detected_industry
    if business_model and business_model != SESSION_STATE["business_model"]:
        SESSION_STATE["business_model"] = business_model

    # — Last VC question (for next-turn evasion detection)
    SESSION_STATE["last_vc_question"] = vc_spoken_response

    # — Skill guardrail
    if new_skill_guardrail and new_skill_guardrail not in SESSION_STATE["skill_rules"]:
        SESSION_STATE["skill_rules"].append(new_skill_guardrail)

    # — History
    turn_record: dict[str, Any] = {
        "turn": len(SESSION_STATE["history"]) + 1,
        "slide_number": slide_number,
        "persona": persona,
        "user_message": user_message,
        "vc_spoken_response": vc_spoken_response,
        "conviction_delta": conviction_delta,
        "evasion_detected": evasion_detected,
        "contradiction_detected": contradiction_detected,
        "attack_vector_badge": attack_vector_badge,
        "engine_used": engine_used,
    }
    SESSION_STATE["history"].append(turn_record)

    evaluation: dict[str, Any] = {
        "contradiction_detected": contradiction_detected,
        "contradiction_detail": contradiction_detail,
        "evasion_detected": evasion_detected,
        "conviction_delta": conviction_delta,
        "attack_vector_badge": attack_vector_badge,
        "vc_spoken_response": vc_spoken_response,
    }

    # ── Build response payload ──────────────────────────────────────────────
    payload: dict[str, Any] = {
        "turn": turn_record,
        "evaluation": evaluation,
        "visual_claims": visual_claims,
        "detected_industry": SESSION_STATE["detected_industry"],
        "business_model": SESSION_STATE["business_model"],
        "contradiction_detected": contradiction_detected,
        "contradiction_detail": contradiction_detail,
        "evasion_detected": evasion_detected,
        "attack_vector_badge": attack_vector_badge,
        "vc_spoken_response": vc_spoken_response,
        "conviction_delta": conviction_delta,
        "simulated_strong_reply": simulated_strong_reply,
        "simulated_evasive_reply": simulated_evasive_reply,
        "new_skill_guardrail": new_skill_guardrail,
        "engine_used": engine_used,
        "session": SESSION_STATE,
    }

    logger.info(
        "Turn %d complete  |  persona=%s  |  Δconv=%+d  |  score=%d  |  engine=%s",
        turn_record["turn"],
        persona,
        conviction_delta,
        SESSION_STATE["conviction_score"],
        engine_used,
    )

    return JSONResponse(content=payload)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Self-Improving Agent Skill Compiler  (/api/skill)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_SKILL_DIR = Path(".claude/skills/pitch-defense")
_SKILL_PATH = _SKILL_DIR / "SKILL.md"


def _compile_skill_md() -> str:
    """Compile the current session learnings into a spec-compliant SKILL.md."""
    industry = SESSION_STATE["detected_industry"]
    score = SESSION_STATE["conviction_score"]
    contradictions = SESSION_STATE["contradictions_logged"]
    rules = SESSION_STATE["skill_rules"]

    # ── YAML frontmatter ────────────────────────────────────────────────────
    frontmatter = (
        "---\n"
        "name: hotseat-pitch-defense\n"
        "description: >\n"
        "  Audit pitch decks, financial projections, and founder narratives for cross-slide\n"
        "  contradictions, unit economics flaws, and investor objections before live VC pitches.\n"
        "license: Apache-2.0\n"
        "metadata:\n"
        "  engine: Gemma 4 Multimodal Harness\n"
        f"  detected_industry: \"{industry}\"\n"
        f"  conviction_score: \"{score}/100\"\n"
        "---\n"
    )

    # ── Section 1: Contradictions & Red Flags ───────────────────────────────
    section1_lines = [
        "## 1. Discovered Cross-Slide Contradictions & Red Flags\n",
    ]
    if contradictions:
        for i, c in enumerate(contradictions, 1):
            section1_lines.append(f"{i}. {c}")
    else:
        section1_lines.append(
            "_No contradictions detected yet. Upload more slides and defend your claims._"
        )
    section1 = "\n".join(section1_lines)

    # ── Section 2: Learned Guardrails ───────────────────────────────────────
    section2_lines = [
        "## 2. Learned Domain & Unit-Economics Guardrails (Hermes Self-Improving Loop)\n",
    ]
    if rules:
        for i, rule in enumerate(rules, 1):
            section2_lines.append(f"{i}. {rule}")
    else:
        section2_lines.append(
            "_No guardrails learned yet. Complete at least one interrogation turn._"
        )
    section2 = "\n".join(section2_lines)

    # ── Section 3: Pre-Pitch Verification Checklist ─────────────────────────
    checklist_items = [
        "Verify all TAM/SAM/SOM figures are internally consistent across slides.",
        "Confirm unit economics (CAC, LTV, gross margin) match the revenue model slide.",
        "Ensure timeline milestones do not contradict fundraising or hiring slides.",
        "Check that competitive landscape claims align with the stated moat/defensibility.",
        "Validate that financial projections use assumptions disclosed elsewhere in the deck.",
    ]
    # Append any industry-specific guardrails as bonus checklist items
    for rule in rules[:5]:
        checklist_items.append(f"[Learned] {rule}")

    section3_lines = [
        "## 3. Mandatory Pre-Pitch Verification Checklist\n",
    ]
    for item in checklist_items:
        section3_lines.append(f"- [ ] {item}")
    section3 = "\n".join(section3_lines)

    # ── Assemble ────────────────────────────────────────────────────────────
    skill_md = "\n".join([
        frontmatter,
        f"# HotSeat Pitch-Defense Skill  —  {industry}\n",
        f"> **Conviction score after interrogation: {score}/100**\n",
        section1,
        "",
        section2,
        "",
        section3,
        "",
    ])

    return skill_md


@app.get("/api/skill")
async def get_skill() -> PlainTextResponse:
    """Compile and return the SKILL.md content without writing to disk."""
    skill_md = _compile_skill_md()
    return PlainTextResponse(content=skill_md, media_type="text/markdown")


@app.post("/api/skill")
async def post_skill() -> JSONResponse:
    """Compile SKILL.md, write it to disk, and return the content."""
    skill_md = _compile_skill_md()

    _SKILL_DIR.mkdir(parents=True, exist_ok=True)
    _SKILL_PATH.write_text(skill_md, encoding="utf-8")
    logger.info("SKILL.md written to %s (%d bytes)", _SKILL_PATH, len(skill_md))

    return JSONResponse(
        content={
            "status": "written",
            "path": str(_SKILL_PATH),
            "size_bytes": len(skill_md),
            "skill_md": skill_md,
        }
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Investment Committee Verdict  (/api/verdict)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _build_verdict_prompt() -> str:
    """Build the IC-memo prompt from the full session history."""
    score = SESSION_STATE["conviction_score"]
    industry = SESSION_STATE["detected_industry"]
    biz_model = SESSION_STATE["business_model"]
    strikes = SESSION_STATE["evasion_strikes"]
    ledger = SESSION_STATE["claim_ledger"][-_MAX_LEDGER_IN_PROMPT:]
    history = SESSION_STATE["history"]

    # Determine band
    if score >= 68:
        decision_band = "TERM SHEET OFFERED"
    elif score >= 45:
        decision_band = "CONDITIONAL SECOND MEETING"
    else:
        decision_band = "HARD PASS"

    history_json = json.dumps(history, indent=2) if history else "[]"
    ledger_json = json.dumps(ledger, indent=2) if ledger else "[]"

    prompt = f"""You are the Investment Committee of a top-tier venture fund.

Below is the complete interrogation record for a startup pitch.

INPUT DATA:
- Detected Industry: {industry}
- Business Model: {biz_model}
- Final Conviction Score: {score}/100
- Evasion Strikes: {strikes}
- Decision Band: {decision_band}
- Claim Ledger (last {_MAX_LEDGER_IN_PROMPT} entries):
{ledger_json}
- Q&A History:
{history_json}

Generate a structured JSON Investment Committee Memo with EXACTLY these keys:

1. "decision": MUST be exactly one of: "TERM SHEET OFFERED", "CONDITIONAL SECOND MEETING", or "HARD PASS" (use the decision band above: "{decision_band}").

2. "headline_offer_or_reason": A single compelling sentence.
   - If TERM SHEET OFFERED: state the offer, e.g. "₹35 Cr Pre-Money Seed Term Sheet" or "$4M Seed at $20M Pre-Money".
   - If CONDITIONAL SECOND MEETING: state what must be resolved, e.g. "Revisit after unit economics audit on D2C channel margins".
   - If HARD PASS: state the reason, e.g. "Passed: Unresolved offline retail margin dilution with contradictory CAC claims".

3. "scores": An object with exactly 4 integer keys (each 0–100):
   - "market_timing": How well-timed is this market entry?
   - "unit_economics": How sound are the financials?
   - "defensibility_moat": How defensible is the business?
   - "founder_conviction": How convincing was the founder under pressure?

4. "biggest_strength": 1 specific sentence citing the founder's strongest claim or defense from the Q&A history.

5. "fatal_flaw": 1 specific sentence citing their worst contradiction or dodged question from the Q&A history.

6. "mandatory_deck_fixes": A JSON array of exactly 3 strings — concrete, actionable slide fixes the founder must make before their next pitch.

Respond ONLY with the JSON object. No markdown fences, no commentary."""

    return prompt


@app.post("/api/verdict")
async def verdict(
    provider: str = Form("gemini_api"),
    api_key: str = Form(""),
    ollama_model: str = Form(""),
) -> JSONResponse:
    """Generate an Investment Committee term-sheet / pass memo.

    Uses the full session history to produce a structured IC verdict
    via a text-only Gemma 4 call (no image).
    """
    prompt = _build_verdict_prompt()

    score = SESSION_STATE["conviction_score"]
    if score >= 68:
        default_decision = "TERM SHEET OFFERED"
    elif score >= 45:
        default_decision = "CONDITIONAL SECOND MEETING"
    else:
        default_decision = "HARD PASS"

    fallback: dict[str, Any] = {
        "decision": default_decision,
        "headline_offer_or_reason": "Unable to generate detailed memo — see session history.",
        "scores": {
            "market_timing": 50,
            "unit_economics": 50,
            "defensibility_moat": 50,
            "founder_conviction": score,
        },
        "biggest_strength": "N/A",
        "fatal_flaw": "N/A",
        "mandatory_deck_fixes": [
            "Add verifiable TAM source citations.",
            "Include a clear unit economics slide.",
            "Address competitive landscape gaps.",
        ],
    }

    result = await router.generate(
        prompt=prompt,
        image_bytes=None,
        fallback_dict=fallback,
        provider=provider,
        api_key_override=api_key if api_key else None,
        ollama_model_override=ollama_model if ollama_model else None,
    )

    # Normalise output
    memo: dict[str, Any] = {
        "decision": result.get("decision", fallback["decision"]),
        "headline_offer_or_reason": result.get(
            "headline_offer_or_reason", fallback["headline_offer_or_reason"]
        ),
        "scores": result.get("scores", fallback["scores"]),
        "biggest_strength": result.get(
            "biggest_strength", fallback["biggest_strength"]
        ),
        "fatal_flaw": result.get("fatal_flaw", fallback["fatal_flaw"]),
        "mandatory_deck_fixes": result.get(
            "mandatory_deck_fixes", fallback["mandatory_deck_fixes"]
        ),
        "engine_used": result.get("engine_used", "unknown"),
        "session": SESSION_STATE,
    }

    logger.info(
        "Verdict generated  |  decision=%s  |  score=%d  |  engine=%s",
        memo["decision"],
        SESSION_STATE["conviction_score"],
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
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

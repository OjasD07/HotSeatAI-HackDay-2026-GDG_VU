# Graph Report - HotSeatAI-HackDay-2026-GDG_VU  (2026-10-23)

## Corpus Check
- 12 files · ~21,382 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 233 nodes · 423 edges · 17 communities (10 shown, 7 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 22 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1a53feff`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app.py
- Any
- app.js
- decks.js
- voice.js
- CLAUDE.md
- _persist_skill_md
- package.json
- .claude/CLAUDE.md
- _gemma_generation_config
- interrogate
- JSONResponse
- verdict
- _is_transient_gemma_error

## God Nodes (most connected - your core abstractions)
1. `Gemma4Router` - 14 edges
2. `fetch()` - 14 edges
3. `interrogate()` - 10 edges
4. `_sanitize_gemini_contents()` - 10 edges
5. `handleInterrogationResponse()` - 10 edges
6. `sanitizeGeminiContents()` - 10 edges
7. `callGeminiCascade()` - 10 edges
8. `_clean_env()` - 9 edges
9. `_build_gemma_contents()` - 9 edges
10. `extract_json_safely()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `6. Cloudflare Workers Edge Deployment & Observability (`https://hotseat-ai.ojasdeshpande.in/`)` --references--> `resolveEnvConfig()`  [INFERRED]
  README.md → worker.js
- `Hackathon Track & Sponsor Compliance Disclosures` --references--> `_persist_skill_md()`  [INFERRED]
  README.md → app.py
- `3. Compulsory Sponsor Integration — Graphify Knowledge Graph` --references--> `interrogate()`  [INFERRED]
  README.md → app.py
- `3. Compulsory Sponsor Integration — Graphify Knowledge Graph` --references--> `verdict()`  [INFERRED]
  README.md → app.py
- `3. Configure Environment Variables (`.env` / Cloudflare Secrets)` --references--> `_clean_env()`  [INFERRED]
  README.md → engine.py

## Import Cycles
- None detected.

## Communities (17 total, 7 thin omitted)

### Community 1 - "app.py"
Cohesion: 0.20
Nodes (27): appendChat(), cachedPingResults, callInterrogate(), downloadSkill(), escapeHtml(), fetchSkillPreview(), formatPingBadge(), generateVerdict() (+19 more)

### Community 2 - "Any"
Cohesion: 0.08
Nodes (17): _build_gemma_contents(), _clean_env(), _extract_gemma_parts(), extract_json_safely(), Gemma4Router, _has_valid_image_payload(), _is_failed_gemma_turn(), _merge_gemma_parts() (+9 more)

### Community 3 - "app.js"
Cohesion: 0.07
Nodes (23): _compile_skill_md(), get_skill(), 1. Material Cross-Slide Contradictions & Audit Flags, 2. Synthesized Institutional Diligence Guardrails (Gemma 4 Live Loop), 3. Pre-Committee Verification Protocol, Institutional Pitch-Defense Skill — Fintech (Cross-Border B2B Treasury & Payments), 1. Clone the Repository & Create a Virtual Environment, 2. Install Dependencies (+15 more)

### Community 4 - "decks.js"
Cohesion: 0.12
Nodes (32): arrayBufferToBase64(), buildGemmaContents(), buildGemmaRequestBody(), buildInterrogationPrompt(), buildSessionHistoryMessages(), buildVerdictPrompt(), callGeminiCascade(), clamp() (+24 more)

### Community 5 - "voice.js"
Cohesion: 0.13
Nodes (14): description, devDependencies, wrangler, main, name, private, scripts, deploy (+6 more)

### Community 7 - "CLAUDE.md"
Cohesion: 0.26
Nodes (13): dataUrlToBlob(), drawSlideToCanvas(), getSlideBlob(), handleFileUpload(), loadImageDownscaled(), loadPDF(), loadSampleDeck(), nextSlide() (+5 more)

### Community 8 - "_persist_skill_md"
Cohesion: 0.25
Nodes (4): _persist_skill_md(), post_ping(), post_skill(), reset_state()

### Community 13 - "interrogate"
Cohesion: 0.25
Nodes (3): _build_interrogation_prompt(), interrogate(), _last_question_in_history()

### Community 14 - "JSONResponse"
Cohesion: 0.32
Nodes (3): get_ping(), get_state(), health_check()

### Community 15 - "verdict"
Cohesion: 0.33
Nodes (3): _build_verdict_prompt(), _clamp(), verdict()

## Knowledge Gaps
- **1 isolated node(s):** `wrangler`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 96 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Gemma4Router` connect `Any` to `app.py`, `app.js`, `HotSeat AI`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Gemma4Router` (e.g. with `1. Track: Best Use of Gemma 4 (via Gemini API)` and `2. Track: Open-Source / Open-Weight AI & Agent Skills`) actually correct?**
  _`Gemma4Router` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `wrangler` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Any` be split into smaller, more focused modules?**
  _Cohesion score 0.0797979797979798 - nodes in this community are weakly interconnected._
- **Why does `Architectural Component Breakdown` connect `app.js` to `Any`, `decks.js`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `_sanitize_gemini_contents()` (e.g. with `Architectural Component Breakdown` and `Key Institutional Features`) actually correct?**
  _`_sanitize_gemini_contents()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `app.js` be split into smaller, more focused modules?**
  _Cohesion score 0.07142857142857142 - nodes in this community are weakly interconnected._
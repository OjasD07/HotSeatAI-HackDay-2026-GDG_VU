# Graph Report - HotSeatAI-HackDay-2026-GDG_VU  (2026-10-23)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 244 nodes · 442 edges · 18 communities (10 shown, 8 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 22 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cb9baf65`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app.py
- app.py
- _persist_skill_md
- app.js
- decks.js
- voice.js
- HotSeat AI
- CLAUDE.md
- interrogate
- package.json
- .claude/CLAUDE.md
- _gemma_timeout_config
- JSONResponse
- verdict
- __main__.py
- Any

## God Nodes (most connected - your core abstractions)
1. `Gemma4Router` - 14 edges
2. `fetch()` - 14 edges
3. `handleInterrogationResponse()` - 10 edges
4. `_sanitize_gemini_contents()` - 10 edges
5. `callGeminiCascade()` - 10 edges
6. `sanitizeGeminiContents()` - 10 edges
7. `interrogate()` - 10 edges
8. `testAllConnections()` - 9 edges
9. `_build_gemma_contents()` - 9 edges
10. `_clean_env()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `1. Track: Best Use of Gemma 4 (via Gemini API)` --references--> `Gemma4Router`  [INFERRED]
  README.md → backend/engine.py
- `2. Track: Open-Source / Open-Weight AI & Agent Skills` --references--> `Gemma4Router`  [INFERRED]
  README.md → backend/engine.py
- `3. Compulsory Sponsor Integration — Graphify Knowledge Graph` --references--> `Gemma4Router`  [INFERRED]
  README.md → backend/engine.py
- `Architectural Component Breakdown` --references--> `Gemma4Router`  [INFERRED]
  README.md → backend/engine.py
- `Architectural Component Breakdown` --references--> `_compile_skill_md()`  [INFERRED]
  README.md → backend/app.py

## Import Cycles
- None detected.

## Communities (18 total, 8 thin omitted)

### Community 1 - "app.py"
Cohesion: 0.17
Nodes (30): appendChat(), cachedPingResults, callInterrogate(), downloadSkill(), escapeHtml(), fetchSkillPreview(), formatPingBadge(), generateVerdict() (+22 more)

### Community 2 - "_persist_skill_md"
Cohesion: 0.25
Nodes (4): _persist_skill_md(), post_ping(), post_skill(), reset_state()

### Community 3 - "app.js"
Cohesion: 0.09
Nodes (21): 1. Material Cross-Slide Contradictions & Audit Flags, 2. Synthesized Institutional Diligence Guardrails (Gemma 4 Live Loop), 3. Pre-Committee Verification Protocol, Institutional Pitch-Defense Skill — Fintech (Cross-Border B2B Treasury & Payments), 1. Clone the Repository & Create a Virtual Environment, 2. Install Dependencies, 3. Configure Environment Variables (`.env` / Cloudflare Secrets), 4-Stage Cognitive Diligence Pipeline (+13 more)

### Community 4 - "decks.js"
Cohesion: 0.12
Nodes (34): 1. Track: Best Use of Gemma 4 (via Gemini API), Architectural Component Breakdown, arrayBufferToBase64(), buildGemmaContents(), buildGemmaRequestBody(), buildInterrogationPrompt(), buildSessionHistoryMessages(), buildVerdictPrompt() (+26 more)

### Community 5 - "voice.js"
Cohesion: 0.13
Nodes (14): description, devDependencies, wrangler, main, name, private, scripts, deploy (+6 more)

### Community 7 - "CLAUDE.md"
Cohesion: 0.26
Nodes (13): dataUrlToBlob(), drawSlideToCanvas(), getSlideBlob(), handleFileUpload(), loadImageDownscaled(), loadPDF(), loadSampleDeck(), nextSlide() (+5 more)

### Community 8 - "interrogate"
Cohesion: 0.25
Nodes (3): _build_interrogation_prompt(), interrogate(), _last_question_in_history()

### Community 13 - "JSONResponse"
Cohesion: 0.32
Nodes (3): get_ping(), get_state(), health_check()

### Community 14 - "verdict"
Cohesion: 0.29
Nodes (4): _build_verdict_prompt(), _clamp(), verdict(), 3. Compulsory Sponsor Integration — Graphify Knowledge Graph

### Community 16 - "Any"
Cohesion: 0.08
Nodes (15): _build_gemma_contents(), _clean_env(), _extract_gemma_parts(), Gemma4Router, _has_valid_image_payload(), _is_failed_gemma_turn(), _is_transient_gemma_error(), _merge_gemma_parts() (+7 more)

## Knowledge Gaps
- **1 isolated node(s):** `wrangler`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 100 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Gemma4Router` connect `Any` to `app.py`, `decks.js`, `HotSeat AI`, `verdict`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Gemma4Router` (e.g. with `1. Track: Best Use of Gemma 4 (via Gemini API)` and `2. Track: Open-Source / Open-Weight AI & Agent Skills`) actually correct?**
  _`Gemma4Router` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `wrangler` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `app.js` be split into smaller, more focused modules?**
  _Cohesion score 0.08695652173913043 - nodes in this community are weakly interconnected._
- **Why does `Architectural Component Breakdown` connect `decks.js` to `app.py`, `Any`, `app.js`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `_sanitize_gemini_contents()` (e.g. with `Architectural Component Breakdown` and `Key Institutional Features`) actually correct?**
  _`_sanitize_gemini_contents()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `decks.js` be split into smaller, more focused modules?**
  _Cohesion score 0.11932773109243698 - nodes in this community are weakly interconnected._
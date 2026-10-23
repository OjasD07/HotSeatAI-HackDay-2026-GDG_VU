# Graph Report - HotSeatAI-HackDay-2026-GDG_VU  (2026-10-23)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 237 nodes · 433 edges · 15 communities (8 shown, 7 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 22 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4f2d61f8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app.py
- app.py
- Any
- app.js
- decks.js
- voice.js
- HotSeat AI
- CLAUDE.md
- Gemma4Router
- package.json
- .claude/CLAUDE.md
- _gemma_generation_config
- _to_genai_contents
- ._cloud_cascade

## God Nodes (most connected - your core abstractions)
1. `Gemma4Router` - 14 edges
2. `fetch()` - 14 edges
3. `interrogate()` - 10 edges
4. `handleInterrogationResponse()` - 10 edges
5. `_sanitize_gemini_contents()` - 10 edges
6. `callGeminiCascade()` - 10 edges
7. `sanitizeGeminiContents()` - 10 edges
8. `testAllConnections()` - 9 edges
9. `_build_gemma_contents()` - 9 edges
10. `extract_json_safely()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `2. Track: Open-Source / Open-Weight AI & Agent Skills` --references--> `Gemma4Router`  [INFERRED]
  README.md → engine.py
- `6. Cloudflare Workers Edge Deployment & Observability (`https://hotseat-ai.ojasdeshpande.in/`)` --references--> `resolveEnvConfig()`  [INFERRED]
  README.md → worker.js
- `1. Track: Best Use of Gemma 4 (via Gemini API)` --references--> `Gemma4Router`  [INFERRED]
  README.md → engine.py
- `3. Compulsory Sponsor Integration — Graphify Knowledge Graph` --references--> `Gemma4Router`  [INFERRED]
  README.md → engine.py
- `Architectural Component Breakdown` --references--> `Gemma4Router`  [INFERRED]
  README.md → engine.py

## Import Cycles
- None detected.

## Communities (15 total, 7 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.06
Nodes (19): _build_interrogation_prompt(), _build_verdict_prompt(), _clamp(), _compile_skill_md(), get_ping(), get_skill(), get_state(), health_check() (+11 more)

### Community 1 - "app.py"
Cohesion: 0.17
Nodes (30): appendChat(), cachedPingResults, callInterrogate(), downloadSkill(), escapeHtml(), fetchSkillPreview(), formatPingBadge(), generateVerdict() (+22 more)

### Community 2 - "Any"
Cohesion: 0.21
Nodes (6): _extract_gemma_parts(), _is_failed_gemma_turn(), _merge_gemma_parts(), _normalise_gemma_role(), _sanitize_gemini_contents(), _session_history_to_messages()

### Community 3 - "app.js"
Cohesion: 0.10
Nodes (18): 1. Material Cross-Slide Contradictions & Audit Flags, 2. Synthesized Institutional Diligence Guardrails (Gemma 4 Live Loop), 3. Pre-Committee Verification Protocol, Institutional Pitch-Defense Skill — Fintech (Cross-Border B2B Treasury & Payments), 1. Clone the Repository & Create a Virtual Environment, 2. Install Dependencies, 3. Configure Environment Variables (`.env` / Cloudflare Secrets), 4. Start the FastAPI Diligence Server (+10 more)

### Community 4 - "decks.js"
Cohesion: 0.12
Nodes (33): 1. Track: Best Use of Gemma 4 (via Gemini API), arrayBufferToBase64(), buildGemmaContents(), buildGemmaRequestBody(), buildInterrogationPrompt(), buildSessionHistoryMessages(), buildVerdictPrompt(), callGeminiCascade() (+25 more)

### Community 5 - "voice.js"
Cohesion: 0.13
Nodes (14): description, devDependencies, wrangler, main, name, private, scripts, deploy (+6 more)

### Community 7 - "CLAUDE.md"
Cohesion: 0.26
Nodes (13): dataUrlToBlob(), drawSlideToCanvas(), getSlideBlob(), handleFileUpload(), loadImageDownscaled(), loadPDF(), loadSampleDeck(), nextSlide() (+5 more)

### Community 16 - "._cloud_cascade"
Cohesion: 0.20
Nodes (5): _build_gemma_contents(), _has_valid_image_payload(), _is_transient_gemma_error(), 2. Track: Open-Source / Open-Weight AI & Agent Skills, Hackathon Track & Sponsor Compliance Disclosures

## Knowledge Gaps
- **1 isolated node(s):** `wrangler`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 97 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Gemma4Router` connect `Gemma4Router` to `app.py`, `._cloud_cascade`, `decks.js`, `HotSeat AI`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Gemma4Router` (e.g. with `1. Track: Best Use of Gemma 4 (via Gemini API)` and `2. Track: Open-Source / Open-Weight AI & Agent Skills`) actually correct?**
  _`Gemma4Router` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `wrangler` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.058823529411764705 - nodes in this community are weakly interconnected._
- **Why does `Architectural Component Breakdown` connect `app.py` to `Gemma4Router`, `Any`, `decks.js`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Should `app.js` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Why does `HotSeat AI` connect `app.js` to `._cloud_cascade`, `app.py`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
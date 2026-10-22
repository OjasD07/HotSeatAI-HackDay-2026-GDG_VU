# Graph Report - HotSeatAI-HackDay-2026-GDG_VU  (2026-10-22)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 180 nodes · 296 edges · 16 communities (10 shown, 6 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e2c6eee6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- _persist_skill_md
- Gemma4Router
- app.js
- decks.js
- HotSeat AI
- CLAUDE.md
- .claude/CLAUDE.md
- worker.js
- package.json
- _compile_skill_md
- JSONResponse
- verdict
- interrogate

## God Nodes (most connected - your core abstractions)
1. `Gemma4Router` - 14 edges
2. `fetch()` - 11 edges
3. `handleInterrogationResponse()` - 10 edges
4. `interrogate()` - 9 edges
5. `extract_json_safely()` - 9 edges
6. `appendChat()` - 8 edges
7. `generateVerdict()` - 8 edges
8. `pitchCurrentSlide()` - 8 edges
9. `sendFounderReply()` - 8 edges
10. `testAllConnections()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `1. Track: Best Use of Gemma 4 (via Gemini API)` --references--> `Gemma4Router`  [INFERRED]
  README.md → engine.py
- `2. Track: Open-Source / Open-Weight AI & Agent Skills` --references--> `Gemma4Router`  [INFERRED]
  README.md → engine.py
- `Architectural Component Breakdown` --references--> `Gemma4Router`  [INFERRED]
  README.md → engine.py
- `Hackathon Track & Sponsor Compliance Disclosures` --references--> `_persist_skill_md()`  [INFERRED]
  README.md → app.py
- `3. Compulsory Sponsor Integration — Graphify Knowledge Graph` --references--> `verdict()`  [INFERRED]
  README.md → app.py

## Import Cycles
- None detected.

## Communities (16 total, 6 thin omitted)

### Community 1 - "_persist_skill_md"
Cohesion: 0.25
Nodes (4): _persist_skill_md(), post_ping(), post_skill(), reset_state()

### Community 2 - "Gemma4Router"
Cohesion: 0.17
Nodes (6): extract_json_safely(), Gemma4Router, 1. Track: Best Use of Gemma 4 (via Gemini API), 2. Track: Open-Source / Open-Weight AI & Agent Skills, 3. Compulsory Sponsor Integration — Graphify Knowledge Graph, Hackathon Track & Sponsor Compliance Disclosures

### Community 3 - "app.js"
Cohesion: 0.20
Nodes (27): appendChat(), cachedPingResults, callInterrogate(), downloadSkill(), escapeHtml(), fetchSkillPreview(), formatPingBadge(), generateVerdict() (+19 more)

### Community 4 - "decks.js"
Cohesion: 0.26
Nodes (13): dataUrlToBlob(), drawSlideToCanvas(), getSlideBlob(), handleFileUpload(), loadImageDownscaled(), loadPDF(), loadSampleDeck(), nextSlide() (+5 more)

### Community 6 - "HotSeat AI"
Cohesion: 0.10
Nodes (18): 1. Material Cross-Slide Contradictions & Audit Flags, 2. Synthesized Institutional Diligence Guardrails (Gemma 4 Live Loop), 3. Pre-Committee Verification Protocol, Institutional Pitch-Defense Skill — Fintech (Cross-Border B2B Treasury & Payments), 1. Clone the Repository & Create a Virtual Environment, 2. Install Dependencies, 3. Configure Environment Variables (`.env` or Infisical Secret Sync), 4. Start the FastAPI Diligence Server (+10 more)

### Community 9 - "worker.js"
Cohesion: 0.22
Nodes (14): arrayBufferToBase64(), buildInterrogationPrompt(), buildVerdictPrompt(), callGeminiCascade(), clamp(), CLOUD_CASCADE, compileSkillMd(), CORS_HEADERS (+6 more)

### Community 10 - "package.json"
Cohesion: 0.13
Nodes (14): description, devDependencies, wrangler, main, name, private, scripts, deploy (+6 more)

### Community 12 - "_compile_skill_md"
Cohesion: 0.25
Nodes (5): _compile_skill_md(), get_skill(), 4-Stage Cognitive Diligence Pipeline, Architectural Component Breakdown, System Architecture

### Community 13 - "JSONResponse"
Cohesion: 0.32
Nodes (3): get_ping(), get_state(), health_check()

### Community 14 - "verdict"
Cohesion: 0.33
Nodes (3): _build_verdict_prompt(), _clamp(), verdict()

## Knowledge Gaps
- **1 isolated node(s):** `wrangler`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 82 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Gemma4Router` connect `Gemma4Router` to `engine.py`, `app.py`, `_compile_skill_md`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Gemma4Router` (e.g. with `1. Track: Best Use of Gemma 4 (via Gemini API)` and `2. Track: Open-Source / Open-Weight AI & Agent Skills`) actually correct?**
  _`Gemma4Router` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `wrangler` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `engine.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Why does `HotSeat AI` connect `HotSeat AI` to `Gemma4Router`, `_compile_skill_md`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Should `HotSeat AI` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Why does `Architectural Component Breakdown` connect `_compile_skill_md` to `worker.js`, `Gemma4Router`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
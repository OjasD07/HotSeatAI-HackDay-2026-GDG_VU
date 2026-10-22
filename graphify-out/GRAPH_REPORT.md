# Graph Report - HotSeatAI-HackDay-2026-GDG_VU  (2026-10-22)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 149 nodes · 257 edges · 9 communities (6 shown, 3 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `11c1930d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app.py
- interrogate
- Gemma4Router
- app.js
- decks.js
- HotSeat AI
- CLAUDE.md
- .claude/CLAUDE.md

## God Nodes (most connected - your core abstractions)
1. `Gemma4Router` - 14 edges
2. `extract_json_safely()` - 10 edges
3. `handleInterrogationResponse()` - 10 edges
4. `interrogate()` - 9 edges
5. `appendChat()` - 8 edges
6. `generateVerdict()` - 8 edges
7. `pitchCurrentSlide()` - 8 edges
8. `sendFounderReply()` - 8 edges
9. `testAllConnections()` - 8 edges
10. `HotSeat AI` - 8 edges

## Surprising Connections (you probably didn't know these)
- `1. Track: Best Use of Gemma 4 (via Gemini API)` --references--> `Gemma4Router`  [INFERRED]
  README.md → engine.py
- `2. Track: Open-Source / Open-Weight AI & Agent Skills` --references--> `Gemma4Router`  [INFERRED]
  README.md → engine.py
- `3. Compulsory Sponsor Integration — Graphify Knowledge Graph` --references--> `Gemma4Router`  [INFERRED]
  README.md → engine.py
- `Architectural Component Breakdown` --references--> `_compile_skill_md()`  [INFERRED]
  README.md → app.py
- `Hackathon Track & Sponsor Compliance Disclosures` --references--> `_persist_skill_md()`  [INFERRED]
  README.md → app.py

## Import Cycles
- None detected.

## Communities (9 total, 3 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.08
Nodes (4): _compile_skill_md(), get_ping(), get_skill(), health_check()

### Community 1 - "interrogate"
Cohesion: 0.11
Nodes (11): _build_interrogation_prompt(), _build_verdict_prompt(), _clamp(), get_state(), interrogate(), _persist_skill_md(), post_ping(), post_skill() (+3 more)

### Community 2 - "Gemma4Router"
Cohesion: 0.14
Nodes (8): extract_json_safely(), Gemma4Router, 1. Track: Best Use of Gemma 4 (via Gemini API), 2. Track: Open-Source / Open-Weight AI & Agent Skills, 4-Stage Cognitive Diligence Pipeline, Architectural Component Breakdown, Hackathon Track & Sponsor Compliance Disclosures, System Architecture

### Community 3 - "app.js"
Cohesion: 0.20
Nodes (27): appendChat(), cachedPingResults, callInterrogate(), downloadSkill(), escapeHtml(), fetchSkillPreview(), formatPingBadge(), generateVerdict() (+19 more)

### Community 4 - "decks.js"
Cohesion: 0.26
Nodes (13): dataUrlToBlob(), drawSlideToCanvas(), getSlideBlob(), handleFileUpload(), loadImageDownscaled(), loadPDF(), loadSampleDeck(), nextSlide() (+5 more)

### Community 6 - "HotSeat AI"
Cohesion: 0.11
Nodes (17): 1. Material Cross-Slide Contradictions & Audit Flags, 2. Synthesized Institutional Diligence Guardrails (Gemma 4 Live Loop), 3. Pre-Committee Verification Protocol, Institutional Pitch-Defense Skill — Enterprise SaaS, 1. Clone the Repository & Create a Virtual Environment, 2. Install Dependencies, 3. Configure Environment Variables (`.env`), 4. Start the FastAPI Diligence Server (+9 more)

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HotSeat AI` connect `HotSeat AI` to `Gemma4Router`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Gemma4Router` (e.g. with `1. Track: Best Use of Gemma 4 (via Gemini API)` and `2. Track: Open-Source / Open-Weight AI & Agent Skills`) actually correct?**
  _`Gemma4Router` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07661290322580645 - nodes in this community are weakly interconnected._
- **Why does `Hackathon Track & Sponsor Compliance Disclosures` connect `Gemma4Router` to `interrogate`, `HotSeat AI`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `extract_json_safely()` (e.g. with `3. Compulsory Sponsor Integration — Graphify Knowledge Graph` and `Architectural Component Breakdown`) actually correct?**
  _`extract_json_safely()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `interrogate` be split into smaller, more focused modules?**
  _Cohesion score 0.11231884057971014 - nodes in this community are weakly interconnected._
- **Why does `Gemma4Router` connect `Gemma4Router` to `app.py`, `interrogate`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
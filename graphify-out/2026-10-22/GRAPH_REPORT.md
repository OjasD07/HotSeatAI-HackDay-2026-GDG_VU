# Graph Report - HotSeatAI-HackDay-2026-GDG_VU  (2026-10-22)

## Corpus Check
- 7 files · ~14,045 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .example 1)

## Summary
- 102 nodes · 152 edges · 11 communities (6 shown, 5 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f7dd3293`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- engine.py
- interrogate
- Gemma4Router
- verdict
- get_skill
- HotSeat AI
- CLAUDE.md
- .claude/CLAUDE.md
- JSONResponse
- interrogate

## God Nodes (most connected - your core abstractions)
1. `Gemma4Router` - 14 edges
2. `extract_json_safely()` - 10 edges
3. `interrogate()` - 9 edges
4. `_persist_skill_md()` - 7 edges
5. `verdict()` - 7 edges
6. `HotSeat AI` - 7 edges
7. `Hackathon Track & Sponsor Compliance Disclosures` - 6 edges
8. `Quickstart & Local Setup Instructions` - 6 edges
9. `_compile_skill_md()` - 5 edges
10. `reset_state()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `Hackathon Track & Sponsor Compliance Disclosures` --references--> `_persist_skill_md()`  [INFERRED]
  README.md → app.py
- `3. Compulsory Sponsor Integration — Graphify Knowledge Graph` --references--> `interrogate()`  [INFERRED]
  README.md → app.py
- `3. Compulsory Sponsor Integration — Graphify Knowledge Graph` --references--> `verdict()`  [INFERRED]
  README.md → app.py
- `3. Compulsory Sponsor Integration — Graphify Knowledge Graph` --references--> `extract_json_safely()`  [INFERRED]
  README.md → engine.py
- `Architectural Component Breakdown` --references--> `extract_json_safely()`  [INFERRED]
  README.md → engine.py

## Import Cycles
- None detected.

## Communities (11 total, 5 thin omitted)

### Community 1 - "interrogate"
Cohesion: 0.25
Nodes (4): _persist_skill_md(), post_ping(), post_skill(), reset_state()

### Community 2 - "Gemma4Router"
Cohesion: 0.18
Nodes (5): Gemma4Router, 1. Track: Best Use of Gemma 4 (via Gemini API), 2. Track: Open-Source / Open-Weight AI & Agent Skills, 3. Compulsory Sponsor Integration — Graphify Knowledge Graph, Hackathon Track & Sponsor Compliance Disclosures

### Community 4 - "verdict"
Cohesion: 0.33
Nodes (3): _build_verdict_prompt(), _clamp(), verdict()

### Community 5 - "get_skill"
Cohesion: 0.25
Nodes (5): _compile_skill_md(), get_skill(), 4-Stage Cognitive Diligence Pipeline, Architectural Component Breakdown, System Architecture

### Community 6 - "HotSeat AI"
Cohesion: 0.11
Nodes (16): 1. Material Cross-Slide Contradictions & Audit Flags, 2. Synthesized Institutional Diligence Guardrails (Gemma 4 Live Loop), 3. Pre-Committee Verification Protocol, Institutional Pitch-Defense Skill — Enterprise SaaS, 1. Clone the Repository & Create a Virtual Environment, 2. Install Dependencies, 3. Configure Environment Variables (`.env`), 4. Start the FastAPI Diligence Server (+8 more)

### Community 9 - "JSONResponse"
Cohesion: 0.32
Nodes (3): get_ping(), get_state(), health_check()

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HotSeat AI` connect `HotSeat AI` to `Gemma4Router`, `get_skill`?**
  _High betweenness centrality (0.292) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Gemma4Router` (e.g. with `1. Track: Best Use of Gemma 4 (via Gemini API)` and `2. Track: Open-Source / Open-Weight AI & Agent Skills`) actually correct?**
  _`Gemma4Router` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `engine.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14166666666666666 - nodes in this community are weakly interconnected._
- **Why does `Hackathon Track & Sponsor Compliance Disclosures` connect `Gemma4Router` to `interrogate`, `HotSeat AI`?**
  _High betweenness centrality (0.255) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `extract_json_safely()` (e.g. with `3. Compulsory Sponsor Integration — Graphify Knowledge Graph` and `Architectural Component Breakdown`) actually correct?**
  _`extract_json_safely()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `HotSeat AI` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
- **Why does `Gemma4Router` connect `Gemma4Router` to `engine.py`, `app.py`, `get_skill`?**
  _High betweenness centrality (0.233) - this node is a cross-community bridge._
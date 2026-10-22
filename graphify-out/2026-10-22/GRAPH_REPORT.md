# Graph Report - HotSeatAI-HackDay-2026-GDG_VU  (2026-10-22)

## Corpus Check
- 7 files · ~13,202 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .example 1)

## Summary
- 92 nodes · 131 edges · 10 communities (5 shown, 5 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0b34a818`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- engine.py
- interrogate
- Gemma4Router
- app.py
- 🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine
- get_skill
- Institutional Pitch-Defense Skill — Awaiting Deck Artifact
- CLAUDE.md
- .claude/CLAUDE.md
- JSONResponse

## God Nodes (most connected - your core abstractions)
1. `Gemma4Router` - 10 edges
2. `extract_json_safely()` - 9 edges
3. `interrogate()` - 8 edges
4. `_persist_skill_md()` - 6 edges
5. `verdict()` - 6 edges
6. `reset_state()` - 5 edges
7. `get_skill()` - 5 edges
8. `post_skill()` - 5 edges
9. `🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine` - 5 edges
10. `🚀 Quickstart` - 5 edges

## Surprising Connections (you probably didn't know these)
- `✨ Key Capabilities` --references--> `extract_json_safely()`  [INFERRED]
  README.md → engine.py

## Import Cycles
- None detected.

## Communities (10 total, 5 thin omitted)

### Community 1 - "interrogate"
Cohesion: 0.16
Nodes (6): _build_interrogation_prompt(), interrogate(), _persist_skill_md(), post_ping(), post_skill(), reset_state()

### Community 3 - "app.py"
Cohesion: 0.15
Nodes (3): _build_verdict_prompt(), _clamp(), verdict()

### Community 4 - "🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine"
Cohesion: 0.20
Nodes (9): 1. Local Setup, 2. Running with Local Open-Weight Gemma 4 (Ollama), 3. Docker Deployment, 4. Graphify Repository Knowledge Graph (`graphify-out/`), Author, 🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine, ✨ Key Capabilities, 🚀 Quickstart (+1 more)

### Community 6 - "Institutional Pitch-Defense Skill — Awaiting Deck Artifact"
Cohesion: 0.40
Nodes (4): 1. Material Cross-Slide Contradictions & Audit Flags, 2. Synthesized Institutional Diligence Guardrails (Gemma 4 Live Loop), 3. Pre-Committee Verification Protocol, Institutional Pitch-Defense Skill — —

### Community 9 - "JSONResponse"
Cohesion: 0.32
Nodes (3): get_ping(), get_state(), health_check()

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `extract_json_safely()` connect `engine.py` to `Gemma4Router`, `🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine`?**
  _High betweenness centrality (0.212) - this node is a cross-community bridge._
- **Should `engine.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14166666666666666 - nodes in this community are weakly interconnected._
- **Why does `Gemma4Router` connect `Gemma4Router` to `engine.py`, `app.py`?**
  _High betweenness centrality (0.190) - this node is a cross-community bridge._
- **Why does `✨ Key Capabilities` connect `🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine` to `engine.py`?**
  _High betweenness centrality (0.160) - this node is a cross-community bridge._
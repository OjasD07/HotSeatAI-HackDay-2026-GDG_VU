# Graph Report - HotSeatAI-HackDay-2026-GDG_VU  (2026-10-22)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 83 nodes · 113 edges · 10 communities (4 shown, 6 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b225c339`
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
1. `extract_json_safely()` - 8 edges
2. `interrogate()` - 8 edges
3. `Gemma4Router` - 7 edges
4. `_persist_skill_md()` - 6 edges
5. `verdict()` - 6 edges
6. `post_skill()` - 5 edges
7. `reset_state()` - 5 edges
8. `get_skill()` - 5 edges
9. `🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine` - 5 edges
10. `🚀 Quickstart` - 5 edges

## Surprising Connections (you probably didn't know these)
- `✨ Key Capabilities` --references--> `extract_json_safely()`  [INFERRED]
  README.md → engine.py

## Import Cycles
- None detected.

## Communities (10 total, 6 thin omitted)

### Community 1 - "interrogate"
Cohesion: 0.20
Nodes (5): _build_interrogation_prompt(), interrogate(), _persist_skill_md(), post_skill(), reset_state()

### Community 3 - "app.py"
Cohesion: 0.15
Nodes (3): _build_verdict_prompt(), _clamp(), verdict()

### Community 4 - "🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine"
Cohesion: 0.20
Nodes (9): 1. Local Setup, 2. Running with Local Open-Weight Gemma 4 (Ollama), 3. Docker Deployment, 4. Graphify Repository Knowledge Graph (`graphify-out/`), Author, 🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine, ✨ Key Capabilities, 🚀 Quickstart (+1 more)

### Community 6 - "Institutional Pitch-Defense Skill — Awaiting Deck Artifact"
Cohesion: 0.40
Nodes (4): 1. Material Cross-Slide Contradictions & Audit Flags, 2. Synthesized Institutional Diligence Guardrails (Gemma 4 Live Loop), 3. Pre-Committee Verification Protocol, Institutional Pitch-Defense Skill — —

## Knowledge Gaps
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `extract_json_safely()` connect `engine.py` to `Gemma4Router`, `🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine`?**
  _High betweenness centrality (0.227) - this node is a cross-community bridge._
- **Should `engine.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14166666666666666 - nodes in this community are weakly interconnected._
- **Why does `✨ Key Capabilities` connect `🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine` to `engine.py`?**
  _High betweenness centrality (0.173) - this node is a cross-community bridge._
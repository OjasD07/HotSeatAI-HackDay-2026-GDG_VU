# Graph Report - HotSeatAI-HackDay-2026-GDG_VU  (2026-10-22)

## Corpus Check
- 7 files · ~15,330 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .example 1)

## Summary
- 78 nodes · 101 edges · 9 communities (4 shown, 5 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `227866b5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- engine.py
- interrogate
- Gemma4Router
- app.py
- 🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine
- get_skill
- HotSeat Pitch-Defense Skill  —  Detecting from pitch...
- CLAUDE.md
- .claude/CLAUDE.md

## God Nodes (most connected - your core abstractions)
1. `interrogate()` - 7 edges
2. `extract_json_safely()` - 7 edges
3. `Gemma4Router` - 7 edges
4. `get_skill()` - 5 edges
5. `post_skill()` - 5 edges
6. `verdict()` - 5 edges
7. `🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine` - 5 edges
8. `🚀 Quickstart` - 5 edges
9. `get_state()` - 4 edges
10. `reset_state()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `✨ Key Capabilities` --references--> `extract_json_safely()`  [INFERRED]
  README.md → engine.py

## Import Cycles
- None detected.

## Communities (9 total, 5 thin omitted)

### Community 1 - "interrogate"
Cohesion: 0.19
Nodes (5): _build_interrogation_prompt(), interrogate(), post_skill(), reset_state(), verdict()

### Community 4 - "🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine"
Cohesion: 0.20
Nodes (9): 1. Local Setup, 2. Running with Local Open-Weight Gemma 4 (Ollama), 3. Docker Deployment, 4. Graphify Repository Knowledge Graph (`graphify-out/`), Author, 🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine, ✨ Key Capabilities, 🚀 Quickstart (+1 more)

### Community 5 - "get_skill"
Cohesion: 0.25
Nodes (3): _compile_skill_md(), get_skill(), get_state()

### Community 6 - "HotSeat Pitch-Defense Skill  —  Detecting from pitch..."
Cohesion: 0.40
Nodes (4): 1. Discovered Cross-Slide Contradictions & Red Flags, 2. Learned Domain & Unit-Economics Guardrails (Hermes Self-Improving Loop), 3. Mandatory Pre-Pitch Verification Checklist, HotSeat Pitch-Defense Skill  —  Detecting from pitch...

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `extract_json_safely()` connect `engine.py` to `Gemma4Router`, `🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine`?**
  _High betweenness centrality (0.230) - this node is a cross-community bridge._
- **Why does `✨ Key Capabilities` connect `🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine` to `engine.py`?**
  _High betweenness centrality (0.181) - this node is a cross-community bridge._
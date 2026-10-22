# Graph Report - HotSeatAI-HackDay-2026-GDG_VU  (2026-10-22)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 58 nodes · 83 edges · 6 communities (2 shown, 4 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6827341c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- engine.py
- post_skill
- Gemma4Router
- interrogate
- get_skill

## God Nodes (most connected - your core abstractions)
1. `Gemma4Router` - 7 edges
2. `interrogate()` - 7 edges
3. `extract_json_safely()` - 6 edges
4. `post_skill()` - 5 edges
5. `verdict()` - 5 edges
6. `get_skill()` - 5 edges
7. `get_state()` - 4 edges
8. `reset_state()` - 4 edges
9. `_compile_skill_md()` - 4 edges
10. `_build_verdict_prompt()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `get_state()` --references--> `get`  [EXTRACTED]
  app.py →   _Bridges community 1 → community 5_
- `interrogate()` --references--> `JSONResponse`  [EXTRACTED]
  app.py →   _Bridges community 4 → community 1_

## Import Cycles
- None detected.

## Communities (6 total, 4 thin omitted)

### Community 1 - "post_skill"
Cohesion: 0.20
Nodes (5): _build_verdict_prompt(), get_state(), post_skill(), reset_state(), verdict()

### Community 4 - "interrogate"
Cohesion: 0.29
Nodes (3): _build_interrogation_prompt(), _clamp(), interrogate()

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Gemma4Router` connect `Gemma4Router` to `engine.py`, `app.py`?**
  _High betweenness centrality (0.250) - this node is a cross-community bridge._
- **Why does `interrogate()` connect `interrogate` to `post_skill`, `app.py`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `get_skill()` connect `get_skill` to `app.py`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
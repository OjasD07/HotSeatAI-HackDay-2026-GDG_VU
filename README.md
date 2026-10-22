<a href="https://www.ojasdeshpande.in" target="_blank"><img src="https://raw.githubusercontent.com/OjasD07/OjasD07/main/Logo.svg" alt="Logo" style="float: ; width: 88px; height: 88px; background: #ffffff; border-radius: 10px; padding: 8px; margin: 0 0 8px 8px;" /></a>


# 🦈 HotSeat AI — Universal VC Pitch Interrogator & Cross-Slide Contradiction Engine

> **Powered by Gemma 4 Multimodal Vision (`gemma-4-26b-a4b-it` / Local Open-Weight Ollama) • Self-Improving Agent `SKILL.md` Compiler • Graphify AST Knowledge Graph**

**HotSeat AI** is an industry-agnostic, multimodal Venture Capital pitch-deck interrogator that visually inspects pitch deck slides, maintains a live **Cross-Slide Claim Ledger**, catches numerical and strategic contradictions across slides and verbal founder defenses, and compiles discovered weaknesses into a portable, self-improving **`.claude/skills/pitch-defense/SKILL.md`** Agent Skill.

---

## ✨ Key Capabilities

1. **👁️ Gemma 4 Multimodal Slide Inspection & Contradiction Engine**
   - Extracts quantitative and strategic claims directly from slide pixels (charts, financial tables, 2×2 matrices, architecture diagrams).
   - Dynamically infers **Industry** and **Business Model** (FinTech, MedTech, D2C Retail, Hardware, Biotech, SaaS, etc.) without hard-coded assumptions.
   - Cross-references every new slide and founder verbal defense against prior entries in the **Cross-Slide Claim Ledger** to catch contradictions (e.g., claiming `$0 CAC` on Slide 1 while budgeting `₹18 Cr Paid Ads ($42 CAC)` on Slide 2).

2. **🔀 Bulletproof Dual-Engine Gemma 4 Router (`engine.py`)**
   - **Cloud Cascade (`gemini_api`)**: Routes through `gemma-4-26b-a4b-it → gemma-4-31b-it → gemma-3-27b-it` via the official `google-genai` SDK with strict multimodal ordering (`[image_part, text_prompt]`).
   - **Local Open-Weight (`ollama`)**: Connects to local Ollama (`http://localhost:11434/api/chat`) and automatically cascades to Gemini API if unreachable.
   - **3-Layer Safe JSON Extractor (`extract_json_safely`)**: Strips `<thought>...</thought>` blocks, removes Markdown fences, and parses outermost JSON braces with a guaranteed zero-500 fallback dictionary.

3. **🎭 4 Investor Personas & Live Conviction Telemetry**
   - Switch on the fly between **🦈 Sand Hill Tier-1 VC**, **📊 Ruthless PE / CFO Auditor**, **🏢 Skeptical Enterprise Buyer**, and **🏆 Hackathon Demo-Day Judge**.
   - Real-time **VC Conviction Score (`0–100`)**, `+Δ / -Δ` turn badges, **Skepticism Heat** (`PROBING → HIGH SKEPTICISM → HOSTILE DILIGENCE`), and **3-Strike Contradiction/Evasion Counter**.

4. **🧪 3 Built-In Multi-Slide Contradiction Benchmark Decks + Client-Side PDF/Image Rasterizer**
   - **🏦 FinTech (`BorderlessPay`)**: `$0 CAC` & `0% Fees` on Slide 1 vs. `₹18 Cr Paid Ads ($42 CAC)` & `2.8% Hidden FX Spread` on Slide 2 + cherry-picked `2x2 Competitor Matrix` omitting Wise & Revolut on Slide 3.
   - **🧬 MedTech (`HemoScan`)**: `100% Offline Edge AI` & `₹10/Scan` on Slide 1 vs. `4K Video Uploaded to Cloud A100 GPU Cluster ($0.65/Scan + ₹15,000/mo)` on Slide 2 + `5,000 Govt Hospitals in 90 Days with Zero CDSCO/FDA Trials` on Slide 3.
   - **🥤 D2C Retail (`AdaptPop`)**: `100% D2C Online (76% Margin)` on Slide 1 vs. `85% Offline Kirana & Supermarkets (35% Distributor Cut + ₹25L Slotting Fees)` on Slide 2 + `Secret Ashwagandha + Lime Flavor Blend` moat on Slide 3.
   - **Zero-Backend PDF & Image Downscaler**: Rasterizes uploaded `.pdf` decks (up to 8 pages via `PDF.js`) and `.png`/`.jpg`/`.webp` images into `1280px` compressed JPEGs (`0.82` quality) entirely in browser memory.

5. **🎙️ Web Speech API Push-to-Talk & Instant Barge-In TTS + 1-Click Judge Simulation Chips**
   - Natural English TTS (`rate = 1.06`) with **Instant Barge-In** (`window.speechSynthesis.cancel()` triggers the moment you click the mic or type in the defense box).
   - **1-Click Judge Simulation Chips** (`💪 Simulate Strong Data-Backed Reply` & `🤡 Simulate Evasive Buzzword Dodge`) let judges test both strong data-backed defenses and evasive buzzword dodges in a single click.

6. **📜 Investment Committee Verdict Memo & 🧠 Self-Improving `SKILL.md` Compiler**
   - Generates a structured IC Verdict (`TERM SHEET OFFERED` / `CONDITIONAL SECOND MEETING` / `HARD PASS`) with 4 score bars (`Market & Timing`, `Unit Economics`, `Defensibility Moat`, `Founder Conviction`), `Biggest Strength`, `Fatal Flaw`, and `3 Mandatory Deck Fixes`.
   - Compiles discovered contradictions and unit-economics guardrails into `.claude/skills/pitch-defense/SKILL.md`.

---

## 🏗️ Repository Architecture

```text
HotSeatAI-HackDay-2026-GDG_VU/
├── app.py                                  # Stateful FastAPI backend (/api/interrogate, /api/verdict, /api/skill, /api/state, /api/reset)
├── engine.py                               # Dual-Engine Gemma4Router (Gemini API cascade + Local Ollama) & 3-layer JSON extractor
├── static/
│   └── index.html                          # Single-page Tailwind War-Room UI, Canvas slide renderer, PDF.js rasterizer, Web Speech API
├── .claude/skills/pitch-defense/SKILL.md   # Compiled self-improving pitch-defense Agent Skill
├── graphify-out/                           # Deterministic AST knowledge graph (graph.json, graph.html, GRAPH_REPORT.md)
├── Dockerfile                              # Lightweight python:3.11-slim container configuration
├── render.yaml                             # 1-Click Render / cloud deployment blueprint
├── requirements.txt                        # Python dependencies
└── .env.example                            # Environment variable template (Gemini API & Local Ollama)
```

---

## 🚀 Quickstart

### 1. Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure your Gemini API key (or use the UI override input box)
cp .env.example .env
export GEMINI_API_KEY="your_gemini_api_key"

# Start the FastAPI server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Open **`http://localhost:8000`** in your browser.

### 2. Running with Local Open-Weight Gemma 4 (Ollama)

```bash
ollama pull gemma4:12b
ollama serve
```

In the HotSeat AI top navigation bar, switch the engine selector to **💻 Local Ollama: Gemma 4 (Open-Weight)**.

### 3. Docker Deployment

```bash
docker build -t hotseat-ai .
docker run -p 8000:8000 -e GEMINI_API_KEY="your_gemini_api_key" hotseat-ai
```

### 4. Graphify Repository Knowledge Graph (`graphify-out/`)

```bash
pip install graphifyy
graphify install --project
python -m graphify . --code-only
GRAPHIFY_BACKEND=none graphify cluster-only .
```

Outputs are generated in:
- `graphify-out/graph.json`
- `graphify-out/graph.html`
- `graphify-out/GRAPH_REPORT.md`


---


## Author

Ojas Deshpande [contact@ojasdeshpande.in]

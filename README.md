---
title: Design System Automation
emoji: 🎨
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
license: mit
---

# Design System Automation

> Extract, analyze, and improve any website's design system — then drop it into Figma as a visual spec. In 15 minutes, not 5 days.

![Version](https://img.shields.io/badge/version-3.2-blue) ![Tests](https://img.shields.io/badge/tests-148%20passing-brightgreen) ![Cost](https://img.shields.io/badge/cost-%240.003%2Frun-orange) ![License](https://img.shields.io/badge/license-MIT-green)

## What It Does

Point it at any live website. The system:

1. **Extracts** every design token (colors, typography, spacing, shadows, radius) from 8 sources
2. **Classifies** colors deterministically using CSS evidence (815 lines, no AI)
3. **Audits** accessibility (WCAG AA/AAA), type scale consistency, spacing grid alignment
4. **Analyzes** with 4 specialized AI agents — brand identification, industry benchmarking, best practices, synthesis
5. **Exports** W3C DTCG-compliant JSON
6. **Generates** a full Figma visual spec via custom plugin

**Cost:** ~$0.003 per analysis. The free rule-based layers do 90% of the work.

## Architecture: Three Layers

```
Layer 1 — Extraction + Normalization (Free, ~90s)
  Playwright visits site at 2 viewports, extracts from 8 CSS sources
  Normalizer: dedup colors, parse radius/shadows, name with numeric shades

Layer 2 — Classification + Rule Engine (Free, <1s)
  Color Classifier: CSS evidence -> category -> token name (deterministic)
  Rule Engine: WCAG contrast, type scale ratio, spacing grid, color stats

Layer 3 — 4 AI Agents (~$0.003)
  AURORA:   Brand color advisor        (Qwen 72B)
  ATLAS:    Industry benchmark advisor  (Llama 3.3 70B)
  SENTINEL: Best practices auditor      (Qwen 72B)
  NEXUS:    Head synthesizer            (Llama 3.3 70B)
```

AI agents are **advisory only** — a strict naming authority chain ensures deterministic, reproducible output:
1. Color Classifier (primary) → 2. AURORA LLM (secondary, semantic roles only) → 3. Normalizer (fallback)

## Quick Start

### Run the App

```bash
git clone https://github.com/hiriazmo/design-system-automation.git
cd design-system-automation

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium

cp config/.env.example config/.env
# Add your HF_TOKEN in .env

python app.py
```

Open `http://localhost:7860`

### Or Use the Hosted Version

**[Live Demo on HuggingFace Spaces](https://huggingface.co/spaces/riazmo/Design-System-Automation)**

### Import to Figma

1. Extract tokens from any website using the app
2. Download the DTCG JSON
3. Load the [Figma plugin](./figma-plugin/) into Figma
4. Upload JSON → get Variables, Styles, and a Visual Spec page

See the [Figma Plugin README](./figma-plugin/README.md) for setup instructions.

## The Workflow

```
Enter URL → Extract AS-IS → Download JSON → Import to Figma (Visual Spec)
                                                      ↓
                                              Review AS-IS spec
                                                      ↓
                                    Run AI Analysis → Accept/Reject suggestions
                                                      ↓
                                    Export TO-BE JSON → Import to Figma
                                                      ↓
                                        Compare AS-IS vs TO-BE side by side
```

## Output Format (W3C DTCG v1)

```json
{
  "color": {
    "brand": {
      "primary": {
        "$type": "color",
        "$value": "#005aa3",
        "$description": "[classifier] brand: primary_action",
        "$extensions": {
          "com.design-system-automation": {
            "frequency": 47,
            "confidence": "high",
            "category": "brand"
          }
        }
      }
    }
  },
  "radius": {
    "md": { "$type": "dimension", "$value": "8px" }
  },
  "shadow": {
    "sm": {
      "$type": "shadow",
      "$value": {
        "offsetX": "0px",
        "offsetY": "2px",
        "blur": "8px",
        "spread": "0px",
        "color": "#00000026"
      }
    }
  }
}
```

Compatible with Tokens Studio, Style Dictionary v4, and any DTCG-compliant tool.

## Project Structure

```
design-system-automation/
├── app.py                        # Main Gradio application (~5000 lines)
├── figma-plugin/                 # Figma plugin for token import + visual spec
│   ├── manifest.json
│   ├── src/code.js               # Plugin logic (v7)
│   └── ui/ui.html                # Plugin UI
├── agents/
│   ├── crawler.py                # Page discovery
│   ├── extractor.py              # 8-source CSS extraction (Playwright)
│   ├── firecrawl_extractor.py    # Deep CSS extraction (Firecrawl)
│   ├── normalizer.py             # Token dedup, naming, normalization
│   ├── llm_agents.py             # AURORA, ATLAS, SENTINEL, NEXUS
│   └── ...
├── core/
│   ├── color_classifier.py       # Deterministic color classification (815 lines)
│   ├── rule_engine.py            # WCAG, type scale, spacing grid analysis
│   ├── color_utils.py            # Color math, contrast, ramp generation
│   ├── token_schema.py           # Pydantic models (DTCG compliant)
│   └── ...
├── config/
│   ├── .env.example              # Environment template
│   ├── settings.py               # Configuration
│   └── agents.yaml               # Agent configurations
├── tests/                        # 148 tests (82 deterministic + 27 agent + 35 live + 4 pipeline)
└── docs/                         # Medium article, LinkedIn post, image guide
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| UI | Gradio |
| Extraction | Playwright + Firecrawl |
| Classification | Custom rule-based (Python) |
| AI Agents | Qwen 72B + Llama 3.3 70B via HuggingFace Inference API |
| Hosting | HuggingFace Spaces (Docker) |
| Figma | Custom plugin (Variables API + Styles API) |
| Token Format | W3C DTCG v1 (October 2025) |
| Tests | pytest — 148 passing |

## Tests

```bash
python -m pytest tests/ -q
```

## License

MIT

---

Built by [Riaz](https://medium.com/@designwithriaz) — a UX Design Manager automating design systems with AI.

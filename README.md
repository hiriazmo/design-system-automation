---
title: Design System Automation v3
emoji: 🎨
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
license: mit
---

# Design System Automation v3

> 🎨 A semi-automated, human-in-the-loop agentic system that reverse-engineers design systems from live websites.

## 🎯 What It Does

When you have a website but no design system documentation (common when the original Sketch/Figma files are lost), this tool helps you:

1. **Crawl** your website to discover pages
2. **Extract** design tokens (colors, typography, spacing, shadows)
3. **Review** and validate extracted tokens with visual previews
4. **Upgrade** your system with modern best practices (optional)
5. **Export** production-ready JSON tokens for Figma/code

## 🧠 Philosophy

This is **not a magic button** — it's a design-aware co-pilot.

- **Agents propose → Humans decide**
- **Every action is visible, reversible, and previewed**
- **No irreversible automation**

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        TECH STACK                            │
├──────────────────────────────────────────────────────────────┤
│  Frontend:       Gradio (interactive UI with live preview)   │
│  Orchestration:  LangGraph (agent workflow management)       │
│  Models:         Claude API (reasoning) + Rule-based         │
│  Browser:        Playwright (crawling & extraction)          │
│  Hosting:        Hugging Face Spaces                         │
└──────────────────────────────────────────────────────────────┘
```

### Agent Personas

| Agent | Persona | Job |
|-------|---------|-----|
| **Agent 1** | Design Archaeologist | Discover pages, extract raw tokens |
| **Agent 2** | Design System Librarian | Normalize, dedupe, structure tokens |
| **Agent 3** | Senior DS Architect | Recommend upgrades (type scales, spacing, a11y) |
| **Agent 4** | Automation Engineer | Generate final JSON for Figma/code |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js (for some dependencies)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd design-system-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy environment file
cp config/.env.example config/.env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Running

```bash
python app.py
```

Open `http://localhost:7860` in your browser.

## 📖 Usage Guide

### Stage 1: Discovery

1. Enter your website URL (e.g., `https://example.com`)
2. Click "Discover Pages"
3. Review discovered pages and select which to extract from
4. Ensure you have a mix of page types (homepage, listing, detail, etc.)

### Stage 2: Extraction

1. Choose viewport (Desktop 1440px or Mobile 375px)
2. Click "Extract Tokens"
3. Review extracted:
   - **Colors**: With frequency, context, and AA compliance
   - **Typography**: Font families, sizes, weights
   - **Spacing**: Values with 8px grid fit indicators
4. Accept or reject individual tokens

### Stage 3: Export

1. Review final token set
2. Export as JSON
3. Import into Figma via Tokens Studio or your plugin

## 📁 Project Structure

```
design-system-automation/
├── app.py                          # Main Gradio application
├── requirements.txt
├── README.md
│
├── config/
│   ├── .env.example                # Environment template
│   ├── agents.yaml                 # Agent personas & settings
│   └── settings.py                 # Configuration loader
│
├── agents/
│   ├── state.py                    # LangGraph state definitions
│   ├── graph.py                    # Workflow orchestration
│   ├── crawler.py                  # Agent 1: Page discovery
│   ├── extractor.py                # Agent 1: Token extraction
│   ├── normalizer.py               # Agent 2: Normalization
│   ├── advisor.py                  # Agent 3: Best practices
│   └── generator.py                # Agent 4: JSON generation
│
├── core/
│   ├── token_schema.py             # Pydantic data models
│   └── color_utils.py              # Color analysis utilities
│
├── ui/
│   └── (Gradio components)
│
└── docs/
    └── CONTEXT.md                  # Context file for AI assistance
```

## 🔧 Configuration

### Environment Variables

```env
# Required
ANTHROPIC_API_KEY=your_key_here

# Optional
DEBUG=false
LOG_LEVEL=INFO
BROWSER_HEADLESS=true
```

### Agent Configuration

Agent personas and behavior are defined in `config/agents.yaml`. This includes:

- Extraction targets (colors, typography, spacing)
- Naming conventions
- Confidence thresholds
- Upgrade options

## 🛠️ Development

### Running Tests

```bash
pytest tests/
```

### Adding New Features

1. Update token schema in `core/token_schema.py`
2. Add agent logic in `agents/`
3. Update UI in `app.py`
4. Update `docs/CONTEXT.md` for AI assistance

## 📦 Output Format

Tokens are exported in a platform-agnostic JSON format:

```json
{
  "metadata": {
    "source_url": "https://example.com",
    "version": "v1-recovered",
    "viewport": "desktop"
  },
  "colors": {
    "primary-500": {
      "value": "#007bff",
      "source": "detected",
      "contrast_white": 4.5
    }
  },
  "typography": {
    "heading-lg": {
      "fontFamily": "Inter",
      "fontSize": "24px",
      "fontWeight": 700
    }
  },
  "spacing": {
    "md": {
      "value": "16px",
      "source": "detected"
    }
  }
}
```

## 🤝 Contributing

Contributions are welcome! Please read the contribution guidelines first.

## 📄 License

MIT

---

Built with ❤️ for designers who've lost their source files.

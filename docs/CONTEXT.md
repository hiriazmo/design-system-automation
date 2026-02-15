# Design System Extractor v2 — Master Context File

> **Upload this file to refresh Claude's context when continuing work on this project.**

**Last Updated:** January 2026

---

## 📁 Files Changed in Latest Session

| File | What Changed |
|------|--------------|
| `agents/extractor.py` | Enhanced 7-source extraction (DOM, CSS vars, SVG, inline, stylesheets, external CSS, page scan) |
| `agents/firecrawl_extractor.py` | **NEW** Agent 1B for deep CSS parsing |
| `agents/semantic_analyzer.py` | **NEW** Agent 1C for semantic color categorization (brand/text/bg/border) |
| `core/preview_generator.py` | AS-IS previews + Color Ramps sorted by brand priority |
| `app.py` | Stage 1 UI now has 6 preview tabs including Semantic Colors |
| `docs/CONTEXT.md` | Updated with semantic analyzer, full architecture diagrams |

---

## 🎯 Project Goal

Build a **semi-automated, human-in-the-loop agentic system** that:
1. Reverse-engineers a design system from a live website
2. Reconstructs and upgrades it into a modern, scalable design system
3. Outputs production-ready JSON tokens (Figma Tokens Studio compatible)

**Philosophy:** This is a design-aware co-pilot, NOT a magic button. Humans decide, agents propose.

---

## 🤔 Why This Project? (Market Differentiation)

### The Problem We Solve

| Pain Point | Who Has It | Current Solutions | Why They Fail |
|------------|------------|-------------------|---------------|
| Legacy websites with no design system | Enterprise teams | Manual audit (weeks) | Time-consuming, error-prone |
| Inconsistent design tokens scattered in CSS | Agencies inheriting projects | Figma plugins (style extractors) | Only extract from Figma, not live sites |
| Need to modernize without breaking existing | Product teams | Design system generators | Generate new, don't reverse-engineer existing |
| AA compliance gaps unknown | Accessibility teams | Contrast checkers | Check one color at a time, no system view |

### Existing Tools & Their Gaps

| Tool | What It Does | Gap We Fill |
|------|--------------|-------------|
| **Figma Tokens Studio** | Manages tokens in Figma | Doesn't extract from websites |
| **Style Dictionary** | Transforms tokens to code | Needs tokens first (we create them) |
| **Polypane/VisBug** | Inspect live sites | No systematic extraction or upgrade |
| **AI Design Tools** (Galileo, Uizard) | Generate new designs | Don't reverse-engineer existing |
| **CSS Stats** | Analyze CSS files | Statistics only, no actionable tokens |
| **Chromatic/Percy** | Visual regression | Compare, don't extract or upgrade |

### Our Unique Value Proposition

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     WHAT MAKES US DIFFERENT                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. REVERSE-ENGINEERING (not generation)                                    │
│     • Extracts from LIVE websites, not design files                         │
│     • Preserves what's working, upgrades what's broken                      │
│     • Respects existing brand decisions                                     │
│                                                                             │
│  2. MULTI-AGENT REASONING (not single LLM)                                  │
│     • Two analysts with different perspectives                              │
│     • HEAD compiler resolves conflicts                                      │
│     • Shows reasoning, not just results                                     │
│                                                                             │
│  3. HUMAN-IN-THE-LOOP (not magic button)                                    │
│     • Designer reviews every stage                                          │
│     • Accept/reject individual tokens                                       │
│     • Choose from upgrade OPTIONS, not forced decisions                     │
│                                                                             │
│  4. VISUAL PREVIEWS (not just data tables)                                  │
│     • Typography rendered in actual detected font                           │
│     • Color ramps with AA compliance per shade                              │
│     • See before you export                                                 │
│                                                                             │
│  5. COST-TRANSPARENT (not black box)                                        │
│     • Shows token usage and cost per analysis                               │
│     • Uses HF free tier ($0.10/mo) or Pro ($2/mo)                          │
│     • ~$0.05 per full analysis                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Target Users

| User | Use Case | Value |
|------|----------|-------|
| **UX Managers** (like you!) | Modernize legacy booking platforms | Weeks → Hours |
| **Design System Teams** | Audit and standardize existing properties | Systematic, not ad-hoc |
| **Agencies** | Onboard client projects with no documentation | Instant design inventory |
| **Accessibility Consultants** | AA compliance audit with fixes | Full palette view |
| **Developers** | Get production-ready tokens from designer's website | No manual translation |

### Why Not Just Use [X]?

**"Why not just inspect the CSS manually?"**
→ You could, but it takes weeks for a complex site. We do it in minutes with systematic coverage.

**"Why not use Figma's native styles?"**
→ Many legacy sites were never in Figma. We extract from the source of truth: the live website.

**"Why do you need AI? Can't rules handle this?"**
→ Rules extract tokens. AI understands *design intent* — why is this color used here? What scale was intended? Where does it deviate from best practices?

**"Isn't this just CSS Stats with AI?"**
→ CSS Stats tells you what exists. We tell you what it *should* be and give you actionable upgrade paths.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TECH STACK                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Frontend:        Gradio (long-scroll, sectioned UI with live preview)      │
│  Orchestration:   LangGraph (agent state management & workflow)             │
│  Models:          HuggingFace Inference Providers (Novita, Groq, etc.)     │
│  Hosting:         Hugging Face Spaces                                       │
│  Storage:         HF Spaces persistent storage                              │
│  Output:          Platform-agnostic JSON tokens (Figma Tokens Studio)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Model Assignments

### Stage 2: Multi-Agent Analysis (4 Named Agents + Rule Engine)

| Agent | Persona | Model | Temperature | Cost |
|-------|---------|-------|-------------|------|
| **Rule Engine** | — (deterministic) | None | — | FREE |
| **AURORA** | Brand Color Analyst | `Qwen/Qwen2.5-72B-Instruct` | 0.4 | ~Free (HF PRO) |
| **ATLAS** | Benchmark Advisor | `meta-llama/Llama-3.3-70B-Instruct` | 0.25 | ~Free (HF PRO) |
| **SENTINEL** | Best Practices Auditor | `Qwen/Qwen2.5-72B-Instruct` | 0.2 | ~Free (HF PRO) |
| **NEXUS** | Head Synthesizer | `meta-llama/Llama-3.3-70B-Instruct` | 0.3 | ~$0.001 |

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: DETERMINISTIC (Free — $0.00)                                      │
│  ├─ WCAG Contrast Checker (actual FG/BG pairs, not just vs white)           │
│  ├─ Type Scale Detection (ratio math, variance, standard comparison)        │
│  ├─ Spacing Grid Analysis (GCD math, alignment %)                           │
│  └─ Color Statistics (unique, near-duplicates, hue distribution)            │
│                                                                             │
│  LAYER 2: 4 AI AGENTS (~$0.003 total)                                       │
│                                                                             │
│   Rule Engine Results                                                        │
│         │                                                                    │
│    ┌────┼────────────────┐                                                   │
│    ↓    ↓                ↓                                                   │
│  ┌────────┐  ┌────────┐  ┌──────────┐                                       │
│  │ AURORA │  │ ATLAS  │  │ SENTINEL │   (analyze in parallel)               │
│  │ Brand  │  │ Bench- │  │ Best     │                                       │
│  │ Colors │  │ marks  │  │ Practices│                                       │
│  │Qwen 72B│  │Llama70B│  │ Qwen 72B │                                       │
│  └───┬────┘  └───┬────┘  └────┬─────┘                                       │
│      └───────────┼────────────┘                                              │
│                  ↓                                                            │
│           ┌───────────┐                                                      │
│           │   NEXUS   │  (final synthesis)                                   │
│           │ Llama 70B │                                                      │
│           │ • Resolve │                                                      │
│           │ • Score   │                                                      │
│           │ • Top 3   │                                                      │
│           └───────────┘                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Other Agents

| Agent | Role | Model | Provider | Why |
|-------|------|-------|----------|-----|
| **Agent 1** | Crawler & Extractor | None (Rule-based) | — | Pure CSS extraction, no LLM needed |
| **Agent 2** | Normalizer | `microsoft/Phi-3.5-mini-instruct` | Novita | Fast, great structured output |
| **Agent 4** | Generator | `mistralai/Codestral-22B-v0.1` | Novita | Code specialist, JSON formatting |

### Provider Configuration

Default provider: **Novita** (configurable in `config/agents.yaml`)

Available providers (via HuggingFace Inference Providers):
- **novita** - Default, good balance
- **groq** - Fastest
- **cerebras** - Ultra-fast
- **sambanova** - Good for Llama
- **together** - Wide model selection

### Cost Tracking

Estimated cost per Stage 2 analysis: **~$0.003**
- Rule Engine: $0.00 (free — pure math)
- AURORA + ATLAS + SENTINEL: ~Free within HF PRO ($9/mo subscription)
- NEXUS: ~$0.001
- HuggingFace PRO tier: $9/month (covers inference for all models)

---

## 👁️ Visual Previews

### Stage 1: AS-IS Previews (No Enhancements)

Shows raw extracted values exactly as found on the website:

| Preview | What It Shows |
|---------|---------------|
| **Typography** | Actual font rendered with detected styles |
| **Colors** | Simple swatches with hex, frequency, context, AA status |
| **Spacing** | Visual bars representing each spacing value |
| **Radius** | Boxes with each border-radius applied |
| **Shadows** | Cards with each box-shadow applied |

### Stage 2: Enhanced Previews (Upgraded)

Shows proposed upgrades and improvements:

| Preview | What It Shows |
|---------|---------------|
| **Typography** | Type scale comparison (1.2, 1.25, 1.333 ratios) |
| **Color Ramps** | 11 shades (50-950) with AA compliance per shade |

---

## 🔍 Enhanced Extraction (Agent 1)

Agent 1 now extracts from **5 sources** to capture ALL colors:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ENHANCED EXTRACTION SOURCES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. DOM Computed Styles                                                     │
│     • window.getComputedStyle(element)                                      │
│     • Captures: color, background-color, border-color, etc.                 │
│                                                                             │
│  2. CSS Variables                                                           │
│     • :root { --primary-color: #3860be; }                                  │
│     • Parses all stylesheets for CSS custom properties                     │
│                                                                             │
│  3. SVG Colors                                                              │
│     • <svg fill="#00c4cc">                                                 │
│     • <path stroke="#3860be">                                              │
│                                                                             │
│  4. Inline Styles                                                           │
│     • <div style="background-color: #bcd432;">                             │
│     • Parses style attributes for color values                             │
│                                                                             │
│  5. Stylesheet Rules                                                        │
│     • Parses CSS rules that may not be applied to visible elements         │
│     • Catches hover states, pseudo-elements, etc.                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Enhanced Logging

### Stage 1 Extraction Logs

Shows detailed extraction progress:
```
============================================================
🖥️ DESKTOP EXTRACTION (1440px)
============================================================

📡 Enhanced extraction from 5 sources:
   1. DOM computed styles (getComputedStyle)
   2. CSS variables (:root { --color: })
   3. SVG colors (fill, stroke)
   4. Inline styles (style='color:')
   5. Stylesheet rules (CSS files)
   6. External CSS files (fetch & parse)
   7. Page content scan (brute-force)

📊 EXTRACTION RESULTS:
   Colors:     45 unique
   Typography: 12 styles
   Spacing:    28 values
   Radius:     8 values
   Shadows:    4 values

🎨 CSS Variables found: 15
   --primary-color: #3860be
   --accent-color: #00c4cc
   --brand-lime: #bcd432
   ... and 12 more

🔄 Normalizing (deduping, naming)...
   ✅ Normalized: 32 colors, 10 typography, 18 spacing

============================================================
🔥 FIRECRAWL CSS EXTRACTION
============================================================

   🌐 Scraping: https://example.com
   ✅ Page scraped (125000 chars)
   📝 Parsing <style> blocks...
      Found 5 style blocks
   🔗 Finding linked CSS files...
      Found 8 CSS files
   📄 Fetching: main.css...
      ✅ Parsed (234 colors)
   📄 Fetching: theme.css...
      ✅ Parsed (45 colors)

📊 FIRECRAWL RESULTS:
   CSS files parsed:    8
   Style blocks parsed: 5
   CSS variables found: 23
   Unique colors found: 156

   🎨 Top colors found:
      #06b2c4 (used 45x)
      #c1df1f (used 38x)
      #373737 (used 120x)

🔀 Merging Firecrawl colors with Playwright extraction...
   ✅ Added 12 new colors from Firecrawl
   📊 Total colors now: 44

============================================================
🧠 SEMANTIC COLOR ANALYSIS
============================================================

   📊 Analyzing 143 colors...
   Using rule-based analysis (no LLM)

📊 SEMANTIC ANALYSIS RESULTS:

   🎨 BRAND COLORS:
      primary: #06b2c4 (high)
         └─ Most frequent saturated color on interactive elements (freq: 33)
      secondary: #c1df1f (medium)
         └─ Second most frequent brand color (freq: 15)

   📝 TEXT COLORS:
      primary: #373737 (high)
      secondary: #666666 (medium)

   🖼️ BACKGROUND COLORS:
      primary: #ffffff (high)
      secondary: #f5f5f5 (medium)

   📈 SUMMARY:
      Total colors analyzed: 143
      Brand colors found: 2
      Clear hierarchy: Yes
      Analysis method: rule-based
```

### Stage 2 LLM Analysis Logs (With Semantic Context)

Shows detailed reasoning from each agent WITH semantic context:

```
============================================================
🧠 STAGE 2: MULTI-AGENT ANALYSIS
============================================================

🧠 SEMANTIC CONTEXT FROM STAGE 1:
   Brand Primary: #06b2c4
   Text Primary: #373737
   Analysis Method: rule-based

=======================================================
🤖 LLM 1: meta-llama/Llama-3.1-70B-Instruct
=======================================================
   Provider: novita
   💰 Cost: $0.29/M in, $0.59/M out
   📝 Task: Typography, Colors, AA, Spacing analysis
   🧠 Semantic context: Yes  ← NEW: LLM knows color roles!

   📊 LLM 1 FINDINGS:
   
   COLORS (with semantic context):
   ├─ Brand Primary (#06b2c4): "Fails AA on white (3.2:1)"
   ├─ Suggested fix: "#0891a8 (4.6:1)"
   └─ Score: 6/10

=======================================================
🎯 HEAD: Compiling final recommendations...
=======================================================

   📥 INPUT: Analyzing outputs from LLM 1 + LLM 2 + Rules + Semantic...
   
   📊 HEAD SYNTHESIS:
   
   COLOR RECOMMENDATIONS (per semantic role):
   ├─ brand.primary: #06b2c4 → Keep for branding, use #0891a8 for text
   ├─ text.primary: #373737 → Keep (passes AA)
   └─ Generate ramps for: brand.primary, brand.secondary, neutral
```

---

## 🤖 Agent Personas

### Agent 1A: Website Crawler & Enhanced Extractor
- **Persona:** Meticulous Design Archaeologist
- **Tool:** Playwright
- **Job:** 
  - Auto-discover 10+ pages from base URL
  - Crawl Desktop (1440px) + Mobile (375px) separately
  - Scroll to bottom + wait for network idle
  - **ENHANCED: Extract from 7 sources:**
    1. DOM computed styles (`getComputedStyle`)
    2. CSS variables (`:root { --primary: #xxx }`)
    3. SVG colors (`fill`, `stroke` attributes)
    4. Inline styles (`style="background-color: #xxx"`)
    5. Stylesheet rules (CSS files, hover states, pseudo-elements)
    6. External CSS files (fetch & parse to bypass CORS)
    7. Page content scan (brute-force regex on HTML)
- **Output:** Raw tokens with frequency, context, confidence, source type

### Agent 1B: Firecrawl CSS Deep Diver
- **Persona:** CSS Deep Diver
- **Tool:** Firecrawl / httpx fallback
- **Job:**
  - Fetch and parse ALL linked CSS files
  - Extract colors from CSS rules and variables
  - Bypass CORS restrictions
  - Find colors missed by DOM inspection
- **Output:** Additional colors merged into main extraction

### Agent 1C: Semantic Color Analyzer (NEW - LLM)
- **Persona:** Design System Semanticist
- **Tool:** Rule-based analysis (LLM optional)
- **Job:**
  - Analyze colors based on actual CSS usage (not guessing)
  - Categorize into semantic roles:
    - **Brand Colors:** Used on buttons, CTAs, links (interactive elements)
    - **Text Colors:** Used with `color` property on p, span, h1-h6
    - **Background Colors:** Used with `background-color` on containers
    - **Border Colors:** Used with `border-color` properties
    - **Feedback Colors:** Error (red), success (green), warning (yellow)
  - Detect color hierarchy (primary → secondary → muted)
- **Input:** Colors WITH context data (css_properties, elements, frequency)
- **Output:** Semantic categorization with confidence levels
- **Why:** Stage 2 LLMs can now give SPECIFIC recommendations per role

### Agent 2: Token Normalizer & Structurer
- **Persona:** Design System Librarian
- **Job:**
  - Clean noisy extraction, dedupe
  - Infer naming patterns
  - Tag tokens as: `detected` | `inferred` | `low-confidence`
- **Output:** Structured token sets with metadata

### Agent 3: Design System Best Practices Advisor
- **Persona:** Senior Staff Design Systems Architect
- **Job:**
  - Research modern DS patterns (Material, Polaris, Carbon, etc.)
  - Propose upgrade OPTIONS (not decisions)
  - Suggest: type scales (3 options), spacing (8px), color ramps (AA compliant), naming conventions
- **Output:** Option sets with rationale

### Agent 4: Plugin & JSON Generator
- **Persona:** Automation Engineer
- **Job:**
  - Convert finalized tokens to Figma-compatible JSON
  - Generate: typography, color (with tints/shades), spacing variables
  - Maintain Desktop + Mobile + version metadata
- **Output:** Production-ready JSON (flat structure for Figma Tokens Studio)

---

## 🖥️ UI Stages (3 Stages)

### Stage 1: Extraction Review (AS-IS)
- **Purpose:** Trust building — show exactly what was extracted
- **Shows:** 
  - Token tables (colors, typography, spacing)
  - **6 Visual Preview Tabs (AS-IS, no enhancements):**
    1. 🔤 Typography — actual font rendered
    2. 🎨 Colors — simple swatches sorted by frequency (no ramps)
    3. 🧠 Semantic Colors — colors organized by usage (brand/text/bg/border)
    4. 📏 Spacing — visual bars
    5. 🔘 Radius — rounded boxes
    6. 🌑 Shadows — shadow cards
- **Human Actions:** Accept/reject tokens, flag anomalies, toggle Desktop↔Mobile

### Stage 2: Upgrade Playground (MOST IMPORTANT)
- **Purpose:** Decision-making through live visuals
- **Shows:** 
  - Side-by-side option selector + live preview
  - **Color Ramps (50-950 shades with AA compliance)**
  - Type scale options (1.2, 1.25, 1.333)
  - **Semantic-aware recommendations:** "Your brand primary #06b2c4 fails AA, consider #0891a8"
- **Human Actions:** Select type scale A/B/C, spacing system, color ramps — preview updates instantly

### Stage 3: Final Review & Export
- **Purpose:** Confidence before export
- **Shows:** Token preview, JSON tree, diff view (original vs final)
- **Human Actions:** Download JSON, save version, label version

---

## 📁 Project Structure

```
design-system-extractor/
├── app.py                          # Gradio main entry point
├── requirements.txt
├── README.md
│
├── config/
│   ├── .env.example                # Environment variables template
│   ├── agents.yaml                 # Agent personas & configurations
│   └── settings.py                 # Application settings
│
├── agents/
│   ├── __init__.py
│   ├── state.py                    # LangGraph state definitions
│   ├── graph.py                    # LangGraph workflow orchestration
│   ├── crawler.py                  # Agent 1A: Website crawler
│   ├── extractor.py                # Agent 1A: Token extraction (7 sources)
│   ├── firecrawl_extractor.py      # Agent 1B: Deep CSS parsing
│   ├── semantic_analyzer.py        # Agent 1C: Semantic color categorization
│   ├── normalizer.py               # Agent 2: Token normalization
│   ├── advisor.py                  # Agent 3: Best practices
│   ├── stage2_graph.py             # Stage 2 multi-agent LLM workflow
│   └── generator.py                # Agent 4: JSON generator
│
├── core/
│   ├── __init__.py
│   ├── color_utils.py              # Color analysis, contrast, ramps
│   ├── preview_generator.py        # HTML preview generation
│   ├── hf_inference.py             # HuggingFace LLM inference
│   └── token_schema.py             # Token data structures (Pydantic)
│
├── ui/
│   └── __init__.py
│
├── templates/
│
├── storage/
│   └── __init__.py
│
├── tests/
│   └── __init__.py
│
└── docs/
    └── CONTEXT.md                  # THIS FILE - upload for context refresh
```

---

## 🔧 Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Viewports | Fixed 1440px + 375px | Simplicity, covers main use cases |
| Scrolling | Bottom + network idle | Captures lazy-loaded content |
| Infinite scroll | Skip | Avoid complexity |
| Modals | Manual trigger | User decides what to capture |
| Color ramps | 5-10 shades, AA compliant | Industry standard |
| Type scales | 3 options (1.25, 1.333, 1.414) | User selects |
| Spacing | 8px base system | Modern standard |
| ML models | Minimal, rule-based preferred | Simplicity, reliability |
| Versioning | HF Spaces persistent storage | Built-in, free |
| Preview | Gradio + iframe (best for dynamic) | Smooth updates |

---

## 📊 Token Schema (Core Data Structures)

```python
class TokenSource(Enum):
    DETECTED = "detected"       # Directly found in CSS
    INFERRED = "inferred"       # Derived from patterns
    UPGRADED = "upgraded"       # User-selected improvement
    
class Confidence(Enum):
    HIGH = "high"               # 10+ occurrences
    MEDIUM = "medium"           # 3-9 occurrences
    LOW = "low"                 # 1-2 occurrences

class Viewport(Enum):
    DESKTOP = "desktop"         # 1440px
    MOBILE = "mobile"           # 375px
```

### Token Types:
- **ColorToken:** value, frequency, contexts, elements, contrast ratios
- **TypographyToken:** family, size, weight, line-height, elements
- **SpacingToken:** value, frequency, contexts, fits_base_8
- **RadiusToken:** value, frequency, elements
- **ShadowToken:** value, frequency, elements

---

## 🔄 LangGraph Workflow

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ URL Input   │
                    └──────┬──────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Agent 1: Discover     │
              │  (find pages)          │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  HUMAN: Confirm pages  │◄─── Checkpoint 1
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  Agent 1: Extract      │
              │  (crawl & extract)     │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  Agent 2: Normalize    │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  HUMAN: Review tokens  │◄─── Checkpoint 2 (Stage 1 UI)
              └───────────┬────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌──────────────────┐            ┌──────────────────┐
│ Agent 3: Advise  │            │  (parallel)      │
│ (best practices) │            │                  │
└────────┬─────────┘            └──────────────────┘
         │
         ▼
┌────────────────────────┐
│  HUMAN: Select options │◄─── Checkpoint 3 (Stage 2 UI)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  Agent 4: Generate     │
│  (final JSON)          │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  HUMAN: Export         │◄─── Checkpoint 4 (Stage 3 UI)
└───────────┬────────────┘
            │
            ▼
      ┌─────────┐
      │   END   │
      └─────────┘
```

---

## 🚦 Human-in-the-Loop Rules

1. **No irreversible automation**
2. **Agents propose → Humans decide**
3. **Every auto action must be:**
   - Visible
   - Reversible
   - Previewed

---

## 📦 Output JSON Format

```json
{
  "metadata": {
    "source_url": "https://example.com",
    "extracted_at": "2025-01-23T10:00:00Z",
    "version": "v1-recovered",
    "viewport": "desktop"
  },
  "colors": {
    "primary": {
      "50": { "value": "#e6f2ff", "source": "upgraded" },
      "500": { "value": "#007bff", "source": "detected" },
      "900": { "value": "#001a33", "source": "upgraded" }
    }
  },
  "typography": {
    "heading-xl": {
      "fontFamily": "Inter",
      "fontSize": "32px",
      "fontWeight": 700,
      "lineHeight": "1.2",
      "source": "detected"
    }
  },
  "spacing": {
    "xs": { "value": "4px", "source": "upgraded" },
    "sm": { "value": "8px", "source": "detected" },
    "md": { "value": "16px", "source": "detected" }
  }
}
```

---

## 🛠️ Implementation Phases & Current Status

### Phase 1 ✅ COMPLETE
- [x] Project structure
- [x] Configuration files
- [x] Token schema (Pydantic models)
- [x] Agent 1: Crawler (page discovery)
- [x] Agent 1: Enhanced Extractor (5-source extraction)
- [x] Agent 2: Normalizer
- [x] Stage 1 UI with 5 AS-IS preview tabs
- [x] LangGraph basic workflow
- [x] JSON export (flat structure for Figma)

### Phase 2 ✅ MOSTLY COMPLETE
- [x] Agent 3: Multi-LLM Advisor (Qwen + Llama + HEAD)
- [x] Stage 2 UI (Upgrade Playground)
- [x] Live preview system (typography, color ramps)
- [x] Enhanced LLM logging with reasoning
- [ ] Accept/Reject checkbox wiring to export

### Phase 3 🔄 IN PROGRESS
- [ ] Agent 4: Generator (component patterns)
- [ ] Stage 3 UI (diff view)
- [ ] Arabic page filtering

### Phase 4 ⏳ PENDING
- [ ] Full LangGraph orchestration
- [ ] HF Spaces deployment
- [ ] Persistent storage
- [ ] MCP Claude / Figma plugin integration (Part 2 of article)

---

## 🐛 Known Issues & Pending Fixes

| Issue | Status | Fix |
|-------|--------|-----|
| Arabic pages included | Pending | Filter `/ar/` URLs in crawler |
| Accept/Reject not wired | Pending | Export should respect checkbox state |
| Stage 1 vs Stage 2 preview confusion | ✅ Fixed | Stage 1 now shows AS-IS (no ramps) |
| Colors missed from CSS variables | ✅ Fixed | Enhanced 5-source extraction |
| JSON nested structure | ✅ Fixed | Flat structure for Figma compatibility |

---

## 🔑 Environment Variables

```env
# Required
HF_TOKEN=your_huggingface_token

# Model Configuration (defaults shown — diverse providers)
AGENT2_MODEL=microsoft/Phi-3.5-mini-instruct      # Microsoft - Fast naming
AGENT3_MODEL=meta-llama/Llama-3.1-70B-Instruct    # Meta - Strong reasoning
AGENT4_MODEL=mistralai/Codestral-22B-v0.1         # Mistral - Code/JSON

# Optional
DEBUG=true
LOG_LEVEL=INFO
```

---

## 📝 Notes for Claude

When continuing this project:
1. **Check current phase** in Implementation Phases section
2. **Review agent personas** in agents.yaml for consistent behavior
3. **Follow token schema** defined in core/token_schema.py
4. **Maintain LangGraph state** consistency across agents
5. **Use Gradio components** from ui/components.py for consistency
6. **Test with** real websites before deployment
7. **Enhanced extraction** captures from 5 sources — check logs to verify
8. **Stage 1 = AS-IS** (no ramps), **Stage 2 = Enhanced** (with ramps)

---

*Last updated: 2025-01-23*

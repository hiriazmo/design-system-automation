# 📸 Image Guide for Episode 6 Article

## Required Images (8-10 total)

### 1. Hero Image
**What:** Screenshot of the Gradio interface showing the full pipeline output
**Where:** After title, before first section
**Specs:** 1200x630px (LinkedIn preview size)
**Content:** Show the Visual Previews section with colors, typography, and NEXUS synthesis visible

### 2. Complete Workflow Diagram
**What:** The 8-step pipeline: Website → Agents → Figma → Compare
**Where:** After "The Complete Workflow" section
**Specs:** 1200x800px
**Content:**
```
🌐 Website URL
     ↓
🤖 AI Agents (7-source extraction)
     ↓
📄 AS-IS JSON
     ↓
🔌 Figma Plugin (Import)
     ↓
📋 AS-IS Specimen (Review)
     ↓
🧠 Rule Engine + 4 AI Agents (Stage 2)
     ↓
☑️ Accept/Reject (Human Decision)
     ↓
📄 TO-BE JSON → 🔌 Figma → 📋 TO-BE Specimen
```

### 3. Two-Layer Architecture Diagram
**What:** Layer 1 (Deterministic, Free) + Layer 2 (4 Named Agents)
**Where:** After "Architecture Overview" section
**Specs:** 1200x600px
**Content:**
```
┌─────────────────────────────────────────────────┐
│  LAYER 1: DETERMINISTIC (Free — $0.00)          │
│  ├─ Crawler + 7-Source Extractor + Normalizer   │
│  ├─ Semantic Color Analyzer (rule-based)        │
│  ├─ WCAG Contrast Checker (math)                │
│  ├─ Type Scale Detection (ratio math)           │
│  ├─ Spacing Grid Analysis (GCD math)            │
│  └─ Color Statistics (deduplication)             │
├─────────────────────────────────────────────────┤
│  LAYER 2: 4 AI AGENTS (~$0.003)                 │
│  ├─ AURORA   — Brand Color Analyst   (Qwen 72B) │
│  ├─ ATLAS    — Benchmark Advisor   (Llama 70B)  │
│  ├─ SENTINEL — Best Practices Auditor (Qwen 72B)│
│  └─ NEXUS    — Head Synthesizer    (Llama 70B)  │
└─────────────────────────────────────────────────┘
```

### 4. Agent Pipeline Flow
**What:** Show the 4 named agents with their flow: parallel analysis → synthesis
**Where:** After "Layer 2" section header
**Specs:** 1200x500px
**Content:**
```
   Rule Engine Results
         │
    ┌────┼────────────────┐
    ↓    ↓                ↓
┌──────┐ ┌──────┐ ┌────────┐
│AURORA│ │ATLAS │ │SENTINEL│
│Brand │ │Bench │ │Audit   │
│Qwen  │ │Llama │ │Qwen    │
└──┬───┘ └──┬───┘ └───┬────┘
   └────────┼──────────┘
            ↓
      ┌──────────┐
      │  NEXUS   │
      │Synthesis │
      │ Llama 70B│
      └──────────┘
            ↓
    Final Recommendations
```

### 5. 7 Extraction Sources Visual
**What:** Show the 7 different methods of extraction
**Where:** After "Stage 1: Extraction" section
**Specs:** 1000x600px
**Content:**
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ 1. Computed │  │ 2. CSS      │  │ 3. Inline   │
│    Styles   │  │    Variables│  │    Styles   │
└─────────────┘  └─────────────┘  └─────────────┘

┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ 4. SVG      │  │ 5. External │  │ 6. Style    │
│    Attrs    │  │    CSS Files│  │    Blocks   │
└─────────────┘  └─────────────┘  └─────────────┘

┌─────────────────────────────────────────────────┐
│              7. Firecrawl Deep Parser            │
└─────────────────────────────────────────────────┘
```

### 6. Rule Engine Output Screenshot
**What:** Screenshot of actual rule engine output in the Gradio logs panel
**Where:** After "The Rule Engine" section
**Specs:** 1200x600px
**Content:** Show the actual emoji-formatted output:
- 📐 TYPE SCALE ANALYSIS
- ♿ ACCESSIBILITY CHECK
- 📏 SPACING GRID
- 📊 CONSISTENCY SCORE

### 7. NEXUS Synthesis Output
**What:** Screenshot of the final synthesis with scores, top 3 actions, color recommendations
**Where:** After "Agent 4: NEXUS" section
**Specs:** 1200x700px
**Content:** Show the final output with:
- Executive summary
- Scores dashboard (overall, accessibility, consistency, organization)
- Top 3 actions with impact/effort
- Color recommendations with accept/reject checkboxes

### 8. Benchmark Comparison Table
**What:** Screenshot of the benchmark comparison showing match percentages
**Where:** After "Agent 2: ATLAS" section
**Specs:** 1000x400px
**Content:** Show:
- 🥇 Polaris: 87% match
- 🥈 Material 3: 77% match
- 🥉 Atlassian: 76% match

### 9. Before/After Comparison
**What:** Side-by-side showing AS-IS vs TO-BE
**Where:** After "Comparing AS-IS vs TO-BE" section
**Specs:** 1200x500px
**Content:**
```
AS-IS                          TO-BE
─────                          ─────
Type: ~1.18 (random)    →     1.25 (Major Third)
Brand: #06b2c4 (AA: 3.2) →   #048391 (AA: 4.5)
Spacing: Mixed           →    8px grid
Colors: 143 unique       →    ~20 semantic
Score: 52/100            →    78/100
```

### 10. Cost Comparison Table
**What:** Visual table comparing V1 vs V2 costs + model assignments
**Where:** After "Cost & Model Strategy" section
**Specs:** 1000x400px
**Content:**
```
Agent       Model        Cost
────────────────────────────
Rule Engine  None         $0.00
AURORA       Qwen 72B     ~Free (HF PRO)
ATLAS        Llama 70B    ~Free (HF PRO)
SENTINEL     Qwen 72B     ~Free (HF PRO)
NEXUS        Llama 70B    ~$0.001
─────────────────────────────
TOTAL                     ~$0.003
```

### 11. Figma Specimen (If Available)
**What:** Screenshot of the Figma specimen page after JSON import
**Where:** After "The Figma Bridge" section
**Specs:** 1200x700px
**Content:** Show Typography + Semantic Colors + Spacing display

---

## Image Creation Tools

**Recommended:**
1. **Figma** — Architecture diagrams, pipeline flows, tech stack
2. **Screenshot tool** — Gradio interface captures (use dark mode)
3. **Excalidraw** — Quick hand-drawn style diagrams (for the architecture)

**Tips:**
- Use dark background screenshots (Gradio dark mode)
- Add subtle drop shadows to screenshots
- Keep consistent color scheme (blues + cyans match brand color #06b2c4)
- Use the agent names (AURORA, ATLAS, SENTINEL, NEXUS) in diagram labels
- Color-code: Layer 1 = green (free), Layer 2 = blue (AI)

---

## File Naming Convention

```
episode6-hero-dashboard.png
episode6-workflow-8steps.png
episode6-architecture-2layers.png
episode6-agent-pipeline.png
episode6-extraction-7sources.png
episode6-rule-engine-output.png
episode6-nexus-synthesis.png
episode6-benchmark-comparison.png
episode6-before-after.png
episode6-cost-table.png
episode6-figma-specimen.png
```

---

## Screenshot Checklist

Before taking screenshots:
- [ ] Clear any sensitive data
- [ ] Use dark mode (Gradio)
- [ ] Expand relevant sections
- [ ] Hide browser bookmarks bar
- [ ] Use a clean browser profile
- [ ] Set consistent window size (1440px wide)
- [ ] Run a real analysis so outputs are populated
- [ ] Ensure agent names (AURORA, ATLAS, etc.) are visible in logs

# AI in My Daily Work — Episode 6: Reverse-Engineering Design Systems with 4 AI Agents, a Rule-Based Color Classifier & a Free Rule Engine

## A Semi-Automated Workflow: From Website URL to Figma-Ready Design System (v3.2)

*How I built a system that extracts any website's design tokens, classifies colors deterministically, audits them like a senior design team, and generates a visual spec in Figma — for ~$0.003 per run.*

[IMAGE: Hero - Complete workflow showing Website -> AI Agents -> Figma Visual Spec]

---

## The Problem Every Designer Knows

I've been managing design systems for consumer-facing apps for over 10 years. And there's one task that never gets easier: **auditing existing websites to extract their design tokens.**

Whether it's analyzing a competitor, inheriting a legacy project, or bringing consistency to a sprawling multi-brand portfolio, the process is always the same:

1. Open DevTools
2. Inspect elements one by one
3. Copy hex codes to a spreadsheet
4. Manually check contrast ratios
5. Try to identify the type scale (is it 1.2? 1.25? Random?)
6. Repeat for spacing, shadows, border radius...
7. Spend days organizing into a coherent system
8. Manually recreate in Figma as variables
9. Manually build a visual spec page

I've done this dozens of times. It takes **3-5 days** for a single website. And by the time you're done, something has already changed.

I wanted a system that could think like a design team:

- a **data engineer** extracting and normalizing every token
- a **color scientist** classifying colors by actual CSS usage (not guessing)
- an **analyst** identifying brand colors and patterns
- a **senior reviewer** benchmarking against industry standards
- and a **chief architect** synthesizing everything into action

So I built one. Three versions later, here's what works.

---

## The Solution (In One Sentence)

I built a 3-layer system — deterministic extraction + rule-based color classification + 4 AI agents — that acts like an entire design audit team. It outputs W3C DTCG-compliant JSON that feeds directly into Figma via a custom plugin that auto-generates a visual spec page. Cost: ~$0.003 per analysis.

---

## The Complete Workflow

[IMAGE: Full workflow diagram showing all 8 steps]

Here's the end-to-end process I now use:

```
+--------------------------------------------------------------+
|                    MY DESIGN SYSTEM WORKFLOW                    |
+--------------------------------------------------------------+
|                                                                |
|  STEP 1: Extract AS-IS (AI Agent App)                         |
|  ----------------------------------------                     |
|  * Enter website URL                                          |
|  * AI auto-discovers pages                                    |
|  * Extracts colors, typography, spacing, shadows, radius      |
|  * Normalizes: dedup, sort, name (radius, shadows, colors)    |
|  * Color Classifier: deterministic role assignment             |
|  * Rule Engine: WCAG + type scale + spacing grid              |
|  * Download AS-IS JSON (W3C DTCG v1 format)                  |
|                                                                |
|                           |                                    |
|                           v                                    |
|                                                                |
|  STEP 2: Import to Figma (My Plugin)                          |
|  ----------------------------------------                     |
|  * Open Figma                                                 |
|  * Upload AS-IS JSON via custom plugin                        |
|  * Plugin auto-detects DTCG format                            |
|  * Creates Variables + Paint/Text/Effect Styles                |
|  * Auto-generates Visual Spec Page                            |
|                                                                |
|                           |                                    |
|                           v                                    |
|                                                                |
|  STEP 3: View AS-IS Visual Spec (Figma)                       |
|  ----------------------------------------                     |
|  * Typography (Desktop + Mobile) with AA badges               |
|  * Colors organized by semantic role                           |
|  * Spacing scale, Radius display, Shadow elevation            |
|  * Review what exists before modernizing                      |
|                                                                |
|                           |                                    |
|                           v                                    |
|                                                                |
|  STEP 4: AI Analysis (AI Agent App - Stage 2)                 |
|  ----------------------------------------                     |
|  * Free Rule Engine: WCAG, type scale, spacing grid           |
|  * AURORA: Brand color identification (advisory)              |
|  * ATLAS: Industry benchmark comparison (8 systems)           |
|  * SENTINEL: Best practices audit with priorities             |
|  * NEXUS: Final synthesis resolving all contradictions         |
|                                                                |
|                           |                                    |
|                           v                                    |
|                                                                |
|  STEP 5: Accept/Reject Suggestions (AI Agent App)             |
|  ----------------------------------------                     |
|  * Review each recommendation                                 |
|  * Accept or Reject individually                              |
|  * I stay in control of what changes                          |
|                                                                |
|                           |                                    |
|                           v                                    |
|                                                                |
|  STEP 6: Export TO-BE (AI Agent App - Stage 3)                |
|  ----------------------------------------                     |
|  * Generate modernized TO-BE JSON (DTCG compliant)            |
|  * Contains accepted improvements                             |
|  * Download new JSON file                                     |
|                                                                |
|                           |                                    |
|                           v                                    |
|                                                                |
|  STEP 7: Import TO-BE to Figma (My Plugin)                    |
|  ----------------------------------------                     |
|  * Upload TO-BE JSON via same plugin                          |
|  * Figma Variables update with new values                     |
|  * New Visual Spec generated for comparison                   |
|                                                                |
|                           |                                    |
|                           v                                    |
|                                                                |
|  STEP 8: Compare AS-IS vs TO-BE (Figma)                       |
|  ----------------------------------------                     |
|  * Side-by-side visual spec pages                             |
|  * See exactly what changed and why                           |
|  * Ready to use in production                                 |
|                                                                |
+--------------------------------------------------------------+
```

**Total time:** ~15 minutes (vs 3-5 days manual)

---

## Architecture Overview: Three Layers, One Clear Authority Chain

My first attempt (V1) made a classic mistake:
**I used a large language model for everything.**

V1 cost $0.50-1.00 per run, took 15+ seconds for basic math, and LLMs hallucinated contrast ratios.

V2 split the work into rules vs AI. Better, but a new problem emerged: **three competing naming systems** for colors. The normalizer used word-based shades ("blue.light"), the export layer used numeric shades ("blue.500"), and the LLM agent used whatever it felt like ("brand.primary"). The output in Figma was chaos.

V3 fixed this with a clear authority chain and a dedicated color classifier:

> **Rule-based code handles certainty. LLMs handle ambiguity. And there's ONE naming authority.**

[IMAGE: Architecture diagram - Layer 1 (Extraction) -> Layer 2 (Classification + Analysis) -> Layer 3 (4 Named Agents)]

```
+--------------------------------------------------+
|  LAYER 1: EXTRACTION + NORMALIZATION (Free)       |
|  +- Crawler + 7-Source Extractor (Playwright)     |
|  +- Normalizer: colors, radius, shadows, typo     |
|  |   +- Radius: parse, deduplicate, sort, name   |
|  |   +- Shadows: parse, sort by blur, name        |
|  |   +- Colors: hue + numeric shade (50-900)      |
|  +- Firecrawl: deep CSS parsing (bypass CORS)     |
+--------------------------------------------------+
|  LAYER 2: CLASSIFICATION + RULE ENGINE (Free)     |
|  +- Color Classifier (815 lines, deterministic)   |
|  |   +- CSS evidence -> category -> token name    |
|  |   +- Capped: brand(3), text(3), bg(3), etc.   |
|  |   +- Every decision logged with evidence       |
|  +- WCAG Contrast Checker (actual FG/BG pairs)    |
|  +- Type Scale Detection (ratio math)             |
|  +- Spacing Grid Analysis (GCD math)              |
|  +- Color Statistics (deduplication)               |
+--------------------------------------------------+
|  LAYER 3: 4 AI AGENTS (~$0.003)                   |
|  +- AURORA   - Brand Advisor        (Qwen 72B)   |
|  +- ATLAS    - Benchmark Advisor    (Llama 70B)   |
|  +- SENTINEL - Best Practices Audit (Qwen 72B)   |
|  +- NEXUS    - Head Synthesizer     (Llama 70B)   |
+--------------------------------------------------+
```

### The Naming Authority Chain (V3's Key Innovation)

This was the single hardest problem to solve. In V2, three systems produced color names:

| System | Convention | Example | Problem |
|--------|-----------|---------|---------|
| Normalizer | Word shades | `color.blue.light` | Inconsistent |
| Export function | Numeric shades | `color.blue.500` | Conflicts |
| AURORA LLM | Whatever it wants | `brand.primary` | Unpredictable |

**Result in Figma: `blue.300`, `blue.dark`, `blue.light`, `blue.base` in the same export. Unusable.**

V3 established a clear chain:

```
1. Color Classifier (PRIMARY) - deterministic, covers ALL colors
   +- Rule-based: CSS evidence -> category -> token name
   +- 100% reproducible, logged with evidence

2. AURORA LLM (SECONDARY) - semantic role enhancer ONLY
   +- Can promote "color.blue.500" -> "color.brand.primary"
   +- CANNOT rename palette colors
   +- Only brand/text/bg/border/feedback roles accepted

3. Normalizer (FALLBACK) - preliminary hue+shade names
   +- Only used if classifier hasn't run yet
```

One naming authority. No conflicts. Clean Figma output every time.

---

## Layer 1: Extraction + Normalization (No LLM)

### Extraction: 7 Sources

A Playwright-powered browser visits each page at **two viewports** (1440px desktop + 375px mobile) and extracts every design token from **8 sources**:

[IMAGE: 8 Extraction Sources diagram]

```
--- Playwright (7 internal sources) ---
Source 1: Computed Styles   -> What the browser actually renders
Source 2: CSS Variables     -> --primary-color, --spacing-md
Source 3: Inline Styles     -> style="color: #06b2c4"
Source 4: SVG Attributes    -> fill, stroke colors
Source 5: Stylesheets       -> CSS rules, hover states, pseudo-elements
Source 6: External CSS      -> Fetched & parsed CSS files
Source 7: Page Scan         -> Brute-force regex on style blocks

--- Separate deep extraction ---
Source 8: Firecrawl         -> Deep CSS parsing (bypasses CORS)
```

### Normalization: Not Just Dedup

The normalizer in V2 was a major pain point. Colors got named, but radius and shadows were passed through raw. Multi-value CSS like `"0px 0px 16px 16px"` became garbage tokens. Percentage values like `"50%"` couldn't be used in Figma.

V3's normalizer actually processes everything:

**Colors:** Deduplicate by exact hex + RGB distance < 30. Assign hue family + numeric shade (50-900). Never use words like "light" or "dark" for shades. Add role hints from CSS context for the classifier.

**Radius:** Parse multi-value shorthand (take max), convert rem/em/% to px, deduplicate by resolved value, sort by size, name semantically (none/sm/md/lg/xl/2xl/full). A raw extraction of `["8px", "0px 0px 16px 16px", "50%", "1rem"]` becomes:
```
radius.sm   = 4px    (from 0.25rem context)
radius.md   = 8px
radius.xl   = 16px   (max of 0 0 16 16)
radius.full = 9999px (from 50%)
```

**Shadows:** Parse CSS shadow strings into components (offset, blur, spread, color). Filter out spread-only (border simulation) and inset shadows. Sort by blur radius. Deduplicate by blur bucket. Name by elevation (xs/sm/md/lg/xl). If fewer than 5 shadows extracted, interpolate to always produce 5 elevation levels.

**Cost: $0.00 | Runtime: ~90 seconds**

---

## Layer 2: Color Classification + Rule Engine (No LLM)

### The Color Classifier (V3's Biggest Addition)

This is 815 lines of deterministic code that replaced what AURORA used to do badly.

**The problem it solves:** Given 30+ extracted colors, which is the brand primary? Which are text colors? Which are backgrounds?

An LLM can reason about this, but inconsistently. The same color might be called "brand.primary" in one run and "accent.main" in the next. And it only named 10 colors, leaving the rest in chaos.

The classifier uses CSS evidence:

```
CSS Evidence -> Category:
  background-color on <button> + saturated + freq>5 -> BRAND
  color on <p>/<span> + low saturation              -> TEXT
  background-color on <div>/<body> + neutral         -> BG
  border-color + low saturation                      -> BORDER
  red hue + sat>0.6 + low freq                       -> FEEDBACK (error)
  everything else                                    -> PALETTE (by hue.shade)
```

**Key features:**
- **Aggressive deduplication**: Colors within RGB distance < 30 AND same category get merged (13 text grays become 3)
- **Capped categories**: brand (max 3), text (max 3), bg (max 3), border (max 3), feedback (max 4), palette (rest)
- **User-selectable naming convention**: semantic, tailwind, or material
- **Every decision logged with evidence**: `[DEDUP] merged #1a1a1a with #1b1b1b (dist=1.7)`, `[CLASSIFY] #06b2c4 -> brand (background-color on <button>, freq=33)`

**Cost: $0.00 | Reproducible: 100% | Runtime: <100ms**

### The Rule Engine

After classification, the rule engine runs every check that can be done with pure math:

```
TYPE SCALE ANALYSIS
+- Detected Ratio: 1.167
+- Closest Standard: Minor Third (1.2)
+- Consistent: Warning (variance: 0.24)
+- Recommendation: 1.25 (Major Third)

ACCESSIBILITY CHECK (WCAG AA/AAA)
+- Colors Analyzed: 210
+- FG/BG Pairs Checked: 220
+- AA Pass: 143
+- AA Fail (real FG/BG pairs): 67
|  +- fg:#06b2c4 on bg:#ffffff -> Fix: #048391 (4.5:1)
|  +- fg:#999999 on bg:#ffffff -> Fix: #757575 (4.6:1)
|  +- ... and 62 more

SPACING GRID
+- Detected Base: 1px (GCD)
+- Grid Aligned: Warning 0%
+- Recommendation: 8px grid

CONSISTENCY SCORE: 52/100
```

Not just "color vs white" — it tests **actual foreground/background pairs** found on the page. And algorithmically generates AA-compliant alternatives.

This entire layer runs **in under 1 second** and costs nothing — the single biggest cost optimization in the system.

---

## Layer 3: AI Analysis & Interpretation (4 Named Agents)

This is where language models actually add value — tasks that require **context, reasoning, and judgment**. But in V3, they're advisory only. They don't control naming.

[IMAGE: Agent pipeline diagram - AURORA -> ATLAS -> SENTINEL -> NEXUS]

---

### Agent 1: AURORA — Brand Color Advisor
**Model:** Qwen 72B (HuggingFace PRO)
**Role change in V3:** Advisory only. Cannot rename colors. Can promote palette colors to semantic roles.

**What AURORA does now:**

The color classifier handles the naming. AURORA's job shifted to:
- Identify brand strategy (complementary? analogous? monochrome?)
- Suggest which palette colors deserve semantic roles (e.g., "color.blue.500 should be color.brand.primary")
- Assess palette cohesion (score 1-10)
- Provide reasoning that helps designers understand the brand's color story

**The key constraint:** `filter_aurora_naming_map()` strips any non-semantic names from AURORA's output. If AURORA tries to rename `color.blue.500` to `color.ocean.primary`, it's rejected. Only `brand.`, `text.`, `bg.`, `border.`, `feedback.` role assignments pass through.

```
AURORA's Analysis:
------------------------------------------
Brand Primary:  #06b2c4 (confidence: HIGH)
  +- 33 buttons, 12 CTAs, dominant accent
  +- Classifier already tagged as brand

Brand Secondary: #c1df1f (confidence: MEDIUM)
  +- 15 accent elements, secondary CTA

Palette Strategy: Complementary
Cohesion Score: 7/10
  +- "Clear hierarchy, accent colors differentiated"
```

---

### Agent 2: ATLAS — Benchmark Advisor
**Model:** Llama 3.3 70B (128K context)

**Unique Capability:** Industry benchmarking against **8 design systems** (Material 3, Polaris, Atlassian, Carbon, Apple HIG, Tailwind, Ant, Chakra).

[IMAGE: Benchmark comparison table from the UI]

This agent reasons about **effort vs. value**:

```
ATLAS's Recommendation:
------------------------------------------
1st: Shopify Polaris: 87% match

Alignment Changes:
  +- Type scale: 1.17 -> 1.25 (effort: medium)
  +- Spacing grid: mixed -> 4px (effort: high)
  +- Base size: 16px -> 16px (already aligned)

Pros: Closest match, e-commerce proven, well-documented
Cons: Spacing migration is significant effort

2nd: Material 3 (77% match)
  +- "Stronger mobile patterns, but 8px grid
       requires more restructuring"
```

ATLAS adds the context that turns analysis into action:

> "You're 87% aligned to Polaris already. Closing the gap on type scale takes ~1 hour and makes your system industry-standard."

---

### Agent 3: SENTINEL — Best Practices Auditor
**Model:** Qwen 72B
**V3 improvement:** Must cite specific data from rule engine. Cross-reference critic validates that scores match actual data.

SENTINEL prioritizes by **business impact** — not just severity:

```
SENTINEL's Audit:
------------------------------------------
Overall Score: 68/100

Checks:
  +- PASS:    Type Scale Standard (1.25 ratio)
  +- WARNING: Type Scale Consistency (variance 0.18)
  +- PASS:    Base Size Accessible (16px)
  +- FAIL:    AA Compliance (67 failures)
  +- WARNING: Spacing Grid (0% aligned)
  +- FAIL:    Near-Duplicates (351 pairs)

Priority Fixes:
  #1 Fix brand color AA compliance
     Impact: HIGH | Effort: 5 min
     -> "Affects 40% of interactive elements"

  #2 Consolidate near-duplicate colors
     Impact: MEDIUM | Effort: 2 hours

  #3 Align spacing to 8px grid
     Impact: MEDIUM | Effort: 1 hour
```

**V3's grounding rule:** If the rule engine says 67 AA failures, SENTINEL's AA check **must** be "fail." A cross-reference critic catches contradictions.

---

### Agent 4: NEXUS — Head Synthesizer
**Model:** Llama 3.3 70B (128K context)

NEXUS takes outputs from **all three agents + the rule engine** and synthesizes a final recommendation using a two-perspective evaluation:

- **Perspective A (Accessibility-First):** Weights AA compliance at 40%
- **Perspective B (Balanced):** Equal weights across dimensions

It evaluates both, then picks the perspective that best reflects the actual data.

```
NEXUS Final Synthesis:
------------------------------------------
Executive Summary:
"Your design system scores 68/100. Critical:
67 color pairs fail AA. Top action: fix brand
primary contrast (5 min, high impact)."

Scores:
  +- Overall:       68/100
  +- Accessibility:  45/100
  +- Consistency:    75/100
  +- Organization:   70/100

Top 3 Actions:
  1. Fix brand color AA (#06b2c4 -> #048391)
     Impact: HIGH | Effort: 5 min
  2. Align type scale to 1.25
     Impact: MEDIUM | Effort: 1 hour
  3. Consolidate 143 -> ~20 semantic colors
     Impact: MEDIUM | Effort: 2 hours

Color Recommendations:
  +- PASS:   brand.primary: #06b2c4 -> #048391 (auto-accept)
  +- PASS:   text.secondary: #999999 -> #757575 (auto-accept)
  +- REJECT: brand.accent: #FF6B35 -> #E65100 (user decides)
```

---

## The Figma Bridge: DTCG JSON -> Variables -> Visual Spec

[IMAGE: Figma plugin UI showing import options]

### W3C DTCG v1 Compliance

V3's export follows the W3C Design Tokens Community Group specification (stable October 2025):

```json
{
  "color": {
    "brand": {
      "primary": {
        "$type": "color",
        "$value": "#005aa3",
        "$description": "[classifier] brand: primary_action",
        "$extensions": {
          "com.design-system-extractor": {
            "frequency": 47,
            "confidence": "high",
            "category": "brand",
            "evidence": ["background-color on <a>", "background-color on <button>"]
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
        "offsetX": "0px", "offsetY": "2px",
        "blur": "8px", "spread": "0px",
        "color": "#00000026"
      }
    }
  }
}
```

Every token includes `$type`, `$value`, and `$description`. Colors include `$extensions` with extraction metadata (frequency, confidence, category, evidence). This means any DTCG-compatible tool can consume our output.

### The Custom Figma Plugin

The plugin closes the loop:

1. **Auto-detects DTCG format** (vs legacy JSON)
2. **Creates Figma Variables** — Color, Number, and String variable collections
3. **Creates Styles** — Paint styles, Text styles, Effect styles
4. **Generates Visual Spec Page** — Separate frames for typography, colors, spacing, radius, shadows

[IMAGE: Figma visual spec page showing all tokens]

```
+-------------------------------------------------------------+
|  BRAND        TEXT           BACKGROUND      FEEDBACK        |
+-------------------------------------------------------------+
|  +----+ +----+   +----+ +----+   +----+ +----+   +----+     |
|  |Prim| |Sec |   |Prim| |Sec |   |Prim| |Sec |   |Err |     |
|  +----+ +----+   +----+ +----+   +----+ +----+   +----+     |
|  #005aa3 #c1df1f #373737 #666666 #fff   #f5f5f5  #dc2626    |
|  AA:Pass AA:Warn AA:Pass AA:Pass                  AA:Pass    |
+-------------------------------------------------------------+
```

The visual spec uses horizontal auto-layout with AA compliance badges on every color swatch. Typography renders in the actual detected font family with size, weight, and line-height metadata.

---

## Comparing AS-IS vs TO-BE

[IMAGE: Side-by-side comparison of AS-IS and TO-BE specimens]

| Token | AS-IS | TO-BE | Change |
|-------|-------|-------|--------|
| Type Scale | ~1.18 (random) | 1.25 (Major Third) | Consistent |
| brand.primary | #06b2c4 | #048391 | AA: 3.2 -> 4.5 |
| Spacing Grid | Mixed | 8px base | Standardized |
| Color Ramps | None | 50-950 | Generated |
| Unique Colors | 143 | ~20 semantic | Consolidated |
| Radius | Raw CSS garbage | none/sm/md/lg/xl/full | Normalized |
| Shadows | Unsorted, unnamed | xs/sm/md/lg/xl (5 levels) | Progressive |

---

## The Numbers

| Metric | Manual Process | My Workflow |
|--------|---------------|-------------|
| Time | 3-5 days | ~15 minutes |
| Cost | Designer salary | ~$0.003 |
| Coverage | ~50 colors | 143 colors (8 sources) |
| Accuracy | Human error | Computed styles (exact) |
| Accessibility | Manual spot checks | Full AA/AAA (all 220 pairs) |
| Benchmarking | Subjective | 8 industry systems compared |
| Color naming | Manual | Deterministic classifier (100% reproducible) |
| Radius/shadows | Copy raw CSS | Normalized, sorted, named |
| Figma ready | Hours more | Instant (DTCG plugin + visual spec) |
| Format | Proprietary | W3C DTCG v1 standard |

---

## Cost & Model Strategy

Different agents use different models — intentionally.

[IMAGE: Cost comparison table]

| Agent | Model | Why This Model | Cost |
|-------|-------|---------------|------|
| Normalizer | None | Math doesn't need AI | $0.00 |
| Color Classifier | None (815 lines) | Deterministic, reproducible | $0.00 |
| Rule Engine | None | Math doesn't need AI | $0.00 |
| AURORA | Qwen 72B | Creative brand reasoning | ~Free (HF PRO) |
| ATLAS | Llama 3.3 70B | 128K context for benchmarks | ~Free (HF PRO) |
| SENTINEL | Qwen 72B | Strict, consistent evaluation | ~Free (HF PRO) |
| NEXUS | Llama 3.3 70B | 128K context for synthesis | ~$0.001 |
| **Total** | | | **~$0.003** |

For designer-scale usage (weekly runs), inference costs are effectively negligible, with HuggingFace PRO ($9/month) covering most models.

The V1-to-V3 journey:
- **V1:** LLM for everything. $0.50-1.00/run. Hallucinated contrast ratios.
- **V2:** Rules + LLM split. $0.003/run. But 3 naming systems fighting.
- **V3:** Rules + Classifier + Advisory LLM. $0.003/run. One naming authority. Clean output.

---

## Graceful Degradation

The system **always produces output**, even when components fail:

| If This Fails... | What Happens |
|-------------------|-------------|
| LLM agents down | Color classifier + rule engine still works (free) |
| Firecrawl unavailable | DOM-only extraction (slightly fewer tokens) |
| Benchmark fetch fails | Hardcoded fallback data from 8 systems |
| NEXUS synthesis fails | `create_fallback_synthesis()` from rule engine |
| AURORA returns garbage | `filter_aurora_naming_map()` strips invalid names |
| **Entire AI layer** | **Full classifier + rule-engine-only report - still useful** |

---

## Tech Stack

[IMAGE: Tech stack diagram with logos]

**AI Agent App:**
- Playwright (browser automation, 8-source extraction)
- Firecrawl (deep CSS parsing)
- Gradio (UI framework)
- Qwen/Qwen2.5-72B-Instruct (AURORA + SENTINEL)
- meta-llama/Llama-3.3-70B-Instruct (ATLAS + NEXUS)
- HuggingFace Spaces (hosting) + HF Inference API
- Docker (containerized deployment)
- 148 tests (82 deterministic + 27 agent evals + 35 live evals + 4 pipeline)

**Figma Integration:**
- Custom Figma Plugin (v7)
- W3C DTCG v1 compliant JSON
- Variables API + Paint/Text/Effect Styles
- Auto-generated Visual Spec pages
- Tokens Studio compatible

---

## What I Learned

### 1. Overusing LLMs Is a Design Failure

If rules can do it faster and cheaper — use rules. My WCAG checker is 100% accurate. An LLM's contrast ratio calculation? Maybe 85% accurate, and 100x slower.

The rule engine + color classifier do 90% of the work for $0.

### 2. The Naming Authority Problem Is Real

V2's biggest failure wasn't technical — it was organizational. Three systems producing color names with no clear hierarchy. The fix wasn't better AI, it was a clear authority chain: classifier is PRIMARY, LLM is SECONDARY (advisory only), normalizer is FALLBACK.

**Lesson:** When multiple systems touch the same data, establish ONE authority. Don't merge competing outputs.

### 3. Industry Benchmarks Are Gold

Without benchmarks: "Your type scale is inconsistent" -- *PM nods*
With benchmarks: "You're 87% aligned to Shopify Polaris. Closing the gap takes 1 hour and makes your system industry-standard." -- *PM schedules meeting*

Time to build benchmark database: 1 day.
Value: Transforms analysis into prioritized action.

### 4. Semi-Automation > Full Automation

I don't want AI to make all decisions. The workflow has human checkpoints:
- Review AS-IS in Figma before modernizing
- Accept/reject each agent suggestion
- Review TO-BE before using in production

AI as **copilot**, not autopilot.

### 5. Specialized Agents > One Big Prompt

One mega-prompt doing brand analysis + benchmark comparison + accessibility audit + synthesis = confused, unfocused output. Four agents, each with a single responsibility = sharp, reliable analysis.

### 6. W3C Standards Matter

Adopting the DTCG v1 spec (October 2025) means our JSON output works with Tokens Studio, Style Dictionary v4, and any tool that follows the standard. Custom formats create lock-in. Standards create ecosystems.

### 7. Deterministic Classification Beats LLM Classification

AURORA (LLM) named 10 colors per run, inconsistently. The color classifier names ALL colors, every time, with logged evidence. For categorization tasks where you have structured input data (CSS properties, element types, frequency), rules beat LLMs on accuracy, speed, cost, and reproducibility.

---

## A Note on the Tech Stack

**On HuggingFace Spaces:** I'm using HF Spaces as the hosting platform with a Gradio frontend running in Docker. The LLM models (Qwen 72B, Llama 3.3 70B) are called via HuggingFace Inference API. Browser automation (Playwright + Chromium) runs inside the container.

**On the Data:** This system works on **live websites** — point it at any URL and it extracts real design tokens from the actual DOM. No synthetic data. The architecture, LLM integrations, and rule engine are production-ready with 148 passing tests.

**On the Standard:** The W3C DTCG specification reached stable v1 in October 2025. Our output includes `$type`, `$value`, `$description`, and `$extensions` with namespaced metadata. Any DTCG-compatible tool can consume it.

---

## Try It Yourself

**AI Agent App:**
- Live Demo: [HuggingFace Space link]
- GitHub: [Repository link]

**Workflow:**
1. Enter website URL -> Extract AS-IS
2. Download DTCG JSON -> Import to Figma
3. Review visual spec -> Run AI analysis
4. Accept suggestions -> Export TO-BE
5. Import to Figma -> Compare visual specs

---

## Closing Thought

AI engineering isn't about fancy models or complex architecture. It's about knowing which problems need AI vs good engineering.

It's **compression** — compressing days of manual audit, multiple expert perspectives, and industry benchmarking into something a team can act on Monday morning.

Instead of 3-5 days reviewing DevTools, your team gets:
> "Top 3 issues, ranked by impact, with specific fixes, benchmark alignment, and a Figma-ready visual spec to compare before and after."

That's AI amplifying design systems impact.

Full code on GitHub: [link]

---

## What's Next: Automated Component Generation (Part 2)

The token extraction and analysis story is complete. But design systems aren't just tokens — they're **components**.

After exhaustive research into 30+ tools (Tokens Studio, Figr Identity, Figma Make, MCP bridges, story.to.design, and more), I found a genuine market gap:

**No production tool takes DTCG JSON and outputs Figma components with proper variants.**

Every tool either:
- Imports tokens as variables (but doesn't create components)
- Creates components from brand config (but can't consume YOUR tokens)
- Uses AI to write to Figma (but is non-deterministic)
- Needs a full Storybook pipeline as intermediary

So I'm building it. The Figma Plugin API supports everything needed: `createComponent()`, `combineAsVariants()`, `setBoundVariable()`. Our existing plugin already imports tokens and creates variables.

**Coming in Episode 7:**
- Auto-generating Figma components from extracted tokens
- Button (60 variants), TextInput (8), Card, Toast, Checkbox/Radio
- Token-to-component binding: `color.brand.primary` -> Button fill, `radius.md` -> Button corners
- Fully deterministic: same tokens in = same components out

---

*This is Episode 6 of "AI in My Daily Work."*

*If you missed the previous episodes:*
- *Episode 5: Building a 7-Agent UX Friction Analysis System in Databricks*
- *Episode 4: Automating UI Regression Testing with AI Agents (Part-1)*
- *Episode 3: Building a Multi-Agent Review Intelligence System*
- *Episode 2: How I Use a Team of AI Agents to Automate Secondary Research*

*What problems are you automating with AI? Drop a comment — I'd love to discuss what you're building.*

---

**About the Author**

I'm Riaz, a UX Design Manager with 10+ years of experience in consumer apps. I combine design thinking with AI engineering to build tools that make design decisions faster and more data-driven.

**Connect:**
- LinkedIn: [link]
- Medium: @designwithriaz
- GitHub: [link]

---

#AIAgents #DesignSystems #UXDesign #Figma #MultiAgentSystems #DesignTokens #Automation #AIEngineering #HuggingFace #WCAG #W3CDTCG

---

*Published on Medium - ~12 min read*

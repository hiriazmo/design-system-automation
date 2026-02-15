# 🚅 AI in My Daily Work — Episode 6: Reverse-Engineering Design Systems with 4 AI Agents + a Free Rule Engine

## A Semi-Automated Workflow: From Website URL to Figma-Ready Design System

*How I built a system that extracts any website's design tokens and audits them like a senior design team — for ~$0.003 per run.*

[IMAGE: Hero - Complete workflow showing Website → AI Agents → Figma]

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

I've done this dozens of times. It takes **3–5 days** for a single website. And by the time you're done, something has already changed.

I wanted a system that could think like a design team:

- a **data engineer** validating extraction quality
- an **analyst** identifying brand colors and patterns
- a **senior reviewer** benchmarking against industry standards
- and a **chief architect** synthesizing everything into action

So I built one.

---

## The Solution (In One Sentence)

I built a 4-agent system backed by a free rule engine that acts like an entire design audit team: data extraction + WCAG compliance + benchmark comparison + brand analysis + prioritized recommendations. It runs on HuggingFace Spaces, costs ~$0.003 per analysis, and feeds directly into Figma via a custom plugin.

---

## The Complete Workflow

[IMAGE: Full workflow diagram showing all 8 steps]

Here's the end-to-end process I now use:

```
┌──────────────────────────────────────────────────────────────┐
│                    MY DESIGN SYSTEM WORKFLOW                    │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  STEP 1: Extract AS-IS (AI Agent App)                         │
│  ──────────────────────────────────────                       │
│  • Enter website URL                                          │
│  • AI auto-discovers pages                                    │
│  • Extracts colors, typography, spacing, shadows, radius      │
│  • Rule Engine checks WCAG + type scale + spacing grid        │
│  • Download AS-IS JSON file                                   │
│                                                                │
│                           ↓                                    │
│                                                                │
│  STEP 2: Import to Figma (My Plugin)                          │
│  ────────────────────────────────────                         │
│  • Open Figma                                                 │
│  • Upload AS-IS JSON via custom plugin                        │
│  • Plugin creates Variables automatically                     │
│                                                                │
│                           ↓                                    │
│                                                                │
│  STEP 3: View AS-IS Specimen (Figma)                          │
│  ────────────────────────────────────                         │
│  • Visual display of current design system                    │
│  • Typography (Desktop + Mobile), Colors, Spacing, etc.       │
│  • Review what exists before modernizing                      │
│                                                                │
│                           ↓                                    │
│                                                                │
│  STEP 4: AI Analysis (AI Agent App - Stage 2)                 │
│  ─────────────────────────────────────────────                │
│  • Free Rule Engine: WCAG, type scale, spacing grid           │
│  • AURORA: Brand color identification                         │
│  • ATLAS: Industry benchmark comparison (8 systems)           │
│  • SENTINEL: Best practices audit with priorities             │
│  • NEXUS: Final synthesis resolving all contradictions         │
│                                                                │
│                           ↓                                    │
│                                                                │
│  STEP 5: Accept/Reject Suggestions (AI Agent App)             │
│  ─────────────────────────────────────────────────            │
│  • Review each recommendation                                 │
│  • Accept ☑️ or Reject ☐ individually                         │
│  • I stay in control of what changes                          │
│                                                                │
│                           ↓                                    │
│                                                                │
│  STEP 6: Export TO-BE (AI Agent App - Stage 3)                │
│  ─────────────────────────────────────────────                │
│  • Generate modernized TO-BE JSON                             │
│  • Contains accepted improvements                             │
│  • Download new JSON file                                     │
│                                                                │
│                           ↓                                    │
│                                                                │
│  STEP 7: Import TO-BE to Figma (My Plugin)                    │
│  ──────────────────────────────────────────                   │
│  • Upload TO-BE JSON via same plugin                          │
│  • Figma Variables update with new values                     │
│                                                                │
│                           ↓                                    │
│                                                                │
│  STEP 8: View TO-BE Specimen (Figma)                          │
│  ────────────────────────────────────                         │
│  • Visual display of modernized design system                 │
│  • Compare AS-IS vs TO-BE                                     │
│  • Ready to use in production                                 │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

**Total time:** ~15 minutes (vs 3–5 days manual)

---

## Architecture Overview: Two Layers, Four Agents

My first attempt (V1) made a classic mistake:
**I used a large language model for everything.**

### Why Two Layers?

My V1 mistake: Used LLMs for everything
❌ Cost: $0.50–1.00 per run
❌ Speed: 15+ seconds for basic math
❌ Accuracy: LLMs hallucinate contrast ratios

The fix: **Not every task needs AI. Some need good engineering.**

V2 flipped the approach.

> **Deterministic code handles certainty. LLMs handle ambiguity.**

This led to a two-layer architecture.

[IMAGE: Architecture diagram — Layer 1 (Deterministic) → Layer 2 (4 Named Agents)]

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

---

## Layer 1: Deterministic Intelligence (No LLM)

These agents do the heavy lifting — no LLMs involved.

### Stage 1: Extraction

A Playwright-powered browser visits each page at **two viewports** (1440px desktop + 375px mobile) and extracts every design token from **7 sources**:

[IMAGE: 7 Extraction Sources diagram]

```
Source 1: Computed Styles → What the browser actually renders
Source 2: CSS Variables    → --primary-color, --spacing-md
Source 3: Inline Styles    → style="color: #06b2c4"
Source 4: SVG Attributes   → fill, stroke colors
Source 5: Stylesheets      → External .css files
Source 6: Style Blocks     → <style> tags
Source 7: Firecrawl        → Deep CSS parsing (bypasses CORS)
```

A **Normalizer** then deduplicates (exact match + Delta-E color distance), infers semantic roles from frequency, and assigns suggested names like `brand.primary`, `text.secondary`.

A **Semantic Analyzer** categorizes every color by *actual CSS usage*:

| Role | Detection Method |
|------|------------------|
| Brand | Saturated colors on buttons, CTAs, links |
| Text | Low saturation with `color` property |
| Background | Used with `background-color` on containers |
| Border | Used with `border-color` properties |
| Feedback | Red=error, Green=success, Yellow=warning |

**Cost: $0.00 | Runtime: ~90 seconds**

The user reviews these tokens before anything touches an LLM.

### The Rule Engine (The Single Biggest Optimization)

After extraction, a rule engine runs every check that can be done with pure math:

```
📐 TYPE SCALE ANALYSIS
├─ Detected Ratio: 1.167
├─ Closest Standard: Minor Third (1.2)
├─ Consistent: ⚠️ No (variance: 0.24)
└─ 💡 Recommendation: 1.25 (Major Third)

♿ ACCESSIBILITY CHECK (WCAG AA/AAA)
├─ Colors Analyzed: 210
├─ FG/BG Pairs Checked: 220
├─ AA Pass: 143 ✅
├─ AA Fail (real FG/BG pairs): 67 ❌
│  ├─ fg:#06b2c4 on bg:#ffffff → 💡 Fix: #048391 (4.5:1)
│  ├─ fg:#999999 on bg:#ffffff → 💡 Fix: #757575 (4.6:1)
│  └─ ... and 62 more

📏 SPACING GRID
├─ Detected Base: 1px (GCD)
├─ Grid Aligned: ⚠️ 0%
└─ 💡 Recommendation: 8px grid

📊 CONSISTENCY SCORE: 52/100
```

Not just "color vs white" — it tests **actual foreground/background pairs** found on the page. And algorithmically generates compliant alternatives.

This entire layer runs **in under 1 second** and costs nothing beyond compute — the single biggest cost optimization in the system.

---

## Layer 2: AI Analysis & Interpretation (4 Named Agents)

This is where language models actually add value — tasks that require **context, reasoning, and judgment**.

[IMAGE: Agent pipeline diagram — AURORA → ATLAS → SENTINEL → NEXUS]

---

### Agent 1: AURORA — Brand Color Analyst
**Model:** Qwen 72B (HuggingFace PRO)
**Cost:** Free within PRO subscription ($9/month)
**Temperature:** 0.4

**The Challenge:** The rule engine found 143 colors. Which one is the *brand* primary?

A rule engine can count that `#06b2c4` appears in 33 buttons. But it can't reason: "33 buttons + 12 CTAs + dominant accent positioning = this is almost certainly the brand primary." That requires **context understanding**.

**Sample Output:**

```
AURORA's Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 Brand Primary:  #06b2c4 (confidence: HIGH)
   └─ 33 buttons, 12 CTAs, dominant accent

🎨 Brand Secondary: #c1df1f (confidence: MEDIUM)
   └─ 15 accent elements, secondary CTA

Palette Strategy: Complementary
Cohesion Score: 7/10
   └─ "Clear hierarchy, accent colors differentiated"

Self-Evaluation: confidence=8/10, data=good
```

---

### Agent 2: ATLAS — Benchmark Advisor
**Model:** Llama 3.3 70B (128K context)
**Cost:** Free within PRO subscription
**Temperature:** 0.25

**Unique Capability:** Industry benchmarking against **8 design systems** (Material 3, Polaris, Atlassian, Carbon, Apple HIG, Tailwind, Ant, Chakra).

[IMAGE: Benchmark comparison table from the UI]

This agent doesn't just pick the closest match — it reasons about **effort vs. value**:

```
ATLAS's Recommendation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🥇 Shopify Polaris: 87% match

Alignment Changes:
  ├─ Type scale: 1.17 → 1.25 (effort: medium)
  ├─ Spacing grid: mixed → 4px (effort: high)
  └─ Base size: 16px → 16px (already aligned ✅)

Pros: Closest match, e-commerce proven, well-documented
Cons: Spacing migration is significant effort

🥈 Alternative: Material 3 (77% match)
  └─ "Stronger mobile patterns, but 8px grid
       requires more restructuring"
```

ATLAS's Value Add:

> "You're 87% aligned to Polaris already. Closing the gap on type scale takes ~1 hour and makes your system industry-standard. **Priority: MEDIUM.**"

---

### Agent 3: SENTINEL — Best Practices Auditor
**Model:** Qwen 72B
**Cost:** Free within PRO subscription
**Temperature:** 0.2 (strict, consistent)

**The Challenge:** The rule engine says "67 AA failures." But which ones matter most?

SENTINEL prioritizes by **business impact** — not just severity:

```
SENTINEL's Audit:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Score: 68/100

Checks:
  ├─ ✅ Type Scale Standard (1.25 ratio)
  ├─ ⚠️ Type Scale Consistency (variance 0.18)
  ├─ ✅ Base Size Accessible (16px)
  ├─ ❌ AA Compliance (67 failures)
  ├─ ⚠️ Spacing Grid (0% aligned)
  └─ ❌ Near-Duplicates (351 pairs)

Priority Fixes:
  #1 Fix brand color AA compliance
     Impact: HIGH | Effort: 5 min
     → "Affects 40% of interactive elements"

  #2 Consolidate near-duplicate colors
     Impact: MEDIUM | Effort: 2 hours

  #3 Align spacing to 8px grid
     Impact: MEDIUM | Effort: 1 hour
```

---

### Agent 4: NEXUS — Head Synthesizer (Final Output)
**Model:** Llama 3.3 70B (128K context)
**Cost:** ~$0.001
**Temperature:** 0.3

NEXUS is the senior architect. It takes outputs from **all three agents + the rule engine** and synthesizes a final recommendation — **resolving contradictions**, weighting scores, and producing the executive summary the user sees.

If ATLAS says "close to Polaris" but SENTINEL says "spacing misaligned," NEXUS reconciles: *"Align to Polaris type scale now (low effort) but defer spacing migration (high effort)."*

```
NEXUS Final Synthesis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Executive Summary:
"Your design system scores 68/100. Critical:
67 color pairs fail AA. Top action: fix brand
primary contrast (5 min, high impact)."

📊 Scores:
  ├─ Overall:       68/100
  ├─ Accessibility:  45/100
  ├─ Consistency:    75/100
  └─ Organization:   70/100

🎯 Top 3 Actions:
  1. Fix brand color AA (#06b2c4 → #048391)
     Impact: HIGH | Effort: 5 min
  2. Align type scale to 1.25
     Impact: MEDIUM | Effort: 1 hour
  3. Consolidate 143 → ~20 semantic colors
     Impact: MEDIUM | Effort: 2 hours

🎨 Color Recommendations:
  ├─ ✅ brand.primary: #06b2c4 → #048391 (auto-accept)
  ├─ ✅ text.secondary: #999999 → #757575 (auto-accept)
  └─ ❌ brand.accent: #FF6B35 → #E65100 (user decides)
```

---

## The Figma Bridge: JSON → Variables → Specimen

[IMAGE: Figma plugin UI showing import options]

I built a custom Figma plugin that closes the loop:

1. **Imports JSON** → Creates Figma Variables
2. **Maps token types:**
   - Colors → Color Variables
   - Typography → Text Styles
   - Spacing → Number Variables
   - Radius → Number Variables
   - Shadows → Effect Styles
3. **Generates a Specimen Page** — visual display of the entire system

The plugin handles both AS-IS and TO-BE imports identically — just different JSON files.

### Viewing the Specimen

[IMAGE: Figma specimen page showing all tokens visually]

```
┌─────────────────────────────────────────────────────────────┐
│  🎨 BRAND        📝 TEXT         🖼️ BACKGROUND    🚨 FEEDBACK │
├─────────────────────────────────────────────────────────────┤
│  ┌────┐ ┌────┐   ┌────┐ ┌────┐   ┌────┐ ┌────┐   ┌────┐    │
│  │Prim│ │Sec │   │Prim│ │Sec │   │Prim│ │Sec │   │Err │    │
│  └────┘ └────┘   └────┘ └────┘   └────┘ └────┘   └────┘    │
│  #06b2c4 #c1df1f #373737 #666666 #fff   #f5f5f5  #dc2626   │
│  AA:⚠️   AA:⚠️   AA:✓    AA:✓                     AA:✓     │
└─────────────────────────────────────────────────────────────┘
```

---

## Comparing AS-IS vs TO-BE

[IMAGE: Side-by-side comparison of AS-IS and TO-BE specimens]

The real power is seeing the transformation:

| Token | AS-IS | TO-BE | Change |
|-------|-------|-------|--------|
| Type Scale | ~1.18 (random) | 1.25 (Major Third) | ✓ Consistent |
| brand.primary | #06b2c4 | #048391 | AA: 3.2 → 4.5 |
| Spacing Grid | Mixed | 8px base | ✓ Standardized |
| Color Ramps | None | 50-950 | ✓ Generated |
| Unique Colors | 143 | ~20 semantic | ✓ Consolidated |

---

## The Numbers

| Metric | Manual Process | My Workflow |
|--------|---------------|-------------|
| Time | 3–5 days | ~15 minutes |
| Cost | Designer salary | ~$0.003 |
| Coverage | ~50 colors | 143 colors (7 sources) |
| Accuracy | Human error | Computed styles (exact) |
| Accessibility | Manual spot checks | Full AA/AAA (all 220 pairs) |
| Benchmarking | Subjective | 8 industry systems compared |
| Figma Ready | Hours more | Instant (JSON plugin) |

---

## Cost & Model Strategy

Different agents use different models — intentionally.

[IMAGE: Cost comparison table]

| Agent | Model | Why This Model | Cost |
|-------|-------|---------------|------|
| Rule Engine | None | Math doesn't need AI | $0.00 |
| AURORA | Qwen 72B | Creative color reasoning | ~Free (HF PRO) |
| ATLAS | Llama 3.3 70B | 128K context for benchmarks | ~Free (HF PRO) |
| SENTINEL | Qwen 72B | Strict, consistent evaluation | ~Free (HF PRO) |
| NEXUS | Llama 3.3 70B | 128K context for synthesis | ~$0.001 |
| **Total** | | | **~$0.003** |

For designer-scale usage (weekly runs), inference costs are effectively negligible, with HuggingFace PRO ($9/month) covering most models.

Compared to V1 (LLM-for-everything):
- **~100–300x cost reduction**
- **Faster execution** (rule engine: <1s vs LLM: 15s for the same math)
- **Better accuracy** (LLMs hallucinate math; rule engines don't)

---

## Graceful Degradation

The system **always produces output**, even when components fail:

| If This Fails... | What Happens |
|-------------------|-------------|
| LLM agents down | Rule engine analysis still works (free) |
| Firecrawl unavailable | DOM-only extraction (slightly fewer tokens) |
| Benchmark fetch fails | Hardcoded fallback data from 8 systems |
| NEXUS synthesis fails | `create_fallback_synthesis()` from rule engine |
| **Entire AI layer** | **Full rule-engine-only report — still useful** |

---

## Tech Stack

[IMAGE: Tech stack diagram with logos]

**AI Agent App:**
- Playwright (browser automation, 7-source extraction)
- Firecrawl (deep CSS parsing)
- Gradio (UI framework)
- Qwen/Qwen2.5-72B-Instruct (AURORA + SENTINEL)
- meta-llama/Llama-3.3-70B-Instruct (ATLAS + NEXUS)
- HuggingFace Spaces (hosting) + HF Inference API
- Docker (containerized deployment)

**Figma Integration:**
- Custom Figma Plugin
- Variables API
- Tokens Studio compatible JSON

---

## What I Learned

### 1. Overusing LLMs Is a Design Failure

If rules can do it faster and cheaper — use rules. My WCAG checker is 100% accurate. An LLM's contrast ratio calculation? Maybe 85% accurate, and 100x slower.

The rule engine does 80% of the work for $0.

### 2. Industry Benchmarks Are Gold

Without benchmarks: "Your type scale is inconsistent" → *PM nods*
With benchmarks: "You're 87% aligned to Shopify Polaris. Closing the gap takes 1 hour and makes your system industry-standard." → *PM schedules meeting*

Time to build benchmark database: 1 day.
Value: Transforms analysis into prioritized action.

### 3. Semi-Automation > Full Automation

I don't want AI to make all decisions. The workflow has human checkpoints:
- Review AS-IS in Figma before modernizing
- Accept/reject each agent suggestion
- Review TO-BE before using in production

AI as **copilot**, not autopilot.

### 4. Specialized Agents > One Big Prompt

One mega-prompt doing brand analysis + benchmark comparison + accessibility audit + synthesis = confused, unfocused output. Four agents, each with a single responsibility = sharp, reliable analysis.

### 5. The JSON Bridge Works

JSON is the perfect interchange format:
- AI agents export JSON
- Figma plugin imports JSON
- No direct integration needed
- Each tool does what it's best at

### 6. Semantic Context Changes Everything

Raw hex values are useless. Knowing that `#06b2c4` is the **brand primary used on 33 buttons** changes how you evaluate it — and how agents reason about it.

---

## A Note on the Tech Stack

**On HuggingFace Spaces:** I'm using HF Spaces as the hosting platform with a Gradio frontend running in Docker. The LLM models (Qwen 72B, Llama 3.3 70B) are called via HuggingFace Inference API. Browser automation (Playwright + Chromium) runs inside the container.

**On the Data:** This system works on **live websites** — point it at any URL and it extracts real design tokens from the actual DOM. No synthetic data. The architecture, LLM integrations, and rule engine are production-ready.

---

## Try It Yourself

**AI Agent App:**
- 🚀 Live Demo: [HuggingFace Space link]
- 💻 GitHub: [Repository link]

**Workflow:**
1. Enter website URL → Extract AS-IS
2. Download JSON → Import to Figma
3. Review specimen → Run AI analysis
4. Accept suggestions → Export TO-BE
5. Import to Figma → Compare specimens

---

## Closing Thought

AI engineering isn't about fancy models or complex architecture. It's about knowing which problems need AI vs good engineering.

It's **compression** — compressing days of manual audit, multiple expert perspectives, and industry benchmarking into something a team can act on Monday morning.

Instead of 3–5 days reviewing DevTools, your team gets:
> "Top 3 issues, ranked by impact, with specific fixes, benchmark alignment, and a Figma-ready specimen to compare before and after."

That's AI amplifying design systems impact.

🔗 Full code on GitHub: [link]

---

## What's Next

**Coming in Episode 7:**
- Auto-generating Figma components from tokens
- Component pattern detection (buttons, cards, forms)
- Design system documentation generation

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

#AIAgents #DesignSystems #UXDesign #Figma #MultiAgentSystems #DesignTokens #Automation #AIEngineering #HuggingFace #WCAG

---

*Published on Medium • ~10 min read*

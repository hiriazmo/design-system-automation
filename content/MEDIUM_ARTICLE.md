# 🚅 AI in My Daily Work — Episode [X]: Building a Design System Analyzer with 4 AI Agents + a Free Rule Engine

*How I built a system that extracts any website's design tokens and audits them like a senior design team — for ~$0.003 per run.*

[IMAGE: Hero banner — Gradio UI showing the pipeline output]

---

## The Problem

Every week, the same story.

A designer opens a website and squints: "Is that our brand blue? Why does this button look different on mobile? How many shades of gray are we actually using?"

Design systems are supposed to prevent this. But **auditing** one? That's a different problem entirely.

- Open DevTools on every page
- Manually extract colors, fonts, spacing
- Cross-reference against WCAG accessibility guidelines
- Compare to industry benchmarks like Material Design or Polaris
- Write a report with prioritized recommendations

For a 20-page website, this takes **2–3 days of manual work**. And by the time you're done, the codebase has already changed.

I wanted a system that could think like a design team:

- a **crawler** discovering every page
- an **extractor** pulling every token from the DOM
- a **rule engine** checking accessibility and consistency — for free
- and **specialized AI agents** interpreting what the numbers actually mean

So I built one.

---

## The Solution (In One Sentence)

I built a 4-agent system backed by a free rule engine that acts like an entire design audit team: data extraction + WCAG compliance + benchmark comparison + brand analysis + prioritized recommendations. It runs on HuggingFace Spaces, costs ~$0.003 per analysis, and delivers actionable output automatically.

---

## Architecture Overview: Two Layers, Four Agents

My first attempt (V1) made a classic mistake:
**I used a large language model for everything.**

### Why Two Layers?

My V1 mistake: Used GPT-4 for everything
❌ Cost: $0.50–1.00 per run
❌ Speed: 15+ seconds for basic math
❌ Accuracy: LLMs hallucinate contrast ratios

The fix: **Not every task needs AI. Some need good engineering.**

V2 flipped the approach.

> **Deterministic code handles certainty. LLMs handle ambiguity.**

This led to a two-layer architecture.

[IMAGE: Architecture diagram — Layer 1 (Deterministic) → Layer 2 (AI Agents)]

```
┌─────────────────────────────────────────────────┐
│  LAYER 1: DETERMINISTIC (Free — $0.00)          │
│  ├─ Crawler + Extractor + Normalizer            │
│  ├─ WCAG Contrast Checker (math)                │
│  ├─ Type Scale Detection (ratio math)           │
│  ├─ Spacing Grid Analysis (GCD math)            │
│  └─ Color Statistics (deduplication)             │
├─────────────────────────────────────────────────┤
│  LAYER 2: AI AGENTS (~$0.003)                   │
│  ├─ AURORA  — Brand Color Analyst               │
│  ├─ ATLAS   — Benchmark Advisor                 │
│  ├─ SENTINEL — Best Practices Auditor           │
│  └─ NEXUS   — Head Synthesizer                  │
└─────────────────────────────────────────────────┘
```

---

## Layer 1: Deterministic Intelligence (No LLM)

These agents do the heavy lifting — no LLMs involved.

### What This Layer Does

- Crawls every page with Playwright (desktop 1440px + mobile 375px)
- Extracts tokens from **7 sources**: DOM computed styles, CSS variables, SVG colors, inline styles, stylesheet rules, external CSS files (Firecrawl), brute-force page scan
- Deduplicates colors (exact hex + Delta-E distance)
- Checks **actual FG/BG pairs** against WCAG — not just "color vs white"
- Detects type scale ratio and spacing grid
- Scores overall consistency (0–100)

### Rule Engine Output:

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

This entire layer runs **in under 1 second** and costs nothing beyond compute — the single biggest cost optimization in the system.

---

## Layer 2: AI Analysis & Interpretation (4 Agents)

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

🎨 Brand Secondary: #373737 (confidence: HIGH)
   └─ 89 text elements, consistent dark tone

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

**Unique Capability:** Industry benchmarking against 8 design systems (Material 3, Polaris, Atlassian, Carbon, Apple HIG, Tailwind, Ant, Chakra).

[IMAGE: Benchmark comparison table from the UI]

This agent doesn't just pick the closest match — it reasons about **effort vs. value**:

```
ATLAS's Recommendation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recommended: Shopify Polaris (87% match)

Alignment Changes:
  ├─ Type scale: 1.17 → 1.25 (effort: medium)
  ├─ Spacing grid: mixed → 4px (effort: high)
  └─ Base size: 16px → 16px (already aligned ✅)

Pros: Closest match, e-commerce proven, well-documented
Cons: Spacing migration is significant effort

Alternative: Material 3 (77% match)
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
SENTINEL's Priority Fixes:
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

**No AI for Agents 1–3 can replace this.** NEXUS takes outputs from ALL three agents + the rule engine and synthesizes a final recommendation — **resolving contradictions**, weighting scores, and producing the executive summary the user actually sees.

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

## Real Analysis: Two Websites

### Website A: The Clean System

```
Landing → Product → Cart → Checkout
```

**Consistency Score:** 78/100
**AA Failures:** 3 (all minor text colors)
**Type Scale:** 1.25 ratio, consistent across pages
**Agent Insight:** "Well-structured system. Minor AA fixes on secondary text. Already 92% aligned to Material 3."

### Website B: The Messy System

```
Landing → Features → Pricing → ⚠️ Contact → Signup
```

**Consistency Score:** 34/100
**AA Failures:** 67
**Colors:** 143 unique (351 near-duplicates)
**Agent Insight:** "No clear type scale. Brand primary fails AA on every interactive element. 143 colors suggests no design system is actually enforced."

**NEXUS's Diagnosis:**
> "This isn't a broken design system — it's the absence of one. Start with AA compliance (5 min fix), then consolidate to ~20 semantic colors (2 hours). Align to Polaris as your foundation."

That last line is the difference between a report and an **action plan**.

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

Compared to V1, this architecture delivers:
- **~100–300x cost reduction**
- **Faster execution** (rule engine: <1s vs LLM: 15s for the same math)
- **Better accuracy** (LLMs hallucinate math; rule engines don't)
- **Graceful degradation** (always produces output, even when LLMs fail)

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

## What I Learned

**1. Overusing LLMs is a design failure.**
If rules can do it faster and cheaper — use rules. My WCAG checker is 100% accurate. An LLM's contrast ratio calculation? Maybe 85% accurate, and 100x slower.

**2. Industry benchmarks are gold.**
Without benchmarks: "Your type scale is inconsistent" → *PM nods*
With benchmarks: "You're 87% aligned to Shopify Polaris. Closing the gap takes 1 hour and makes your system industry-standard." → *PM schedules meeting*

Time to build benchmark database: 1 day
Value: Transforms analysis into prioritized action

**3. Specialized agents > one big prompt.**
One mega-prompt doing brand analysis + benchmark comparison + accessibility audit + synthesis = confused, unfocused output. Four agents, each with a single responsibility = sharp, reliable analysis.

The same principle as microservices: do one thing well.

**4. UX skills transfer directly to AI systems.**
Agent design feels a lot like service design:
- flows
- handoffs
- failure modes
- human interpretation

The best AI architectures are the ones designed like good products.

---

## A Note on the Tech Stack

**On HuggingFace Spaces:** I'm using HF Spaces as the hosting platform with a Gradio frontend running in Docker. The LLM models (Qwen 72B, Llama 3.3 70B) are called via HuggingFace Inference API. Browser automation (Playwright + Chromium) runs inside the container.

**On the Data:** This system works on **live websites** — point it at any URL and it extracts real design tokens from the actual DOM. No synthetic data. The architecture, LLM integrations, and rule engine are production-ready.

🔗 **HuggingFace Space** (Live Demo): [link]

[IMAGE: Screenshot of the Gradio UI showing full analysis results]

---

## Closing Thought

AI engineering isn't about fancy models or complex architecture. It's about knowing which problems need AI vs good engineering.

It's **compression** — compressing days of manual audit, multiple expert perspectives, and industry benchmarking into something a team can act on Monday morning.

Instead of 2–3 days reviewing DevTools, your team gets:
> "Top 3 issues, ranked by impact, with specific fixes, benchmark alignment, and brand color identification"

That's AI amplifying design systems impact.

🔗 Full code on GitHub: [link]

---

*This is Episode [X] of "AI in My Daily Work."*

*If you missed the previous episodes:*
- *Episode 5: Building a 7-Agent UX Friction Analysis System in Databricks*
- *Episode 4: Automating UI Regression Testing with AI Agents (Part-1)*
- *Episode 3: Building a Multi-Agent Review Intelligence System*
- *Episode 2: How I Use a Team of AI Agents to Automate Secondary Research*

*What problems are you automating with AI? Drop a comment — I'd love to discuss what you're building.*

# Design System Automation — Complete Architecture

## Overview

A **2-stage pipeline** that extracts, analyzes, and recommends improvements to any website's design system. Combines **deterministic rule-based analysis** (free, fast, reliable) with **4 specialized LLM agents** (context-aware reasoning) — each agent does one thing well.

```
┌─────────────────────────────────────────────────────────────────┐
│                        STAGE 1: EXTRACTION                       │
│                        (No LLM — $0.00)                          │
│                                                                   │
│  URL → Crawler → Extractor → Normalizer → Semantic Analyzer      │
│                         ↓                                         │
│              [HUMAN REVIEW CHECKPOINT]                             │
│         Accept/reject tokens, Desktop ↔ Mobile toggle             │
├─────────────────────────────────────────────────────────────────┤
│                     STAGE 2: ANALYSIS                             │
│                                                                   │
│  Layer 1: Rule Engine ──────────────── FREE ($0.00)               │
│     ├─ WCAG Contrast (AA/AAA)                                     │
│     ├─ Type Scale Detection                                       │
│     ├─ Spacing Grid Alignment                                     │
│     └─ Color Statistics                                           │
│                                                                   │
│  Layer 2: Benchmark Research ──────── Semi-Free                   │
│     └─ Compare to Material 3, Polaris, Atlassian, etc.            │
│                                                                   │
│  Layer 3: LLM Agents ─────────────── ~$0.003/run                  │
│     ├─ AURORA  → Brand color identification                       │
│     ├─ ATLAS   → Benchmark recommendation                        │
│     └─ SENTINEL → Best practices validation                      │
│                                                                   │
│  Layer 4: HEAD Synthesizer ────────── Final output                │
│     └─ NEXUS   → Combines everything → User-facing results       │
│                                                                   │
│  [GRACEFUL DEGRADATION: Each layer has fallbacks]                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Extraction & Normalization (No LLM)

### 1A. PageDiscoverer (Crawler)

| | |
|---|---|
| **File** | `agents/crawler.py` |
| **Model** | None |
| **Input** | Base URL |
| **Output** | List of discovered pages (title, URL, page type) |
| **How** | Playwright browser crawling + heuristic page type detection |
| **Why no LLM** | Pure URL discovery — deterministic crawling |

### 1B. TokenExtractor

| | |
|---|---|
| **File** | `agents/extractor.py` + `agents/firecrawl_extractor.py` |
| **Model** | None |
| **Input** | Confirmed page URLs + Viewport (1440px desktop / 375px mobile) |
| **Output** | `ExtractedTokens` — colors, typography, spacing, radius, shadows, FG/BG pairs, CSS variables |
| **How** | 7-source extraction via Playwright |
| **Why no LLM** | DOM parsing + regex — no reasoning needed |

**7 Extraction Sources:**
1. DOM computed styles (`getComputedStyle`)
2. CSS variables (`:root { --color: }`)
3. SVG colors (fill, stroke)
4. Inline styles (`style='color:'`)
5. Stylesheet rules (CSS files)
6. External CSS files (fetched via Firecrawl)
7. Page content scan (brute-force token search)

### 1C. TokenNormalizer

| | |
|---|---|
| **File** | `agents/normalizer.py` |
| **Model** | None |
| **Input** | Raw `ExtractedTokens` |
| **Output** | `NormalizedTokens` — deduplicated, named, confidence-tagged |
| **How** | Deduplication (exact hex + Delta-E merge), role inference from frequency, semantic naming |
| **Why no LLM** | Algorithmic deduplication — pure math |

### 1D. SemanticColorAnalyzer

| | |
|---|---|
| **File** | `agents/semantic_analyzer.py` |
| **Model** | None |
| **Input** | Extracted colors with usage/frequency data |
| **Output** | Semantic mapping: `{brand, text, background, border, feedback}` |
| **How** | Rule-based: buttons → brand, `color` property → text, `background-color` → background, red → error, green → success |
| **Why no LLM** | CSS property analysis — pattern matching on property names |

### Human Review Checkpoint

After Stage 1, the user sees:
- Desktop vs Mobile token comparison (side-by-side)
- Accept/reject individual colors, typography, spacing tokens
- Viewport toggle to switch views
- All accepted tokens flow into Stage 2

---

## Stage 2: Analysis (Hybrid — Rule Engine + LLM)

### Layer 1: Rule Engine (FREE — No LLM)

**File:** `core/rule_engine.py`
**Cost:** $0.00
**Speed:** < 1 second

The rule engine handles everything that can be computed with math. No LLM reasoning needed.

#### What It Calculates:

**1. Typography Analysis (TypeScaleAnalysis)**
```
Input:  [11, 12, 14, 16, 18, 22, 24, 32]  (extracted font sizes)
Output:
  ├─ Detected Ratio: 1.167
  ├─ Closest Standard: Minor Third (1.2)
  ├─ Consistent: No (variance: 0.24)
  └─ Recommendation: 1.25 (Major Third)
```
- Compares to standard ratios: 1.067, 1.125, 1.2, 1.25, 1.333, 1.414, 1.5
- Calculates variance to determine consistency
- 100% deterministic math

**2. Color Accessibility (WCAG AA/AAA)**
```
Input:  210 colors + 220 FG/BG pairs
Output:
  ├─ AA Pass: 143
  ├─ AA Fail (real pairs): 67
  └─ Fix suggestions: #06b2c4 → #048391 (4.5:1)
```
- WCAG 2.1 contrast ratio formula
- Tests actual FG/BG pairs found on page (not just color vs white)
- Algorithmically generates AA-compliant alternatives
- Pure math — no LLM

**3. Spacing Grid Detection**
```
Input:  [3, 8, 10, 16, 20, 24, 32, 40]  (spacing values)
Output:
  ├─ Detected Base: 1px (GCD)
  ├─ Grid Aligned: 0%
  └─ Recommendation: 8px grid
```
- GCD math + alignment percentage calculation

**4. Color Statistics**
```
Input:  143 extracted colors
Output:
  ├─ Unique: 143
  ├─ Near-Duplicates: 351
  ├─ Grays: 68 | Saturated: 69
  └─ Hue Distribution: {gray: 68, blue: 14, red: 11, ...}
```

**5. Overall Consistency Score (0–100)**
```
Weights:
  ├─ AA Compliance:        25 pts
  ├─ Type Scale Consistent: 15 pts
  ├─ Base Size (≥16px):     15 pts
  ├─ Spacing Grid Aligned:  15 pts
  ├─ Color Count (< 20):    10 pts
  └─ No Near-Duplicates:    10 pts
```

---

### Layer 2: Benchmark Research

**File:** `agents/benchmark_researcher.py`
**Cost:** Near-free (optional HF LLM for doc extraction, mostly cached)

**Available Benchmarks:**
| System | Short Name |
|--------|-----------|
| Material Design 3 | Material 3 |
| Apple HIG | Apple |
| Shopify Polaris | Polaris |
| Atlassian Design | Atlassian |
| IBM Carbon | Carbon |
| Tailwind CSS | Tailwind |
| Ant Design | Ant |
| Chakra UI | Chakra |

**Process:**
1. Check 24-hour cache per benchmark
2. If expired: Fetch docs via Firecrawl → Extract specs → Cache
3. Compare user's tokens to each benchmark:
   - Type ratio diff, base size diff, spacing grid diff
   - Weighted similarity score
4. Sort by similarity (closest match first)

**Fallback:** Hardcoded `FALLBACK_BENCHMARKS` dict — no external fetch needed

---

### Layer 3: LLM Agents (4 Specialized Agents)

**File:** `agents/llm_agents.py`

Each agent has a single responsibility. They run after the rule engine — they reason about patterns the rule engine can't detect.

---

#### Agent 1: AURORA — Brand Color Identifier

| | |
|---|---|
| **Persona** | Senior Brand Color Analyst |
| **Model** | Qwen 72B |
| **Temperature** | 0.4 (allows creative interpretation) |
| **Input** | Color tokens with usage counts + semantic CSS analysis |
| **Output** | `BrandIdentification` |

**Why LLM:** Requires context understanding — "33 button instances using #06b2c4 = likely brand primary." A rule engine can count colors, but can't reason about which one is the *brand* color based on where and how it's used.

**Sample Output:**
```
AURORA's Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Brand Primary:  #06b2c4 (confidence: HIGH)
  └─ 33 buttons, 12 CTAs, dominant accent

Brand Secondary: #373737 (confidence: HIGH)
  └─ 89 text elements, consistent dark tone

Palette Strategy: Complementary
Cohesion Score: 7/10
  └─ "Clear primary-secondary hierarchy,
      accent colors well-differentiated"

Self-Evaluation:
  ├─ Confidence: 8/10
  ├─ Data Quality: good
  └─ Flags: []
```

---

#### Agent 2: ATLAS — Benchmark Advisor

| | |
|---|---|
| **Persona** | Senior Design System Benchmark Analyst |
| **Model** | Llama 3.3 70B (128K context) |
| **Temperature** | 0.25 (analytical, data-driven) |
| **Input** | User's type ratio, base size, spacing + benchmark comparison data |
| **Output** | `BenchmarkAdvice` |

**Why LLM:** Requires trade-off reasoning. The closest mathematical match (85%) might not be the best fit if alignment effort is high. ATLAS reasons about effort vs. value — "Polaris is 87% match and your spacing already aligns. Material 3 is 77% but would require restructuring your grid."

**Sample Output:**
```
ATLAS's Recommendation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recommended: Shopify Polaris (87% match)

Alignment Changes:
  ├─ Type scale: 1.17 → 1.25 (effort: medium)
  ├─ Spacing grid: mixed → 4px (effort: high)
  └─ Base size: 16px → 16px (already aligned!)

Pros:
  ├─ Closest match to existing system
  ├─ E-commerce proven at scale
  └─ Well-documented, community supported

Cons:
  ├─ Spacing migration is significant effort
  └─ Type scale shift affects all components

Alternative: Material 3 (77% match)
  └─ "Stronger mobile patterns, 8px grid"
```

---

#### Agent 3: SENTINEL — Best Practices Validator

| | |
|---|---|
| **Persona** | Design System Best Practices Auditor |
| **Model** | Qwen 72B |
| **Temperature** | 0.2 (strict, consistent evaluation) |
| **Input** | Rule Engine results (typography, accessibility, spacing, color stats) |
| **Output** | `BestPracticesResult` |

**Why LLM:** Requires impact assessment and prioritization. The rule engine says "67 colors fail AA." SENTINEL says "Brand primary failing AA affects 40% of interactive elements — fix this FIRST, it's 5 minutes of work with high impact."

**Sample Output:**
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
  ├─ ⚠️ Color Count (143 unique — too many)
  └─ ❌ Near-Duplicates (351 pairs)

Priority Fixes:
  #1 Fix brand color AA compliance
     Impact: HIGH | Effort: 5 min
     Action: #06b2c4 → #048391

  #2 Consolidate near-duplicate colors
     Impact: MEDIUM | Effort: 2 hours
     Action: Merge 351 near-duplicate pairs

  #3 Align spacing to 8px grid
     Impact: MEDIUM | Effort: 1 hour
     Action: Snap values to [8, 16, 24, 32, 40]
```

---

#### Agent 4: NEXUS — HEAD Synthesizer (Final Agent)

| | |
|---|---|
| **Persona** | Senior Design System Architect & Synthesizer |
| **Model** | Llama 3.3 70B (128K context) |
| **Temperature** | 0.3 (balanced synthesis) |
| **Input** | ALL Rule Engine results + AURORA + ATLAS + SENTINEL outputs |
| **Output** | `HeadSynthesis` — the final user-facing result |

**Why LLM:** Synthesis and contradiction resolution. If ATLAS says "close to Polaris" but SENTINEL says "spacing misaligned," NEXUS reconciles: "Align to Polaris type scale now (low effort) but defer spacing migration (high effort)."

**Sample Output:**
```
NEXUS Final Synthesis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Executive Summary:
"Your design system scores 68/100. Critical issue:
67 color pairs fail AA compliance. Top action:
fix brand primary contrast (5 min, high impact)."

Scores:
  ├─ Overall:       68/100
  ├─ Accessibility:  45/100
  ├─ Consistency:    75/100
  └─ Organization:   70/100

Benchmark Fit:
  ├─ Closest: Shopify Polaris (87%)
  └─ Recommendation: Adopt Polaris type scale

Top 3 Actions:
  1. Fix brand color AA → #06b2c4 → #048391
     Impact: HIGH | Effort: 5 min
  2. Align type scale to 1.25
     Impact: MEDIUM | Effort: 1 hour
  3. Consolidate 143 → ~20 semantic colors
     Impact: MEDIUM | Effort: 2 hours

Color Recommendations:
  ├─ ✅ brand.primary: #06b2c4 → #048391 (AA fix — auto-accept)
  ├─ ✅ text.secondary: #999999 → #757575 (AA fix — auto-accept)
  └─ ❌ brand.accent: #FF6B35 → #E65100 (aesthetic — user decides)

Self-Evaluation:
  ├─ Confidence: 7/10
  ├─ Data Quality: good
  └─ Flags: ["high near-duplicate count may indicate extraction noise"]
```

---

## Cost Model

| Component | LLM? | Cost per Run |
|-----------|-------|-------------|
| Stage 1 (Crawl + Extract + Normalize) | No | $0.00 |
| Rule Engine | No | $0.00 |
| Benchmark Research | Optional | ~$0.0005 |
| AURORA (Qwen 72B) | Yes | ~$0.0005 |
| ATLAS (Llama 3.3 70B) | Yes | ~$0.0005 |
| SENTINEL (Qwen 72B) | Yes | ~$0.0005 |
| NEXUS (Llama 3.3 70B) | Yes | ~$0.001 |
| **Total** | | **~$0.003** |

All LLM inference via HuggingFace Inference API (PRO subscription at $9/month includes generous free tier for these models).

---

## Graceful Degradation

The system is designed to **always produce output**, even when components fail:

| If This Fails... | Fallback |
|-------------------|----------|
| Firecrawl (CSS fetch) | Use DOM-only extraction |
| Benchmark fetch | Use hardcoded `FALLBACK_BENCHMARKS` |
| AURORA (brand ID) | Skip brand analysis, use defaults |
| ATLAS (benchmark advice) | Skip recommendation, show raw comparisons |
| SENTINEL (practices) | Use rule engine score directly |
| NEXUS (synthesis) | `create_fallback_synthesis()` from rule engine data |
| Entire LLM layer | Full rule-engine-only analysis still works |

---

## Key Data Structures

```
ExtractedTokens (Stage 1 raw)
├─ colors: dict[ColorToken]
├─ typography: dict[TypographyToken]
├─ spacing: dict[SpacingToken]
├─ radius: dict[RadiusToken]
├─ shadows: dict[ShadowToken]
├─ fg_bg_pairs: list[dict]      ← for real AA checking
└─ css_variables: dict[str, str] ← CSS var mappings

NormalizedTokens (Stage 1 clean)
├─ colors, typography, spacing, radius, shadows (deduplicated)
├─ font_families: dict[FontFamily]
├─ detected_spacing_base: int (4 or 8)
└─ detected_naming_convention: str

RuleEngineResults (Layer 1)
├─ typography: TypeScaleAnalysis
├─ accessibility: list[ColorAccessibility]
├─ spacing: SpacingGridAnalysis
├─ color_stats: ColorStatistics
├─ aa_failures: int
└─ consistency_score: int (0-100)

HeadSynthesis (Final output)
├─ executive_summary: str
├─ scores: {overall, accessibility, consistency, organization}
├─ benchmark_fit: {closest, similarity, recommendation}
├─ brand_analysis: {primary, secondary, cohesion}
├─ top_3_actions: [{action, impact, effort, details}]
├─ color_recommendations: [{role, current, suggested, reason, accept}]
├─ type_scale_recommendation: dict
├─ spacing_recommendation: dict
└─ self_evaluation: {confidence, reasoning, data_quality, flags}
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Gradio 4.x |
| Browser Automation | Playwright (Chromium) |
| Web Scraping | Firecrawl |
| LLM Inference | HuggingFace Inference API |
| Models | Qwen 72B, Llama 3.3 70B |
| Color Math | Custom WCAG implementation |
| Deployment | Docker → HuggingFace Spaces |

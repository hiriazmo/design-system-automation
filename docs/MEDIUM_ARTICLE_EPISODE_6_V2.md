# AI in My Daily Work — Episode 6: How 4 AI Agents + a Color Classifier Reverse-Engineer Any Website's Design System

## From URL to Figma in 15 Minutes (Not 5 Days)

*I built a system that extracts design tokens from any live website, classifies colors by actual CSS usage, audits everything against industry standards, and drops it into Figma as a visual spec — for less than a cent per run.*

[IMAGE: Hero - Website URL -> AI Agents -> Figma Visual Spec]

---

## The 5-Day Problem

If you've ever inherited a website and needed to understand its design system, you know the drill. Open DevTools. Click an element. Copy the hex code. Repeat 200 times. Manually check contrast ratios. Squint at font sizes trying to figure out if they follow a scale. Paste everything into a spreadsheet. Spend another day recreating it in Figma.

I've done this dozens of times across 10+ years managing design systems. It takes **3-5 days per site**. And honestly? The result is never complete.

I wanted something that thinks the way a design team does — one person extracting values, another classifying colors, someone checking accessibility, and a lead synthesizing it all into clear recommendations.

So I built one. Three versions and many mistakes later, here's what actually works.

---

## What It Does (The 30-Second Version)

You paste a URL. The system visits the site, extracts every design token it can find (colors, fonts, spacing, shadows, border radius), classifies and normalizes them, runs accessibility and consistency checks, then hands the data to 4 AI agents who analyze it like a senior design team.

You get a clean JSON file. Drop it into Figma with a custom plugin. Out comes a full visual spec page — every token displayed, organized, with AA compliance badges.

**15 minutes. Not 5 days.**

---

## How It Works: One Workflow, Three Layers

The biggest lesson from building V1 and V2 was this: **don't use AI for things math can do better.** My first version used a language model for everything — including contrast ratio calculations. It cost $1 per run and hallucinated the math.

V3 splits the work into three layers. The first two are free. Only the third uses AI, and only for tasks that genuinely need judgment.

[IMAGE: Architecture + Workflow combined — URL enters Layer 1, flows through Layer 2, then Layer 3, out to Figma]

### Layer 1 — Extraction & Normalization (Free, ~90 seconds)

A headless browser (Playwright) visits your site at two screen sizes — desktop and mobile — and pulls design values from **8 different sources**: computed styles, CSS variables, inline styles, SVG attributes, stylesheets, external CSS files, page scan, and a deep CSS parser (Firecrawl) that bypasses restrictions.

Why 8 sources? Because no single method catches everything. A brand color might live in a CSS variable, an inline style on a hero section, and an SVG logo — all at once. Casting a wide net means fewer missed tokens.

The raw output is messy. You'll get the same blue in three slightly different hex values. Border radius values like `"0px 0px 16px 16px"` that Figma can't use. Shadow CSS strings with no meaningful names.

The normalizer cleans all of this:

- **Colors** — Merges near-duplicates (if two blues are almost identical, keep one). Assigns a hue family and numeric shade: `color.blue.500`, `color.neutral.200`. Never vague labels like "light" or "dark."
- **Border Radius** — Parses multi-value shorthand, converts percentages and rem units to pixels, removes duplicates, and names them logically: `radius.sm` (4px), `radius.md` (8px), `radius.full` (9999px).
- **Shadows** — Breaks down CSS shadow strings into components, filters out fake shadows (like spread-only borders), sorts by blur amount, and always produces 5 clean elevation levels: `shadow.xs` through `shadow.xl`.

Nothing here uses AI. It's parsing, math, and sorting.

### Layer 2 — Classification & Rules (Free, <1 second)

This is where V3 made its biggest leap. Instead of asking an AI to figure out which color is "brand primary," I wrote 815 lines of deterministic code that reads the CSS evidence directly.

**The Color Classifier** looks at how each color is actually used on the page:

- A saturated color on `<button>` elements, appearing 30+ times? That's a brand color.
- A low-saturation color on `<p>` and `<span>` text? That's a text color.
- A neutral on `<div>` and `<body>` backgrounds? That's a background color.
- A red with high saturation appearing infrequently? Likely an error/feedback color.
- Everything else goes into the palette by hue family.

Every single decision gets logged with evidence: *"#06b2c4 classified as brand — found on background-color of button elements, frequency 33."* Run it twice, get the exact same result. An LLM can't promise that.

The classifier also caps each category (max 3 brand colors, max 3 text colors, etc.) so you don't end up with 15 things all called "brand."

**The Rule Engine** then runs pure-math checks on the classified tokens:

- **Accessibility**: Tests actual foreground/background color pairs found on the page (not just "does this color pass on white?"). Generates AA-compliant alternatives automatically.
- **Type Scale**: Calculates the ratio between consecutive font sizes, finds the closest standard scale (Major Third, Minor Third, etc.), and flags inconsistencies.
- **Spacing Grid**: Detects the mathematical base (4px? 8px?) and measures how well the site's spacing values align.
- **Color Statistics**: Counts near-duplicates, hue distribution, and saturation patterns.

The result is a consistency score out of 100, backed entirely by data.

### Layer 3 — 4 AI Agents (~$0.003)

Now the AI enters — but with strict guardrails. Each agent has one job, uses one model, and is **advisory only**. They cannot override the classifier's naming.

**AURORA (Brand Advisor)** — *Qwen 72B*
Looks at the classified colors and identifies brand strategy. Is it complementary? Monochrome? Which palette color deserves promotion to a semantic role like `brand.primary`? AURORA can suggest promotions, but a filter (`filter_aurora_naming_map`) rejects anything that isn't a valid semantic role. No creative renaming allowed.

**ATLAS (Benchmark Advisor)** — *Llama 3.3 70B*
Compares your extracted system against 8 industry design systems (Material 3, Shopify Polaris, Atlassian, Carbon, Apple HIG, Tailwind, Ant Design, Chakra). Tells you which one you're closest to and what it would take to align: *"You're 87% aligned to Polaris. Closing the type scale gap takes about an hour."*

**SENTINEL (Best Practices Auditor)** — *Qwen 72B*
Scores your system across 6 checks (AA compliance, type scale consistency, spacing grid, near-duplicates, etc.) and prioritizes fixes by business impact. Must cite actual data from the rule engine — if the engine found 67 AA failures, SENTINEL can't claim accessibility "passes." A cross-reference critic catches contradictions.

**NEXUS (Head Synthesizer)** — *Llama 3.3 70B*
Takes everything — classifier output, rule engine scores, all three agents' analyses — and produces a final executive summary. Evaluates from two perspectives (accessibility-weighted vs. balanced), picks the one that best reflects reality, and outputs a ranked top-3 action list with specific hex values and effort estimates.

```
NEXUS Summary:
  Score: 68/100
  Top Action: Fix brand primary contrast (#06b2c4 -> #048391)
              Impact: HIGH | Effort: 5 min | Affects 40% of CTAs
```

---

## The Naming Problem (And Why It Matters)

This deserves its own callout because it was the hardest problem to solve — and it's invisible to most people.

In V2, three different systems produced color names:

| System | Output | Example |
|--------|--------|---------|
| Normalizer | Word shades | `color.blue.light` |
| Export function | Numeric shades | `color.blue.500` |
| AURORA (LLM) | Creative names | `brand.primary` |

The result in Figma? `blue.300`, `blue.dark`, `blue.light`, and `blue.base` — all in the same file. Completely unusable.

V3 established a strict chain of command:

1. **Color Classifier** (primary authority) — names every color, deterministically
2. **AURORA** (secondary, advisory) — can suggest semantic role promotions only
3. **Normalizer** (fallback) — only if the classifier hasn't run

One authority. No conflicts. Clean output every time.

---

## Into Figma: The Last Mile

The system exports W3C DTCG-compliant JSON — the industry standard for design tokens (finalized October 2025). Every token includes its type, value, description, and extraction metadata:

```json
{
  "color": {
    "brand": {
      "primary": {
        "$type": "color",
        "$value": "#005aa3",
        "$description": "[classifier] brand: primary_action"
      }
    }
  },
  "radius": {
    "md": { "$type": "dimension", "$value": "8px" }
  }
}
```

A custom Figma plugin imports this JSON and:

1. Creates **Figma Variables** (color, number, and string collections)
2. Creates **Styles** (paint, text, and effect styles)
3. Auto-generates a **Visual Spec Page** — separate frames for typography, colors, spacing, radius, and shadows, with AA compliance badges on every color swatch

[IMAGE: Figma visual spec page showing organized tokens with AA badges]

You run the full workflow twice — once for the AS-IS (what exists today) and once for the TO-BE (with accepted improvements). Place them side by side in Figma and the story tells itself:

| Token | AS-IS | TO-BE |
|-------|-------|-------|
| Brand Primary | #06b2c4 (fails AA) | #048391 (passes AA) |
| Type Scale | ~1.18 (random) | 1.25 (Major Third) |
| Spacing | Mixed values | 8px grid |
| Unique Colors | 143 | ~20 semantic |
| Radius | Raw CSS garbage | none/sm/md/lg/xl/full |
| Shadows | Unsorted, unnamed | 5 progressive levels |

---

## What It Costs

| Component | Cost |
|-----------|------|
| Extraction + Normalization | $0.00 |
| Color Classifier (815 lines of code) | $0.00 |
| Rule Engine (WCAG, type scale, spacing) | $0.00 |
| 4 AI Agents (via HuggingFace Inference) | ~$0.003 |
| **Total per analysis** | **~$0.003** |

The free layers do 90% of the work. The AI adds context, benchmarks, and synthesis — the parts that genuinely need language understanding.

For context, V1 (all-LLM) cost $0.50-1.00 per run. Same output quality? Worse, actually — it hallucinated contrast ratios and named colors inconsistently.

---

## When Things Break

The system always produces output, even when parts fail:

| Failure | What Happens |
|---------|-------------|
| AI agents are down | Classifier + rule engine still work (free) |
| Firecrawl unavailable | 7 Playwright sources still extract |
| AURORA returns nonsense | Filter strips invalid names automatically |
| Full AI layer offline | You still get classified tokens + accessibility audit |

The architecture was designed so that the free deterministic layers are independently useful. The AI layer is a bonus, not a dependency.

---

## What I Learned Building Three Versions

**Use AI where it adds value, not everywhere.** My WCAG contrast checker is mathematically exact. An LLM doing the same calculation? Slower, expensive, and sometimes wrong. Rules handle certainty. AI handles ambiguity.

**When multiple systems touch the same data, pick one authority.** V2's three competing naming systems was the single worst architectural decision. Not because any individual system was bad — but because nobody was in charge.

**Benchmarks change conversations.** "Your type scale is inconsistent" gets a nod. "You're 87% aligned to Shopify Polaris and closing the gap takes an hour" gets a meeting scheduled.

**Specialized agents beat mega-prompts.** One giant prompt doing brand analysis + benchmarking + accessibility audit = confused output. Four agents, each with a single job = focused, reliable results.

**Semi-automation beats full automation.** The workflow has deliberate human checkpoints: review the AS-IS before modernizing, accept or reject each suggestion, inspect the TO-BE before shipping. AI as copilot, not autopilot.

**Standards create ecosystems.** Adopting W3C DTCG v1 means our output works with Tokens Studio, Style Dictionary v4, and any tool following the spec. Custom formats create lock-in.

---

## The Tech Under the Hood

**AI Agent App:** Playwright (extraction), Firecrawl (deep CSS), Gradio (UI), Qwen 72B + Llama 3.3 70B (agents), HuggingFace Spaces + Inference API (hosting), Docker, 148 tests.

**Figma Plugin:** Custom plugin (v7), W3C DTCG v1 import, Variables API, auto-generated visual spec pages, Tokens Studio compatible.

**Open Source:** Full code on GitHub — [link]

---

## What's Next: From Tokens to Components

The token story is complete. But design systems aren't just tokens — they're **components**.

After researching 30+ tools, I found a genuine gap: **no production tool takes DTCG JSON and outputs Figma components with proper variants.** Every existing tool either imports tokens without creating components, creates components from its own format but can't consume yours, or uses AI non-deterministically.

The Figma Plugin API supports everything needed. Coming in Episode 7: auto-generating Button (60 variants), TextInput, Card, Toast, and Checkbox/Radio — directly from the extracted tokens. Same tokens in, same components out.

---

*Episode 6 of "AI in My Daily Work."*

*Previous episodes:*
- *Episode 5: Building a 7-Agent UX Friction Analysis System in Databricks*
- *Episode 4: Automating UI Regression Testing with AI Agents (Part-1)*
- *Episode 3: Building a Multi-Agent Review Intelligence System*
- *Episode 2: How I Use a Team of AI Agents to Automate Secondary Research*

*What are you automating? Drop a comment — I'd love to hear what you're building.*

---

**About the Author**

I'm Riaz, a UX Design Manager with 10+ years in consumer apps. I combine design thinking with AI engineering to build tools that make design decisions faster and more data-driven.

**Connect:** LinkedIn | Medium: @designwithriaz | GitHub

---

#AIAgents #DesignSystems #UXDesign #Figma #DesignTokens #Automation #AIEngineering #HuggingFace #WCAG #W3CDTCG

---

*~9 min read*

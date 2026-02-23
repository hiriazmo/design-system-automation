# LinkedIn Post - Episode 6: Design System Extractor v3.2

## Main Post (Copy-Paste Ready)

---

Every designer has done this: Open DevTools. Inspect element. Copy hex code. Paste to spreadsheet. Recreate in Figma. Repeat 200 times.

I spent 3-5 days manually extracting design tokens from websites. Then more time recreating them in Figma as variables.

So I built a 3-layer system: deterministic extraction + rule-based color classifier + 4 AI agents.

**The Architecture (v3.2):**

Layer 1 (FREE, <1 second):
- 7-source extraction (Playwright + Firecrawl)
- Normalizer: radius, shadows, colors all cleaned and named
- Color Classifier (815 lines, deterministic): CSS evidence -> category -> token name

Layer 2 (FREE, <1 second):
- Rule Engine: WCAG contrast (actual FG/BG pairs), type scale detection, spacing grid
- 113 tests passing, 100% reproducible

Layer 3 (~$0.003, 4 specialized agents):
- AURORA: brand color advisor (Qwen 72B) — advisory only, can't override classifier
- ATLAS: benchmarks against 8 industry design systems (Llama 70B)
- SENTINEL: prioritizes fixes by business impact (Qwen 72B)
- NEXUS: synthesizes everything, resolves contradictions (Llama 70B)

**The Pipeline:**

Website URL -> 7-Source Extraction -> Color Classifier -> Rule Engine -> DTCG JSON
-> Figma Plugin -> Variables + Styles + Auto-Generated Visual Spec Page
-> AI Analysis -> Accept/Reject -> TO-BE JSON -> Compare in Figma

**My biggest lesson building V1 -> V2 -> V3:**

V1: LLMs for everything. $0.50/run. Hallucinated contrast ratios.
V2: Rules + LLM split. $0.003/run. But 3 naming systems fighting in exports.
V3: Rules + Classifier + Advisory LLM. $0.003/run. ONE naming authority. Clean output.

The fix wasn't better AI. It was a clear authority chain:
1. Color Classifier (PRIMARY) - deterministic, covers ALL colors
2. AURORA LLM (SECONDARY) - can only suggest semantic roles
3. Normalizer (FALLBACK) - hue + numeric shade

**Real results:**
- 143 colors extracted, classified, and named (deterministically)
- 220 FG/BG pairs checked for AA compliance
- Radius: raw CSS garbage -> none/sm/md/lg/xl/full (normalized)
- Shadows: unsorted -> xs/sm/md/lg/xl (5 progressive levels)
- Benchmarked against Material 3, Polaris, Atlassian + 5 more
- Output: W3C DTCG v1 compliant JSON with $extensions metadata
- Figma: auto-generated visual spec with AA badges
- Time: 3-5 days -> ~15 minutes
- Cost: ~$0.003

The key? **I stay in control.** AI recommends, I decide.

Full workflow + architecture: [Medium link]
Try it: [HuggingFace Space link]
Code: [GitHub link]

Episode 6 of "AI in My Daily Work"

What design workflows are you automating?

#UXDesign #AIEngineering #DesignSystems #Figma #HuggingFace #Accessibility #WCAG #DesignTokens #W3CDTCG #BuildInPublic

---

## First Comment (Post Immediately After)

**Resources:**

Medium Article: [link]
Complete architecture breakdown + V1 -> V2 -> V3 evolution + Figma integration

Live Demo: [HuggingFace Space link]
Try it with any website URL

GitHub: [link]
Open source - star it if useful!

---

**The Naming Authority Problem (V3's key insight):**

V2 had THREE competing systems naming colors:
- Normalizer: "color.blue.light" (word-based)
- Export layer: "color.blue.500" (numeric)
- AURORA LLM: "brand.primary" (whatever it wanted)

Result in Figma: blue.300, blue.dark, blue.light, blue.base — ALL in the same export.

V3 fix: ONE authority. Color Classifier (deterministic) is PRIMARY. AURORA is advisory only — it can suggest "this blue should be brand.primary" but can't rename palette colors.

`filter_aurora_naming_map()` enforces the boundary. Clean Figma output, every time.

---

**What's Next — Episode 7: Automated Component Generation**

Researched 30+ tools. Found a genuine market gap:
No production tool takes DTCG JSON and outputs Figma components with variants.

Building it. Button (60 variants), TextInput, Card, Toast, Checkbox/Radio.
Figma Plugin API supports everything: createComponent(), combineAsVariants(), setBoundVariable().

Same tokens in = same components out. Fully deterministic.

---

**Previous Episodes:**
- Episode 5: UX Friction Analysis (7 agents + Databricks)
- Episode 4: UI Regression Testing
- Episode 3: Review Intelligence System

What should I build for Episode 7? Drop ideas below

---

## Alternative Version (Shorter, Story-Driven)

---

"Can you audit their design system and document it in Figma?"

3-5 days of DevTools, spreadsheets, and manual Figma work.

I built something different. Three versions, actually.

V1: Used LLMs for everything. $0.50/run. They hallucinate math.

V2: Split into rules + AI. $0.003/run. But three systems fought over color names. Figma output was chaos.

V3: Clear authority chain. One color classifier (deterministic, 815 lines). LLMs are advisory only. W3C DTCG-compliant JSON. Auto-generated visual spec in Figma.

What it does now:
- 7-source extraction from any website
- Rule-based color classification (brand/text/bg/border/feedback)
- WCAG AA check on 220 actual FG/BG pairs
- 4 AI agents for brand analysis, benchmarking, audit, synthesis
- W3C standard JSON output
- Figma plugin: variables + styles + visual spec page

15 minutes. $0.003. I stay in control.

Full architecture: [Medium link]
Demo: [HuggingFace link]

Episode 6 of "AI in My Daily Work"

#DesignSystems #AIAgents #UXDesign #Figma #Automation #HuggingFace #WCAG #W3CDTCG

---

## Image Suggestions

1. **Hero:** V1 vs V2 vs V3 comparison table showing the evolution
2. **Architecture:** 3-layer diagram (Extraction -> Classification+Rules -> 4 Agents)
3. **Naming Authority:** Before/after showing Figma chaos vs clean output
4. **Figma Visual Spec:** Screenshot of auto-generated spec page
5. **Agent Output:** NEXUS synthesis with scores + top 3 actions

---

## Hashtags (Optimized)

Primary (always include):
#UXDesign #AIEngineering #DesignSystems #Figma #HuggingFace

Secondary (mix based on audience):
#DesignTokens #W3CDTCG #Accessibility #WCAG #BuildInPublic #Automation #MultiAgent

---

## Posting Strategy

**Best time:** Tuesday-Thursday, 8-10 AM your timezone

**Key messages for V3:**
1. V1 -> V2 -> V3 evolution story (naming authority problem)
2. Color Classifier (815 lines, deterministic) as key innovation
3. W3C DTCG v1 compliance — standards over proprietary formats
4. Figma visual spec auto-generation
5. Component generation gap (Episode 7 teaser)

**Differentiation from Episode 5:**
- Episode 5 = UX friction analysis (GA4 + Clarity + Databricks)
- Episode 6 = Design system extraction (Playwright + Classifier + Figma + HuggingFace)
- Same philosophy: deterministic code for certainty, LLMs for ambiguity

# Image Guide for Episode 6 Article (v3.2)

## Required Images (10-12 total)

### 1. Hero Image
**What:** Screenshot of the Gradio interface showing the full pipeline output
**Where:** After title, before first section
**Specs:** 1200x630px (LinkedIn preview size)
**Content:** Show the Visual Spec page in Figma with colors, typography, and agent synthesis visible

### 2. Complete Workflow Diagram
**What:** The 8-step pipeline: Website -> Agents -> Figma -> Compare
**Where:** After "The Complete Workflow" section
**Specs:** 1200x800px
**Content:**
```
Website URL
     |
7-Source Extraction (Playwright + Firecrawl)
     |
Normalizer (radius, shadows, colors)
     |
Color Classifier (deterministic)
     |
Rule Engine (WCAG, type scale, spacing)
     |
DTCG JSON (AS-IS)
     |
Figma Plugin -> Variables + Visual Spec
     |
4 AI Agents (AURORA, ATLAS, SENTINEL, NEXUS)
     |
Accept/Reject -> DTCG JSON (TO-BE)
     |
Figma Plugin -> Compare AS-IS vs TO-BE
```

### 3. Three-Layer Architecture Diagram
**What:** Layer 1 (Extraction) + Layer 2 (Classification + Rules) + Layer 3 (4 Agents)
**Where:** After "Architecture Overview" section
**Specs:** 1200x700px
**Content:**
```
+--------------------------------------------------+
|  LAYER 1: EXTRACTION + NORMALIZATION (Free)       |
|  +- 7-Source Extractor + Normalizer               |
|  +- Radius/Shadow/Color normalization             |
+--------------------------------------------------+
|  LAYER 2: CLASSIFICATION + RULE ENGINE (Free)     |
|  +- Color Classifier (815 lines, deterministic)   |
|  +- WCAG + Type Scale + Spacing Grid              |
+--------------------------------------------------+
|  LAYER 3: 4 AI AGENTS (~$0.003)                   |
|  +- AURORA -> ATLAS -> SENTINEL -> NEXUS          |
+--------------------------------------------------+
```

### 4. Naming Authority Chain (NEW - V3 Key Innovation)
**What:** Diagram showing the V2 chaos vs V3 clean authority
**Where:** After "The Naming Authority Chain" section
**Specs:** 1200x500px
**Content:**
```
V2 (BROKEN):                         V3 (FIXED):
+----------+                         +------------------+
|Normalizer| -> "blue.light"         |Color Classifier  | -> PRIMARY
+----------+                         |  (deterministic) |
+----------+                         +------------------+
| Export   | -> "blue.500"                    |
+----------+                         +------------------+
+----------+                         |AURORA (advisory) | -> SECONDARY
| AURORA   | -> "brand.primary"      |  roles only      |
+----------+                         +------------------+
                                              |
    = CHAOS in Figma                 +------------------+
                                     |Normalizer        | -> FALLBACK
                                     +------------------+

                                         = CLEAN output
```

### 5. Agent Pipeline Flow
**What:** Show the 4 named agents with their flow: parallel analysis -> synthesis
**Where:** After "Layer 3" section header
**Specs:** 1200x500px
**Content:**
```
   Rule Engine + Classifier Results
         |
    +----+----------------+
    v    v                v
+------+ +------+ +--------+
|AURORA| |ATLAS | |SENTINEL|
|Brand | |Bench | |Audit   |
|Qwen  | |Llama | |Qwen    |
+--+---+ +--+---+ +---+----+
   +--------+----------+
            v
      +----------+
      |  NEXUS   |
      |Synthesis |
      | Llama 70B|
      +----------+
            v
    Final Recommendations
```

### 6. 7 Extraction Sources Visual
**What:** Show the 7 different methods of extraction
**Where:** After "Extraction: 7 Sources" section
**Specs:** 1000x600px
**Content:**
```
+-------------+  +-------------+  +-------------+
| 1. Computed |  | 2. CSS      |  | 3. Inline   |
|    Styles   |  |    Variables|  |    Styles   |
+-------------+  +-------------+  +-------------+

+-------------+  +-------------+  +-------------+
| 4. SVG      |  | 5. External |  | 6. Style    |
|    Attrs    |  |    CSS Files|  |    Blocks   |
+-------------+  +-------------+  +-------------+

+-------------------------------------------------+
|              7. Firecrawl Deep Parser            |
+-------------------------------------------------+
```

### 7. Color Classifier Output (NEW)
**What:** Show the classifier's evidence-based categorization
**Where:** After "The Color Classifier" section
**Specs:** 1200x600px
**Content:**
```
[CLASSIFY] #06b2c4 -> BRAND
  Evidence: background-color on <button> (freq=33)

[CLASSIFY] #373737 -> TEXT
  Evidence: color on <p> (freq=120)

[CLASSIFY] #ffffff -> BG
  Evidence: background-color on <body> (freq=1)

[DEDUP] #1a1a1a merged with #1b1b1b (dist=1.7)

Category Caps: brand(3) text(3) bg(3) border(3) feedback(4) palette(rest)
```

### 8. Rule Engine Output
**What:** Screenshot of actual rule engine output
**Where:** After "The Rule Engine" section
**Specs:** 1200x600px
**Content:** Show the emoji-formatted output:
- TYPE SCALE ANALYSIS (ratio, variance, recommendation)
- ACCESSIBILITY CHECK (actual pairs, not just vs white)
- SPACING GRID (GCD, alignment %)
- CONSISTENCY SCORE

### 9. NEXUS Synthesis Output
**What:** Screenshot of the final synthesis with scores and top 3 actions
**Where:** After "Agent 4: NEXUS" section
**Specs:** 1200x700px
**Content:** Show final output with:
- Executive summary
- Scores (overall, accessibility, consistency, organization)
- Top 3 actions with impact/effort
- Color recommendations with accept/reject

### 10. DTCG JSON Example (NEW)
**What:** Code block showing the W3C DTCG format with $extensions
**Where:** After "W3C DTCG v1 Compliance" section
**Specs:** 1000x500px
**Content:** Show:
```json
{
  "color": {
    "brand": {
      "primary": {
        "$type": "color",
        "$value": "#005aa3",
        "$extensions": {
          "com.design-system-extractor": {
            "frequency": 47,
            "confidence": "high"
          }
        }
      }
    }
  }
}
```

### 11. Figma Visual Spec Page (NEW)
**What:** Screenshot of the auto-generated visual spec in Figma
**Where:** After "The Custom Figma Plugin" section
**Specs:** 1200x700px
**Content:** Show:
- Typography frame (Desktop + Mobile) with font metadata
- Color frame organized by semantic role (brand/text/bg/border/feedback)
- AA compliance badges on each swatch
- Radius display, Spacing scale, Shadow elevation

### 12. Before/After Comparison
**What:** Side-by-side showing AS-IS vs TO-BE
**Where:** After "Comparing AS-IS vs TO-BE" section
**Specs:** 1200x500px
**Content:**
```
AS-IS                          TO-BE
-----                          -----
Type: ~1.18 (random)    ->    1.25 (Major Third)
Brand: #06b2c4 (AA: 3.2) ->  #048391 (AA: 4.5)
Spacing: Mixed           ->   8px grid
Colors: 143 unique       ->   ~20 semantic
Radius: raw CSS          ->   none/sm/md/lg/xl/full
Shadows: unsorted        ->   xs/sm/md/lg/xl
Score: 52/100            ->   78/100
```

### 13. V1 vs V2 vs V3 Evolution (NEW)
**What:** Table showing the version progression
**Where:** After "Cost & Model Strategy" section
**Specs:** 1000x400px
**Content:**
```
Version    Cost       Naming         LLM Role        Output
-------    -------    ----------     ----------      --------
V1         $0.50      LLM decides    Everything      Unreliable
V2         $0.003     3 systems      Split w/ rules  Naming chaos
V3         $0.003     1 authority    Advisory only   Clean DTCG
```

---

## Image Creation Tools

**Recommended:**
1. **Figma** - Architecture diagrams, pipeline flows, tech stack
2. **Screenshot tool** - Gradio interface captures (use dark mode)
3. **Excalidraw** - Quick hand-drawn style diagrams

**Tips:**
- Use dark background screenshots (Gradio dark mode)
- Add subtle drop shadows to screenshots
- Keep consistent color scheme (blues match brand)
- Use the agent names (AURORA, ATLAS, SENTINEL, NEXUS) in diagram labels
- Color-code: Layer 1 = green (free), Layer 2 = blue (rules), Layer 3 = purple (AI)
- NEW: Include W3C DTCG logo/badge where format is mentioned
- NEW: Show the naming authority chain prominently - it's the V3 key story

---

## File Naming Convention

```
episode6-hero-dashboard.png
episode6-workflow-8steps.png
episode6-architecture-3layers.png
episode6-naming-authority.png
episode6-agent-pipeline.png
episode6-extraction-7sources.png
episode6-color-classifier.png
episode6-rule-engine-output.png
episode6-nexus-synthesis.png
episode6-dtcg-json.png
episode6-figma-visual-spec.png
episode6-before-after.png
episode6-v1-v2-v3-evolution.png
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
- [ ] Ensure color classifier evidence logs are visible
- [ ] Capture the Figma visual spec page with AA badges
- [ ] Show DTCG format in JSON export preview

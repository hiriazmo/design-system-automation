# Design System Extractor — Part 2: Component Generation

## Session Context

**Prerequisite**: Part 1 (Token Extraction + Analysis) is COMPLETE at v3.2
- Phases 1-3 DONE: Normalizer, Stage 2 agents, Export all working
- 113 tests passing, W3C DTCG v1 compliant output
- GitHub: https://github.com/hiriazmo/design-system-extractor-v3
- Project: `/Users/yahya/design-system-extractor-v3/`

**This session**: Build automated component generation from extracted tokens into Figma.

---

## THE GAP: Nobody Does This

Exhaustive research of 30+ tools (Feb 2026) confirms:

**No production tool takes DTCG JSON and outputs Figma Components.**

```
YOUR EXTRACTOR                    THE GAP                     FIGMA
+--------------+    +----------------------------+    +------------------+
| DTCG JSON    |--->|  ??? Nothing does this     |--->| Button component |
| with tokens  |    |  tokens -> components      |    | with 60 variants |
+--------------+    +----------------------------+    +------------------+
```

### What Exists (and What It Can't Do)

| Category | Best Tool | What It Does | Creates Components? |
|----------|-----------|-------------|-------------------|
| Token Importers | Tokens Studio (1M+ installs) | JSON -> Figma Variables | NO - variables only |
| AI Design | Figma Make | Prompt -> prototype | NO - not token-driven |
| MCP Bridges | Figma Console MCP (543 stars) | AI writes to Figma | YES but non-deterministic |
| Code-to-Figma | story.to.design | Storybook -> Figma components | YES but needs full Storybook |
| Generators | Figr Identity | Brand config -> components | YES but can't consume YOUR tokens |
| Commercial | Knapsack ($10M), Supernova | Token management | NO - manages, doesn't create |
| DEAD | Specify.app (shutting down), Backlight.dev (shut down June 2025) | - | - |

### Key Findings Per Category

**Token Importers** (7+ tools evaluated): Tokens Studio, TokensBrucke, Styleframe, DTCG Token Manager, GitFig, Supa Design Tokens, Design System Automator — ALL create Figma Variables from JSON, NONE create components.

**MCP Bridges** (5 tools): Figma Console MCP (Southleft), claude-talk-to-figma-mcp, cursor-talk-to-figma-mcp (Grab), figma-mcp-write-server, Figma-MCP-Write-Bridge — ALL have full write access, but component creation is AI-interpreted (non-deterministic, varies per run).

**Code-to-Figma**: story.to.design is the standout — creates REAL Figma components with proper variants from Storybook. But requires a full coded component library + running Storybook instance as intermediary.

**figma-json2component** (GitHub): Experimental proof-of-concept that generates components from custom JSON schema. Not DTCG, not production quality, but validates the concept IS possible.

---

## FOUR APPROACHES — RANKED

### Option A: Custom Figma Plugin (RECOMMENDED)
```
DTCG JSON -> Your Plugin reads JSON -> Creates Variables -> Generates Components -> Done
```
- **Effort**: 4-8 weeks (~1400 lines of plugin code for 5 MVP components)
- **Quality**: Highest — fully deterministic, consistent every run
- **Advantage**: We already have a working plugin (code.js) that imports tokens
- **Risk**: Low — Figma Plugin API supports everything needed

### Option B: Pipeline — shadcn + Storybook + story.to.design
```
DTCG JSON -> Style Dictionary -> CSS vars -> shadcn themed -> Storybook -> story.to.design -> Figma
```
- **Effort**: 2-3 days setup, then 15-30 min per extraction
- **Quality**: High — battle-tested shadcn components
- **Dependency**: story.to.design (commercial, paid)
- **Risk**: Medium — many moving parts

### Option C: MCP + Claude AI Chain
```
DTCG JSON -> Claude reads tokens -> Figma Console MCP -> AI creates components -> Figma
```
- **Effort**: 2-3 weeks
- **Quality**: Medium — non-deterministic
- **Risk**: High — AI output varies per run

### Option D: Figr Identity + Manual Token Swap
```
Figr Identity generates base system -> Manually swap tokens -> Adjust
```
- **Effort**: 1-2 days
- **Quality**: Medium — not YOUR tokens
- **Risk**: Medium — manual alignment needed

**Decision: Option A (Custom Plugin)** — we already have 80% of the infrastructure, it's deterministic, no external dependencies, and fills a genuine market gap.

---

## FIGMA PLUGIN API: FULL CAPABILITY CHECK

Every feature needed for component generation is supported:

| Requirement | API Method | Status |
|------------|-----------|--------|
| Create components | `figma.createComponent()` | Supported |
| Variant sets (60 variants) | `figma.combineAsVariants()` | Supported |
| Auto-layout with padding | `layoutMode`, `paddingTop/Right/Bottom/Left`, `itemSpacing` | Supported |
| Text labels | `figma.createText()` + `loadFontAsync()` | Supported |
| Icon slot (optional) | `addComponentProperty("ShowIcon", "BOOLEAN", true)` | Supported |
| Instance swap (icons) | `addComponentProperty("Icon", "INSTANCE_SWAP", id)` | Supported |
| Border radius from tokens | `setBoundVariable('topLeftRadius', radiusVar)` | Supported |
| Colors from tokens | `setBoundVariableForPaint()` -> binds to variables | Supported |
| Shadows from tokens | `setBoundVariableForEffect()` | Supported (has spread bug, workaround exists) |
| Hover/press interactions | `node.setReactionsAsync()` with `ON_HOVER`/`ON_PRESS` | Supported |
| Expose text property | `addComponentProperty("Label", "TEXT", "Button")` | Supported |
| Disabled opacity | `node.opacity = 0.5` | Supported |

---

## MVP SCOPE: 5 Components, 62 Variants

| Component | Variants | Automatable? | Effort |
|-----------|---------|-------------|--------|
| **Button** | 4 variants x 3 sizes x 5 states = 60 | Fully | 2-3 days |
| **Text Input** | 4 states x 2 sizes = 8 | Fully | 1-2 days |
| **Card** | 2 configurations | Semi | 1 day |
| **Toast/Notification** | 4 types (success/error/warn/info) | Fully | 1 day |
| **Checkbox + Radio** | ~12 variants | Fully | 1-2 days |
| **Total** | **~86 variants** | | **8-12 days** |

### Post-MVP Components

| Component | Variants | Automatable? | Effort |
|-----------|---------|-------------|--------|
| Toggle/Switch | on/off x enabled/disabled = 4 | Fully | 0.5 day |
| Select/Dropdown | Multiple states | Semi | 1-2 days |
| Modal/Dialog | 3 sizes | Semi | 1 day |
| Table | Header + data rows | Template-based | 2 days |

---

## TOKEN-TO-COMPONENT MAPPING

How extracted tokens bind to component properties:

### Button Example
```
Token                    -> Figma Property
-------------------------------------------------
color.brand.primary      -> Fill (default state)
color.brand.600          -> Fill (hover state)
color.brand.700          -> Fill (pressed state)
color.text.inverse       -> Text color
color.neutral.200        -> Fill (secondary variant)
color.neutral.300        -> Fill (secondary hover)
radius.md                -> Corner radius (all corners)
shadow.sm                -> Drop shadow (elevated variant)
spacing.3                -> Padding horizontal (16px)
spacing.2                -> Padding vertical (8px)
font.body.md             -> Text style (label)
```

### Variable Collections Needed
```
1. Primitives     -> Raw color palette (blue.50 through blue.900, etc.)
2. Semantic       -> Role-based aliases (brand.primary -> blue.500)
3. Spacing        -> 4px grid (spacing.1=4, spacing.2=8, spacing.3=12...)
4. Radius         -> none/sm/md/lg/xl/full
5. Shadow         -> xs/sm/md/lg/xl elevation levels
6. Typography     -> Font families, sizes, weights, line-heights
```

---

## COMPONENT DEFINITION SCHEMA (Proposed)

Each component needs a JSON definition describing its anatomy, token bindings, and variant matrix:

```json
{
  "component": "Button",
  "anatomy": {
    "root": {
      "type": "frame",
      "layout": "horizontal",
      "padding": { "h": "spacing.3", "v": "spacing.2" },
      "radius": "radius.md",
      "fill": "color.brand.primary",
      "gap": "spacing.2"
    },
    "icon_slot": {
      "type": "instance_swap",
      "size": 16,
      "visible": false,
      "property": "ShowIcon"
    },
    "label": {
      "type": "text",
      "style": "font.body.md",
      "color": "color.text.inverse",
      "content": "Button",
      "property": "Label"
    }
  },
  "variants": {
    "Variant": ["Primary", "Secondary", "Outline", "Ghost"],
    "Size": ["Small", "Medium", "Large"],
    "State": ["Default", "Hover", "Pressed", "Focused", "Disabled"]
  },
  "variant_overrides": {
    "Variant=Secondary": {
      "root.fill": "color.neutral.200",
      "label.color": "color.text.primary"
    },
    "Variant=Outline": {
      "root.fill": "transparent",
      "root.stroke": "color.border.primary",
      "root.strokeWeight": 1,
      "label.color": "color.brand.primary"
    },
    "Variant=Ghost": {
      "root.fill": "transparent",
      "label.color": "color.brand.primary"
    },
    "State=Hover": {
      "root.fill": "color.brand.600"
    },
    "State=Pressed": {
      "root.fill": "color.brand.700"
    },
    "State=Disabled": {
      "root.opacity": 0.5
    },
    "Size=Small": {
      "root.padding.h": "spacing.2",
      "root.padding.v": "spacing.1",
      "label.style": "font.body.sm"
    },
    "Size=Large": {
      "root.padding.h": "spacing.4",
      "root.padding.v": "spacing.3",
      "label.style": "font.body.lg"
    }
  }
}
```

### Component Generation Pattern (Plugin Code)

Every component follows the same pipeline:
```
1. Read tokens from DTCG JSON
2. Create Variable Collections (if not exist)
3. For each variant combination:
   a. Create frame with auto-layout
   b. Add child nodes (icon slot, label, etc.)
   c. Apply token bindings via setBoundVariable()
   d. Apply variant-specific overrides
4. combineAsVariants() -> component set
5. Add component properties (Label text, ShowIcon boolean)
```

---

## ARCHITECTURE FOR PLUGIN EXTENSION

Current plugin (`code.js`) already does:
- Parse DTCG JSON (isDTCGFormat detection)
- Create paint styles from colors
- Create text styles from typography
- Create effect styles from shadows
- Create variable collections

What needs to be ADDED:
```
code.js (existing ~1200 lines)
  |
  +-- componentGenerator.js (NEW ~1400 lines)
  |     |-- generateButton()      ~250 lines
  |     |-- generateTextInput()   ~200 lines
  |     |-- generateCard()        ~150 lines
  |     |-- generateToast()       ~150 lines
  |     |-- generateCheckbox()    ~200 lines
  |     |-- generateRadio()       ~150 lines
  |     +-- shared utilities      ~300 lines
  |          |-- createAutoLayoutFrame()
  |          |-- bindTokenToVariable()
  |          |-- buildVariantMatrix()
  |          |-- resolveTokenValue()
  |
  +-- componentDefinitions.json (NEW ~500 lines)
        |-- Button definition
        |-- TextInput definition
        |-- Card definition
        |-- Toast definition
        +-- Checkbox/Radio definition
```

### Implementation Order
```
Week 1-2: Infrastructure
  - Variable collection builder (primitives, semantic, spacing, radius, shadow)
  - Token resolver (DTCG path -> Figma variable reference)
  - Auto-layout frame builder with token bindings
  - Variant matrix generator

Week 3-4: MVP Components
  - Button (60 variants) — most complex, validates the full pipeline
  - TextInput (8 variants) — validates form patterns
  - Toast (4 variants) — validates feedback patterns

Week 5-6: Remaining MVP + Polish
  - Card (2 configs) — validates layout composition
  - Checkbox + Radio (12 variants) — validates toggle patterns
  - Error handling, edge cases, testing

Week 7-8: Post-MVP (if time)
  - Toggle/Switch, Select, Modal
  - Documentation
```

---

## EXISTING FILES TO KNOW ABOUT

| File | Purpose | Lines |
|------|---------|-------|
| `app.py` | Main Gradio app, token extraction orchestration | ~5000 |
| `agents/llm_agents.py` | AURORA, ATLAS, SENTINEL, NEXUS LLM agents | ~1200 |
| `agents/normalizer.py` | Token normalization (colors, radius, shadows) | ~950 |
| `core/color_classifier.py` | Rule-based color classification (PRIMARY authority) | ~815 |
| `core/color_utils.py` | Color math (hex/RGB/HSL, contrast, ramps) | ~400 |
| `core/rule_engine.py` | Type scale, WCAG, spacing grid analysis | ~1100 |
| `output_json/figma-plugin-extracted/figma-design-token-creator 5/src/code.js` | **Figma plugin — EXTEND THIS** | ~1200 |
| `output_json/figma-plugin-extracted/figma-design-token-creator 5/src/ui.html` | Plugin UI | ~500 |

### DTCG Output Format (What the Plugin Receives)

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
    "md": { "$type": "dimension", "$value": "8px" },
    "lg": { "$type": "dimension", "$value": "16px" },
    "full": { "$type": "dimension", "$value": "9999px" }
  },
  "shadow": {
    "sm": {
      "$type": "shadow",
      "$value": {
        "offsetX": "0px",
        "offsetY": "2px",
        "blur": "8px",
        "spread": "0px",
        "color": "#00000026"
      }
    }
  },
  "typography": {
    "body": {
      "md": {
        "$type": "typography",
        "$value": {
          "fontFamily": "Inter",
          "fontSize": "16px",
          "fontWeight": 400,
          "lineHeight": 1.5,
          "letterSpacing": "0px"
        }
      }
    }
  },
  "spacing": {
    "1": { "$type": "dimension", "$value": "4px" },
    "2": { "$type": "dimension", "$value": "8px" },
    "3": { "$type": "dimension", "$value": "16px" }
  }
}
```

---

## COMPETITIVE ADVANTAGE

Building this fills a genuine market gap:
- **Tokens Studio** (1M+ installs) = token management, no component generation
- **Figr Identity** = generates components but from brand config, not YOUR tokens
- **story.to.design** = needs full Storybook pipeline as intermediary
- **MCP bridges** = non-deterministic AI interpretation
- **Us** = DTCG JSON in, deterministic Figma components out. Nobody else does this.

### Strategic Position
```
[Extract from website] -> [Analyze & Score] -> [Generate Components in Figma]
     Part 1 (DONE)          Part 1 (DONE)          Part 2 (THIS)
```

We become the only tool that goes from URL to complete Figma design system with components — fully automated.

---

## OPEN QUESTIONS FOR THIS SESSION

1. Should component definitions live in JSON (data-driven) or be hardcoded in JS (simpler)?
2. Should we generate all 60 Button variants at once, or let user pick which variants?
3. How to handle missing tokens? (e.g., site has no shadow tokens — skip shadow on buttons or use defaults?)
4. Should we support dark mode variants from the start, or add later?
5. Icon system — use a bundled icon set (Lucide?) or just placeholder frames?

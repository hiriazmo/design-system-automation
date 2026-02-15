# Design System Extractor v2 — Project Context

## Overview

A multi-agent system that extracts, analyzes, and recommends improvements for design systems from websites. The system operates in two stages:

1. **Stage 1 (Deterministic)**: Extract CSS values → Normalize → Rule Engine analysis (free, no LLM)
2. **Stage 2 (LLM-powered)**: Brand identification → Benchmark comparison → Best practices → Final synthesis

---

## CURRENT STATUS: BROKEN — NEEDS RETHINK

### What's Wrong (observed from real site tests)

**Tested sites**: sixflagsqiddiyacity.com, others

#### Problem 1: Color Naming is Inconsistent (CRITICAL)
Three competing naming systems produce mixed output:

| Source | Convention | Example |
|--------|-----------|---------|
| `normalizer.py` (line 266-275) | Word-based: light/dark/base | `color.blue.light` |
| `app.py _generate_color_name_from_hex()` | Numeric: 50-900 | `color.blue.500` |
| AURORA LLM agent | Anything it wants | `brand.primary` |

**Result in Figma**: `blue.300`, `blue.dark`, `blue.light`, `blue.base` — ALL IN THE SAME EXPORT. Unusable.

#### Problem 2: Border Radius is Broken (CRITICAL)
- `md = 1616` (concatenated garbage)
- `full = 50` (should be 9999px)
- Nested structures: `radius.full.9999` and `radius.full.100` incorrectly inside `radius.full`
- Multi-value radii like `"0px 0px 16px 16px"` passed as-is — Figma can't use these
- **Root cause**: Normalizer doesn't process radius at all (line 94-97 just stores raw values)

#### Problem 3: LLM Agents Are Single-Shot, No Reasoning (CRITICAL)
- AURORA does one LLM call → returns whatever it returns → no verification
- SENTINEL does one LLM call → scores and checks not validated against actual data
- NEXUS does one LLM call → synthesizes without checking if inputs make sense
- No ReAct/ToT/reflection loop. No self-correction. No critic.
- Models (Qwen 72B, Llama 3.3 70B via HF Inference) may not follow structured output reliably

#### Problem 4: AURORA Only Names ~10 Colors
- Prompt says "Suggest Semantic Names for top 10 most-used colors"
- Remaining 20+ colors keep their normalizer names (word-based)
- AURORA doesn't see existing names — only receives hex + usage count
- No cleanup pass exists to unify naming after AURORA

#### Problem 5: Shadow Ordering Wrong
- xs has blur=25px, sm has blur=30px, md has blur=80px — non-progressive
- Shadow naming (xs/sm/md/lg/xl) doesn't match actual elevation hierarchy
- No validation that shadow progression makes physical sense

#### Problem 6: Font Family Detection
- All fonts showing as "sans-serif" (the fallback) instead of actual font name
- Extraction gets computed style which resolves to generic family

---

## ARCHITECTURE RETHINK PLAN

### Phase 1: Fix Stage 2 (LLM Agents) — ADD AGENTIC REASONING

Current Stage 2 is just 4 single-shot LLM calls. Needs proper agentic framework.

#### Current (Broken):
```
Color Data ──→ [Single LLM Call] ──→ Output (hope for the best)
```

#### Target (With Reasoning):
```
Color Data ──→ [THINK] ──→ [ACT] ──→ [OBSERVE] ──→ [REFLECT] ──→ [VERIFY] ──→ Output
                  │            │           │             │             │
                  │            │           │             │        Does it pass
                  │            │           │        Is this       validation?
                  │            │      Check against  consistent?   If no, loop
                  │         Generate   real data
                  │         initial
                  │         analysis
                Plan approach
```

#### Option A: ReAct Framework (Recommended for AURORA + SENTINEL)
```
Thought: I need to identify brand colors from 30 extracted colors
Action: Analyze usage frequency — #005aa3 used 47x in buttons/CTAs
Observation: #005aa3 is clearly the primary CTA color
Thought: Now check if secondary color exists — look for headers/nav
Action: #ff0000 used 23x in headers → likely brand secondary
Observation: Red + Blue = complementary strategy
Thought: Now I need to name ALL colors consistently using numeric shades
Action: Generate full naming map using Tailwind convention (50-900)
Observation: 28 colors named, all using numeric shades
Thought: Let me verify — any naming conflicts? Any mixed conventions?
Action: Self-check naming consistency
Final Answer: {complete consistent output}
```

#### Option B: Tree of Thought (For NEXUS synthesis)
```
Branch 1: Weight accessibility heavily → overall score 45
Branch 2: Weight consistency heavily → overall score 68
Branch 3: Balanced weighting → overall score 55
Evaluate: Which scoring best reflects reality?
Select: Branch 3 with adjustments
```

#### Option C: Critic/Verifier Pattern (For ALL agents)
```
Agent Output ──→ [CRITIC LLM] ──→ Pass? ──→ Final Output
                      │              │
                      │          No: feedback
                      │              │
                      │              ▼
                      │         [RETRY with feedback]
                      │
                 Checks:
                 - Naming convention consistent?
                 - Scores match actual data?
                 - All required fields present?
                 - Values in valid ranges?
```

### Proposed New Stage 2 Architecture:

```
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 2: AGENTIC ANALYSIS                                         │
│                                                                     │
│  ┌───────────────────────────────────────────────────┐              │
│  │  STEP 1: AURORA (ReAct, 2-3 reasoning steps)     │              │
│  │  Think → Identify brand → Name ALL colors         │              │
│  │  → Self-verify naming consistency                 │              │
│  │  → Critic check → Retry if needed                 │              │
│  └───────────────────────────────────────────────────┘              │
│                          │                                          │
│  ┌───────────────────────┼───────────────────────────┐              │
│  │                       │                           │              │
│  ▼                       ▼                           ▼              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐              │
│  │   ATLAS     │   │  SENTINEL   │   │  VALIDATOR   │              │
│  │  Benchmark  │   │  Best Prac  │   │  (Critic)    │              │
│  │  (ReAct)    │   │  (ReAct)    │   │  Checks ALL  │              │
│  │             │   │             │   │  outputs      │              │
│  └─────────────┘   └─────────────┘   └─────────────┘              │
│         │                │                 │                        │
│         └────────────────┼─────────────────┘                        │
│                          ▼                                          │
│                  ┌─────────────┐                                    │
│                  │   NEXUS     │                                    │
│                  │   (ToT)     │                                    │
│                  │  + Critic   │                                    │
│                  └─────────────┘                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Model Selection Rethink

Current models via HuggingFace Inference API:
| Agent | Current Model | Problem |
|-------|--------------|---------|
| AURORA | Qwen 72B | Doesn't follow structured output reliably |
| ATLAS | Llama 3.3 70B | Adequate for comparison |
| SENTINEL | Qwen 72B | Doesn't validate against actual data |
| NEXUS | Llama 3.3 70B | Single-shot synthesis, no verification |

**Models to evaluate:**
- **Qwen 2.5 72B Instruct** — Better instruction following than Qwen 72B
- **Mixtral 8x22B** — Good at structured JSON output
- **DeepSeek V3** — Strong at reasoning chains
- **Llama 3.1 405B** — Largest open model, best reasoning (but slow/expensive)
- **Command R+** — Designed for tool use and structured output

**Key question**: Should we use ONE model for all agents (consistency) or specialized models per task?

### Phase 2: Fix Stage 1 (After Stage 2 is stable)

#### Normalizer Fixes Needed:
1. **Unify color shade convention** — Pick ONE system (numeric 50-900 recommended)
2. **Add radius normalization** — Currently just stores raw values
3. **Handle multi-value radius** — `"0px 0px 16px 16px"` needs decomposition
4. **Deduplicate radius values** — Multiple entries for same visual radius

#### Rule Engine Fixes Needed:
1. **Base font size filter** — DONE (>= 10px filter applied)
2. **Shadow progression validation** — Check blur/offset increase with elevation
3. **Radius grid alignment** — Check if radii follow base-4/base-8

#### Export Fixes Needed:
1. **Validation layer before export** — Catch mixed conventions, nested garbage
2. **Radius structure flattening** — Never nest tokens inside tokens
3. **Unit consistency** — All radius values must have `px` units

---

## FILE STRUCTURE

```
design-system-extractor-v2-hf-fix/
├── app.py                    # Main Gradio app, orchestrates everything
├── CLAUDE.md                 # THIS FILE — project context and plan
│
├── agents/
│   ├── crawler.py            # Page discovery (finds links on site)
│   ├── extractor.py          # Playwright-based CSS extraction
│   ├── firecrawl_extractor.py # Firecrawl CSS deep extraction
│   ├── normalizer.py         # Token deduplication and naming
│   ├── llm_agents.py         # AURORA, ATLAS, SENTINEL, NEXUS agents
│   ├── stage2_graph.py       # LangGraph orchestration for Stage 2
│   ├── advisor.py            # Upgrade advisor
│   ├── benchmark_researcher.py # Benchmark data collection
│   └── semantic_analyzer.py  # Semantic CSS analysis
│
├── core/
│   ├── token_schema.py       # Pydantic models for all token types
│   ├── color_utils.py        # Color parsing, contrast, ramp generation
│   ├── rule_engine.py        # Deterministic analysis (type scale, WCAG, spacing)
│   ├── hf_inference.py       # HuggingFace Inference API client
│   ├── preview_generator.py  # HTML preview generation
│   ├── validation.py         # Output validation
│   └── logging.py            # Logging utilities
│
├── config/
│   └── settings.py           # Configuration (viewports, timeouts, thresholds)
│
├── tests/
│   ├── test_stage1_extraction.py  # 82 deterministic tests
│   ├── test_agent_evals.py        # 27 LLM agent schema/behavior tests
│   └── test_stage2_pipeline.py    # Pipeline integration tests
│
└── output_json/
    ├── file (16).json             # Latest extraction output (sixflags)
    └── figma-plugin-extracted/    # Figma plugin source
        └── figma-design-token-creator 5/
            └── src/code.js        # Figma plugin main code
```

---

## DATA FLOW (Current vs Target)

### Current Flow (Broken):
```
Extraction → Normalizer (word shades) → Rule Engine → LLM (single-shot)
     ↓              ↓                       ↓              ↓
  Raw CSS     color.blue.light         Stats only    Unverified output
  values      color.neutral.dark       No radius     Mixed naming
              No radius processing     validation    No self-correction
                    ↓
              Export (merges 3 naming conventions → chaos)
```

### Target Flow:
```
Extraction → Normalizer (numeric shades, radius too) → Rule Engine
     ↓              ↓                                      ↓
  Raw CSS     color.blue.500                          Stats + validation
  values      color.neutral.200                       Shadow progression
              radius.md = 8px                         Radius grid check
                    ↓                                      ↓
              LLM Agents (ReAct framework)                 │
                    ↓                                      │
              AURORA: Think → Act → Observe → Verify       │
              SENTINEL: Think → Check data → Score         │
              NEXUS: ToT → Select best synthesis           │
                    ↓                                      │
              CRITIC/VALIDATOR ←────────────────────────────┘
                    ↓                    (validates against Stage 1 data)
              Pass? → Export
              Fail? → Retry with feedback
```

---

## WHAT EACH AGENT SHOULD ACTUALLY DO

### AURORA (Brand Identifier) — Needs ReAct
**Current**: Single-shot, names 10 colors, no verification
**Target**:
- Step 1 (Think): Plan approach based on color count and usage patterns
- Step 2 (Act): Identify brand primary/secondary/accent from usage evidence
- Step 3 (Observe): Check if identification makes sense (is primary really the most-used CTA color?)
- Step 4 (Act): Name ALL colors using consistent numeric convention (50-900)
- Step 5 (Verify): Self-check — are all names consistent? Any mixed conventions?
- Step 6 (Critic): External validation — does output match schema? Names all `color.{family}.{shade}`?

### SENTINEL (Best Practices) — Needs ReAct + Data Grounding
**Current**: Single-shot, scores without verifying against actual data
**Target**:
- Step 1 (Think): What checks apply given the data?
- Step 2 (Act): Score each check CITING SPECIFIC DATA from rule engine
- Step 3 (Observe): Does my score match what the data shows?
- Step 4 (Verify): If rule engine says 5 AA failures, my AA check MUST be "fail" not "pass"
- Step 5 (Critic): Cross-check scores against rule engine numbers

### NEXUS (Synthesizer) — Needs ToT
**Current**: Single-shot synthesis, no evaluation of alternatives
**Target**:
- Branch 1: Accessibility-focused scoring (weight AA failures heavily)
- Branch 2: Consistency-focused scoring (weight naming/grid alignment)
- Branch 3: Balanced approach
- Evaluate: Which branch best reflects reality?
- Critic: Does final score contradict any agent's findings?

---

## KNOWN FIXES ALREADY APPLIED

### 1. Base Font Size Detection (FIXED in rule_engine.py)
Filters out sizes < 10px before detecting base size.

### 2. Garbage Color Names (PARTIALLY FIXED in app.py)
Detects `firecrawl.N` names and regenerates — but the replacement still creates mixed conventions.

### 3. Visual Spec Error Handling (FIXED in code.js)
Defensive error handling for undefined errors.

---

## IDEAL OUTPUT REFERENCE

What the exported JSON SHOULD look like (for Figma):

```json
{
  "color": {
    "brand": {
      "primary": { "$type": "color", "$value": "#005aa3" },
      "secondary": { "$type": "color", "$value": "#ff0000" }
    },
    "text": {
      "primary": { "$type": "color", "$value": "#000000" },
      "secondary": { "$type": "color", "$value": "#999999" },
      "muted": { "$type": "color", "$value": "#cccccc" }
    },
    "background": {
      "primary": { "$type": "color", "$value": "#ebedef" },
      "secondary": { "$type": "color", "$value": "#bfbfbf" }
    },
    "blue": {
      "50": { "$type": "color", "$value": "#b9daff" },
      "300": { "$type": "color", "$value": "#7fdbff" },
      "500": { "$type": "color", "$value": "#6f7597" },
      "800": { "$type": "color", "$value": "#2c3e50" }
    },
    "neutral": {
      "200": { "$type": "color", "$value": "#b2b8bf" },
      "700": { "$type": "color", "$value": "#333333" }
    }
  },
  "radius": {
    "none": { "$type": "dimension", "$value": "0px" },
    "sm": { "$type": "dimension", "$value": "2px" },
    "md": { "$type": "dimension", "$value": "4px" },
    "lg": { "$type": "dimension", "$value": "8px" },
    "xl": { "$type": "dimension", "$value": "16px" },
    "2xl": { "$type": "dimension", "$value": "24px" },
    "full": { "$type": "dimension", "$value": "9999px" }
  }
}
```

**Key rules**:
- Palette colors ALWAYS use numeric shades (50-900)
- Role colors use semantic names (primary, secondary, muted)
- Radius is FLAT — never nested, always single px values
- No mixed conventions in the same category

---

## FILES TO UPDATE ON HUGGINGFACE

When making changes, these files need updating:
1. `app.py` — Main application logic
2. `core/rule_engine.py` — Deterministic analysis
3. `agents/llm_agents.py` — LLM agent prompts and reasoning
4. `agents/normalizer.py` — Token naming and dedup
5. `agents/extractor.py` — CSS extraction
6. `output_json/figma-plugin-extracted/figma-design-token-creator 5/src/code.js` — Figma plugin

---

## CRITICAL DISCOVERY: TWO COMPETING STAGE 2 ARCHITECTURES

The codebase has **two parallel Stage 2 systems** that partially overlap:

### System A: `llm_agents.py` (4 Specialized Agents)
```
AURORA (brand ID) → ATLAS (benchmark) → SENTINEL (best practices) → NEXUS (synthesis)
```
- Each agent has a focused prompt + dedicated data class
- Called from `app.py` directly via `hf_client.complete_async()`
- Uses `Qwen/Qwen2.5-72B-Instruct` and `Llama-3.3-70B-Instruct`
- **Problem**: Single-shot calls, no reasoning, no verification

### System B: `stage2_graph.py` (LangGraph Parallel)
```
LLM1 (Qwen) ──┐
               ├──→ HEAD ──→ Final
LLM2 (Llama) ─┘
Rule Engine ───┘
```
- Two generic "analyst" LLMs run in parallel + rule engine
- Uses LangGraph `StateGraph` with `asyncio.gather()`
- HEAD compiler merges results
- **Problem**: Generic prompts, no specialization, same analysis duplicated

### Decision: Merge into ONE system with ReAct reasoning

Keep System A's **specialized agents** (AURORA, SENTINEL, NEXUS) but add System B's **parallel execution** and **LangGraph state management**. Drop the duplicate generic analysts (LLM1/LLM2).

---

## DETAILED AGENTIC ARCHITECTURE FOR STAGE 2

### Design Principles
1. **ReAct (Reasoning + Acting)**: Each agent THINKS before it acts, OBSERVES the result, REFLECTS on quality
2. **Critic/Verifier**: A lightweight validation pass after each agent output
3. **Grounded Reasoning**: LLMs must cite specific data from Stage 1, not hallucinate
4. **Fail-Safe Defaults**: If LLM fails or produces garbage, fall back to rule-engine defaults
5. **Single Convention**: ALL naming uses numeric shades (50-900), enforced post-LLM

### New Stage 2 Flow

```
Stage 1 Output (NormalizedTokens + RuleEngineResults)
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  PRE-PROCESSING (Deterministic, no LLM)                      │
│  • Unify all color names to numeric shades (50-900)          │
│  • Normalize radius values (flatten, deduplicate)            │
│  • Validate shadow progression (sort by blur)                │
│  • Build structured data packets for each agent              │
└──────────────────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   AURORA    │ │   ATLAS     │ │  SENTINEL   │
│   (ReAct)   │ │  (Single)   │ │  (ReAct)    │
│   2 steps   │ │   1 step    │ │  2 steps    │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  CRITIC 1   │ │  (no critic │ │  CRITIC 2   │
│  Validate   │ │   needed)   │ │  Cross-ref  │
│  naming     │ │             │ │  with data  │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       └───────────────┼───────────────┘
                       ▼
              ┌─────────────────┐
              │     NEXUS       │
              │  (ToT: 2 branches, pick best)  │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │  POST-VALIDATION│
              │  (Deterministic)│
              │  • Names consistent? │
              │  • Scores in range?  │
              │  • All fields present?│
              └─────────────────┘
```

### AURORA — Brand Identifier (ReAct, 2 LLM Calls)

**Why ReAct**: Brand identification requires reasoning about CONTEXT (why a color is used 47x on buttons) not just statistics. The model needs to think step-by-step.

**Step 1: Identify + Name (Main Call)**
```
System: You are AURORA. You will receive color data with usage context.

TASK (do these in order, show your reasoning):

THINK: Look at the color usage data. Which colors appear most in
       interactive elements (buttons, links, CTAs)?
ACT:   Identify brand primary, secondary, accent.
THINK: Now look at ALL colors. Group them by hue family.
ACT:   Assign EVERY color a name using this EXACT convention:
       - Role colors: color.{role}.{shade} where role=brand/text/background/border/feedback
       - Palette colors: color.{hue}.{shade} where hue=red/orange/yellow/green/teal/blue/purple/pink/neutral
       - Shade MUST be numeric: 50/100/200/300/400/500/600/700/800/900
       - NEVER use words like "light", "dark", "base" for shades
OBSERVE: Check your naming. Are ALL names using numeric shades?
         Any duplicates? Any conflicts?

Output JSON with brand_colors + complete naming_map for ALL colors.
```

**Step 2: Critic Check (Lightweight Call or Rule-Based)**
```python
# Can be done WITHOUT an LLM call — just Python validation:
def validate_aurora_output(output: dict, input_colors: list[str]) -> tuple[bool, list[str]]:
    errors = []
    naming_map = output.get("naming_map", {})

    # Check 1: All input colors have names
    for hex_val in input_colors:
        if hex_val not in naming_map:
            errors.append(f"Missing name for {hex_val}")

    # Check 2: No word-based shades
    for hex_val, name in naming_map.items():
        parts = name.split(".")
        last = parts[-1]
        if last in ("light", "dark", "base", "muted", "deep"):
            errors.append(f"Word shade '{last}' in {name} — must be numeric")

    # Check 3: No duplicate names
    names = list(naming_map.values())
    dupes = [n for n in names if names.count(n) > 1]
    if dupes:
        errors.append(f"Duplicate names: {set(dupes)}")

    return len(errors) == 0, errors
```

If validation fails → retry ONCE with error feedback appended to prompt. If still fails → fall back to deterministic HSL-based naming (already in `color_utils.py`).

### SENTINEL — Best Practices (ReAct, 2 LLM Calls)

**Why ReAct**: Scoring must be GROUNDED in actual data. The model needs to cite specific numbers, not make up scores.

**Step 1: Score + Prioritize (Main Call)**
```
System: You are SENTINEL. You MUST cite specific data for every score.

INPUT DATA (from Rule Engine — these are FACTS, not opinions):
- AA Pass: 18 of 25 colors (72%)
- AA Fail: 7 colors (list: #ff0000 3.2:1, #ffdc00 1.8:1, ...)
- Type Scale Ratio: 1.18 (variance: 0.22)
- Base Font: 14px
- Spacing: 8px grid, 85% aligned
- Shadows: 5 defined, blur progression: 25→30→80→80→90 (non-monotonic)
- Near-duplicates: 3 pairs

TASK (cite data for EVERY check):

CHECK 1 - AA Compliance:
  THINK: Rule Engine says 7 of 25 fail. That's 28% failure rate.
  SCORE: "fail" — cite "7 colors fail AA, including brand primary #ff0000 (3.2:1)"

CHECK 2 - Type Scale:
  THINK: Ratio 1.18 is not standard (nearest: 1.2 Minor Third). Variance 0.22 > 0.15.
  SCORE: "warn" — cite "1.18 is close to Minor Third but inconsistent (variance 0.22)"

... (continue for all 8 checks)

THEN calculate overall_score using the weighting:
  AA: 25pts × (pass%/100) = 25 × 0.72 = 18
  Type Scale Consistent: ...
  ... total = sum

Output JSON with checks, overall_score, priority_fixes.
```

**Step 2: Cross-Reference Critic (Rule-Based)**
```python
def validate_sentinel_output(output: dict, rule_engine: RuleEngineResults) -> tuple[bool, list[str]]:
    errors = []
    checks = output.get("checks", {})

    # If rule engine found AA failures, sentinel MUST mark aa_compliance as fail/warn
    aa_failures = len([a for a in rule_engine.accessibility if not a.passes_aa_normal])
    if aa_failures > 0 and checks.get("aa_compliance", {}).get("status") == "pass":
        errors.append(f"Sentinel says AA passes but rule engine found {aa_failures} failures")

    # Score must be 0-100
    score = output.get("overall_score", -1)
    if not (0 <= score <= 100):
        errors.append(f"Score {score} out of range")

    # If many failures, score can't be high
    fail_count = sum(1 for c in checks.values() if isinstance(c, dict) and c.get("status") == "fail")
    if fail_count >= 3 and score > 70:
        errors.append(f"Score {score} too high with {fail_count} failures")

    return len(errors) == 0, errors
```

### ATLAS — Benchmark Advisor (Single Call, No ReAct Needed)

**Why single call**: This agent receives well-structured benchmark comparison data and just needs to pick the best fit. The reasoning is straightforward comparison.

Keep current implementation but improve prompt to:
1. Explicitly output the top 3 benchmarks ranked
2. Include specific numeric diffs for each
3. Cap alignment changes at 4

### NEXUS — HEAD Synthesizer (ToT: 2 Branches)

**Why Tree of Thought**: The synthesizer needs to weigh competing priorities. Should it emphasize accessibility (SENTINEL's input) or brand fidelity (AURORA's input)? ToT lets it explore both and pick the best.

**Branch 1: Accessibility-First Scoring**
```
Weight accessibility at 40%, consistency at 30%, organization at 30%.
If SENTINEL found 7 AA failures → accessibility score tanks → overall score lower.
Result: overall ~55
```

**Branch 2: Balanced Scoring**
```
Weight accessibility at 30%, consistency at 35%, organization at 35%.
Same data but organization counts more.
Result: overall ~65
```

**Selection**: Pick the branch that:
1. Doesn't contradict any agent's hard failures (if SENTINEL says AA fails, score CAN'T say accessibility is "good")
2. Produces actionable top-3 actions (not generic)
3. Has color recommendations with specific hex values

**Implementation**: This can be done as a SINGLE LLM call with explicit instruction:

```
TASK: You will synthesize from two perspectives.

PERSPECTIVE A (Accessibility-First): Weight AA compliance heavily.
Calculate scores with accessibility=40%, consistency=30%, org=30%.

PERSPECTIVE B (Balanced): Equal weights.
Calculate scores with accessibility=33%, consistency=33%, org=33%.

THEN: Compare both perspectives. Choose the one that:
1. Better reflects the ACTUAL data (don't ignore failures)
2. Produces the most actionable top-3 list
3. Is internally consistent

Output your CHOSEN perspective's scores + explain WHY you chose it.
```

### Model Selection (Final Decision)

After reviewing all agents' needs:

| Agent | Model | Reasoning |
|-------|-------|-----------|
| AURORA | `Qwen/Qwen2.5-72B-Instruct` | Best at structured JSON, good reasoning |
| ATLAS | `meta-llama/Llama-3.3-70B-Instruct` | 128K context for benchmark data |
| SENTINEL | `Qwen/Qwen2.5-72B-Instruct` | Methodical, follows rubrics well |
| NEXUS | `meta-llama/Llama-3.3-70B-Instruct` | Good synthesis, large context |

**Keep current models** — the problem isn't the models, it's the prompting strategy (single-shot vs ReAct) and lack of validation.

### Cost Budget Per Extraction

| Step | LLM Calls | Est. Tokens | Est. Cost |
|------|-----------|-------------|-----------|
| AURORA main | 1 | ~2K in, ~1K out | $0.001 |
| AURORA retry (10% of time) | 0.1 | ~2K in, ~1K out | $0.0001 |
| ATLAS | 1 | ~1.5K in, ~0.8K out | $0.001 |
| SENTINEL main | 1 | ~2K in, ~1K out | $0.001 |
| SENTINEL retry (10% of time) | 0.1 | ~2K in, ~1K out | $0.0001 |
| NEXUS | 1 | ~3K in, ~1.2K out | $0.002 |
| **Total** | **~4.2** | **~14K** | **~$0.005** |

Well within HF free tier ($0.10/mo).

---

## IMPLEMENTATION PLAN

### Step 1: Consolidate Stage 2 into ONE system
- Keep `llm_agents.py` as the agent definitions (AURORA, SENTINEL, NEXUS)
- Use `stage2_graph.py` for orchestration (parallel AURORA+ATLAS+SENTINEL, then NEXUS)
- Delete the duplicate generic LLM1/LLM2 analyst nodes
- Single entry point: `run_stage2_analysis()`

### Step 2: Add Pre-Processing Layer
- Before any LLM call, run deterministic cleanup:
  - Unify ALL color names to numeric shades (50-900)
  - Flatten and deduplicate radius values
  - Sort shadows by blur radius
  - Build structured data packets for each agent

### Step 3: Rewrite AURORA with ReAct Prompt
- New prompt: Think → Identify brand → Name ALL colors → Self-verify
- Add `validate_aurora_output()` rule-based critic
- Retry once on validation failure
- Fallback to `_generate_color_name_from_hex()` if LLM fails

### Step 4: Rewrite SENTINEL with Grounded Scoring
- New prompt: Must cite rule-engine data for every check
- Add `validate_sentinel_output()` cross-reference critic
- Ensure scores match actual data (no inflated pass when data says fail)

### Step 5: Rewrite NEXUS with ToT
- Two-perspective evaluation in single prompt
- Must choose perspective and explain why
- Post-validation: scores internally consistent, actions are specific

### Step 6: Add Post-Validation Layer
- After all agents complete, run deterministic checks:
  - All color names follow `color.{family}.{shade}` pattern
  - All scores are in valid ranges
  - No contradictions between agents
  - All required fields present
- If post-validation fails, apply rule-based fixes (not another LLM call)

### Step 7: Fix Normalizer (Stage 1)
- Unify `_generate_color_name_from_value()` to use numeric shades only
- Add radius normalization (flatten, single-value, deduplicate)
- Handle multi-value radius (`"0px 0px 16px 16px"` → individual values or skip)

### Step 8: Fix Export Layer
- Validation before JSON export
- Ensure DTCG format (`$type`, `$value`)
- Flat radius (never nested tokens inside tokens)
- Consistent units (all px for dimensions)

---

## STAGE 1 AUDIT: WHAT IS VALID vs WHAT NEEDS RETHINKING

Stage 1 feeds Stage 2 — if Stage 1 produces garbage, no amount of agentic reasoning in Stage 2 can fix it. Let's audit every rule-based component honestly.

### OVERALL VERDICT: Stage 1 is ~60% correct, 40% broken/missing

The extraction (Playwright CSS scraping) is solid. The normalizer and rule engine have real problems that corrupt data BEFORE any LLM ever sees it.

---

### Component 1: Extractor (`agents/extractor.py`) — ✅ MOSTLY VALID

**What it does**: Playwright visits pages, extracts computed CSS styles for every element.
**What it produces**: `ExtractedTokens` — lists of `ColorToken`, `TypographyToken`, `SpacingToken`, `RadiusToken`, `ShadowToken`.

**What's working**:
- Color extraction: Gets hex values, usage frequency, CSS property context (background-color, color, border-color), element types (button, h1, p). This is exactly what Stage 2 needs.
- Typography extraction: Gets font-family, font-size, font-weight, line-height, element context. Solid.
- Spacing extraction: Gets margin/padding/gap values with px conversion. Solid.

**What's broken**:
- **Font family**: Returns `"sans-serif"` (the computed fallback) instead of `"Inter"` (the actual font). This is a browser behavior issue — `getComputedStyle()` resolves the font stack to the generic family. **Fix needed**: Use `document.fonts.check()` or extract from CSS `font-family` declarations before resolution.
- **Radius**: Extracts raw CSS values including multi-value shorthand like `"0px 0px 16px 16px"` and percentage values like `"50%"`. The RadiusToken has `value: str` and `value_px: Optional[int]` but the extractor doesn't parse multi-value or percentage. **Fix needed**: Parse in extractor or normalizer.
- **Shadows**: Extracts full CSS shadow string but parsing into components (offset_x, offset_y, blur, spread, color) is unreliable. Some shadows have `None` for all parsed fields. **Fix needed**: Better CSS shadow parser.

**Verdict**: Extraction is the least broken part. Font family is the biggest issue but it's a well-known Playwright limitation with known workarounds.

---

### Component 2: Normalizer (`agents/normalizer.py`) — ❌ NEEDS MAJOR RETHINK

**What it does**: Takes raw `ExtractedTokens` lists → deduplicates → names → outputs `NormalizedTokens` dicts.

**What's working**:
- Color deduplication by exact hex: Correct. Merges frequency/contexts.
- Similar color merging (RGB Euclidean distance < 10): Reasonable threshold, works.
- Typography dedup by unique `family|size|weight|lineHeight`: Correct.
- Spacing dedup and base-8 alignment preference: Correct.
- Confidence scoring by frequency (10+=high, 3-9=medium, 1-2=low): Reasonable.

**What's BROKEN**:

#### Problem 2A: Color Naming — TWO COMPETING FUNCTIONS

```
_generate_color_name(color, role) → line 236-256
  Input: color + inferred role (from CSS context keywords)
  Output: "color.{role}.{shade}" where shade = 50/200/500/700/900
  Uses: NUMERIC shades based on luminance buckets ✅

_generate_color_name_from_value(color) → line 258-275
  Input: color (no role found)
  Output: "color.{category}.{shade}" where shade = light/base/dark
  Uses: WORD shades ❌ ← THIS IS THE ROOT OF THE NAMING PROBLEM
```

**The irony**: The first function (with role) already uses numeric shades! But only colors where `_infer_color_role()` finds a keyword match get numeric names. All other colors fall through to the word-based function.

**`_infer_color_role()` (line 220-234)**: Searches color.contexts + color.elements for keywords like "primary", "button", "background". **Problem**: Most extracted colors don't have semantic class names — they come from computed styles on generic elements. A `<div>` with `background-color: #005aa3` has no "primary" keyword anywhere. So MOST colors fall through to word-based naming.

**How often does role inference work?** Rough estimate:
- Sites with BEM/utility classes (Tailwind, Bootstrap): ~40% of colors get roles
- Sites with generic/minified classes: ~5-10% of colors get roles
- Remaining get word-based names → causes mixed convention chaos

**Fix needed**: Remove `_generate_color_name_from_value()` entirely. Make `_generate_color_name()` the only path, and if no role is inferred, use hue-family + numeric shade (which `_generate_color_name_from_hex()` in app.py already does correctly).

#### Problem 2B: Radius — NO PROCESSING AT ALL

```python
# Line 93-97: Just stores raw values
radius_dict = {}
for r in extracted.radius:
    key = f"radius-{r.value}"   # Raw CSS value as dict key!
    radius_dict[key] = r
```

**What this produces**:
- `"radius-8px"` → ok
- `"radius-0px 0px 16px 16px"` → garbage key, multi-value
- `"radius-50%"` → percentage, Figma can't use
- `"radius-16px"` AND `"radius-1rem"` → duplicates (both = 16px)

**What's missing**:
1. No value parsing (multi-value → skip or take max)
2. No unit normalization (%, rem, em → px)
3. No deduplication by resolved px value
4. No semantic naming (none/sm/md/lg/xl/full)
5. No sorting by size

#### Problem 2C: Shadows — NO PROCESSING AT ALL

```python
# Line 99-102: Hash-based key, no analysis
shadows_dict = {}
for s in extracted.shadows:
    key = f"shadow-{hash(s.value) % 1000}"  # Meaningless key!
    shadows_dict[key] = s
```

**What's missing**:
1. No deduplication by visual similarity
2. No sorting by elevation (blur radius)
3. No semantic naming (xs/sm/md/lg/xl)
4. No validation of shadow progression (blur should increase with elevation level)
5. No filtering of garbage shadows (blur=0, identical to another, etc.)

#### Problem 2D: Typography Naming — COLLISION RISK

```python
# Line 310-339: Size-tier names can collide
"font.{category}.{size_tier}"
# Two different h2 styles (24px/700 and 24px/400) both become "font.heading.lg"
```

The dedup key at line 86 is `suggested_name or f"{font_family}-{font_size}"`, so if two styles get the SAME suggested name, the second overwrites the first silently.

---

### Component 3: Rule Engine (`core/rule_engine.py`) — ✅ MOSTLY VALID

**What it does**: Deterministic analysis — type scale ratios, WCAG contrast, spacing grid detection, color statistics.

**What's working**:
- **Type scale analysis**: Detects ratio between consecutive font sizes, identifies closest standard scale, measures consistency (variance). Correctly filters sizes < 10px. ✅
- **WCAG contrast checking**: Correct `get_relative_luminance()` per WCAG 2.1 spec. Correct 4.5:1 threshold for AA normal text, 3.0:1 for large text. ✅
- **AA fix suggestions**: `find_aa_compliant_color()` iterates darken/lighten in 1% steps until 4.5:1 is reached. Brute-force but correct. ✅
- **Spacing grid detection**: GCD-based base detection, alignment % calculation. Correct. ✅
- **Color statistics**: Near-duplicate detection, hue distribution, gray/saturated counts. Correct. ✅
- **Consistency score**: Weighted formula combining all checks. Reasonable. ✅

**What's broken/questionable**:

#### Problem 3A: Accessibility Only Tests Against White/Black

```python
# Line 545-550
contrast_white = get_contrast_ratio(hex_color, "#ffffff")
contrast_black = get_contrast_ratio(hex_color, "#000000")
passes_aa_normal = contrast_white >= 4.5 or contrast_black >= 4.5
```

This tests every color against pure white AND pure black. If it passes against EITHER, it's marked as passing. But:
- A brand blue (#005aa3) that passes on white (7.2:1) might be used on a dark navy background (#1a1a2e) where it fails (1.8:1)
- A light gray (#cccccc) passes on black but is used as text on white (#ffffff) where it fails (1.6:1)

The `fg_bg_pairs` logic (line 577-610) partially addresses this — it checks actual foreground-background combinations from the DOM. **But**: it only adds FAILURES to the results, doesn't correct the per-color assessment above. So a color could show as "passes AA" in the per-color check but "fails AA" in the pair check. **Contradictory data sent to SENTINEL**.

**Fix needed**: Two modes — (1) per-color against white/black for palette overview, (2) per-pair for actual accessibility score. SENTINEL should see BOTH clearly labeled.

#### Problem 3B: No Radius Analysis

The rule engine receives `radius_tokens` (line 1034) but does NOTHING with them. No grid alignment check, no progression validation, no statistics. It's just passed through.

#### Problem 3C: Shadow Analysis Is Minimal

The rule engine receives `shadow_tokens` but only passes them to SENTINEL's prompt as raw strings. No programmatic analysis of:
- Blur progression (should increase with elevation)
- Y-offset progression (should increase with elevation)
- Color consistency (should all use same base color/alpha)
- Whether shadows form a coherent elevation system

This means SENTINEL gets raw shadow CSS strings and has to evaluate them purely from text — no pre-computed metrics to ground its scoring.

---

### Component 4: Semantic Analyzer (`agents/semantic_analyzer.py`) — ⚠️ USEFUL BUT UNDERTRUSTED

**What it does**: Rule-based categorization of colors by CSS property usage. If a color is used in `background-color` on buttons → it's likely brand primary. If used in `color` property on `<p>` → it's likely text color.

**What's working**: The logic is sound — CSS property + element type is a strong signal for color role. This is actually one of the best parts of Stage 1.

**What's broken**: AURORA receives this as `semantic_analysis` parameter but the data is passed as a secondary input, not the primary. AURORA's prompt says "Suggest Semantic Names for top 10 most-used colors" — it ignores the semantic analysis for the OTHER 20 colors. The semantic analyzer's work is wasted for most colors.

---

### Component 5: Color Utils (`core/color_utils.py`) — ✅ VALID

**What it does**: Hex/RGB/HSL parsing, contrast calculation, color categorization by hue, color ramp generation.

**What's working**: All the pure color math is correct. `categorize_color()` returns the right hue family. `generate_color_ramp()` produces reasonable 50-900 shade ramps using OKLCH.

**No issues found.** This is the most solid component.

---

### Component 6: Export Layer (`app.py` export functions) — ❌ NEEDS RETHINK

Already documented above in the AS-IS flow. The 3-way naming merge is the killer.

---

## WHAT STAGE 1 SHOULD ACTUALLY PRODUCE (for Stage 2 to work)

### Current: What Stage 2 receives
```
NormalizedTokens:
  colors: {
    "color.blue.light": ColorToken(value="#7fdbff", freq=5, contexts=["background"]),
    "color.blue.dark": ColorToken(value="#2c3e50", freq=12, contexts=["text", "button"]),
    "color.blue.base": ColorToken(value="#005aa3", freq=47, contexts=["button", "link"]),
    "color.neutral.dark": ColorToken(value="#333333", freq=89, contexts=["text"]),
    // ← word-based shades, no consistent convention
  }
  radius: {
    "radius-8px": RadiusToken(value="8px"),
    "radius-0px 0px 16px 16px": RadiusToken(value="0px 0px 16px 16px"),  // ← garbage
    "radius-50%": RadiusToken(value="50%"),  // ← Figma can't use
  }
  shadows: {
    "shadow-234": ShadowToken(value="0px 4px 25px rgba(0,0,0,0.1)"),  // ← meaningless key
    "shadow-891": ShadowToken(value="0px 2px 30px rgba(0,0,0,0.15)"),  // ← unsorted
  }
```

### Target: What Stage 2 SHOULD receive
```
NormalizedTokens:
  colors: {
    "color.blue.300": ColorToken(value="#7fdbff", freq=5, contexts=["background"],
                                  role="palette", hue="blue", shade=300),
    "color.blue.800": ColorToken(value="#2c3e50", freq=12, contexts=["text", "button"],
                                  role="palette", hue="blue", shade=800),
    "color.blue.500": ColorToken(value="#005aa3", freq=47, contexts=["button", "link"],
                                  role="brand_candidate", hue="blue", shade=500),
    "color.neutral.700": ColorToken(value="#333333", freq=89, contexts=["text"],
                                    role="text_candidate", hue="neutral", shade=700),
    // ← ALL numeric shades, with role hints for AURORA
  }
  radius: {
    "radius.sm": RadiusToken(value="4px", value_px=4),
    "radius.md": RadiusToken(value="8px", value_px=8),
    "radius.xl": RadiusToken(value="16px", value_px=16),
    "radius.full": RadiusToken(value="9999px", value_px=9999),
    // ← flat, single-value, deduped, sorted, named
  }
  shadows: {
    "shadow.xs": ShadowToken(value="...", blur_px=4, y_offset_px=2),
    "shadow.sm": ShadowToken(value="...", blur_px=8, y_offset_px=4),
    "shadow.md": ShadowToken(value="...", blur_px=16, y_offset_px=8),
    // ← sorted by elevation, named progressively
  }
```

### What changes are needed in Stage 1:

| Component | Current State | What's Wrong | Fix |
|-----------|--------------|-------------|-----|
| **Normalizer: color naming** | Two functions, word vs numeric | Mixed conventions | Remove word-based function, use numeric for ALL |
| **Normalizer: color role hints** | Keyword-based inference (5-40% hit rate) | Most colors get no role | Add `role_hint` field: "brand_candidate", "text_candidate", "bg_candidate" based on CSS property (from semantic analyzer) |
| **Normalizer: radius** | Raw values stored, no processing | Multi-value, %, no dedup | Parse → single px value → deduplicate → sort → name (none/sm/md/lg/xl/full) |
| **Normalizer: shadows** | Hash-based keys, no processing | Unsorted, unnamed, no metrics | Parse components → sort by blur → deduplicate → name (xs/sm/md/lg/xl) |
| **Normalizer: typography** | Collision-prone naming | Same name for different styles | Add weight suffix: `font.heading.lg.700` vs `font.heading.lg.400` |
| **Rule engine: accessibility** | Tests against white/black only | Doesn't match real usage | Add separate per-pair analysis, label both modes clearly |
| **Rule engine: radius** | Not analyzed | No grid check, no stats | Add radius grid analysis (base-4/base-8), dedup stats |
| **Rule engine: shadows** | Not analyzed | No progression check | Add shadow elevation analysis (blur/offset progression) |
| **Extractor: font family** | Returns fallback generic | Browser resolves to "sans-serif" | Extract from CSS declaration before computed resolution |

---

## REVISED EXECUTION ORDER (Stage 1 fixes interleaved, not deferred)

The original plan was "fix Stage 2 first, Stage 1 later." But the audit reveals:
**If normalizer sends word-based shade names to AURORA, AURORA's ReAct naming will STILL conflict with normalizer names in the export merge.**

The pre-processing layer (Step 2 in the old plan) was supposed to fix this. But that's a bandaid — it re-normalizes what the normalizer already normalized. It's cleaner to fix the normalizer itself so it produces correct output from the start.

### New Execution Order:

```
PHASE 1: FIX NORMALIZER (makes Stage 1 output clean)
  1a. Unify color naming → numeric shades only
  1b. Add radius normalization (parse, deduplicate, sort, name)
  1c. Add shadow normalization (parse, sort by blur, name)
  1d. Feed semantic_analyzer role hints into normalizer

PHASE 2: FIX STAGE 2 (agents can now trust their input)
  2a. Consolidate two Stage 2 systems into one
  2b. Rewrite AURORA with ReAct + critic (names ALL colors, not 10)
  2c. Rewrite SENTINEL with grounded scoring + critic
  2d. Rewrite NEXUS with ToT
  2e. Add post-validation layer

PHASE 3: FIX EXPORT (single naming authority)
  3a. AURORA naming_map is THE authority (not 3-way merge)
  3b. Radius/shadow export uses normalizer output directly
  3c. Validation before JSON write

PHASE 4: FIX EXTRACTION (nice-to-have, not blocking)
  4a. Font family detection improvement
  4b. Rule engine: radius grid analysis
  4c. Rule engine: shadow elevation analysis
```

### Why this order is better:

1. **Phase 1 first** because AURORA can't name colors well if the input names are garbage. The ReAct prompt says "observe your naming" but if the LLM sees `color.blue.light` in its input AND is asked to output `color.blue.300`, it gets confused.

2. **Phase 2 after Phase 1** because now the LLM agents receive clean, consistently-named input. AURORA's job becomes "confirm or improve these names" rather than "fix the mess from normalizer."

3. **Phase 3 after Phase 2** because the export layer just needs to respect one naming authority (AURORA), not reconcile three.

4. **Phase 4 last** because font family and enhanced rule engine analysis are improvements, not blockers.

### Deploy Plan:
- **Deploy 1**: After Phase 1 (normalizer fixes) — even without Stage 2 improvements, the export will be cleaner
- **Deploy 2**: After Phase 2 + 3 (full Stage 2 rework + export) — the big quality jump
- **Deploy 3**: After Phase 4 (font family, enhanced analysis) — polish

---

## CRITIC REVIEW: SHOULD EACH COMPONENT STAY RULE-BASED OR USE LLM?

Every rule-based component needs to justify itself. Rules are free and fast, but if they produce garbage that LLMs then have to fix, the "free" part is an illusion — you pay in bad output quality instead.

### Decision Framework

| Use Rules When... | Use LLM When... |
|---|---|
| Math with right answers (contrast ratio) | Judgment with context (is this the brand color?) |
| Deterministic transforms (hex→RGB) | Ambiguous signals (is this a button or just a styled div?) |
| Simple pattern matching (is 16 divisible by 8?) | Weighing competing evidence (high freq but wrong context) |
| Zero tolerance for hallucination (export format) | Understanding intent (why is this color used here?) |
| Must be 100% reproducible | Acceptable to vary slightly between runs |

---

### 1. Color Naming (Normalizer) — ❌ RULES FAILING, NEEDS RETHINK

**Current**: Rule-based. Two functions: keyword-match for role → numeric shade, fallback → word shade.

**Critic's Question**: Can rules correctly name 30 colors with just CSS property + element context?

**Honest Answer**: No. Here's why:

The normalizer's `_infer_color_role()` searches for keywords like "primary", "button", "background" in the element/context strings. But:

```
Extracted color: #005aa3, freq=47
  css_properties: ["background-color"]
  elements: ["div", "a"]
  contexts: ["background"]
```

No keyword "primary" or "button" anywhere. Rules classify this as "unknown role" → falls to word-based naming → `color.blue.base`. But this is CLEARLY the brand primary (used 47 times on links and divs with background-color).

An LLM can reason: "47 uses on `<a>` elements with `background-color` = this is a CTA color = brand primary." Rules can't make that inference.

**But**: An LLM to name 30 colors costs ~$0.001 and adds 2-3 seconds. For something that happens once per extraction, this is acceptable.

**Verdict**:
- **Keep rules for**: Hue family detection (HSL math), shade number assignment (luminance → 50-900), deduplication (exact hex + RGB distance)
- **Move to LLM (AURORA)**: Semantic role assignment (brand.primary vs text.secondary vs background.primary). This is already AURORA's job — but currently AURORA only does it for 10 colors. Expand AURORA to name ALL colors.
- **ELIMINATE from normalizer**: The `_generate_color_name_from_value()` function and the `_infer_color_role()` function. Replace with a simpler `_generate_preliminary_name()` that just uses hue + numeric shade. Let AURORA do the semantic naming.

**New flow**:
```
Normalizer: "color.blue.500" (hue + shade, no role)
     ↓
AURORA: "color.brand.primary" (semantic role from context reasoning)
     ↓
Export: Uses AURORA name, falls back to normalizer name
```

---

### 2. Radius Processing — ✅ RULES ARE CORRECT APPROACH, JUST MISSING

**Current**: No processing at all (raw values stored).

**Critic's Question**: Does radius naming need LLM intelligence?

**Honest Answer**: No. Radius is pure math:
- Parse CSS value → px number
- Skip multi-value shorthand (or take max)
- Convert 50% → 9999px (full circle)
- Sort by px value
- Name by size tier: 0=none, 1-3=sm, 4-8=md, 9-16=lg, 17-24=xl, 25+=2xl, 9999=full

No ambiguity, no judgment needed. An LLM would add nothing here.

**Verdict**: Keep rule-based. Just implement the processing that's currently missing.

---

### 3. Shadow Processing — ⚠️ MOSTLY RULES, BUT LLM COULD HELP WITH EDGE CASES

**Current**: No processing at all (hash-based keys).

**Critic's Question**: Can rules correctly name and sort shadows?

**Mostly yes**:
- Parse CSS shadow string → {x, y, blur, spread, color} — regex, no LLM needed
- Sort by blur radius — math
- Name by elevation tier (xs/sm/md/lg/xl) — math
- Detect non-monotonic progression — math

**But**: Some edge cases are hard for rules:
- `0px 0px 0px 4px rgba(0,0,0,0.2)` — is this a shadow or a border simulation? (spread-only, no blur)
- Multiple shadows on same element — which is the "primary" shadow?
- `inset` shadows — different semantic meaning (inner glow vs elevation)

These edge cases affect maybe 10% of shadows. Rules can handle 90% correctly.

**Verdict**: Keep rule-based for parsing, sorting, naming. Add simple heuristic rules for edge cases (spread-only → treat as border, inset → separate category). NOT worth an LLM call.

---

### 4. Accessibility Checking (Rule Engine) — ✅ RULES ARE THE ONLY CORRECT APPROACH

**Current**: WCAG contrast math + fix suggestions.

**Critic's Question**: Could an LLM improve accessibility checking?

**Absolutely not.** WCAG is a mathematical standard. 4.5:1 is 4.5:1. An LLM cannot calculate contrast ratios — it would hallucinate them. The rule engine's `get_relative_luminance()` implementation follows the exact WCAG 2.1 spec. This MUST stay rule-based.

**What rules CAN'T do** (and LLM CAN): Prioritize which failures matter most. "Brand primary fails AA" is more critical than "a decorative border color fails AA." This is judgment → belongs in SENTINEL.

**Verdict**: Keep accessibility math 100% rule-based. Use SENTINEL to prioritize/contextualize the results.

---

### 5. Type Scale Detection (Rule Engine) — ✅ RULES ARE CORRECT

**Current**: Ratio calculation between consecutive font sizes, variance check, standard scale matching.

**Critic's Question**: Could an LLM detect type scales better?

**No.** Type scale detection is pure math: sizes → ratios → average → closest standard. An LLM would be slower and less accurate at arithmetic.

**What rules CAN'T do**: Recommend which scale to adopt. "Your ratio is 1.18, should you round to 1.2 (Minor Third) or 1.25 (Major Third)?" — this depends on the site's purpose (content-heavy = 1.2, marketing = 1.333). This is judgment → belongs in ATLAS/NEXUS.

**Verdict**: Keep rule-based. Already working correctly after the 10px filter fix.

---

### 6. Spacing Grid Detection (Rule Engine) — ✅ RULES ARE CORRECT

**Current**: GCD-based detection, alignment percentage, base-4/base-8 check.

**Verdict**: Pure math, working correctly. Keep rule-based.

---

### 7. Semantic Color Analysis (`semantic_analyzer.py`) — ⚠️ OVERLAPS WITH AURORA, CONSOLIDATE

**Current**: Rule-based fallback + optional LLM call. Categorizes colors into brand/text/background/border/feedback.

**Critic's Question**: This does THE SAME JOB as AURORA. Why do we have both?

**The overlap**:
- Semantic Analyzer: "This color is brand.primary because it's on buttons" (rule-based + optional LLM)
- AURORA: "This color is brand.primary because it's used 47x on CTAs" (LLM)
- Both produce semantic names for colors
- Both feed into export

**The problem**: They run at DIFFERENT STAGES:
- Semantic Analyzer runs in Stage 1 (during extraction)
- AURORA runs in Stage 2 (during analysis)
- Their outputs can conflict
- Export tries to merge both → more naming chaos

**Verdict**: ELIMINATE the semantic analyzer as a separate component. Move its rule-based heuristics INTO the normalizer as `role_hint` field (e.g., "brand_candidate", "text_candidate"). These hints become INPUT to AURORA, not a competing output.

```
BEFORE:
  Semantic Analyzer → state.semantic_analysis → AURORA (partially uses it)
                                              → Export (also uses it, conflicts)

AFTER:
  Normalizer adds role_hints → AURORA uses hints as evidence → AURORA names → Export
  (no separate semantic analyzer)
```

---

### 8. Color Deduplication (Normalizer) — ⚠️ RULES ARE CORRECT BUT THRESHOLD IS QUESTIONABLE

**Current**: RGB Euclidean distance < 10 → merge.

**Critic's Question**: Is RGB distance the right metric?

**Not really.** RGB Euclidean distance is NOT perceptually uniform. Two colors that look identical to humans can have large RGB distance, and two that look different can have small RGB distance. The industry standard for perceptual color difference is Delta-E (CIE2000).

However: For the purpose of "should we keep both #1a1a1a and #1b1b1b in the design system?" — RGB distance < 10 is a reasonable approximation. These truly are near-identical grays.

The color_utils.py `color_distance()` function also uses RGB Euclidean. It's used in the rule engine for near-duplicate detection.

**Verdict**: Keep rule-based, but consider switching to Delta-E (CIEDE2000) for better perceptual accuracy. Low priority — the current approach works for most cases.

---

### 9. Color Statistics (Rule Engine) — ✅ RULES ARE CORRECT

Counting uniques, duplicates, hue distribution — pure counting. Keep rule-based.

---

### 10. Pre-Processing Layer (NEW — proposed in architecture) — SHOULD THIS BE AN LLM?

**Current plan**: Deterministic pre-processing before Stage 2 agents.

**Critic's Question**: The pre-processing unifies names, flattens radius, sorts shadows. Should this use an LLM?

**No.** Everything pre-processing does is deterministic:
- Rename color.blue.light → color.blue.300 (luminance lookup table)
- Flatten "0px 0px 16px 16px" → skip or max(16)
- Sort shadows by blur px

No judgment needed, no ambiguity. Keep deterministic.

---

## SUMMARY: WHAT STAYS RULE-BASED, WHAT MOVES TO LLM

```
┌─────────────────────────────────────────────────────────────────┐
│  KEEP RULE-BASED (correct, no LLM needed)                       │
│                                                                  │
│  ✅ WCAG contrast calculation                                    │
│  ✅ Type scale ratio detection                                   │
│  ✅ Spacing grid detection (GCD)                                 │
│  ✅ Color deduplication (RGB/Delta-E distance)                   │
│  ✅ Color statistics (counts, hue distribution)                  │
│  ✅ Radius processing (parse, sort, name) — needs implementing   │
│  ✅ Shadow processing (parse, sort, name) — needs implementing   │
│  ✅ Color hue family detection (HSL math)                        │
│  ✅ Color shade number assignment (luminance → 50-900)           │
│  ✅ Pre-processing layer (rename, flatten, sort)                 │
│  ✅ Post-validation layer (check conventions, ranges)            │
│  ✅ AA fix suggestions (darken/lighten iteration)                │
│  ✅ Export format (DTCG structure)                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  MOVE TO LLM (requires judgment, context, ambiguity)            │
│                                                                  │
│  🤖 Color semantic naming (brand.primary vs text.secondary)     │
│     Currently: normalizer (bad) + semantic analyzer (conflicts)  │
│     Move to: AURORA (ReAct, names ALL colors)                    │
│                                                                  │
│  🤖 Prioritizing which AA failures matter most                  │
│     Currently: all treated equally                               │
│     Move to: SENTINEL (cites data, ranks by impact)              │
│                                                                  │
│  🤖 Scoring cohesion/consistency holistically                    │
│     Currently: simple weighted formula                           │
│     Move to: NEXUS (weighs competing dimensions)                 │
│                                                                  │
│  🤖 Recommending which design system to align with              │
│     Currently: ATLAS (already LLM) — keep as is                  │
│                                                                  │
│  🤖 Recommending scale/spacing changes                           │
│     Currently: defaults to "1.25 Major Third"                    │
│     Move to: NEXUS (considers site purpose and brand)            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ELIMINATE (redundant or actively harmful)                       │
│                                                                  │
│  ❌ normalizer._generate_color_name_from_value()                │
│     Word-based shades (light/dark/base) — root cause of chaos   │
│                                                                  │
│  ❌ normalizer._infer_color_role()                              │
│     Keyword matching for role — too low hit rate (5-40%)        │
│     Replace with: role_hint from CSS property + element type    │
│                                                                  │
│  ❌ semantic_analyzer.py as separate component                   │
│     Overlaps with AURORA, creates competing names               │
│     Replace with: role_hints embedded in normalizer output      │
│                                                                  │
│  ❌ app.py _generate_color_name_from_hex()                      │
│     Third naming system (numeric), conflicts with other two     │
│     Replace with: normalizer's single naming path               │
│                                                                  │
│  ❌ app.py _get_semantic_color_overrides() 3-way merge          │
│     Merges semantic + AURORA + NEXUS names → chaos              │
│     Replace with: AURORA naming_map as single authority         │
└─────────────────────────────────────────────────────────────────┘
```

### New LLM Budget After Critic Review

No new LLM calls needed. We're just:
1. Expanding AURORA from "name 10 colors" to "name ALL colors" (same 1 call, slightly larger output)
2. Eliminating the semantic analyzer's optional LLM call (saves $0.001)
3. All other changes are rule-based fixes

Net LLM cost: Same or slightly less than today (~$0.005 per extraction).

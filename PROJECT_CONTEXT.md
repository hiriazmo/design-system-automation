# Design System Extractor v2 — Project Context

## Architecture Overview

```
Stage 0: Configuration         Stage 1: Discovery & Extraction         Stage 2: AI Analysis              Stage 3: Export
 ┌──────────────────┐           ┌──────────────────────────┐           ┌──────────────────────────┐     ┌──────────────┐
 │ HF Token Setup   │ ──────>  │ URL Discovery (sitemap/   │ ──────>  │ Layer 1: Rule Engine     │ ──> │ Figma Tokens │
 │ Benchmark Select │           │ crawl) + Token Extraction │           │ Layer 2: Benchmarks      │     │ JSON Export   │
 └──────────────────┘           │ (Desktop + Mobile CSS)    │           │ Layer 3: LLM Agents (x3) │     └──────────────┘
                                └──────────────────────────┘           │ Layer 4: HEAD Synthesizer│
                                                                       └──────────────────────────┘
```

### Stage 1: Discovery & Extraction (Rule-Based, Free)
- **Discover Pages**: Fetches sitemap.xml or crawls site to find pages
- **Extract Tokens**: Playwright visits each page at 2 viewports (Desktop 1440px, Mobile 375px), extracts computed CSS for colors, typography, spacing, radius, shadows
- **User Review**: Interactive tables with Accept/Reject checkboxes + visual previews

### Stage 2: AI-Powered Analysis (4 Layers)

| Layer | Type | What It Does | Cost |
|-------|------|--------------|------|
| **Layer 1** | Rule Engine | Type scale detection, AA contrast checking, spacing grid analysis, color statistics | FREE |
| **Layer 2** | Benchmark Research | Compare against Material Design 3, Apple HIG, Tailwind, etc. | ~$0.001 |
| **Layer 3** | LLM Agents (x3) | AURORA (Brand ID) + ATLAS (Benchmark) + SENTINEL (Best Practices) | ~$0.002 |
| **Layer 4** | HEAD Synthesizer | NEXUS combines all outputs into final recommendations | ~$0.001 |

### Stage 3: Export
- Apply/reject individual color, typography, spacing recommendations
- Export Figma Tokens Studio-compatible JSON

---

## Agent Roster

| Agent | Codename | Model | Temp | Input | Output | Specialty |
|-------|----------|-------|------|-------|--------|-----------|
| Brand Identifier | **AURORA** | Qwen/Qwen2.5-72B-Instruct | 0.4 | Color tokens + semantic CSS analysis | Brand primary/secondary/accent, palette strategy, cohesion score, semantic names | Creative/visual reasoning, color harmony assessment |
| Benchmark Advisor | **ATLAS** | meta-llama/Llama-3.3-70B-Instruct | 0.25 | User's type scale, spacing, font sizes + benchmark comparison data | Recommended benchmark, alignment changes, pros/cons | 128K context for large benchmark data, comparative reasoning |
| Best Practices Validator | **SENTINEL** | Qwen/Qwen2.5-72B-Instruct | 0.2 | Rule Engine results (typography, accessibility, spacing, color stats) | Overall score (0-100), check results, prioritized fix list | Methodical rule-following, precise judgment |
| HEAD Synthesizer | **NEXUS** | meta-llama/Llama-3.3-70B-Instruct | 0.3 | All 3 agent outputs + Rule Engine facts | Executive summary, scores, top 3 actions, color/type/spacing recs | 128K context for combined inputs, synthesis capability |

### Why These Models

- **Qwen 72B** (AURORA, SENTINEL): Strong creative reasoning for brand analysis; methodical structured output for best practices. Available on HF serverless without gated access.
- **Llama 3.3 70B** (ATLAS, NEXUS): 128K context window handles large combined inputs from multiple agents. Excellent comparative and synthesis reasoning.
- **Fallback**: Qwen/Qwen2.5-7B-Instruct (free tier, available when primary models fail)

### Temperature Rationale

- **0.4** (AURORA): Allows creative interpretation of color stories and palette harmony
- **0.25** (ATLAS): Analytical comparison needs consistency but some flexibility for trade-off reasoning
- **0.2** (SENTINEL): Strict rule evaluation — consistency is critical for compliance scoring
- **0.3** (NEXUS): Balanced — needs to synthesize creatively but stay grounded in agent data

---

## Evaluation & Scoring

### Self-Evaluation (All Agents)
Each agent includes a `self_evaluation` block in its JSON output:
```json
{
  "confidence": 8,          // 1-10: How confident the agent is
  "reasoning": "Clear usage patterns with 20+ colors",
  "data_quality": "good",   // good | fair | poor
  "flags": []               // e.g., ["insufficient_context", "ambiguous_data"]
}
```

### AURORA Scoring Rubric (Cohesion 1-10)
- **9-10**: Clear harmony rule, distinct brand colors, consistent palette
- **7-8**: Mostly harmonious, clear brand identity
- **5-6**: Some relationships visible but not systematic
- **3-4**: Random palette, no clear strategy
- **1-2**: Conflicting colors, no brand identity

### SENTINEL Scoring Rubric (Overall 0-100)
Weighted checks:
- AA Compliance: 25 points
- Type Scale Consistency: 15 points
- Base Size Accessible: 15 points
- Spacing Grid: 15 points
- Type Scale Standard Ratio: 10 points
- Color Count: 10 points
- No Near-Duplicates: 10 points

### NEXUS Scoring Rubric (Overall 0-100)
- **90-100**: Production-ready, minor polishing only
- **75-89**: Solid foundation, 2-3 targeted improvements
- **60-74**: Functional but needs focused attention
- **40-59**: Significant gaps requiring systematic improvement
- **20-39**: Major rework needed
- **0-19**: Fundamental redesign recommended

### Evaluation Summary (Logged After Analysis)
```
═══════════════════════════════════════════════════
🔍 AGENT EVALUATION SUMMARY
═══════════════════════════════════════════════════
   🎨 AURORA  (Brand ID):    confidence=8/10, data=good
   🏢 ATLAS   (Benchmark):   confidence=7/10, data=good
   ✅ SENTINEL (Practices):  confidence=9/10, data=good, score=72/100
   🧠 NEXUS   (Synthesis):   confidence=8/10, data=good, overall=65/100
═══════════════════════════════════════════════════
```

---

## User Journey

1. **Enter HF Token** — Required for LLM inference (free tier works)
2. **Enter Website URL** — The site to extract design tokens from
3. **Discover Pages** — Auto-finds pages via sitemap or crawling
4. **Select Pages** — Check/uncheck pages to include (max 10)
5. **Extract Tokens** — Scans selected pages at Desktop + Mobile viewports
6. **Review Stage 1** — Interactive tables: Colors, Typography, Spacing, Radius, Shadows, Semantic Colors. Each tab has a data table + visual preview accordion. Accept/reject individual tokens.
7. **Proceed to Stage 2** — Select benchmarks to compare against
8. **Run AI Analysis** — 4-layer pipeline executes (Rule Engine -> Benchmarks -> LLM Agents -> Synthesis)
9. **Review Analysis** — Dashboard with scores, recommendations, benchmark comparison, color recs
10. **Apply Upgrades** — Accept/reject individual recommendations
11. **Export JSON** — Download Figma Tokens Studio-compatible JSON

---

## File Structure

| File | Responsibility |
|------|----------------|
| `app.py` | Main Gradio UI — all stages, CSS, event bindings, formatting functions |
| `agents/llm_agents.py` | 4 LLM agent classes (AURORA, ATLAS, SENTINEL, NEXUS) + dataclasses |
| `agents/semantic_analyzer.py` | Semantic color categorization (brand, text, background, etc.) |
| `config/settings.py` | Model routing, env var loading, agent-to-model mapping |
| `core/hf_inference.py` | HF Inference API client, model registry, temperature mapping |
| `core/preview_generator.py` | HTML preview generators for Stage 1 visual previews |
| `core/rule_engine.py` | Layer 1: Type scale, AA contrast, spacing grid, color stats |
| `core/benchmarks.py` | Benchmark definitions (Material Design 3, Apple HIG, etc.) |
| `core/extractor.py` | Playwright-based CSS token extraction |
| `core/discovery.py` | Page discovery via sitemap.xml / crawling |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_TOKEN` | (required) | HuggingFace API token |
| `BRAND_IDENTIFIER_MODEL` | `Qwen/Qwen2.5-72B-Instruct` | Model for AURORA |
| `BENCHMARK_ADVISOR_MODEL` | `meta-llama/Llama-3.3-70B-Instruct` | Model for ATLAS |
| `BEST_PRACTICES_MODEL` | `Qwen/Qwen2.5-72B-Instruct` | Model for SENTINEL |
| `HEAD_SYNTHESIZER_MODEL` | `meta-llama/Llama-3.3-70B-Instruct` | Model for NEXUS |
| `FALLBACK_MODEL` | `Qwen/Qwen2.5-7B-Instruct` | Fallback when primary fails |
| `HF_MAX_NEW_TOKENS` | `2048` | Max tokens per LLM response |
| `HF_TEMPERATURE` | `0.3` | Global default temperature |
| `MAX_PAGES` | `20` | Max pages to discover |
| `BROWSER_TIMEOUT` | `30000` | Playwright timeout (ms) |

### Model Override Examples
```bash
# Use Llama for all agents
export BRAND_IDENTIFIER_MODEL="meta-llama/Llama-3.3-70B-Instruct"
export BEST_PRACTICES_MODEL="meta-llama/Llama-3.3-70B-Instruct"

# Use budget models
export BRAND_IDENTIFIER_MODEL="Qwen/Qwen2.5-7B-Instruct"
export BENCHMARK_ADVISOR_MODEL="mistralai/Mixtral-8x7B-Instruct-v0.1"
```

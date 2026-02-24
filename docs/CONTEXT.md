# Design System Automation v3.2 — Master Context File

> **Upload this file to refresh Claude's context when continuing work on this project.**

**Last Updated:** February 2026

---

## Current Status

| Component | Status | Version |
|-----------|--------|---------|
| Token Extraction (Part 1) | COMPLETE | v3.2 |
| Color Classification | COMPLETE | v3.1 |
| DTCG Compliance | COMPLETE | v3.2 |
| Naming Authority Chain | COMPLETE | v3.2 |
| Figma Plugin (Visual Spec) | COMPLETE | v7 |
| Component Generation (Part 2) | RESEARCH DONE | - |
| Tests | 113 passing | - |

---

## Project Goal

Build a **semi-automated, human-in-the-loop system** that:
1. Reverse-engineers a design system from a live website
2. Classifies colors deterministically by CSS evidence
3. Audits against industry benchmarks and best practices
4. Outputs W3C DTCG v1 compliant JSON
5. Generates Figma Variables, Styles, and Visual Spec pages
6. (Part 2) Auto-generates Figma components from tokens

**Philosophy:** AI as copilot, not autopilot. Humans decide, agents propose.

---

## Architecture (v3.2)

```
+--------------------------------------------------+
|  LAYER 1: EXTRACTION + NORMALIZATION (Free)       |
|  +- Crawler + 7-Source Extractor (Playwright)     |
|  +- Normalizer: colors, radius, shadows, typo     |
|  +- Firecrawl: deep CSS parsing                   |
+--------------------------------------------------+
|  LAYER 2: CLASSIFICATION + RULE ENGINE (Free)     |
|  +- Color Classifier (815 lines, deterministic)   |
|  +- WCAG Contrast Checker (actual FG/BG pairs)    |
|  +- Type Scale Detection (ratio math)             |
|  +- Spacing Grid Analysis (GCD math)              |
+--------------------------------------------------+
|  LAYER 3: 4 AI AGENTS (~$0.003)                   |
|  +- AURORA   - Brand Advisor        (Qwen 72B)   |
|  +- ATLAS    - Benchmark Advisor    (Llama 70B)   |
|  +- SENTINEL - Best Practices Audit (Qwen 72B)   |
|  +- NEXUS    - Head Synthesizer     (Llama 70B)   |
+--------------------------------------------------+
|  EXPORT: W3C DTCG v1 Compliant JSON               |
|  +- $type, $value, $description, $extensions      |
|  +- Figma Plugin: Variables + Styles + Visual Spec|
+--------------------------------------------------+
```

### Naming Authority Chain (v3.2)

```
1. Color Classifier (PRIMARY) - deterministic, covers ALL colors
   +- CSS evidence -> category -> token name
   +- 100% reproducible, logged with evidence

2. AURORA LLM (SECONDARY) - semantic role enhancer ONLY
   +- Can promote "color.blue.500" -> "color.brand.primary"
   +- CANNOT rename palette colors
   +- filter_aurora_naming_map() enforces boundary

3. Normalizer (FALLBACK) - preliminary hue+shade names
```

---

## File Structure

```
design-system-automation/
+-- app.py                          # Main Gradio app (~5000 lines)
+-- CLAUDE.md                       # Project context and architecture
+-- PART2_COMPONENT_GENERATION.md   # Part 2 research + plan
|
+-- agents/
|   +-- crawler.py                  # Page discovery
|   +-- extractor.py                # Playwright 7-source extraction
|   +-- firecrawl_extractor.py      # Deep CSS parsing
|   +-- normalizer.py               # Token normalization (~950 lines)
|   +-- llm_agents.py               # AURORA, ATLAS, SENTINEL, NEXUS
|   +-- semantic_analyzer.py        # DEPRECATED in v3.2
|   +-- stage2_graph.py             # DEPRECATED in v3.2
|
+-- core/
|   +-- color_classifier.py         # Rule-based classification (815 lines)
|   +-- color_utils.py              # Color math (hex/RGB/HSL, contrast)
|   +-- rule_engine.py              # Type scale, WCAG, spacing grid (~1100 lines)
|   +-- hf_inference.py             # HuggingFace Inference API client
|   +-- token_schema.py             # Pydantic models
|
+-- config/
|   +-- settings.py                 # Configuration
|
+-- tests/
|   +-- test_stage1_extraction.py   # 82 deterministic tests
|   +-- test_agent_evals.py         # 27 LLM agent schema/behavior tests
|   +-- test_stage2_pipeline.py     # Pipeline integration tests
|
+-- output_json/
|   +-- figma-plugin-extracted/
|       +-- figma-design-token-creator 5/
|           +-- src/code.js          # Figma plugin (~1200 lines)
|           +-- src/ui.html          # Plugin UI (~500 lines)
|
+-- docs/
    +-- MEDIUM_ARTICLE_EPISODE_6.md  # Medium article
    +-- LINKEDIN_POST_EPISODE_6.md   # LinkedIn post
    +-- IMAGE_GUIDE_EPISODE_6.md     # Image specs for article
    +-- FIGMA_SPECIMEN_IDEAS.md      # Visual spec layout reference
    +-- CONTEXT.md                   # THIS FILE
```

---

## Model Assignments

| Agent | Model | Temperature | Role |
|-------|-------|-------------|------|
| Rule Engine | None | - | WCAG, type scale, spacing (FREE) |
| Color Classifier | None | - | CSS evidence -> category (FREE) |
| AURORA | Qwen/Qwen2.5-72B-Instruct | 0.4 | Brand advisor (SECONDARY) |
| ATLAS | meta-llama/Llama-3.3-70B-Instruct | 0.25 | Benchmark comparison |
| SENTINEL | Qwen/Qwen2.5-72B-Instruct | 0.2 | Best practices audit |
| NEXUS | meta-llama/Llama-3.3-70B-Instruct | 0.3 | Final synthesis |

**Total cost per analysis:** ~$0.003

---

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Color naming | Numeric shades (50-900) | Never words (light/dark/base) |
| Naming authority | Classifier PRIMARY, LLM SECONDARY | One source of truth |
| Export format | W3C DTCG v1 | Industry standard (Oct 2025) |
| Token metadata | $extensions (namespaced) | Frequency, confidence, evidence |
| Radius processing | Parse, deduplicate, sort, name | none/sm/md/lg/xl/2xl/full |
| Shadow processing | Parse, sort by blur, name | xs/sm/md/lg/xl (always 5 levels) |
| Accessibility | Actual FG/BG pairs from DOM | Not just color vs white |
| Figma output | Variables + Styles + Visual Spec | Auto-generated specimen page |
| LLM role | Advisory only, never naming authority | Deterministic reproducibility |

---

## Execution Status

### Part 1: Token Extraction + Analysis (COMPLETE)

```
PHASE 1: NORMALIZER       [DONE]
PHASE 2: STAGE 2 AGENTS   [DONE]
PHASE 3: EXPORT + DTCG    [DONE]
PHASE 4: EXTRACTION IMPROVEMENTS [NOT STARTED]
  4a. Font family detection (still returns "sans-serif")
  4b. Rule engine: radius grid analysis
  4c. Rule engine: shadow elevation analysis
```

### Part 2: Component Generation (RESEARCH COMPLETE)

**Decision:** Custom Figma Plugin (Option A)
**Scope:** 5 MVP components, ~86 variants, ~1400 lines new plugin code
**See:** `PART2_COMPONENT_GENERATION.md` for full details

---

## GitHub

- **Repository:** https://github.com/hiriazmo/design-system-automation
- **Latest commit:** `6b43e51` (DTCG compliance + naming authority)
- **Tests:** 113 passing

---

*Last updated: 2026-02-23*

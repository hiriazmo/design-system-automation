"""
Stage 2 LLM Agents — v3 Agentic Architecture
==============================================

Each agent:
- Researches ALL token types (colors, typography, spacing, radius, shadows)
- Uses ReAct framework: THINK → ACT → OBSERVE → VERIFY
- Returns visible reasoning chain for the UI
- Has a Python-based critic for validation

Agents run IN PARALLEL (asyncio.gather), then NEXUS compiles.

Agent Responsibilities:
- AURORA: Brand identity + semantic naming for ALL colors + notes on all token types
- SENTINEL: Best practices audit across ALL token types, grounded in rule-engine data
- ATLAS: Benchmark comparison for ALL token types
- NEXUS (HEAD): Tree-of-Thought synthesis, compiles all agent outputs
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from datetime import datetime


# =============================================================================
# DATA CLASSES — v3: includes reasoning_trace + naming_map
# =============================================================================

@dataclass
class BrandIdentification:
    """Results from AURORA — Brand Identifier (ReAct)."""
    brand_primary: dict = field(default_factory=dict)
    brand_secondary: dict = field(default_factory=dict)
    brand_accent: dict = field(default_factory=dict)
    palette_strategy: str = ""
    cohesion_score: int = 5
    cohesion_notes: str = ""

    # v3: naming_map covers ALL colors, not just top 10
    naming_map: dict = field(default_factory=dict)
    # {hex: "color.brand.primary"} or {hex: "color.blue.500"}

    semantic_names: dict = field(default_factory=dict)  # backward compat
    self_evaluation: dict = field(default_factory=dict)

    # v3: reasoning trace visible to user
    reasoning_trace: list = field(default_factory=list)
    validation_passed: bool = False
    retry_count: int = 0

    # v3: per-token-type observations
    typography_notes: str = ""
    spacing_notes: str = ""
    radius_notes: str = ""
    shadow_notes: str = ""

    def to_dict(self) -> dict:
        return {
            "brand_primary": self.brand_primary,
            "brand_secondary": self.brand_secondary,
            "brand_accent": self.brand_accent,
            "palette_strategy": self.palette_strategy,
            "cohesion_score": self.cohesion_score,
            "cohesion_notes": self.cohesion_notes,
            "naming_map": self.naming_map,
            "semantic_names": self.semantic_names,
            "self_evaluation": self.self_evaluation,
            "typography_notes": self.typography_notes,
            "spacing_notes": self.spacing_notes,
            "radius_notes": self.radius_notes,
            "shadow_notes": self.shadow_notes,
        }


@dataclass
class BenchmarkAdvice:
    """Results from ATLAS — Benchmark Advisor (ReAct)."""
    recommended_benchmark: str = ""
    recommended_benchmark_name: str = ""
    reasoning: str = ""
    alignment_changes: list = field(default_factory=list)
    pros_of_alignment: list = field(default_factory=list)
    cons_of_alignment: list = field(default_factory=list)
    alternative_benchmarks: list = field(default_factory=list)
    self_evaluation: dict = field(default_factory=dict)

    # v3: per-token-type benchmark comparison
    typography_comparison: dict = field(default_factory=dict)
    spacing_comparison: dict = field(default_factory=dict)
    color_comparison: dict = field(default_factory=dict)
    radius_comparison: dict = field(default_factory=dict)
    shadow_comparison: dict = field(default_factory=dict)

    reasoning_trace: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "recommended_benchmark": self.recommended_benchmark,
            "recommended_benchmark_name": self.recommended_benchmark_name,
            "reasoning": self.reasoning,
            "alignment_changes": self.alignment_changes,
            "pros": self.pros_of_alignment,
            "cons": self.cons_of_alignment,
            "alternatives": self.alternative_benchmarks,
            "self_evaluation": self.self_evaluation,
            "typography_comparison": self.typography_comparison,
            "spacing_comparison": self.spacing_comparison,
            "color_comparison": self.color_comparison,
            "radius_comparison": self.radius_comparison,
            "shadow_comparison": self.shadow_comparison,
        }


@dataclass
class BestPracticesResult:
    """Results from SENTINEL — Best Practices Auditor (ReAct)."""
    overall_score: int = 50
    checks: dict = field(default_factory=dict)
    priority_fixes: list = field(default_factory=list)
    passing_practices: list = field(default_factory=list)
    failing_practices: list = field(default_factory=list)
    self_evaluation: dict = field(default_factory=dict)

    # v3: per-token-type assessments
    color_assessment: dict = field(default_factory=dict)
    typography_assessment: dict = field(default_factory=dict)
    spacing_assessment: dict = field(default_factory=dict)
    radius_assessment: dict = field(default_factory=dict)
    shadow_assessment: dict = field(default_factory=dict)

    reasoning_trace: list = field(default_factory=list)
    validation_passed: bool = False

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "checks": self.checks,
            "priority_fixes": self.priority_fixes,
            "passing": self.passing_practices,
            "failing": self.failing_practices,
            "self_evaluation": self.self_evaluation,
            "color_assessment": self.color_assessment,
            "typography_assessment": self.typography_assessment,
            "spacing_assessment": self.spacing_assessment,
            "radius_assessment": self.radius_assessment,
            "shadow_assessment": self.shadow_assessment,
        }


@dataclass
class HeadSynthesis:
    """Results from NEXUS — HEAD Synthesizer (Tree of Thought)."""
    executive_summary: str = ""
    scores: dict = field(default_factory=dict)
    benchmark_fit: dict = field(default_factory=dict)
    brand_analysis: dict = field(default_factory=dict)
    top_3_actions: list = field(default_factory=list)
    color_recommendations: list = field(default_factory=list)
    type_scale_recommendation: dict = field(default_factory=dict)
    spacing_recommendation: dict = field(default_factory=dict)
    radius_recommendation: dict = field(default_factory=dict)
    shadow_recommendation: dict = field(default_factory=dict)
    self_evaluation: dict = field(default_factory=dict)

    # v3: ToT branches visible to user
    perspective_a: dict = field(default_factory=dict)
    perspective_b: dict = field(default_factory=dict)
    chosen_perspective: str = ""
    choice_reasoning: str = ""

    reasoning_trace: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "executive_summary": self.executive_summary,
            "scores": self.scores,
            "benchmark_fit": self.benchmark_fit,
            "brand_analysis": self.brand_analysis,
            "top_3_actions": self.top_3_actions,
            "color_recommendations": self.color_recommendations,
            "type_scale_recommendation": self.type_scale_recommendation,
            "spacing_recommendation": self.spacing_recommendation,
            "radius_recommendation": self.radius_recommendation,
            "shadow_recommendation": self.shadow_recommendation,
            "self_evaluation": self.self_evaluation,
            "chosen_perspective": self.chosen_perspective,
            "choice_reasoning": self.choice_reasoning,
        }


# =============================================================================
# SHARED HELPERS — format token data for prompts
# =============================================================================

def _fmt_colors(tokens: dict, limit: int = 40) -> str:
    """Format color tokens for any agent prompt."""
    if not tokens:
        return "No color data"
    lines = []
    for name, t in list(tokens.items())[:limit]:
        d = t if isinstance(t, dict) else t.__dict__ if hasattr(t, '__dict__') else {}
        hex_val = d.get("value", "")
        freq = d.get("frequency", 0)
        hint = d.get("role_hint", "")
        ctx = ", ".join((d.get("contexts") or [])[:3])
        els = ", ".join((d.get("elements") or [])[:3])
        hint_s = f" [hint:{hint}]" if hint else ""
        lines.append(f"- {hex_val}: {freq}x, ctx=[{ctx}], el=[{els}]{hint_s}")
    return "\n".join(lines)


def _fmt_typography(tokens: dict, limit: int = 15) -> str:
    if not tokens:
        return "No typography data"
    lines = []
    for name, t in list(tokens.items())[:limit]:
        d = t if isinstance(t, dict) else t.__dict__ if hasattr(t, '__dict__') else {}
        fam = d.get("font_family", "?")
        sz = d.get("font_size", "?")
        w = d.get("font_weight", 400)
        lh = d.get("line_height", "?")
        freq = d.get("frequency", 0)
        els = ", ".join((d.get("elements") or [])[:3])
        lines.append(f"- {fam} {sz} w{w} lh={lh} ({freq}x) [{els}]")
    return "\n".join(lines)


def _fmt_spacing(tokens: dict, limit: int = 15) -> str:
    if not tokens:
        return "No spacing data"
    lines = []
    for name, t in list(tokens.items())[:limit]:
        d = t if isinstance(t, dict) else t.__dict__ if hasattr(t, '__dict__') else {}
        val = d.get("value", "?")
        px = d.get("value_px", "?")
        freq = d.get("frequency", 0)
        ctx = ", ".join((d.get("contexts") or [])[:3])
        lines.append(f"- {val} ({px}px) {freq}x [{ctx}]")
    return "\n".join(lines)


def _fmt_radius(tokens: dict, limit: int = 10) -> str:
    if not tokens:
        return "No radius data"
    lines = []
    for name, t in list(tokens.items())[:limit]:
        d = t if isinstance(t, dict) else t.__dict__ if hasattr(t, '__dict__') else {}
        val = d.get("value", "?")
        px = d.get("value_px", "?")
        freq = d.get("frequency", 0)
        b4 = d.get("fits_base_4", False)
        b8 = d.get("fits_base_8", False)
        els = ", ".join((d.get("elements") or [])[:3])
        lines.append(f"- {name}: {val} (base4={b4}, base8={b8}, {freq}x) [{els}]")
    return "\n".join(lines)


def _fmt_shadows(tokens: dict, limit: int = 10) -> str:
    if not tokens:
        return "No shadow data"
    lines = []
    for name, t in list(tokens.items())[:limit]:
        d = t if isinstance(t, dict) else t.__dict__ if hasattr(t, '__dict__') else {}
        blur = d.get("blur_px", "?")
        y = d.get("y_offset_px", "?")
        freq = d.get("frequency", 0)
        els = ", ".join((d.get("elements") or [])[:3])
        lines.append(f"- {name}: blur={blur}px y={y}px ({freq}x) [{els}]")
    return "\n".join(lines)


def _log_reasoning(steps: list, log_fn: Callable):
    """Log ReAct reasoning steps with icons."""
    icons = {"THINK": "🧠", "ACT": "⚡", "OBSERVE": "👁️", "VERIFY": "✅"}
    for step in (steps or []):
        if isinstance(step, dict):
            st = step.get("step", "?")
            area = step.get("area", "")
            content = step.get("content", "")[:90]
            icon = icons.get(st, "📝")
            log_fn(f"   {icon} [{area}] {content}")


def _extract_hexes(tokens: dict) -> list:
    """Get list of hex values from color token dict."""
    hexes = []
    for name, t in tokens.items():
        if isinstance(t, dict):
            h = t.get("value", "")
        else:
            h = getattr(t, "value", "")
        if h:
            hexes.append(h.lower())
    return hexes


# =============================================================================
# AURORA — Brand Identifier (ReAct Framework)
# =============================================================================

class BrandIdentifierAgent:
    """
    AURORA — Senior Brand & Visual Identity Analyst.
    ReAct on ALL token types. Names ALL colors.
    Model: Qwen 72B · Temperature: 0.4
    """

    SYSTEM_PROMPT = """You are AURORA, a Senior Brand & Visual Identity Analyst.

## REASONING FRAMEWORK (ReAct)
Structure your response with explicit reasoning steps.
For each area: THINK → ACT → OBSERVE → VERIFY.

## ANALYZE ALL TOKEN TYPES:

### 1. COLORS (Primary focus)
- Identify brand primary/secondary/accent from usage + role_hints
- Name EVERY color: color.{role}.{sub} or color.{hue}.{shade}
- Shades MUST be numeric (50-900), NEVER words (light/dark/base)
- Role colors: color.brand.primary, color.text.primary, color.bg.primary
- Palette colors: color.blue.500, color.neutral.200

### 2. TYPOGRAPHY — Identify heading vs body hierarchy, font pairing
### 3. SPACING — Identify grid system, note consistency
### 4. RADIUS — Identify radius strategy (sharp/rounded/pill)
### 5. SHADOWS — Identify elevation strategy, blur progression

## QUALITY RULES
- naming_map MUST include EVERY hex color — no orphans
- Brand Primary MUST cite usage evidence (e.g. "47x on buttons")
- Cohesion 1-10: most sites score 5-7. Use the full range.

## OUTPUT (JSON)

{
  "reasoning_steps": [
    {"step": "THINK", "area": "colors", "content": "..."},
    {"step": "ACT", "area": "colors", "content": "..."},
    {"step": "OBSERVE", "area": "typography", "content": "..."},
    {"step": "ACT", "area": "typography", "content": "..."},
    {"step": "ACT", "area": "spacing", "content": "..."},
    {"step": "ACT", "area": "radius", "content": "..."},
    {"step": "ACT", "area": "shadows", "content": "..."},
    {"step": "VERIFY", "area": "all", "content": "Cross-checking consistency..."}
  ],
  "brand_primary": {"color": "#hex", "confidence": "high|medium|low", "reasoning": "cite evidence", "usage_count": N},
  "brand_secondary": {"color": "#hex", "confidence": "...", "reasoning": "..."},
  "brand_accent": {"color": "#hex or null", "confidence": "...", "reasoning": "..."},
  "palette_strategy": "complementary|analogous|triadic|monochromatic|random",
  "cohesion_score": N,
  "cohesion_notes": "...",
  "naming_map": {"#hex1": "color.brand.primary", "#hex2": "color.blue.500", ...},
  "typography_notes": "Heading: Inter 700, Body: Inter 400. Clean hierarchy.",
  "spacing_notes": "8px grid, 92% aligned.",
  "radius_notes": "Rounded style: 4px inputs, 8px cards.",
  "shadow_notes": "3-level elevation: blur 4/8/24px.",
  "self_evaluation": {"confidence": N, "reasoning": "...", "data_quality": "good|fair|poor", "flags": []}
}

Return ONLY valid JSON."""

    PROMPT_TEMPLATE = """Analyze the complete design system.

## COLORS (with role_hints)
{color_data}

## TYPOGRAPHY
{typography_data}

## SPACING
{spacing_data}

## RADIUS
{radius_data}

## SHADOWS
{shadow_data}

Use ReAct for each area. Name EVERY color in naming_map."""

    def __init__(self, hf_client):
        self.hf_client = hf_client

    async def analyze(
        self,
        color_tokens: dict,
        typography_tokens: dict = None,
        spacing_tokens: dict = None,
        radius_tokens: dict = None,
        shadow_tokens: dict = None,
        log_callback: Callable = None,
    ) -> BrandIdentification:
        def log(msg):
            if log_callback:
                log_callback(msg)

        log("   🎨 AURORA — Brand & Visual Identity (Qwen 72B)")
        log("   └─ ReAct: Analyzing colors + typography + spacing + radius + shadows...")

        prompt = self.PROMPT_TEMPLATE.format(
            color_data=_fmt_colors(color_tokens),
            typography_data=_fmt_typography(typography_tokens),
            spacing_data=_fmt_spacing(spacing_tokens),
            radius_data=_fmt_radius(radius_tokens),
            shadow_data=_fmt_shadows(shadow_tokens),
        )

        try:
            start = datetime.now()
            response = await self.hf_client.complete_async(
                agent_name="brand_identifier",
                system_prompt=self.SYSTEM_PROMPT,
                user_message=prompt,
                max_tokens=2000,
                json_mode=True,
            )
            dur = (datetime.now() - start).total_seconds()
            result = self._parse(response)

            # Critic validation
            input_hexes = _extract_hexes(color_tokens)
            passed, errors = validate_aurora_output(result, input_hexes)
            result.validation_passed = passed

            if not passed and result.retry_count == 0:
                log(f"   ⚠️ Critic: {len(errors)} issues — retrying with feedback...")
                for e in errors[:3]:
                    log(f"      └─ {e}")
                retry_prompt = prompt + "\n\n## CRITIC FEEDBACK — Fix:\n" + "\n".join(errors[:10])
                resp2 = await self.hf_client.complete_async(
                    agent_name="brand_identifier",
                    system_prompt=self.SYSTEM_PROMPT,
                    user_message=retry_prompt,
                    max_tokens=2000,
                    json_mode=True,
                )
                result = self._parse(resp2)
                result.retry_count = 1
                p2, e2 = validate_aurora_output(result, input_hexes)
                result.validation_passed = p2
                if not p2:
                    log(f"   ⚠️ Retry: still {len(e2)} issues — using normalizer fallback names")

            # Log reasoning chain
            log(f"   ─────────────────────────────────────────")
            log(f"   🎨 AURORA — COMPLETE ({dur:.1f}s)")
            _log_reasoning(result.reasoning_trace, log)
            log(f"   ├─ Brand Primary: {result.brand_primary.get('color', '?')} ({result.brand_primary.get('confidence', '?')})")
            log(f"   ├─ Palette: {result.palette_strategy} · Cohesion: {result.cohesion_score}/10")
            log(f"   ├─ Colors Named: {len(result.naming_map)}/{len(input_hexes)}")
            log(f"   ├─ Typography: {(result.typography_notes or 'N/A')[:60]}")
            log(f"   ├─ Spacing: {(result.spacing_notes or 'N/A')[:60]}")
            log(f"   ├─ Radius: {(result.radius_notes or 'N/A')[:60]}")
            log(f"   ├─ Shadows: {(result.shadow_notes or 'N/A')[:60]}")
            log(f"   └─ Critic: {'✅ PASSED' if result.validation_passed else '⚠️ FALLBACK'}")
            return result

        except Exception as e:
            log(f"   ⚠️ AURORA failed: {str(e)[:120]}")
            return BrandIdentification()

    def _parse(self, response: str) -> BrandIdentification:
        try:
            m = re.search(r'\{[\s\S]*\}', response)
            if m:
                d = json.loads(m.group())
                return BrandIdentification(
                    brand_primary=d.get("brand_primary", {}),
                    brand_secondary=d.get("brand_secondary", {}),
                    brand_accent=d.get("brand_accent", {}),
                    palette_strategy=d.get("palette_strategy", "unknown"),
                    cohesion_score=d.get("cohesion_score", 5),
                    cohesion_notes=d.get("cohesion_notes", ""),
                    naming_map=d.get("naming_map", {}),
                    semantic_names=d.get("naming_map", {}),
                    self_evaluation=d.get("self_evaluation", {}),
                    reasoning_trace=d.get("reasoning_steps", []),
                    typography_notes=d.get("typography_notes", ""),
                    spacing_notes=d.get("spacing_notes", ""),
                    radius_notes=d.get("radius_notes", ""),
                    shadow_notes=d.get("shadow_notes", ""),
                )
        except Exception:
            pass
        return BrandIdentification()


# =============================================================================
# ATLAS — Benchmark Advisor (ReAct Framework)
# =============================================================================

class BenchmarkAdvisorAgent:
    """
    ATLAS — Senior Design System Benchmark Analyst.
    ReAct comparison of ALL token types against industry benchmarks.
    Model: Llama 3.3 70B · Temperature: 0.25
    """

    SYSTEM_PROMPT = """You are ATLAS, a Senior Design System Benchmark Analyst.

## REASONING FRAMEWORK (ReAct)
For EACH token type: THINK → ACT → OBSERVE → VERIFY.

Compare the user's values against benchmarks for:
1. TYPOGRAPHY — ratio, base size, scale pattern
2. SPACING — grid base, alignment, scale
3. COLORS — palette size, brand color usage
4. RADIUS — strategy (sharp/rounded/pill), tier count
5. SHADOWS — elevation levels, blur range

Then pick the BEST OVERALL FIT benchmark.
Max 4 alignment changes. If >85% match, say "already well-aligned".

## OUTPUT (JSON)

{
  "reasoning_steps": [
    {"step": "THINK", "area": "typography", "content": "User ratio 1.18 vs Material 1.25..."},
    {"step": "ACT", "area": "typography", "content": "Material closest for type"},
    {"step": "THINK", "area": "spacing", "content": "8px matches Material and Polaris"},
    {"step": "ACT", "area": "spacing", "content": "Both aligned"},
    {"step": "THINK", "area": "colors", "content": "25 colors vs Polaris 18..."},
    {"step": "THINK", "area": "radius", "content": "4/8px tiers..."},
    {"step": "THINK", "area": "shadows", "content": "3 levels vs Material 5..."},
    {"step": "VERIFY", "area": "overall", "content": "Material best: 4/5 areas align"}
  ],
  "recommended_benchmark": "material_design_3",
  "recommended_benchmark_name": "Material Design 3",
  "reasoning": "Best fit across all token types — cite data",
  "alignment_changes": [
    {"change": "Type scale", "from": "1.18", "to": "1.25", "effort": "medium", "token_type": "typography"}
  ],
  "typography_comparison": {"user": "1.18", "benchmark": "1.25", "gap": "minor"},
  "spacing_comparison": {"user": "8px", "benchmark": "8px", "gap": "aligned"},
  "color_comparison": {"user": "25", "benchmark": "18", "gap": "reduce"},
  "radius_comparison": {"user": "2 tiers", "benchmark": "3 tiers", "gap": "add xl"},
  "shadow_comparison": {"user": "3 levels", "benchmark": "5 levels", "gap": "add 2"},
  "pros_of_alignment": ["..."],
  "cons_of_alignment": ["..."],
  "alternative_benchmarks": [{"name": "Polaris", "reason": "..."}],
  "self_evaluation": {"confidence": N, "reasoning": "...", "data_quality": "...", "flags": []}
}

Return ONLY valid JSON."""

    PROMPT_TEMPLATE = """Compare this design system against benchmarks — ALL token types.

## CURRENT VALUES
- Type Scale Ratio: {user_ratio} | Base: {user_base}px | Sizes: {user_sizes}
- Spacing Grid: {user_spacing}px | Values: {spacing_values}
- Colors: {color_count} unique | Brand: {brand_info}
- Radius: {radius_data}
- Shadows: {shadow_data}

## BENCHMARKS
{benchmark_comparison}

Use ReAct per token type. Pick the best overall fit."""

    def __init__(self, hf_client):
        self.hf_client = hf_client

    async def analyze(
        self,
        user_ratio: float, user_base: int, user_spacing: int,
        benchmark_comparisons: list,
        color_count: int = 0, brand_info: str = "",
        user_sizes: str = "", spacing_values: str = "",
        radius_data: str = "", shadow_data: str = "",
        log_callback: Callable = None,
    ) -> BenchmarkAdvice:
        def log(msg):
            if log_callback:
                log_callback(msg)

        log("")
        log("   🏢 ATLAS — Benchmark Advisor (Llama 3.3 70B)")
        log("   └─ ReAct: Comparing typography + spacing + colors + radius + shadows...")

        prompt = self.PROMPT_TEMPLATE.format(
            user_ratio=user_ratio, user_base=user_base, user_spacing=user_spacing,
            user_sizes=user_sizes or "N/A",
            spacing_values=spacing_values or "N/A",
            color_count=color_count, brand_info=brand_info or "N/A",
            radius_data=radius_data or "No radius data",
            shadow_data=shadow_data or "No shadow data",
            benchmark_comparison=self._fmt_benchmarks(benchmark_comparisons),
        )

        try:
            start = datetime.now()
            response = await self.hf_client.complete_async(
                agent_name="benchmark_advisor",
                system_prompt=self.SYSTEM_PROMPT,
                user_message=prompt,
                max_tokens=1500,
                json_mode=True,
            )
            dur = (datetime.now() - start).total_seconds()
            result = self._parse(response)

            log(f"   ─────────────────────────────────────────")
            log(f"   🏢 ATLAS — COMPLETE ({dur:.1f}s)")
            _log_reasoning(result.reasoning_trace, log)
            log(f"   ├─ Recommended: {result.recommended_benchmark_name}")
            log(f"   ├─ Changes: {len(result.alignment_changes)}")
            log(f"   ├─ Typography: {result.typography_comparison}")
            log(f"   ├─ Spacing: {result.spacing_comparison}")
            log(f"   ├─ Colors: {result.color_comparison}")
            log(f"   ├─ Radius: {result.radius_comparison}")
            log(f"   └─ Shadows: {result.shadow_comparison}")
            return result

        except Exception as e:
            log(f"   ⚠️ ATLAS failed: {str(e)[:120]}")
            return BenchmarkAdvice()

    def _fmt_benchmarks(self, comparisons: list) -> str:
        lines = []
        for i, c in enumerate(comparisons[:5]):
            b = c.benchmark
            lines.append(f"{i+1}. {b.icon} {b.name} — Match: {c.overall_match_pct:.0f}%"
                         f" | Type: {b.typography.get('scale_ratio', '?')}"
                         f" | Spacing: {b.spacing.get('base', '?')}px"
                         f" | Best for: {', '.join(b.best_for)}")
        return "\n".join(lines) if lines else "No benchmark data"

    def _parse(self, response: str) -> BenchmarkAdvice:
        try:
            m = re.search(r'\{[\s\S]*\}', response)
            if m:
                d = json.loads(m.group())
                return BenchmarkAdvice(
                    recommended_benchmark=d.get("recommended_benchmark", ""),
                    recommended_benchmark_name=d.get("recommended_benchmark_name", ""),
                    reasoning=d.get("reasoning", ""),
                    alignment_changes=d.get("alignment_changes", []),
                    pros_of_alignment=d.get("pros_of_alignment", []),
                    cons_of_alignment=d.get("cons_of_alignment", []),
                    alternative_benchmarks=d.get("alternative_benchmarks", []),
                    self_evaluation=d.get("self_evaluation", {}),
                    typography_comparison=d.get("typography_comparison", {}),
                    spacing_comparison=d.get("spacing_comparison", {}),
                    color_comparison=d.get("color_comparison", {}),
                    radius_comparison=d.get("radius_comparison", {}),
                    shadow_comparison=d.get("shadow_comparison", {}),
                    reasoning_trace=d.get("reasoning_steps", []),
                )
        except Exception:
            pass
        return BenchmarkAdvice()


# =============================================================================
# SENTINEL — Best Practices Auditor (ReAct + Grounded Scoring)
# =============================================================================

class BestPracticesValidatorAgent:
    """
    SENTINEL — Design System Best Practices Auditor.
    ReAct: Grounds EVERY score in actual rule-engine data. Audits ALL token types.
    Model: Qwen 72B · Temperature: 0.2
    """

    SYSTEM_PROMPT = """You are SENTINEL, a Design System Best Practices Auditor.

## REASONING FRAMEWORK (ReAct + Grounded)
For EACH check: THINK → ACT (cite data) → OBSERVE → VERIFY.
You MUST CITE the exact input data for every score.

## AUDIT ALL TOKEN TYPES:

### COLORS (25 pts)
- aa_compliance: CITE AA pass/fail count
- color_count: < 20 semantic colors ideal
- near_duplicates: should be 0

### TYPOGRAPHY (25 pts)
- type_scale_standard: nearest standard ratio
- type_scale_consistent: variance check
- base_size_accessible: >= 16px

### SPACING (20 pts)
- spacing_grid: 4px or 8px consistency
- spacing_alignment: > 80% target

### RADIUS (15 pts)
- radius_consistency: base-4/8 grid, clear tiers

### SHADOWS (15 pts)
- shadow_system: elevation hierarchy, blur progression

## CRITICAL: If data says 7 AA failures, you CANNOT say "pass".

## OUTPUT (JSON)

{
  "reasoning_steps": [
    {"step": "THINK", "area": "colors", "content": "7/25 fail AA = 28%"},
    {"step": "ACT", "area": "colors", "content": "aa_compliance = FAIL"},
    {"step": "THINK", "area": "typography", "content": "ratio 1.18, variance 0.22"},
    {"step": "ACT", "area": "typography", "content": "type_scale_consistent = WARN"},
    {"step": "THINK", "area": "spacing", "content": "8px base, 85% aligned"},
    {"step": "ACT", "area": "spacing", "content": "spacing_grid = PASS"},
    {"step": "THINK", "area": "radius", "content": "4px,8px,16px all base-4"},
    {"step": "ACT", "area": "radius", "content": "radius_consistency = PASS"},
    {"step": "THINK", "area": "shadows", "content": "3 levels, blur 4→8→24"},
    {"step": "ACT", "area": "shadows", "content": "shadow_system = WARN"},
    {"step": "VERIFY", "area": "scoring", "content": "3 pass, 2 warn, 1 fail → 62/100"}
  ],
  "overall_score": N,
  "checks": {
    "aa_compliance": {"status": "pass|warn|fail", "note": "CITE: 7/25 fail AA"},
    "type_scale_standard": {"status": "...", "note": "CITE: ratio 1.18 nearest 1.2"},
    "type_scale_consistent": {"status": "...", "note": "CITE: variance 0.22 > 0.15"},
    "base_size_accessible": {"status": "...", "note": "CITE: base = Npx"},
    "spacing_grid": {"status": "...", "note": "CITE: N% aligned to Npx"},
    "color_count": {"status": "...", "note": "CITE: N unique colors"},
    "near_duplicates": {"status": "...", "note": "CITE: N pairs"},
    "radius_consistency": {"status": "...", "note": "CITE: tiers and grid"},
    "shadow_system": {"status": "...", "note": "CITE: N levels, progression"}
  },
  "color_assessment": {"aa_pass_rate": "72%", "palette_size": 25, "verdict": "needs work"},
  "typography_assessment": {"ratio": 1.18, "consistent": false, "base_ok": true, "verdict": "fair"},
  "spacing_assessment": {"grid": "8px", "alignment": "85%", "verdict": "good"},
  "radius_assessment": {"tiers": 3, "base_aligned": true, "verdict": "good"},
  "shadow_assessment": {"levels": 3, "progression": "non-linear", "verdict": "fair"},
  "priority_fixes": [
    {"rank": 1, "issue": "...", "impact": "high", "effort": "low", "action": "Specific fix", "token_type": "color"}
  ],
  "passing_practices": ["spacing_grid"],
  "failing_practices": ["aa_compliance"],
  "self_evaluation": {"confidence": N, "reasoning": "...", "data_quality": "...", "flags": []}
}

Return ONLY valid JSON."""

    PROMPT_TEMPLATE = """Audit this design system. CITE the data for every score.

## RULE ENGINE FACTS (verified)

### Typography
- Ratio: {type_ratio} ({type_consistent}) | Base: {base_size}px | Sizes: {sizes}

### Accessibility
- Total: {total_colors} | AA Pass: {aa_pass} | AA Fail: {aa_fail}
- Failing: {failing_colors}

### Spacing
- Base: {spacing_base}px | Aligned: {spacing_aligned}% | Values: {spacing_values}

### Color Stats
- Unique: {unique_colors} | Near-Duplicates: {near_duplicates}

### Radius
{radius_data}

### Shadows
{shadow_data}

CITE the EXACT numbers above for every check."""

    def __init__(self, hf_client):
        self.hf_client = hf_client

    async def analyze(
        self,
        rule_engine_results: Any,
        radius_tokens: dict = None,
        shadow_tokens: dict = None,
        log_callback: Callable = None,
    ) -> BestPracticesResult:
        def log(msg):
            if log_callback:
                log_callback(msg)

        log("")
        log("   ✅ SENTINEL — Best Practices Auditor (Qwen 72B)")
        log("   └─ ReAct: Auditing colors + typography + spacing + radius + shadows...")

        typo = rule_engine_results.typography
        spacing = rule_engine_results.spacing
        color_stats = rule_engine_results.color_stats
        accessibility = rule_engine_results.accessibility
        failures = [a for a in accessibility if not a.passes_aa_normal]
        failing_str = ", ".join([f"{a.hex_color} ({a.contrast_on_white:.1f}:1)" for a in failures[:8]])
        sizes_str = ", ".join([f"{s}px" for s in typo.sizes_px[:8]]) if typo.sizes_px else "N/A"
        sp_vals = ", ".join([f"{v}px" for v in spacing.current_values[:10]]) if hasattr(spacing, 'current_values') and spacing.current_values else "N/A"

        prompt = self.PROMPT_TEMPLATE.format(
            type_ratio=f"{typo.detected_ratio:.3f}",
            type_consistent="consistent" if typo.is_consistent else f"inconsistent (var={typo.variance:.2f})",
            base_size=typo.sizes_px[0] if typo.sizes_px else 16,
            sizes=sizes_str,
            total_colors=len(accessibility),
            aa_pass=len(accessibility) - len(failures),
            aa_fail=len(failures),
            failing_colors=failing_str or "None",
            spacing_base=spacing.detected_base,
            spacing_aligned=f"{spacing.alignment_percentage:.0f}",
            spacing_values=sp_vals,
            unique_colors=color_stats.unique_count,
            near_duplicates=len(color_stats.near_duplicates),
            radius_data=_fmt_radius(radius_tokens) if radius_tokens else "No radius data",
            shadow_data=_fmt_shadows(shadow_tokens) if shadow_tokens else "No shadow data",
        )

        try:
            start = datetime.now()
            response = await self.hf_client.complete_async(
                agent_name="best_practices_validator",
                system_prompt=self.SYSTEM_PROMPT,
                user_message=prompt,
                max_tokens=2000,
                json_mode=True,
            )
            dur = (datetime.now() - start).total_seconds()
            result = self._parse(response)

            # Critic cross-reference
            passed, errors = validate_sentinel_output(result, rule_engine_results)
            result.validation_passed = passed
            if not passed:
                log(f"   ⚠️ Critic: {len(errors)} issues — applying fixes...")
                for e in errors[:3]:
                    log(f"      └─ {e}")
                result = _apply_sentinel_fixes(result, rule_engine_results, errors)

            log(f"   ─────────────────────────────────────────")
            log(f"   ✅ SENTINEL — COMPLETE ({dur:.1f}s)")
            _log_reasoning(result.reasoning_trace, log)
            log(f"   ├─ Overall Score: {result.overall_score}/100")
            for cn, cv in (result.checks or {}).items():
                if isinstance(cv, dict):
                    s = cv.get("status", "?")
                    si = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(s, "?")
                    log(f"   │  {si} {cn}: {s}")
            log(f"   ├─ Priority Fixes: {len(result.priority_fixes)}")
            log(f"   └─ Critic: {'✅ PASSED' if result.validation_passed else '⚠️ FIXED'}")
            return result

        except Exception as e:
            log(f"   ⚠️ SENTINEL failed: {str(e)[:120]}")
            return BestPracticesResult()

    def _parse(self, response: str) -> BestPracticesResult:
        try:
            m = re.search(r'\{[\s\S]*\}', response)
            if m:
                d = json.loads(m.group())
                return BestPracticesResult(
                    overall_score=d.get("overall_score", 50),
                    checks=d.get("checks", {}),
                    priority_fixes=d.get("priority_fixes", []),
                    passing_practices=d.get("passing_practices", []),
                    failing_practices=d.get("failing_practices", []),
                    self_evaluation=d.get("self_evaluation", {}),
                    color_assessment=d.get("color_assessment", {}),
                    typography_assessment=d.get("typography_assessment", {}),
                    spacing_assessment=d.get("spacing_assessment", {}),
                    radius_assessment=d.get("radius_assessment", {}),
                    shadow_assessment=d.get("shadow_assessment", {}),
                    reasoning_trace=d.get("reasoning_steps", []),
                )
        except Exception:
            pass
        return BestPracticesResult()


# =============================================================================
# NEXUS — HEAD Synthesizer (Tree of Thought)
# =============================================================================

class HeadSynthesizerAgent:
    """
    NEXUS — Senior Design System Architect.
    Tree of Thought: 2 perspectives, picks best, compiles all agent outputs.
    Recommendations for ALL token types.
    Model: Llama 3.3 70B · Temperature: 0.3
    """

    SYSTEM_PROMPT = """You are NEXUS, a Senior Design System Architect — the final synthesizer.

## REASONING FRAMEWORK (Tree of Thought)
Evaluate TWO perspectives:

### PERSPECTIVE A — Accessibility-First
Weights: accessibility=40%, consistency=30%, organization=30%
Penalize heavily for AA failures.

### PERSPECTIVE B — Balanced
Weights: accessibility=30%, consistency=35%, organization=35%
Equal emphasis across areas.

For each: calculate scores, determine top 3 actions.
Then CHOOSE the perspective that better reflects reality.

## SYNTHESIZE ALL TOKEN TYPES:
- Colors: AURORA brand + SENTINEL AA findings → color recommendations
- Typography: ATLAS benchmark match + SENTINEL scale audit → type scale rec
- Spacing: ATLAS grid comparison + SENTINEL alignment → spacing rec
- Radius: SENTINEL consistency + ATLAS benchmark → radius rec
- Shadows: SENTINEL elevation + ATLAS benchmark → shadow rec

## OUTPUT (JSON)

{
  "reasoning_steps": [
    {"step": "THINK", "area": "perspective_a", "content": "Accessibility-first weighting..."},
    {"step": "ACT", "area": "perspective_a", "content": "Score: overall=52..."},
    {"step": "THINK", "area": "perspective_b", "content": "Balanced weighting..."},
    {"step": "ACT", "area": "perspective_b", "content": "Score: overall=63..."},
    {"step": "OBSERVE", "area": "comparison", "content": "A shows severity of AA failures..."},
    {"step": "VERIFY", "area": "decision", "content": "Choosing A — honest about AA issues"}
  ],
  "perspective_a": {"scores": {"overall": 52, "accessibility": 38, "consistency": 72, "organization": 68}, "reasoning": "..."},
  "perspective_b": {"scores": {"overall": 63, "accessibility": 45, "consistency": 72, "organization": 68}, "reasoning": "..."},
  "chosen_perspective": "A",
  "choice_reasoning": "AA failures affect real users — lower score is more honest",
  "executive_summary": "Your design system scores X/100...",
  "scores": {"overall": 52, "accessibility": 38, "consistency": 72, "organization": 68},
  "top_3_actions": [
    {"action": "Fix AA compliance", "impact": "high", "effort": "medium", "details": "#X→#Y", "token_type": "color"}
  ],
  "color_recommendations": [
    {"role": "brand.primary", "current": "#hex", "suggested": "#hex", "reason": "AA", "accept": true}
  ],
  "type_scale_recommendation": {"current_ratio": 1.18, "recommended_ratio": 1.25, "reason": "..."},
  "spacing_recommendation": {"current": "8px", "recommended": "8px", "reason": "Already aligned"},
  "radius_recommendation": {"current": "3 tiers", "recommended": "Add xl tier", "reason": "..."},
  "shadow_recommendation": {"current": "3 levels", "recommended": "Add 2 more", "reason": "..."},
  "benchmark_fit": {"closest": "Material", "similarity": "78%", "recommendation": "..."},
  "brand_analysis": {"primary": "#hex", "secondary": "#hex", "cohesion": 7},
  "self_evaluation": {"confidence": N, "reasoning": "...", "data_quality": "...", "flags": []}
}

Return ONLY valid JSON."""

    PROMPT_TEMPLATE = """Synthesize all analysis into a final report.

## RULE ENGINE FACTS
- Type: {type_ratio} ({type_status}) | Base: {base_size}px
- AA Failures: {aa_failures}/{total_colors}
- Spacing: {spacing_status}
- Colors: {unique_colors} unique | Consistency: {consistency_score}/100
- Radius: {radius_facts}
- Shadows: {shadow_facts}

## AURORA — Brand Analysis
- Primary: {brand_primary} ({brand_confidence}) | Secondary: {brand_secondary}
- Palette: {palette_strategy} | Cohesion: {cohesion_score}/10
- Typography: {aurora_typo}
- Spacing: {aurora_spacing}
- Radius: {aurora_radius}
- Shadows: {aurora_shadows}

## ATLAS — Benchmark
- Closest: {closest_benchmark} ({match_pct}%)
- Typo: {atlas_typo} | Spacing: {atlas_spacing} | Colors: {atlas_colors}
- Radius: {atlas_radius} | Shadows: {atlas_shadows}
- Changes: {benchmark_changes}

## SENTINEL — Audit
- Score: {best_practices_score}/100
- Color: {sentinel_color} | Typo: {sentinel_typo} | Spacing: {sentinel_spacing}
- Radius: {sentinel_radius} | Shadows: {sentinel_shadows}
- Fixes: {priority_fixes}

## AA FIXES NEEDED
{accessibility_fixes}

Evaluate from TWO perspectives (Tree of Thought). Choose one. Recommend for ALL token types."""

    def __init__(self, hf_client):
        self.hf_client = hf_client

    async def synthesize(
        self,
        rule_engine_results: Any,
        benchmark_comparisons: list,
        brand_identification: BrandIdentification,
        benchmark_advice: BenchmarkAdvice,
        best_practices: BestPracticesResult,
        log_callback: Callable = None,
    ) -> HeadSynthesis:
        def log(msg):
            if log_callback:
                log_callback(msg)

        log("")
        log("═" * 60)
        log("🧠 NEXUS — HEAD SYNTHESIZER (Tree of Thought)")
        log("═" * 60)
        log("   Evaluating Perspective A (Accessibility-First) vs B (Balanced)...")
        log("   Compiling: Rule Engine + AURORA + ATLAS + SENTINEL...")

        typo = rule_engine_results.typography
        spacing = rule_engine_results.spacing
        color_stats = rule_engine_results.color_stats
        accessibility = rule_engine_results.accessibility
        failures = [a for a in accessibility if not a.passes_aa_normal]
        aa_fixes_str = "\n".join([
            f"- {a.name}: {a.hex_color} ({a.contrast_on_white:.1f}:1) → {a.suggested_fix} ({a.suggested_fix_contrast:.1f}:1)"
            for a in failures[:8] if a.suggested_fix
        ])
        closest = benchmark_comparisons[0] if benchmark_comparisons else None

        def _s(obj):
            """Safely stringify a dict/value for prompt."""
            if isinstance(obj, dict):
                parts = [f"{k}={v}" for k, v in list(obj.items())[:4]]
                return ", ".join(parts) if parts else "N/A"
            return str(obj) if obj else "N/A"

        prompt = self.PROMPT_TEMPLATE.format(
            type_ratio=f"{typo.detected_ratio:.3f}",
            type_status="consistent" if typo.is_consistent else "inconsistent",
            base_size=typo.sizes_px[0] if typo.sizes_px else 16,
            aa_failures=len(failures), total_colors=len(accessibility),
            spacing_status=f"{spacing.detected_base}px, {spacing.alignment_percentage:.0f}% aligned",
            unique_colors=color_stats.unique_count,
            consistency_score=rule_engine_results.consistency_score,
            radius_facts=_s(best_practices.radius_assessment) or "N/A",
            shadow_facts=_s(best_practices.shadow_assessment) or "N/A",
            brand_primary=brand_identification.brand_primary.get("color", "?"),
            brand_confidence=brand_identification.brand_primary.get("confidence", "?"),
            brand_secondary=brand_identification.brand_secondary.get("color", "?"),
            palette_strategy=brand_identification.palette_strategy,
            cohesion_score=brand_identification.cohesion_score,
            aurora_typo=brand_identification.typography_notes or "N/A",
            aurora_spacing=brand_identification.spacing_notes or "N/A",
            aurora_radius=brand_identification.radius_notes or "N/A",
            aurora_shadows=brand_identification.shadow_notes or "N/A",
            closest_benchmark=closest.benchmark.name if closest else "?",
            match_pct=f"{closest.overall_match_pct:.0f}" if closest else "0",
            atlas_typo=_s(benchmark_advice.typography_comparison),
            atlas_spacing=_s(benchmark_advice.spacing_comparison),
            atlas_colors=_s(benchmark_advice.color_comparison),
            atlas_radius=_s(benchmark_advice.radius_comparison),
            atlas_shadows=_s(benchmark_advice.shadow_comparison),
            benchmark_changes="; ".join([c.get("change", "") for c in benchmark_advice.alignment_changes[:4]]),
            best_practices_score=best_practices.overall_score,
            sentinel_color=_s(best_practices.color_assessment),
            sentinel_typo=_s(best_practices.typography_assessment),
            sentinel_spacing=_s(best_practices.spacing_assessment),
            sentinel_radius=_s(best_practices.radius_assessment),
            sentinel_shadows=_s(best_practices.shadow_assessment),
            priority_fixes="; ".join([f.get("issue", "") for f in best_practices.priority_fixes[:5]]),
            accessibility_fixes=aa_fixes_str or "None needed",
        )

        try:
            start = datetime.now()
            response = await self.hf_client.complete_async(
                agent_name="head_synthesizer",
                system_prompt=self.SYSTEM_PROMPT,
                user_message=prompt,
                max_tokens=2500,
                json_mode=True,
            )
            dur = (datetime.now() - start).total_seconds()
            result = self._parse(response)

            log("")
            log(f"   🧠 NEXUS — COMPLETE ({dur:.1f}s)")
            _log_reasoning(result.reasoning_trace, log)
            pa = result.perspective_a.get("scores", {}).get("overall", "?") if result.perspective_a else "?"
            pb = result.perspective_b.get("scores", {}).get("overall", "?") if result.perspective_b else "?"
            log(f"   ├─ Perspective A: {pa}/100")
            log(f"   ├─ Perspective B: {pb}/100")
            log(f"   ├─ Chosen: {result.chosen_perspective}")
            log(f"   ├─ Why: {(result.choice_reasoning or 'N/A')[:80]}")
            log(f"   ├─ Final Score: {result.scores.get('overall', '?')}/100" if result.scores else "   ├─ Scores: N/A")
            log(f"   ├─ Actions: {len(result.top_3_actions)} | Color Recs: {len(result.color_recommendations)}")
            log(f"   ├─ Typography: {_s(result.type_scale_recommendation)}")
            log(f"   ├─ Spacing: {_s(result.spacing_recommendation)}")
            log(f"   ├─ Radius: {_s(result.radius_recommendation)}")
            log(f"   └─ Shadows: {_s(result.shadow_recommendation)}")
            log("")
            return result

        except Exception as e:
            log(f"   ⚠️ NEXUS failed: {str(e)[:120]}")
            return HeadSynthesis()

    def _parse(self, response: str) -> HeadSynthesis:
        try:
            m = re.search(r'\{[\s\S]*\}', response)
            if m:
                d = json.loads(m.group())
                return HeadSynthesis(
                    executive_summary=d.get("executive_summary", ""),
                    scores=d.get("scores", {}),
                    benchmark_fit=d.get("benchmark_fit", {}),
                    brand_analysis=d.get("brand_analysis", {}),
                    top_3_actions=d.get("top_3_actions", []),
                    color_recommendations=d.get("color_recommendations", []),
                    type_scale_recommendation=d.get("type_scale_recommendation", {}),
                    spacing_recommendation=d.get("spacing_recommendation", {}),
                    radius_recommendation=d.get("radius_recommendation", {}),
                    shadow_recommendation=d.get("shadow_recommendation", {}),
                    self_evaluation=d.get("self_evaluation", {}),
                    perspective_a=d.get("perspective_a", {}),
                    perspective_b=d.get("perspective_b", {}),
                    chosen_perspective=d.get("chosen_perspective", ""),
                    choice_reasoning=d.get("choice_reasoning", ""),
                    reasoning_trace=d.get("reasoning_steps", []),
                )
        except Exception:
            pass
        return HeadSynthesis()


# =============================================================================
# CRITIC / VALIDATOR FUNCTIONS (Rule-based, no LLM)
# =============================================================================

def validate_aurora_output(output: BrandIdentification, input_hexes: list) -> tuple:
    """Validate AURORA naming_map. Returns (passed, errors)."""
    errors = []
    nm = output.naming_map or {}

    # All input colors must have names
    for h in input_hexes:
        if h not in nm and h.lower() not in nm:
            errors.append(f"Missing name for {h}")

    # No word-based shades
    bad_words = {"light", "dark", "base", "muted", "deep", "lighter", "darker"}
    for h, name in nm.items():
        for part in name.split("."):
            if part.lower() in bad_words:
                errors.append(f"Word shade '{part}' in {name}")

    # No duplicates
    seen = set()
    for n in nm.values():
        if n in seen:
            errors.append(f"Duplicate: {n}")
        seen.add(n)

    # Convention: color.X.Y
    for h, name in nm.items():
        if not name.startswith("color."):
            errors.append(f"'{name}' must start with 'color.'")
        if len(name.split(".")) < 3:
            errors.append(f"'{name}' needs 3+ parts")

    return len(errors) == 0, errors


def validate_sentinel_output(output: BestPracticesResult, rule_engine) -> tuple:
    """Cross-reference SENTINEL scores against rule engine data."""
    errors = []
    checks = output.checks or {}
    accessibility = rule_engine.accessibility

    aa_failures = len([a for a in accessibility if not a.passes_aa_normal])
    aa_check = checks.get("aa_compliance", {})
    if aa_failures > 0 and isinstance(aa_check, dict) and aa_check.get("status") == "pass":
        errors.append(f"aa_compliance='pass' but {aa_failures} fail AA")

    score = output.overall_score
    if not (0 <= score <= 100):
        errors.append(f"Score {score} out of 0-100 range")

    fail_count = sum(1 for c in checks.values() if isinstance(c, dict) and c.get("status") == "fail")
    if fail_count >= 3 and score > 70:
        errors.append(f"Score {score} too high with {fail_count} failures")

    typo = rule_engine.typography
    base_size = typo.sizes_px[0] if typo.sizes_px else 16
    base_check = checks.get("base_size_accessible", {})
    if base_size < 16 and isinstance(base_check, dict) and base_check.get("status") == "pass":
        errors.append(f"base_size 'pass' but {base_size}px < 16")

    return len(errors) == 0, errors


def _apply_sentinel_fixes(result: BestPracticesResult, rule_engine, errors: list) -> BestPracticesResult:
    """Deterministic fixes when critic finds issues."""
    accessibility = rule_engine.accessibility
    failures = [a for a in accessibility if not a.passes_aa_normal]

    for err in errors:
        if "aa_compliance" in err and "pass" in err:
            if "aa_compliance" in result.checks:
                result.checks["aa_compliance"]["status"] = "fail"
                result.checks["aa_compliance"]["note"] = f"CORRECTED: {len(failures)} fail AA"

        if "too high" in err.lower():
            fail_count = sum(1 for c in result.checks.values() if isinstance(c, dict) and c.get("status") == "fail")
            max_s = max(30, 100 - fail_count * 15)
            if result.overall_score > max_s:
                result.overall_score = max_s

    result.overall_score = max(0, min(100, result.overall_score))
    result.validation_passed = True
    return result


def post_validate_stage2(
    aurora: BrandIdentification,
    sentinel: BestPracticesResult,
    nexus: HeadSynthesis,
    rule_engine: Any,
) -> list:
    """Final deterministic checks after ALL agents. Returns issues list."""
    issues = []

    for h, name in (aurora.naming_map or {}).items():
        if not re.match(r'^color\.\w+\.[\w]+$', name):
            issues.append(f"Bad name: {name}")

    for key, val in (nexus.scores or {}).items():
        if isinstance(val, (int, float)) and not (0 <= val <= 100):
            issues.append(f"Score {key}={val} OOB")

    aa_failures = len([a for a in rule_engine.accessibility if not a.passes_aa_normal])
    n_acc = nexus.scores.get("accessibility", 50) if nexus.scores else 50
    if aa_failures > 3 and n_acc > 85:
        issues.append(f"Nexus accessibility={n_acc} but {aa_failures} AA failures")

    for rec in (nexus.color_recommendations or []):
        for field in ("current", "suggested"):
            v = rec.get(field, "")
            if v and not v.startswith("#"):
                issues.append(f"Color rec {field} missing #: {v}")

    return issues

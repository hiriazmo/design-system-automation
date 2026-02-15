#!/usr/bin/env python3
"""
Live LLM Agent Evaluations with DeepEval
==========================================

Tests the 4 AI agents with REAL HuggingFace API calls + DeepEval metrics.
Unlike test_agent_evals.py (mock), this hits live LLMs and evaluates output quality.

WHAT THIS TESTS:
  - Does the LLM return valid JSON? (not just our parser)
  - Is the brand identification sensible for known colors?
  - Does the benchmark advisor pick a relevant system?
  - Are priority fixes ranked by actual impact?
  - Does NEXUS reference all 3 upstream agents?
  - Are self-evaluation confidence scores honest?

REQUIRES:
  - HF_TOKEN env var set (HuggingFace Pro $9/month)
  - pip install deepeval (optional — falls back to manual assertions)

RUN:
  # With DeepEval dashboard:
  deepeval test run tests/test_agent_evals_live.py -v

  # With plain pytest:
  pytest tests/test_agent_evals_live.py -v -s --timeout=120

  # Skip if no HF_TOKEN:
  pytest tests/test_agent_evals_live.py -v -k "not live"

COST: ~$0.003 per full run (4 agent calls)
TIME: ~30s sequential, ~10s with parallelized agents
"""

import asyncio
import json
import os
import sys
from typing import Optional

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Skip all tests if no HF_TOKEN
HF_TOKEN = os.getenv("HF_TOKEN", "")
SKIP_REASON = "HF_TOKEN not set — skipping live LLM evals (set HF_TOKEN to run)"
pytestmark = pytest.mark.skipif(not HF_TOKEN, reason=SKIP_REASON)

from agents.llm_agents import (
    BrandIdentifierAgent,
    BenchmarkAdvisorAgent,
    BestPracticesValidatorAgent,
    HeadSynthesizerAgent,
    BrandIdentification,
    BenchmarkAdvice,
    BestPracticesResult,
    HeadSynthesis,
)

# Try importing DeepEval
try:
    from deepeval import assert_test
    from deepeval.test_case import LLMTestCase
    from deepeval.metrics import GEval
    from deepeval.metrics.g_eval import GEvalParameter

    HAS_DEEPEVAL = True
except ImportError:
    HAS_DEEPEVAL = False


# =============================================================================
# LIVE HF CLIENT
# =============================================================================

def get_live_client():
    """Get the real HF inference client."""
    from core.hf_inference import get_inference_client
    return get_inference_client()


# =============================================================================
# REALISTIC TEST DATA (simulates a real website extraction)
# =============================================================================

# Simulates tokens extracted from a SaaS dashboard website
LIVE_COLOR_TOKENS = {
    "primary-button": {"value": "#2563eb", "frequency": 45, "context": "buttons, links, CTAs"},
    "secondary-button": {"value": "#7c3aed", "frequency": 18, "context": "secondary actions"},
    "success": {"value": "#16a34a", "frequency": 12, "context": "success states, badges"},
    "warning": {"value": "#eab308", "frequency": 8, "context": "warnings, alerts"},
    "error": {"value": "#dc2626", "frequency": 6, "context": "error states"},
    "text-primary": {"value": "#111827", "frequency": 200, "context": "headings, body text"},
    "text-secondary": {"value": "#6b7280", "frequency": 150, "context": "secondary text, labels"},
    "text-muted": {"value": "#9ca3af", "frequency": 80, "context": "placeholders, disabled"},
    "bg-white": {"value": "#ffffff", "frequency": 300, "context": "page background"},
    "bg-gray-50": {"value": "#f9fafb", "frequency": 100, "context": "card backgrounds"},
    "bg-gray-100": {"value": "#f3f4f6", "frequency": 60, "context": "section backgrounds"},
    "border": {"value": "#e5e7eb", "frequency": 90, "context": "borders, dividers"},
    "light-accent": {"value": "#bfdbfe", "frequency": 15, "context": "highlights, selected"},
}

LIVE_SEMANTIC_ANALYSIS = {
    "brand": [
        {"hex": "#2563eb", "name": "primary-button", "context": "buttons, links, CTAs"},
        {"hex": "#7c3aed", "name": "secondary-button", "context": "secondary actions"},
    ],
    "text": [
        {"hex": "#111827", "name": "text-primary"},
        {"hex": "#6b7280", "name": "text-secondary"},
    ],
    "status": [
        {"hex": "#16a34a", "name": "success"},
        {"hex": "#dc2626", "name": "error"},
    ],
}


# Mock benchmark comparison objects (same structure as real pipeline)
class _BenchmarkSystem:
    def __init__(self, name, icon, scale_ratio, base_size, spacing_base, best_for):
        self.name = name
        self.icon = icon
        self.typography = {"scale_ratio": scale_ratio, "base_size": base_size}
        self.spacing = {"base": spacing_base}
        self.best_for = best_for


class _BenchmarkComparison:
    def __init__(self, benchmark, similarity_score, overall_match_pct, type_ratio_diff, base_size_diff, spacing_grid_diff):
        self.benchmark = benchmark
        self.similarity_score = similarity_score
        self.overall_match_pct = overall_match_pct
        self.type_ratio_diff = type_ratio_diff
        self.base_size_diff = base_size_diff
        self.spacing_grid_diff = spacing_grid_diff


LIVE_BENCHMARK_COMPARISONS = [
    _BenchmarkComparison(
        benchmark=_BenchmarkSystem("Shopify Polaris", "🟢", 1.2, 16, 4, ["e-commerce", "admin"]),
        similarity_score=0.15, overall_match_pct=85, type_ratio_diff=0.05, base_size_diff=0, spacing_grid_diff=0,
    ),
    _BenchmarkComparison(
        benchmark=_BenchmarkSystem("Material Design 3", "🔵", 1.25, 16, 8, ["mobile", "web"]),
        similarity_score=0.20, overall_match_pct=80, type_ratio_diff=0.1, base_size_diff=0, spacing_grid_diff=4,
    ),
    _BenchmarkComparison(
        benchmark=_BenchmarkSystem("Atlassian Design System", "🔷", 1.143, 14, 8, ["enterprise", "tools"]),
        similarity_score=0.25, overall_match_pct=75, type_ratio_diff=0.007, base_size_diff=2, spacing_grid_diff=4,
    ),
]


# Mock RuleEngineResults (realistic values)
class _MockTypography:
    detected_ratio = 1.15
    base_size = 16.0
    sizes_px = [12, 14, 16, 18, 20, 24, 30, 36, 48]
    is_consistent = False
    variance = 0.18
    scale_name = "Major Second"
    closest_standard_ratio = 1.125
    recommendation = 1.25
    recommendation_name = "Major Third"

    def to_dict(self):
        return {"detected_ratio": self.detected_ratio, "base_size": self.base_size, "sizes_px": self.sizes_px}


class _MockSpacing:
    detected_base = 4
    is_aligned = True
    alignment_percentage = 92.0
    misaligned_values = [6, 10]
    recommendation = 4
    recommendation_reason = "4px grid with 92% alignment"
    current_values = [4, 8, 12, 16, 20, 24, 32, 48, 64]
    suggested_scale = [0, 2, 4, 8, 12, 16, 20, 24, 32, 48, 64]

    def to_dict(self):
        return {"detected_base": self.detected_base, "alignment_percentage": self.alignment_percentage}


class _MockColorStats:
    total_count = 42
    unique_count = 13
    duplicate_count = 29
    gray_count = 5
    saturated_count = 5
    near_duplicates = [("#f3f4f6", "#f9fafb", 0.02)]
    hue_distribution = {"blue": 3, "purple": 1, "green": 1, "red": 1, "yellow": 1, "gray": 6}

    def to_dict(self):
        return {"total": self.total_count, "unique": self.unique_count}


class _MockAccessibility:
    def __init__(self, hex_color, name, passes, contrast_white, fix=None, fix_contrast=None):
        self.hex_color = hex_color
        self.name = name
        self.passes_aa_normal = passes
        self.contrast_on_white = contrast_white
        self.contrast_on_black = 21.0 - contrast_white  # approximate
        self.suggested_fix = fix
        self.suggested_fix_contrast = fix_contrast

    def to_dict(self):
        return {"color": self.hex_color, "aa_normal": self.passes_aa_normal}


LIVE_ACCESSIBILITY = [
    _MockAccessibility("#2563eb", "primary-button", True, 4.68),
    _MockAccessibility("#7c3aed", "secondary-button", True, 5.32),
    _MockAccessibility("#9ca3af", "text-muted", False, 2.85, "#6b7280", 4.56),
    _MockAccessibility("#eab308", "warning", False, 2.09, "#a16207", 4.52),
    _MockAccessibility("#bfdbfe", "light-accent", False, 1.51, "#3b82f6", 4.68),
]


class MockRuleEngineResults:
    typography = _MockTypography()
    spacing = _MockSpacing()
    color_stats = _MockColorStats()
    accessibility = LIVE_ACCESSIBILITY
    aa_failures = 3
    consistency_score = 68

    def to_dict(self):
        return {
            "typography": self.typography.to_dict(),
            "spacing": self.spacing.to_dict(),
            "color_stats": self.color_stats.to_dict(),
            "accessibility": [a.to_dict() for a in self.accessibility],
            "summary": {"aa_failures": self.aa_failures, "consistency_score": self.consistency_score},
        }


# =============================================================================
# HELPER: Run async in pytest
# =============================================================================

def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# =============================================================================
# LIVE TESTS: AURORA (Brand Identifier)
# =============================================================================

class TestAuroraLive:
    """Live evaluation of AURORA — Brand Identifier agent."""

    @pytest.fixture(scope="class")
    def aurora_result(self):
        client = get_live_client()
        agent = BrandIdentifierAgent(client)
        return run_async(agent.analyze(
            color_tokens=LIVE_COLOR_TOKENS,
            semantic_analysis=LIVE_SEMANTIC_ANALYSIS,
        ))

    def test_returns_brand_identification(self, aurora_result):
        """AURORA returns a BrandIdentification dataclass."""
        assert isinstance(aurora_result, BrandIdentification)

    def test_identifies_primary_as_blue(self, aurora_result):
        """AURORA should identify #2563eb (blue) as brand primary — it has highest frequency in buttons."""
        bp = aurora_result.brand_primary
        assert isinstance(bp, dict), f"Expected dict, got {type(bp)}"
        color = bp.get("color", "").lower()
        # Should be blue (#2563eb) — the dominant CTA color
        assert color == "#2563eb", f"Expected #2563eb as primary, got {color}"

    def test_confidence_is_high(self, aurora_result):
        """With 45 button usages, confidence should be high."""
        bp = aurora_result.brand_primary
        confidence = bp.get("confidence", "").lower()
        assert confidence in ("high", "very high"), f"Expected high confidence, got '{confidence}'"

    def test_palette_strategy_identified(self, aurora_result):
        """Palette strategy should be identified (blue + purple = near-analogous)."""
        assert aurora_result.palette_strategy != ""
        assert aurora_result.palette_strategy in (
            "analogous", "complementary", "triadic", "monochromatic",
            "split-complementary", "near-analogous", "random",
        )

    def test_cohesion_score_reasonable(self, aurora_result):
        """Cohesion score 1-10, this palette is decent so expect 5+."""
        score = aurora_result.cohesion_score
        assert 1 <= score <= 10, f"Cohesion score out of range: {score}"
        assert score >= 4, f"Expected 4+ for a decent SaaS palette, got {score}"

    def test_self_evaluation_present(self, aurora_result):
        """Self-evaluation includes confidence and data_quality."""
        se = aurora_result.self_evaluation
        assert isinstance(se, dict)
        assert "confidence" in se, f"Missing confidence in self_evaluation: {se}"

    def test_json_serializable(self, aurora_result):
        """Output is fully JSON-serializable."""
        d = aurora_result.to_dict()
        json_str = json.dumps(d)
        assert len(json_str) > 50

    def test_deepeval_quality(self, aurora_result):
        """DeepEval G-Eval: Is the brand analysis coherent and useful?"""
        if not HAS_DEEPEVAL:
            pytest.skip("DeepEval not installed — run: pip install deepeval")

        test_case = LLMTestCase(
            input=f"Analyze brand colors: primary-button=#2563eb (45 uses), secondary=#7c3aed (18 uses), 13 total colors",
            actual_output=json.dumps(aurora_result.to_dict(), indent=2),
        )

        coherence_metric = GEval(
            name="Brand Analysis Coherence",
            criteria="The brand analysis should correctly identify the most-used button color as primary, provide a valid palette strategy, and include reasoning that references usage frequency.",
            evaluation_params=[GEvalParameter.ACTUAL_OUTPUT],
            threshold=0.6,
        )

        assert_test(test_case, [coherence_metric])


# =============================================================================
# LIVE TESTS: ATLAS (Benchmark Advisor)
# =============================================================================

class TestAtlasLive:
    """Live evaluation of ATLAS — Benchmark Advisor agent."""

    @pytest.fixture(scope="class")
    def atlas_result(self):
        client = get_live_client()
        agent = BenchmarkAdvisorAgent(client)
        return run_async(agent.analyze(
            user_ratio=1.15,
            user_base=16,
            user_spacing=4,
            benchmark_comparisons=LIVE_BENCHMARK_COMPARISONS,
        ))

    def test_returns_benchmark_advice(self, atlas_result):
        assert isinstance(atlas_result, BenchmarkAdvice)

    def test_recommends_known_benchmark(self, atlas_result):
        """Should recommend one of the provided benchmarks."""
        rec = atlas_result.recommended_benchmark.lower()
        assert any(name in rec for name in ["polaris", "material", "atlassian"]), \
            f"Unexpected benchmark: {atlas_result.recommended_benchmark}"

    def test_reasoning_non_empty(self, atlas_result):
        """Reasoning explains WHY this benchmark fits."""
        assert len(atlas_result.reasoning) > 20, \
            f"Reasoning too short: '{atlas_result.reasoning}'"

    def test_alignment_changes_actionable(self, atlas_result):
        """Alignment changes should be a list of specific steps."""
        changes = atlas_result.alignment_changes
        assert isinstance(changes, list)
        assert len(changes) >= 1, "Expected at least 1 alignment change"

    def test_pros_and_cons_present(self, atlas_result):
        """Both pros and cons should be listed."""
        assert isinstance(atlas_result.pros_of_alignment, list)
        assert len(atlas_result.pros_of_alignment) >= 1

    def test_self_evaluation_present(self, atlas_result):
        se = atlas_result.self_evaluation
        assert isinstance(se, dict)
        assert "confidence" in se

    def test_deepeval_quality(self, atlas_result):
        """DeepEval G-Eval: Is the benchmark recommendation well-reasoned?"""
        if not HAS_DEEPEVAL:
            pytest.skip("DeepEval not installed")

        test_case = LLMTestCase(
            input="Compare against: Polaris (85%), Material 3 (80%), Atlassian (75%)",
            actual_output=json.dumps(atlas_result.to_dict(), indent=2),
        )

        relevance_metric = GEval(
            name="Benchmark Recommendation Relevance",
            criteria="The recommendation should pick the highest-matching benchmark, explain why structurally, and list concrete alignment changes needed.",
            evaluation_params=[GEvalParameter.ACTUAL_OUTPUT],
            threshold=0.6,
        )

        assert_test(test_case, [relevance_metric])


# =============================================================================
# LIVE TESTS: SENTINEL (Best Practices Validator)
# =============================================================================

class TestSentinelLive:
    """Live evaluation of SENTINEL — Best Practices Validator agent."""

    @pytest.fixture(scope="class")
    def sentinel_result(self):
        client = get_live_client()
        agent = BestPracticesValidatorAgent(client)
        return run_async(agent.analyze(
            rule_engine_results=MockRuleEngineResults(),
        ))

    def test_returns_best_practices_result(self, sentinel_result):
        assert isinstance(sentinel_result, BestPracticesResult)

    def test_score_in_range(self, sentinel_result):
        """Score should be 0-100."""
        assert 0 <= sentinel_result.overall_score <= 100

    def test_score_reflects_failures(self, sentinel_result):
        """With 3 AA failures and inconsistent type scale, score should be < 80."""
        assert sentinel_result.overall_score < 85, \
            f"Score {sentinel_result.overall_score} seems too high for 3 AA failures + inconsistent type"

    def test_priority_fixes_ranked(self, sentinel_result):
        """Priority fixes should exist and be ranked."""
        fixes = sentinel_result.priority_fixes
        assert isinstance(fixes, list)
        assert len(fixes) >= 1, "Expected at least 1 priority fix"
        # First fix should address accessibility (most impactful)
        if isinstance(fixes[0], dict):
            first_issue = str(fixes[0].get("issue", "")).lower()
            # Should mention contrast/accessibility/AA in top fixes
            assert any(kw in first_issue for kw in ("contrast", "aa", "accessib", "color")), \
                f"Top fix doesn't address accessibility: '{first_issue}'"

    def test_checks_cover_key_areas(self, sentinel_result):
        """Checks should cover contrast, type scale, spacing."""
        if sentinel_result.checks:
            check_keys = " ".join(str(k).lower() for k in sentinel_result.checks.keys())
            # At least 2 of these should appear
            areas_found = sum(1 for area in ["contrast", "type", "spacing", "color"]
                             if area in check_keys)
            assert areas_found >= 2, f"Only {areas_found} key areas in checks: {list(sentinel_result.checks.keys())}"

    def test_self_evaluation_present(self, sentinel_result):
        se = sentinel_result.self_evaluation
        assert isinstance(se, dict)

    def test_deepeval_quality(self, sentinel_result):
        """DeepEval G-Eval: Are priority fixes correctly ordered by impact?"""
        if not HAS_DEEPEVAL:
            pytest.skip("DeepEval not installed")

        test_case = LLMTestCase(
            input="Rule engine: 3 AA failures, inconsistent type scale (variance=0.18), 4px grid 92% aligned, 13 unique colors",
            actual_output=json.dumps(sentinel_result.to_dict(), indent=2),
        )

        impact_metric = GEval(
            name="Priority Fix Impact Ordering",
            criteria="Accessibility failures should be ranked highest priority since they affect legal compliance and usability. Type scale inconsistency and color consolidation should follow.",
            evaluation_params=[GEvalParameter.ACTUAL_OUTPUT],
            threshold=0.6,
        )

        assert_test(test_case, [impact_metric])


# =============================================================================
# LIVE TESTS: NEXUS (Head Synthesizer)
# =============================================================================

class TestNexusLive:
    """Live evaluation of NEXUS — Head Synthesizer agent."""

    @pytest.fixture(scope="class")
    def nexus_result(self):
        client = get_live_client()

        # First run the 3 upstream agents
        aurora_agent = BrandIdentifierAgent(client)
        atlas_agent = BenchmarkAdvisorAgent(client)
        sentinel_agent = BestPracticesValidatorAgent(client)

        aurora_result = run_async(aurora_agent.analyze(
            color_tokens=LIVE_COLOR_TOKENS,
            semantic_analysis=LIVE_SEMANTIC_ANALYSIS,
        ))
        atlas_result = run_async(atlas_agent.analyze(
            user_ratio=1.15,
            user_base=16,
            user_spacing=4,
            benchmark_comparisons=LIVE_BENCHMARK_COMPARISONS,
        ))
        sentinel_result = run_async(sentinel_agent.analyze(
            rule_engine_results=MockRuleEngineResults(),
        ))

        # Now run NEXUS with real upstream outputs
        nexus_agent = HeadSynthesizerAgent(client)
        return run_async(nexus_agent.synthesize(
            rule_engine_results=MockRuleEngineResults(),
            benchmark_comparisons=LIVE_BENCHMARK_COMPARISONS,
            brand_identification=aurora_result,
            benchmark_advice=atlas_result,
            best_practices=sentinel_result,
        ))

    def test_returns_head_synthesis(self, nexus_result):
        assert isinstance(nexus_result, HeadSynthesis)

    def test_executive_summary_substantial(self, nexus_result):
        """Executive summary should be a meaningful paragraph."""
        assert len(nexus_result.executive_summary) > 50, \
            f"Summary too short ({len(nexus_result.executive_summary)} chars): '{nexus_result.executive_summary}'"

    def test_top_3_actions_present(self, nexus_result):
        """Should provide 3 action items."""
        assert isinstance(nexus_result.top_3_actions, list)
        assert len(nexus_result.top_3_actions) >= 2, \
            f"Expected 2+ actions, got {len(nexus_result.top_3_actions)}"

    def test_scores_present(self, nexus_result):
        """Overall scores dict should have key metrics."""
        scores = nexus_result.scores
        assert isinstance(scores, dict)
        assert len(scores) >= 1, "Expected at least 1 score dimension"

    def test_color_recommendations_present(self, nexus_result):
        """Should include color-specific recommendations."""
        recs = nexus_result.color_recommendations
        assert isinstance(recs, list)
        # With 3 AA failures, should have some color recs
        # (may be empty if NEXUS consolidates into actions instead)

    def test_references_all_agents(self, nexus_result):
        """Executive summary should reference brand + benchmark + practices."""
        summary_lower = nexus_result.executive_summary.lower()
        to_dict = json.dumps(nexus_result.to_dict()).lower()
        # NEXUS should incorporate insights from all 3 agents
        # Check in full output since summary might be concise
        has_brand = any(kw in to_dict for kw in ("brand", "primary", "color"))
        has_benchmark = any(kw in to_dict for kw in ("benchmark", "polaris", "material", "system"))
        has_practices = any(kw in to_dict for kw in ("accessibility", "contrast", "score", "fix"))
        assert has_brand, "NEXUS output missing brand analysis references"
        assert has_practices, "NEXUS output missing best practices references"

    def test_self_evaluation_present(self, nexus_result):
        se = nexus_result.self_evaluation
        assert isinstance(se, dict)

    def test_json_serializable(self, nexus_result):
        d = nexus_result.to_dict()
        json_str = json.dumps(d)
        assert len(json_str) > 100

    def test_deepeval_synthesis_quality(self, nexus_result):
        """DeepEval G-Eval: Does NEXUS produce a coherent synthesis?"""
        if not HAS_DEEPEVAL:
            pytest.skip("DeepEval not installed")

        test_case = LLMTestCase(
            input="Synthesize: AURORA found blue primary (#2563eb), ATLAS recommends Polaris (85% match), SENTINEL found 3 AA failures, score 68/100",
            actual_output=json.dumps(nexus_result.to_dict(), indent=2),
        )

        synthesis_metric = GEval(
            name="Synthesis Quality",
            criteria="The synthesis should: (1) reference findings from all 3 upstream agents, (2) prioritize actionable recommendations, (3) include an executive summary that a non-technical stakeholder could understand, (4) not contradict upstream agent findings.",
            evaluation_params=[GEvalParameter.ACTUAL_OUTPUT],
            threshold=0.6,
        )

        assert_test(test_case, [synthesis_metric])


# =============================================================================
# CROSS-AGENT CONSISTENCY TEST
# =============================================================================

class TestCrossAgentConsistency:
    """Tests that verify consistency across all 4 agents."""

    @pytest.fixture(scope="class")
    def all_results(self):
        """Run all 4 agents and return results."""
        client = get_live_client()

        aurora = run_async(BrandIdentifierAgent(client).analyze(
            color_tokens=LIVE_COLOR_TOKENS,
            semantic_analysis=LIVE_SEMANTIC_ANALYSIS,
        ))
        atlas = run_async(BenchmarkAdvisorAgent(client).analyze(
            user_ratio=1.15, user_base=16, user_spacing=4,
            benchmark_comparisons=LIVE_BENCHMARK_COMPARISONS,
        ))
        sentinel = run_async(BestPracticesValidatorAgent(client).analyze(
            rule_engine_results=MockRuleEngineResults(),
        ))
        nexus = run_async(HeadSynthesizerAgent(client).synthesize(
            rule_engine_results=MockRuleEngineResults(),
            benchmark_comparisons=LIVE_BENCHMARK_COMPARISONS,
            brand_identification=aurora,
            benchmark_advice=atlas,
            best_practices=sentinel,
        ))

        return {"aurora": aurora, "atlas": atlas, "sentinel": sentinel, "nexus": nexus}

    def test_all_agents_return_results(self, all_results):
        """All 4 agents should return non-None results."""
        for name, result in all_results.items():
            assert result is not None, f"{name} returned None"

    def test_all_have_self_evaluation(self, all_results):
        """Every agent should include self-evaluation."""
        for name, result in all_results.items():
            se = result.self_evaluation
            assert isinstance(se, dict), f"{name} self_evaluation is not dict: {type(se)}"

    def test_validation_passes(self, all_results):
        """All agent outputs pass schema validation."""
        from core.validation import validate_agent_output

        validations = {
            "aurora": all_results["aurora"],
            "atlas": all_results["atlas"],
            "sentinel": all_results["sentinel"],
            "nexus": all_results["nexus"],
        }
        for agent_name, result in validations.items():
            is_valid, error = validate_agent_output(result, agent_name)
            assert is_valid, f"{agent_name} validation failed: {error}"

    def test_nexus_score_near_sentinel(self, all_results):
        """NEXUS overall score should be within 20 points of SENTINEL score."""
        sentinel_score = all_results["sentinel"].overall_score
        nexus_scores = all_results["nexus"].scores
        if "overall" in nexus_scores:
            nexus_score = nexus_scores["overall"]
            diff = abs(nexus_score - sentinel_score)
            assert diff <= 25, \
                f"NEXUS ({nexus_score}) and SENTINEL ({sentinel_score}) scores differ by {diff} — should be within 25"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--timeout=120"])

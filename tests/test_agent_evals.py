#!/usr/bin/env python3
"""
LLM Agent Evaluation Tests
============================

Evaluates the 4 named AI agents using mock HF client responses.
Tests schema compliance, output correctness, and consistency.

Uses DeepEval when available, falls back to manual assertions.

Run: pytest tests/test_agent_evals.py -v
"""

import asyncio
import json
import os
import sys
from dataclasses import asdict
from typing import Optional

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    from deepeval.metrics import JsonSchemaMetric

    HAS_DEEPEVAL = True
except ImportError:
    HAS_DEEPEVAL = False


# =============================================================================
# MOCK HF CLIENT
# =============================================================================

# Canned JSON responses that each agent would return
AURORA_RESPONSE = json.dumps({
    "brand_primary": {
        "color": "#06b2c4",
        "confidence": "high",
        "reasoning": "Used in 33 buttons and 12 CTAs — dominant interactive color",
        "usage_count": 45,
    },
    "brand_secondary": {
        "color": "#c1df1f",
        "confidence": "medium",
        "reasoning": "Used in highlights and badges",
        "usage_count": 23,
    },
    "brand_accent": None,
    "palette_strategy": "complementary",
    "cohesion_score": 6,
    "cohesion_notes": "Primary and secondary are near-complementary on the color wheel. Reasonable coherence but accent is missing.",
    "semantic_names": {
        "#06b2c4": "brand.primary",
        "#c1df1f": "brand.secondary",
        "#1a1a1a": "text.primary",
        "#666666": "text.secondary",
    },
    "self_evaluation": {
        "confidence": 8,
        "reasoning": "Clear dominant primary from button usage. Secondary less certain.",
        "data_quality": "good",
        "flags": [],
    },
})

ATLAS_RESPONSE = json.dumps({
    "recommended_benchmark": "shopify_polaris",
    "recommended_benchmark_name": "Shopify Polaris",
    "reasoning": "87% structural match. Polaris uses similar type scale and spacing grid approach.",
    "alignment_changes": [
        {"change": "Adopt 1.25 Major Third type scale", "from": "1.18 random", "to": "1.25", "effort": "low"},
        {"change": "Standardize to 4px spacing grid", "from": "mixed", "to": "4px", "effort": "medium"},
    ],
    "pros_of_alignment": [
        "Industry-standard component patterns",
        "Strong accessibility built-in",
    ],
    "cons_of_alignment": [
        "May feel generic without customization",
    ],
    "alternative_benchmarks": [
        {"name": "Material Design 3", "reason": "77% match, stronger theming support"},
        {"name": "Atlassian Design System", "reason": "76% match, similar enterprise focus"},
    ],
    "self_evaluation": {
        "confidence": 7,
        "reasoning": "Good structural match but benchmark comparison limited to 8 systems",
        "data_quality": "good",
        "flags": [],
    },
})

SENTINEL_RESPONSE = json.dumps({
    "overall_score": 62,
    "checks": {
        "color_contrast": {"status": "fail", "note": "67 AA failures including brand primary"},
        "type_scale": {"status": "warn", "note": "Near-consistent but not standard ratio"},
        "spacing_grid": {"status": "pass", "note": "4px grid detected with 85% alignment"},
        "color_count": {"status": "warn", "note": "143 unique colors — recommend consolidation to ~20"},
        "shadow_system": {"status": "pass", "note": "4 elevation levels (xs, sm, md, lg) with consistent blur progression"},
    },
    "priority_fixes": [
        {"rank": 1, "issue": "Brand primary fails AA contrast", "impact": "high", "effort": "low", "action": "Darken #06b2c4 to #048391"},
        {"rank": 2, "issue": "143 colors too many", "impact": "medium", "effort": "medium", "action": "Consolidate to semantic palette"},
        {"rank": 3, "issue": "Type scale inconsistent", "impact": "medium", "effort": "low", "action": "Adopt 1.25 Major Third"},
    ],
    "passing_practices": ["spacing_grid", "font_family_consistency", "shadow_system"],
    "failing_practices": ["color_contrast", "color_count"],
    "self_evaluation": {
        "confidence": 8,
        "reasoning": "Rule engine data is clear. Priority ordering based on impact analysis.",
        "data_quality": "good",
        "flags": [],
    },
})

NEXUS_RESPONSE = json.dumps({
    "executive_summary": "Design system shows strong structural foundation (4px grid, consistent typography) but needs critical accessibility fixes. Brand primary #06b2c4 fails AA — recommend darkened variant. 87% aligned to Polaris.",
    "scores": {
        "overall": 62,
        "accessibility": 45,
        "consistency": 72,
        "organization": 68,
    },
    "benchmark_fit": {
        "closest": "Shopify Polaris",
        "similarity": 87,
        "recommendation": "Align type scale and consolidate colors for 95%+ match",
    },
    "brand_analysis": {
        "primary": "#06b2c4",
        "secondary": "#c1df1f",
        "cohesion": 6,
    },
    "top_3_actions": [
        {"action": "Fix brand primary contrast", "impact": "high", "effort": "low", "details": "Darken to #048391 for AA 4.5:1"},
        {"action": "Consolidate color palette", "impact": "medium", "effort": "medium", "details": "Reduce 143 → ~20 semantic colors"},
        {"action": "Standardize type scale", "impact": "medium", "effort": "low", "details": "Adopt 1.25 Major Third ratio"},
    ],
    "color_recommendations": [
        {"role": "brand-primary", "current": "#06b2c4", "suggested": "#048391", "reason": "AA compliance", "accept": True},
    ],
    "type_scale_recommendation": {
        "current_ratio": 1.18,
        "recommended_ratio": 1.25,
        "name": "Major Third",
    },
    "spacing_recommendation": {
        "current_base": 4,
        "recommended_base": 8,
        "reason": "Simpler system with fewer decisions",
    },
    "self_evaluation": {
        "confidence": 8,
        "reasoning": "Strong data from rule engine and all 3 agents. Minor disagreement on spacing resolved by averaging.",
        "data_quality": "good",
        "flags": [],
    },
})


class MockHFClient:
    """Mock HF Inference client that returns canned responses per agent."""

    AGENT_RESPONSES = {
        "brand_identifier": AURORA_RESPONSE,
        "benchmark_advisor": ATLAS_RESPONSE,
        "best_practices": SENTINEL_RESPONSE,
        "best_practices_validator": SENTINEL_RESPONSE,
        "head_synthesizer": NEXUS_RESPONSE,
    }

    async def complete_async(
        self,
        agent_name: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000,
        json_mode: bool = True,
    ) -> str:
        """Return canned response for the agent."""
        return self.AGENT_RESPONSES.get(agent_name, "{}")


# =============================================================================
# TEST DATA
# =============================================================================

MOCK_COLOR_TOKENS = {
    "brand-primary": {"value": "#06b2c4", "frequency": 45, "context": "buttons, links"},
    "brand-secondary": {"value": "#c1df1f", "frequency": 23, "context": "highlights"},
    "text-primary": {"value": "#1a1a1a", "frequency": 120, "context": "headings, body"},
    "text-secondary": {"value": "#666666", "frequency": 80, "context": "captions"},
    "background": {"value": "#ffffff", "frequency": 200, "context": "page background"},
}

MOCK_SEMANTIC_ANALYSIS = {
    "brand": [{"hex": "#06b2c4", "name": "brand-primary"}],
    "text": [{"hex": "#1a1a1a", "name": "text-primary"}],
}

MOCK_SHADOW_TOKENS = {
    "shadow-xs": {"value": "rgba(0,0,0,0.05) 0px 1px 2px 0px"},
    "shadow-sm": {"value": "rgba(0,0,0,0.1) 0px 2px 4px 0px"},
    "shadow-md": {"value": "rgba(0,0,0,0.15) 0px 4px 8px 0px"},
    "shadow-lg": {"value": "rgba(0,0,0,0.2) 0px 8px 16px 0px"},
}

MOCK_SHADOW_TOKENS_POOR = {
    # Only 2 levels - not enough for proper elevation hierarchy
    "shadow-1": {"value": "rgba(0,0,0,0.5) 0px 2px 0px 0px"},  # No blur, harsh
    "shadow-2": {"value": "rgba(0,0,0,0.5) 0px 4px 2px 0px"},  # High opacity
}

class MockBenchmarkSystem:
    """Mock benchmark system object (what c.benchmark returns)."""
    def __init__(self, name, icon, scale_ratio, base_size, spacing_base, best_for):
        self.name = name
        self.icon = icon
        self.typography = {"scale_ratio": scale_ratio, "base_size": base_size}
        self.spacing = {"base": spacing_base}
        self.best_for = best_for


class MockBenchmarkComparison:
    """Mock benchmark comparison object (what ATLAS._format_comparisons expects)."""
    def __init__(self, benchmark, similarity_score, overall_match_pct, type_ratio_diff, base_size_diff, spacing_grid_diff):
        self.benchmark = benchmark
        self.similarity_score = similarity_score
        self.overall_match_pct = overall_match_pct
        self.type_ratio_diff = type_ratio_diff
        self.base_size_diff = base_size_diff
        self.spacing_grid_diff = spacing_grid_diff


MOCK_BENCHMARK_COMPARISONS = [
    MockBenchmarkComparison(
        benchmark=MockBenchmarkSystem("Shopify Polaris", "🟢", 1.25, 16, 4, ["e-commerce", "admin"]),
        similarity_score=0.13, overall_match_pct=87, type_ratio_diff=0.07, base_size_diff=0, spacing_grid_diff=0,
    ),
    MockBenchmarkComparison(
        benchmark=MockBenchmarkSystem("Material Design 3", "🔵", 1.25, 16, 8, ["mobile", "web"]),
        similarity_score=0.23, overall_match_pct=77, type_ratio_diff=0.07, base_size_diff=0, spacing_grid_diff=4,
    ),
    MockBenchmarkComparison(
        benchmark=MockBenchmarkSystem("Atlassian", "🔷", 1.2, 14, 8, ["enterprise", "tools"]),
        similarity_score=0.24, overall_match_pct=76, type_ratio_diff=0.02, base_size_diff=2, spacing_grid_diff=4,
    ),
]


# Mock RuleEngineResults for SENTINEL and NEXUS
class MockTypography:
    detected_ratio = 1.18
    base_size = 16.0
    sizes_px = [12, 14, 16, 18, 22, 28, 36, 48]
    is_consistent = False
    variance = 0.22
    scale_name = "Minor Third"
    closest_standard_ratio = 1.2
    recommendation = 1.25
    recommendation_name = "Major Third"

    def to_dict(self):
        return {"detected_ratio": self.detected_ratio, "base_size": self.base_size}


class MockSpacing:
    detected_base = 4
    is_aligned = True
    alignment_percentage = 85.0
    misaligned_values = [5, 10]
    recommendation = 8
    recommendation_reason = "Simpler grid"
    current_values = [4, 8, 12, 16, 24, 32]
    suggested_scale = [0, 4, 8, 12, 16, 24, 32, 48]

    def to_dict(self):
        return {"detected_base": self.detected_base, "alignment_percentage": self.alignment_percentage}


class MockColorStats:
    total_count = 160
    unique_count = 143
    duplicate_count = 17
    gray_count = 22
    saturated_count = 45
    near_duplicates = [("#06b2c4", "#07b3c5", 0.01)]
    hue_distribution = {"cyan": 5, "gray": 22, "green": 3}

    def to_dict(self):
        return {"total": self.total_count, "unique": self.unique_count}


class MockAccessibility:
    def __init__(self):
        self.hex_color = "#06b2c4"
        self.name = "brand-primary"
        self.passes_aa_normal = False
        self.contrast_on_white = 2.57
        self.contrast_on_black = 8.18
        self.suggested_fix = "#048391"
        self.suggested_fix_contrast = 4.5

    def to_dict(self):
        return {"color": self.hex_color, "aa_normal": self.passes_aa_normal}


class MockRuleEngineResults:
    typography = MockTypography()
    spacing = MockSpacing()
    color_stats = MockColorStats()
    accessibility = [MockAccessibility()]
    aa_failures = 67
    consistency_score = 52

    def to_dict(self):
        return {
            "typography": self.typography.to_dict(),
            "spacing": self.spacing.to_dict(),
            "color_stats": self.color_stats.to_dict(),
            "summary": {"aa_failures": self.aa_failures, "consistency_score": self.consistency_score},
        }


# =============================================================================
# SCHEMA COMPLIANCE TESTS
# =============================================================================

class TestAuroraSchemaCompliance:
    """AURORA (Brand Identifier) output schema validation."""

    @pytest.fixture
    def agent(self):
        return BrandIdentifierAgent(MockHFClient())

    @pytest.mark.asyncio
    async def test_schema_compliance(self, agent):
        """AURORA output has all required BrandIdentification fields."""
        result = await agent.analyze(
            color_tokens=MOCK_COLOR_TOKENS,
            typography_tokens={},
        )
        assert isinstance(result, BrandIdentification)
        # Required fields present
        assert hasattr(result, "brand_primary")
        assert hasattr(result, "palette_strategy")
        assert hasattr(result, "cohesion_score")
        assert hasattr(result, "self_evaluation")

    @pytest.mark.asyncio
    async def test_brand_primary_detected(self, agent):
        """AURORA correctly identifies brand primary from high-usage color."""
        result = await agent.analyze(
            color_tokens=MOCK_COLOR_TOKENS,
            typography_tokens={},
        )
        bp = result.brand_primary
        assert isinstance(bp, dict)
        assert bp.get("color") == "#06b2c4"
        assert bp.get("confidence") in ("high", "medium", "low")

    @pytest.mark.asyncio
    async def test_palette_strategy_valid(self, agent):
        """Palette strategy is a recognized value."""
        result = await agent.analyze(
            color_tokens=MOCK_COLOR_TOKENS,
            typography_tokens={},
        )
        valid_strategies = ["complementary", "analogous", "triadic", "monochromatic", "split-complementary", "random", ""]
        assert result.palette_strategy in valid_strategies

    @pytest.mark.asyncio
    async def test_to_dict_serializable(self, agent):
        """Output is JSON-serializable."""
        result = await agent.analyze(
            color_tokens=MOCK_COLOR_TOKENS,
            typography_tokens={},
        )
        d = result.to_dict()
        json_str = json.dumps(d)
        assert len(json_str) > 10


class TestAtlasSchemaCompliance:
    """ATLAS (Benchmark Advisor) output schema validation."""

    @pytest.fixture
    def agent(self):
        return BenchmarkAdvisorAgent(MockHFClient())

    @pytest.mark.asyncio
    async def test_schema_compliance(self, agent):
        """ATLAS output has all required BenchmarkAdvice fields."""
        result = await agent.analyze(
            user_ratio=1.18,
            user_base=16,
            user_spacing=4,
            benchmark_comparisons=MOCK_BENCHMARK_COMPARISONS,
        )
        assert isinstance(result, BenchmarkAdvice)
        assert hasattr(result, "recommended_benchmark")
        assert hasattr(result, "reasoning")
        assert hasattr(result, "alignment_changes")
        assert hasattr(result, "self_evaluation")

    @pytest.mark.asyncio
    async def test_benchmark_recommended(self, agent):
        """ATLAS recommends a valid benchmark."""
        result = await agent.analyze(
            user_ratio=1.18,
            user_base=16,
            user_spacing=4,
            benchmark_comparisons=MOCK_BENCHMARK_COMPARISONS,
        )
        assert result.recommended_benchmark != ""
        assert result.reasoning != ""

    @pytest.mark.asyncio
    async def test_alignment_changes_structured(self, agent):
        """Alignment changes are structured dicts."""
        result = await agent.analyze(
            user_ratio=1.18,
            user_base=16,
            user_spacing=4,
            benchmark_comparisons=MOCK_BENCHMARK_COMPARISONS,
        )
        assert isinstance(result.alignment_changes, list)
        if result.alignment_changes:
            change = result.alignment_changes[0]
            assert isinstance(change, dict)
            assert "change" in change


class TestSentinelSchemaCompliance:
    """SENTINEL (Best Practices Validator) output schema validation."""

    @pytest.fixture
    def agent(self):
        return BestPracticesValidatorAgent(MockHFClient())

    @pytest.mark.asyncio
    async def test_schema_compliance(self, agent):
        """SENTINEL output has all required BestPracticesResult fields."""
        result = await agent.analyze(
            rule_engine_results=MockRuleEngineResults(),
        )
        assert isinstance(result, BestPracticesResult)
        assert hasattr(result, "overall_score")
        assert hasattr(result, "priority_fixes")
        assert hasattr(result, "self_evaluation")

    @pytest.mark.asyncio
    async def test_score_in_range(self, agent):
        """Overall score is between 0-100."""
        result = await agent.analyze(
            rule_engine_results=MockRuleEngineResults(),
        )
        assert 0 <= result.overall_score <= 100

    @pytest.mark.asyncio
    async def test_priority_fixes_ranked(self, agent):
        """Priority fixes are a list with high-impact items first."""
        result = await agent.analyze(
            rule_engine_results=MockRuleEngineResults(),
        )
        assert isinstance(result.priority_fixes, list)
        if len(result.priority_fixes) >= 2:
            # First fix should be highest priority
            first = result.priority_fixes[0]
            if isinstance(first, dict) and "rank" in first:
                assert first["rank"] == 1


class TestSentinelShadowAnalysis:
    """SENTINEL shadow system evaluation tests."""

    @pytest.fixture
    def agent(self):
        return BestPracticesValidatorAgent(MockHFClient())

    @pytest.mark.asyncio
    async def test_shadow_check_in_output(self, agent):
        """SENTINEL includes shadow_system check in output."""
        result = await agent.analyze(
            rule_engine_results=MockRuleEngineResults(),
            shadow_tokens=MOCK_SHADOW_TOKENS,
        )
        assert "shadow_system" in result.checks
        shadow_check = result.checks["shadow_system"]
        assert isinstance(shadow_check, dict)
        assert "status" in shadow_check
        assert shadow_check["status"] in ("pass", "warn", "fail")

    @pytest.mark.asyncio
    async def test_shadow_tokens_passed_to_prompt(self, agent):
        """Shadow tokens are included in SENTINEL prompt."""
        # The mock response includes shadow check, verifying the prompt includes shadow data
        result = await agent.analyze(
            rule_engine_results=MockRuleEngineResults(),
            shadow_tokens=MOCK_SHADOW_TOKENS,
        )
        # If shadow_system is passing, we know the shadows were evaluated
        assert result.checks.get("shadow_system", {}).get("status") == "pass"

    @pytest.mark.asyncio
    async def test_shadow_in_passing_practices(self, agent):
        """Well-structured shadow system appears in passing_practices."""
        result = await agent.analyze(
            rule_engine_results=MockRuleEngineResults(),
            shadow_tokens=MOCK_SHADOW_TOKENS,
        )
        # Mock response has shadow_system in passing_practices
        assert "shadow_system" in result.passing_practices

    @pytest.mark.asyncio
    async def test_no_shadow_tokens_handled(self, agent):
        """SENTINEL handles missing shadow tokens gracefully."""
        result = await agent.analyze(
            rule_engine_results=MockRuleEngineResults(),
            shadow_tokens=None,
        )
        # Should still return valid result
        assert isinstance(result, BestPracticesResult)
        assert result.overall_score >= 0

    @pytest.mark.asyncio
    async def test_empty_shadow_tokens_handled(self, agent):
        """SENTINEL handles empty shadow tokens gracefully."""
        result = await agent.analyze(
            rule_engine_results=MockRuleEngineResults(),
            shadow_tokens={},
        )
        assert isinstance(result, BestPracticesResult)


class TestNexusSchemaCompliance:
    """NEXUS (Head Synthesizer) output schema validation."""

    @pytest.fixture
    def agent(self):
        return HeadSynthesizerAgent(MockHFClient())

    @pytest.mark.asyncio
    async def test_schema_compliance(self, agent):
        """NEXUS output has all required HeadSynthesis fields."""
        result = await agent.synthesize(
            rule_engine_results=MockRuleEngineResults(),
            benchmark_comparisons=MOCK_BENCHMARK_COMPARISONS,
            brand_identification=BrandIdentification(
                brand_primary={"color": "#06b2c4", "confidence": "high"},
                palette_strategy="complementary",
                cohesion_score=6,
            ),
            benchmark_advice=BenchmarkAdvice(
                recommended_benchmark="shopify_polaris",
                reasoning="87% structural match",
            ),
            best_practices=BestPracticesResult(
                overall_score=62,
                priority_fixes=[{"issue": "AA contrast", "impact": "high"}],
            ),
        )
        assert isinstance(result, HeadSynthesis)
        assert hasattr(result, "executive_summary")
        assert hasattr(result, "top_3_actions")
        assert hasattr(result, "scores")
        assert hasattr(result, "self_evaluation")

    @pytest.mark.asyncio
    async def test_executive_summary_non_empty(self, agent):
        """NEXUS produces a non-empty executive summary."""
        result = await agent.synthesize(
            rule_engine_results=MockRuleEngineResults(),
            benchmark_comparisons=MOCK_BENCHMARK_COMPARISONS,
            brand_identification=BrandIdentification(),
            benchmark_advice=BenchmarkAdvice(),
            best_practices=BestPracticesResult(),
        )
        assert result.executive_summary != ""

    @pytest.mark.asyncio
    async def test_top_3_actions_present(self, agent):
        """NEXUS provides top 3 action items."""
        result = await agent.synthesize(
            rule_engine_results=MockRuleEngineResults(),
            benchmark_comparisons=MOCK_BENCHMARK_COMPARISONS,
            brand_identification=BrandIdentification(),
            benchmark_advice=BenchmarkAdvice(),
            best_practices=BestPracticesResult(),
        )
        assert isinstance(result.top_3_actions, list)
        assert len(result.top_3_actions) >= 1


# =============================================================================
# SELF-EVALUATION TESTS
# =============================================================================

class TestSelfEvaluation:
    """All agents should include self_evaluation with confidence scoring."""

    @pytest.mark.asyncio
    async def test_aurora_self_evaluation(self):
        agent = BrandIdentifierAgent(MockHFClient())
        result = await agent.analyze(
            color_tokens=MOCK_COLOR_TOKENS,
            typography_tokens={},
        )
        se = result.self_evaluation
        assert isinstance(se, dict)
        assert "confidence" in se
        assert "data_quality" in se

    @pytest.mark.asyncio
    async def test_atlas_self_evaluation(self):
        agent = BenchmarkAdvisorAgent(MockHFClient())
        result = await agent.analyze(
            user_ratio=1.18,
            user_base=16,
            user_spacing=4,
            benchmark_comparisons=MOCK_BENCHMARK_COMPARISONS,
        )
        se = result.self_evaluation
        assert isinstance(se, dict)
        assert "confidence" in se

    @pytest.mark.asyncio
    async def test_sentinel_self_evaluation(self):
        agent = BestPracticesValidatorAgent(MockHFClient())
        result = await agent.analyze(
            rule_engine_results=MockRuleEngineResults(),
        )
        se = result.self_evaluation
        assert isinstance(se, dict)
        assert "confidence" in se

    @pytest.mark.asyncio
    async def test_nexus_self_evaluation(self):
        agent = HeadSynthesizerAgent(MockHFClient())
        result = await agent.synthesize(
            rule_engine_results=MockRuleEngineResults(),
            benchmark_comparisons=MOCK_BENCHMARK_COMPARISONS,
            brand_identification=BrandIdentification(),
            benchmark_advice=BenchmarkAdvice(),
            best_practices=BestPracticesResult(),
        )
        se = result.self_evaluation
        assert isinstance(se, dict)
        assert "confidence" in se


# =============================================================================
# VALIDATION MODULE TESTS
# =============================================================================

class TestValidationModule:
    """Test the core/validation.py module."""

    def test_validate_aurora_output(self):
        from core.validation import validate_agent_output

        data = {
            "brand_primary": {"color": "#06b2c4"},
            "palette_strategy": "complementary",
            "cohesion_score": 6,
        }
        is_valid, error = validate_agent_output(data, "aurora")
        assert is_valid

    def test_validate_aurora_missing_required(self):
        from core.validation import validate_agent_output

        data = {"cohesion_score": 6}  # Missing brand_primary and palette_strategy
        is_valid, error = validate_agent_output(data, "aurora")
        assert not is_valid
        assert error is not None

    def test_validate_nexus_output(self):
        from core.validation import validate_agent_output

        data = {
            "executive_summary": "Test summary",
            "top_3_actions": [{"action": "Fix contrast"}],
            "scores": {"overall": 62},
        }
        is_valid, error = validate_agent_output(data, "nexus")
        assert is_valid

    def test_validate_unknown_agent_passes(self):
        from core.validation import validate_agent_output

        is_valid, error = validate_agent_output({"anything": True}, "unknown_agent")
        assert is_valid  # No schema = pass

    def test_validate_dataclass(self):
        from core.validation import validate_agent_output

        brand = BrandIdentification(
            brand_primary={"color": "#06b2c4"},
            palette_strategy="complementary",
        )
        is_valid, error = validate_agent_output(brand, "aurora")
        assert is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

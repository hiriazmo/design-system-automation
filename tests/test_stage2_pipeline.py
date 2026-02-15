#!/usr/bin/env python3
"""
Stage 2 Pipeline Test Script
============================

Tests the new Stage 2 architecture:
- Layer 1: Rule Engine
- Layer 2: Benchmark Research
- Layer 3: LLM Agents
- Layer 4: HEAD Synthesizer

Run: python tests/test_stage2_pipeline.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Optional

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# TEST DATA - Mock extracted tokens
# =============================================================================

MOCK_TYPOGRAPHY_TOKENS = {
    "heading-1": {"font_size": "48px", "font_weight": "700", "line_height": "1.2", "font_family": "Inter"},
    "heading-2": {"font_size": "36px", "font_weight": "600", "line_height": "1.25", "font_family": "Inter"},
    "heading-3": {"font_size": "28px", "font_weight": "600", "line_height": "1.3", "font_family": "Inter"},
    "heading-4": {"font_size": "22px", "font_weight": "500", "line_height": "1.35", "font_family": "Inter"},
    "body-large": {"font_size": "18px", "font_weight": "400", "line_height": "1.5", "font_family": "Inter"},
    "body": {"font_size": "16px", "font_weight": "400", "line_height": "1.5", "font_family": "Inter"},
    "body-small": {"font_size": "14px", "font_weight": "400", "line_height": "1.5", "font_family": "Inter"},
    "caption": {"font_size": "12px", "font_weight": "400", "line_height": "1.4", "font_family": "Inter"},
}

MOCK_COLOR_TOKENS = {
    "brand-primary": {"value": "#06b2c4", "frequency": 45, "context": "buttons, links"},
    "brand-secondary": {"value": "#c1df1f", "frequency": 23, "context": "highlights, badges"},
    "text-primary": {"value": "#1a1a1a", "frequency": 120, "context": "headings, body"},
    "text-secondary": {"value": "#666666", "frequency": 80, "context": "captions, muted"},
    "text-tertiary": {"value": "#999999", "frequency": 40, "context": "placeholders"},
    "background-primary": {"value": "#ffffff", "frequency": 200, "context": "page background"},
    "background-secondary": {"value": "#f5f5f5", "frequency": 60, "context": "cards, sections"},
    "background-tertiary": {"value": "#e8e8e8", "frequency": 30, "context": "dividers"},
    "border-default": {"value": "#dddddd", "frequency": 50, "context": "borders"},
    "border-focus": {"value": "#06b2c4", "frequency": 15, "context": "focus rings"},
    "success": {"value": "#22c55e", "frequency": 10, "context": "success states"},
    "warning": {"value": "#f59e0b", "frequency": 8, "context": "warning states"},
    "error": {"value": "#ef4444", "frequency": 12, "context": "error states"},
    "info": {"value": "#3b82f6", "frequency": 6, "context": "info states"},
    # Some problematic colors for testing
    "light-cyan": {"value": "#7dd3fc", "frequency": 5, "context": "light accent"},  # Fails AA
    "light-lime": {"value": "#d9f99d", "frequency": 3, "context": "light highlight"},  # Fails AA
}

MOCK_SPACING_TOKENS = {
    "space-1": {"value": "4px", "value_px": 4, "frequency": 30},
    "space-2": {"value": "8px", "value_px": 8, "frequency": 80},
    "space-3": {"value": "12px", "value_px": 12, "frequency": 45},
    "space-4": {"value": "16px", "value_px": 16, "frequency": 60},
    "space-5": {"value": "20px", "value_px": 20, "frequency": 25},
    "space-6": {"value": "24px", "value_px": 24, "frequency": 40},
    "space-8": {"value": "32px", "value_px": 32, "frequency": 20},
    "space-10": {"value": "40px", "value_px": 40, "frequency": 15},
    "space-12": {"value": "48px", "value_px": 48, "frequency": 10},
    # Some misaligned values for testing
    "space-odd-1": {"value": "5px", "value_px": 5, "frequency": 3},
    "space-odd-2": {"value": "10px", "value_px": 10, "frequency": 5},
}

MOCK_SEMANTIC_ANALYSIS = {
    "brand": [{"hex": "#06b2c4", "name": "brand-primary"}, {"hex": "#c1df1f", "name": "brand-secondary"}],
    "text": [{"hex": "#1a1a1a", "name": "text-primary"}, {"hex": "#666666", "name": "text-secondary"}],
    "background": [{"hex": "#ffffff", "name": "background-primary"}, {"hex": "#f5f5f5", "name": "background-secondary"}],
    "border": [{"hex": "#dddddd", "name": "border-default"}],
    "feedback": [{"hex": "#22c55e", "name": "success"}, {"hex": "#ef4444", "name": "error"}],
}


# =============================================================================
# TEST HELPERS
# =============================================================================

class TestLogger:
    """Simple logger for tests."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.logs = []
    
    def log(self, msg: str):
        self.logs.append(msg)
        if self.verbose:
            print(msg)
    
    def get_logs(self) -> str:
        return "\n".join(self.logs)


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def print_result(name: str, passed: bool, details: str = ""):
    """Print a test result."""
    icon = "✅" if passed else "❌"
    print(f"  {icon} {name}")
    if details:
        print(f"     {details}")


# =============================================================================
# LAYER 1: RULE ENGINE TESTS
# =============================================================================

def test_rule_engine():
    """Test the Rule Engine layer."""
    print_section("LAYER 1: RULE ENGINE TESTS")
    
    all_passed = True
    
    try:
        from core.rule_engine import (
            run_rule_engine,
            analyze_type_scale,
            analyze_accessibility,
            analyze_spacing_grid,
            analyze_color_statistics,
        )
        print_result("Import rule_engine", True)
    except Exception as e:
        print_result("Import rule_engine", False, str(e))
        return False
    
    # Test Type Scale Analysis
    try:
        typo_result = analyze_type_scale(MOCK_TYPOGRAPHY_TOKENS)
        
        assert typo_result.detected_ratio > 0, "Ratio should be positive"
        assert typo_result.closest_standard_ratio > 0, "Standard ratio should be positive"
        assert typo_result.scale_name != "", "Scale name should not be empty"
        assert len(typo_result.sizes_px) > 0, "Should detect sizes"
        
        print_result(
            "Type Scale Analysis", 
            True, 
            f"ratio={typo_result.detected_ratio:.3f}, consistent={typo_result.is_consistent}"
        )
    except Exception as e:
        print_result("Type Scale Analysis", False, str(e))
        all_passed = False
    
    # Test Accessibility Analysis
    try:
        access_result = analyze_accessibility(MOCK_COLOR_TOKENS)
        
        assert len(access_result) > 0, "Should analyze colors"
        
        failures = [a for a in access_result if not a.passes_aa_normal]
        passes = len(access_result) - len(failures)
        
        # Check that fixes are generated for failures
        fixes_generated = sum(1 for a in failures if a.suggested_fix)
        
        print_result(
            "Accessibility Analysis",
            True,
            f"total={len(access_result)}, pass={passes}, fail={len(failures)}, fixes={fixes_generated}"
        )
    except Exception as e:
        print_result("Accessibility Analysis", False, str(e))
        all_passed = False
    
    # Test Spacing Grid Analysis
    try:
        spacing_result = analyze_spacing_grid(MOCK_SPACING_TOKENS)
        
        assert spacing_result.detected_base > 0, "Base should be positive"
        assert len(spacing_result.current_values) > 0, "Should detect values"
        assert len(spacing_result.suggested_scale) > 0, "Should suggest scale"
        
        print_result(
            "Spacing Grid Analysis",
            True,
            f"base={spacing_result.detected_base}px, aligned={spacing_result.alignment_percentage:.0f}%"
        )
    except Exception as e:
        print_result("Spacing Grid Analysis", False, str(e))
        all_passed = False
    
    # Test Color Statistics
    try:
        color_stats = analyze_color_statistics(MOCK_COLOR_TOKENS)
        
        assert color_stats.total_count > 0, "Should count colors"
        assert color_stats.unique_count > 0, "Should count unique"
        
        print_result(
            "Color Statistics",
            True,
            f"total={color_stats.total_count}, unique={color_stats.unique_count}, grays={color_stats.gray_count}"
        )
    except Exception as e:
        print_result("Color Statistics", False, str(e))
        all_passed = False
    
    # Test Full Rule Engine
    try:
        logger = TestLogger(verbose=False)
        
        full_result = run_rule_engine(
            typography_tokens=MOCK_TYPOGRAPHY_TOKENS,
            color_tokens=MOCK_COLOR_TOKENS,
            spacing_tokens=MOCK_SPACING_TOKENS,
            log_callback=logger.log,
        )
        
        assert full_result.typography is not None
        assert full_result.accessibility is not None
        assert full_result.spacing is not None
        assert full_result.color_stats is not None
        assert 0 <= full_result.consistency_score <= 100
        
        print_result(
            "Full Rule Engine",
            True,
            f"consistency_score={full_result.consistency_score}, aa_failures={full_result.aa_failures}"
        )
        
        # Check logs were generated
        log_lines = len(logger.logs)
        print_result("Log Generation", log_lines > 10, f"{log_lines} log lines")
        
    except Exception as e:
        print_result("Full Rule Engine", False, str(e))
        all_passed = False
    
    return all_passed


# =============================================================================
# LAYER 2: BENCHMARK RESEARCH TESTS
# =============================================================================

def test_benchmark_research():
    """Test the Benchmark Research layer."""
    print_section("LAYER 2: BENCHMARK RESEARCH TESTS")
    
    all_passed = True
    
    try:
        from agents.benchmark_researcher import (
            BenchmarkResearcher,
            BenchmarkCache,
            DESIGN_SYSTEM_SOURCES,
            FALLBACK_BENCHMARKS,
            get_available_benchmarks,
            get_benchmark_choices,
        )
        print_result("Import benchmark_researcher", True)
    except Exception as e:
        print_result("Import benchmark_researcher", False, str(e))
        return False
    
    # Test Design System Sources
    try:
        assert len(DESIGN_SYSTEM_SOURCES) >= 6, "Should have at least 6 design systems"
        
        required_systems = ["material_design_3", "shopify_polaris", "atlassian_design"]
        for sys in required_systems:
            assert sys in DESIGN_SYSTEM_SOURCES, f"Missing {sys}"
            assert "urls" in DESIGN_SYSTEM_SOURCES[sys], f"Missing URLs for {sys}"
            assert "best_for" in DESIGN_SYSTEM_SOURCES[sys], f"Missing best_for for {sys}"
        
        print_result("Design System Sources", True, f"{len(DESIGN_SYSTEM_SOURCES)} systems defined")
    except Exception as e:
        print_result("Design System Sources", False, str(e))
        all_passed = False
    
    # Test Fallback Benchmarks
    try:
        assert len(FALLBACK_BENCHMARKS) >= 6, "Should have fallbacks"
        
        for key, fallback in FALLBACK_BENCHMARKS.items():
            assert "typography" in fallback, f"Missing typography for {key}"
            assert "spacing" in fallback, f"Missing spacing for {key}"
            assert fallback["typography"].get("scale_ratio"), f"Missing scale_ratio for {key}"
        
        print_result("Fallback Benchmarks", True, f"{len(FALLBACK_BENCHMARKS)} fallbacks defined")
    except Exception as e:
        print_result("Fallback Benchmarks", False, str(e))
        all_passed = False
    
    # Test Cache
    try:
        cache = BenchmarkCache()
        
        # Test set/get
        from agents.benchmark_researcher import BenchmarkData
        test_data = BenchmarkData(
            key="test_system",
            name="Test System",
            short_name="Test",
            vendor="Test Vendor",
            icon="🧪",
            typography={"scale_ratio": 1.25, "base_size": 16},
            spacing={"base": 8},
            fetched_at=datetime.now().isoformat(),
            confidence="high",
        )
        
        cache.set("test_system", test_data)
        retrieved = cache.get("test_system")
        
        assert retrieved is not None, "Should retrieve cached data"
        assert retrieved.typography.get("scale_ratio") == 1.25, "Data should match"
        
        print_result("Benchmark Cache", True, "set/get working")
    except Exception as e:
        print_result("Benchmark Cache", False, str(e))
        all_passed = False
    
    # Test Helper Functions
    try:
        benchmarks = get_available_benchmarks()
        assert len(benchmarks) >= 6, "Should list benchmarks"
        assert all("key" in b and "name" in b for b in benchmarks)
        
        choices = get_benchmark_choices()
        assert len(choices) >= 6, "Should have choices"
        assert all(isinstance(c, tuple) and len(c) == 2 for c in choices)
        
        print_result("Helper Functions", True, f"{len(benchmarks)} benchmarks available")
    except Exception as e:
        print_result("Helper Functions", False, str(e))
        all_passed = False
    
    # Test Researcher Initialization
    try:
        researcher = BenchmarkResearcher(firecrawl_client=None, hf_client=None)
        assert researcher.cache is not None
        
        print_result("Researcher Initialization", True, "initialized without clients")
    except Exception as e:
        print_result("Researcher Initialization", False, str(e))
        all_passed = False
    
    # Test Comparison Logic (with fallback data)
    try:
        researcher = BenchmarkResearcher(firecrawl_client=None, hf_client=None)
        
        # Create mock benchmark data
        from agents.benchmark_researcher import BenchmarkData
        mock_benchmarks = []
        for key in ["material_design_3", "shopify_polaris", "atlassian_design"]:
            source = DESIGN_SYSTEM_SOURCES[key]
            fallback = FALLBACK_BENCHMARKS[key]
            mock_benchmarks.append(BenchmarkData(
                key=key,
                name=source["name"],
                short_name=source["short_name"],
                vendor=source["vendor"],
                icon=source["icon"],
                typography=fallback["typography"],
                spacing=fallback["spacing"],
                fetched_at=datetime.now().isoformat(),
                confidence="fallback",
                best_for=source["best_for"],
            ))
        
        comparisons = researcher.compare_to_benchmarks(
            your_ratio=1.18,
            your_base_size=16,
            your_spacing_grid=8,
            benchmarks=mock_benchmarks,
            log_callback=lambda x: None,
        )
        
        assert len(comparisons) == 3, "Should have 3 comparisons"
        assert comparisons[0].similarity_score <= comparisons[1].similarity_score, "Should be sorted"
        
        print_result(
            "Comparison Logic",
            True,
            f"closest={comparisons[0].benchmark.short_name}, score={comparisons[0].similarity_score:.2f}"
        )
    except Exception as e:
        print_result("Comparison Logic", False, str(e))
        all_passed = False
    
    return all_passed


# =============================================================================
# LAYER 3: LLM AGENTS TESTS
# =============================================================================

def test_llm_agents():
    """Test the LLM Agents layer."""
    print_section("LAYER 3: LLM AGENTS TESTS")
    
    all_passed = True
    
    try:
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
        print_result("Import llm_agents", True)
    except Exception as e:
        print_result("Import llm_agents", False, str(e))
        return False
    
    # Test Data Classes
    try:
        brand = BrandIdentification(
            brand_primary={"color": "#06b2c4", "confidence": "high"},
            cohesion_score=7,
        )
        assert brand.to_dict()["brand_primary"]["color"] == "#06b2c4"
        
        advice = BenchmarkAdvice(
            recommended_benchmark="shopify_polaris",
            reasoning="Best fit for e-commerce",
        )
        assert advice.to_dict()["recommended_benchmark"] == "shopify_polaris"
        
        practices = BestPracticesResult(
            overall_score=65,
            priority_fixes=[{"issue": "AA compliance", "impact": "high"}],
        )
        assert practices.to_dict()["overall_score"] == 65
        
        synthesis = HeadSynthesis(
            executive_summary="Test summary",
            scores={"overall": 60},
        )
        assert synthesis.to_dict()["scores"]["overall"] == 60
        
        print_result("Data Classes", True, "all serializable")
    except Exception as e:
        print_result("Data Classes", False, str(e))
        all_passed = False
    
    # Test Agent Initialization (without HF client)
    try:
        brand_agent = BrandIdentifierAgent(hf_client=None)
        benchmark_agent = BenchmarkAdvisorAgent(hf_client=None)
        practices_agent = BestPracticesValidatorAgent(hf_client=None)
        head_agent = HeadSynthesizerAgent(hf_client=None)
        
        print_result("Agent Initialization", True, "all agents created")
    except Exception as e:
        print_result("Agent Initialization", False, str(e))
        all_passed = False
    
    # Test Prompt Templates exist
    try:
        assert hasattr(BrandIdentifierAgent, 'PROMPT_TEMPLATE')
        assert hasattr(BenchmarkAdvisorAgent, 'PROMPT_TEMPLATE')
        assert hasattr(BestPracticesValidatorAgent, 'PROMPT_TEMPLATE')
        assert hasattr(HeadSynthesizerAgent, 'PROMPT_TEMPLATE')
        
        # Check templates have placeholders
        assert "{color_data}" in BrandIdentifierAgent.PROMPT_TEMPLATE
        assert "{user_ratio}" in BenchmarkAdvisorAgent.PROMPT_TEMPLATE
        assert "{type_ratio}" in BestPracticesValidatorAgent.PROMPT_TEMPLATE
        assert "{type_ratio}" in HeadSynthesizerAgent.PROMPT_TEMPLATE
        
        print_result("Prompt Templates", True, "all templates defined with placeholders")
    except Exception as e:
        print_result("Prompt Templates", False, str(e))
        all_passed = False
    
    return all_passed


# =============================================================================
# INTEGRATION TEST
# =============================================================================

@pytest.mark.asyncio
async def test_integration():
    """Test the full pipeline integration (without actual LLM calls)."""
    print_section("INTEGRATION TEST")
    
    all_passed = True
    
    # Test full Rule Engine + Benchmark comparison flow
    try:
        from core.rule_engine import run_rule_engine
        from agents.benchmark_researcher import (
            BenchmarkResearcher, 
            BenchmarkData, 
            DESIGN_SYSTEM_SOURCES, 
            FALLBACK_BENCHMARKS
        )
        from agents.llm_agents import (
            BrandIdentification,
            BenchmarkAdvice,
            BestPracticesResult,
            HeadSynthesis,
        )
        
        logger = TestLogger(verbose=False)
        
        # Step 1: Run Rule Engine
        rule_results = run_rule_engine(
            typography_tokens=MOCK_TYPOGRAPHY_TOKENS,
            color_tokens=MOCK_COLOR_TOKENS,
            spacing_tokens=MOCK_SPACING_TOKENS,
            log_callback=logger.log,
        )
        
        print_result("Step 1: Rule Engine", True, f"score={rule_results.consistency_score}")
        
        # Step 2: Benchmark Research (using fallbacks)
        researcher = BenchmarkResearcher(firecrawl_client=None, hf_client=None)
        
        mock_benchmarks = []
        for key in ["material_design_3", "shopify_polaris", "atlassian_design"]:
            source = DESIGN_SYSTEM_SOURCES[key]
            fallback = FALLBACK_BENCHMARKS[key]
            mock_benchmarks.append(BenchmarkData(
                key=key,
                name=source["name"],
                short_name=source["short_name"],
                vendor=source["vendor"],
                icon=source["icon"],
                typography=fallback["typography"],
                spacing=fallback["spacing"],
                fetched_at=datetime.now().isoformat(),
                confidence="fallback",
                best_for=source["best_for"],
            ))
        
        comparisons = researcher.compare_to_benchmarks(
            your_ratio=rule_results.typography.detected_ratio,
            your_base_size=int(rule_results.typography.sizes_px[0]) if rule_results.typography.sizes_px else 16,
            your_spacing_grid=rule_results.spacing.detected_base,
            benchmarks=mock_benchmarks,
            log_callback=logger.log,
        )
        
        print_result("Step 2: Benchmark Comparison", True, f"closest={comparisons[0].benchmark.short_name}")
        
        # Step 3: Mock LLM results (simulating what agents would return)
        brand_result = BrandIdentification(
            brand_primary={"color": "#06b2c4", "confidence": "high", "reasoning": "Most used on CTAs"},
            brand_secondary={"color": "#c1df1f", "confidence": "medium"},
            palette_strategy="complementary",
            cohesion_score=7,
        )
        
        benchmark_advice = BenchmarkAdvice(
            recommended_benchmark="shopify_polaris",
            recommended_benchmark_name="Shopify Polaris",
            reasoning="Best match for e-commerce UX",
            alignment_changes=[
                {"change": "Type scale", "from": "1.18", "to": "1.25", "effort": "medium"}
            ],
        )
        
        best_practices = BestPracticesResult(
            overall_score=58,
            checks={
                "type_scale_standard": {"status": "warn", "note": "1.18 close to Minor Third"},
                "aa_compliance": {"status": "fail", "note": "2 colors fail AA"},
            },
            priority_fixes=[
                {"rank": 1, "issue": "Brand primary fails AA", "impact": "high", "effort": "low"},
            ],
        )
        
        print_result("Step 3: Mock LLM Results", True, "all results created")
        
        # Step 4: Verify data can be serialized
        output = {
            "rule_engine": rule_results.to_dict(),
            "benchmarks": [c.to_dict() for c in comparisons],
            "brand": brand_result.to_dict(),
            "advice": benchmark_advice.to_dict(),
            "practices": best_practices.to_dict(),
        }
        
        json_str = json.dumps(output, indent=2)
        assert len(json_str) > 100, "Should produce substantial output"
        
        print_result("Step 4: Serialization", True, f"{len(json_str)} bytes")
        
        # Final summary
        print("\n  📊 Integration Summary:")
        print(f"     - Rule Engine Score: {rule_results.consistency_score}/100")
        print(f"     - AA Failures: {rule_results.aa_failures}")
        print(f"     - Closest Benchmark: {comparisons[0].benchmark.name}")
        print(f"     - Match: {comparisons[0].overall_match_pct:.0f}%")
        
        all_passed = True
        
    except Exception as e:
        import traceback
        print_result("Integration Test", False, str(e))
        traceback.print_exc()
        all_passed = False
    
    return all_passed


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all tests."""
    print("\n" + "█" * 60)
    print("  STAGE 2 PIPELINE TEST SUITE")
    print("█" * 60)
    print(f"\n  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run tests
    results["Rule Engine"] = test_rule_engine()
    results["Benchmark Research"] = test_benchmark_research()
    results["LLM Agents"] = test_llm_agents()
    results["Integration"] = asyncio.run(test_integration())
    
    # Summary
    print_section("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for name, result in results.items():
        icon = "✅" if result else "❌"
        print(f"  {icon} {name}")
    
    print(f"\n  Total: {passed}/{total} passed")
    
    if passed == total:
        print("\n  🎉 All tests passed!")
        return 0
    else:
        print("\n  ⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

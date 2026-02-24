"""
Core utilities for Design System Automation.
"""

from core.token_schema import (
    TokenSource,
    Confidence,
    Viewport,
    PageType,
    ColorToken,
    TypographyToken,
    SpacingToken,
    RadiusToken,
    ShadowToken,
    ExtractedTokens,
    NormalizedTokens,
    FinalTokens,
    WorkflowState,
)

from core.color_utils import (
    parse_color,
    normalize_hex,
    get_contrast_ratio,
    check_wcag_compliance,
    generate_color_ramp,
    generate_accessible_ramp,
    categorize_color,
    suggest_color_name,
)

from core.rule_engine import (
    run_rule_engine,
    analyze_type_scale,
    analyze_accessibility,
    analyze_spacing_grid,
    analyze_color_statistics,
    TypeScaleAnalysis,
    ColorAccessibility,
    SpacingGridAnalysis,
    ColorStatistics,
    RuleEngineResults,
)

# HF Inference is imported lazily to avoid circular imports
# Use: from core.hf_inference import get_inference_client

__all__ = [
    # Enums
    "TokenSource",
    "Confidence",
    "Viewport",
    "PageType",
    # Token models
    "ColorToken",
    "TypographyToken",
    "SpacingToken",
    "RadiusToken",
    "ShadowToken",
    # Result models
    "ExtractedTokens",
    "NormalizedTokens",
    "FinalTokens",
    "WorkflowState",
    # Color utilities
    "parse_color",
    "normalize_hex",
    "get_contrast_ratio",
    "check_wcag_compliance",
    "generate_color_ramp",
    "generate_accessible_ramp",
    "categorize_color",
    "suggest_color_name",
    # Rule Engine
    "run_rule_engine",
    "analyze_type_scale",
    "analyze_accessibility",
    "analyze_spacing_grid",
    "analyze_color_statistics",
    "TypeScaleAnalysis",
    "ColorAccessibility",
    "SpacingGridAnalysis",
    "ColorStatistics",
    "RuleEngineResults",
]

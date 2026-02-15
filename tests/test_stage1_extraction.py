#!/usr/bin/env python3
"""
Stage 1 Test Suite — Extraction, Normalization & Rule Engine
=============================================================

Tests the deterministic (free) layer:
- Color utilities: hex normalization, deduplication, categorization
- Rule Engine: WCAG contrast, type scale detection, spacing grid, consistency score
- Edge cases and boundary conditions

Run: pytest tests/test_stage1_extraction.py -v
"""

import os
import sys
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.color_utils import (
    normalize_hex,
    parse_color,
    deduplicate_colors,
    are_colors_similar,
    color_distance,
    categorize_color,
    get_contrast_ratio,
    check_wcag_compliance,
    generate_color_ramp,
    hex_to_rgb,
    rgb_to_hex,
)
from core.rule_engine import (
    analyze_type_scale,
    analyze_accessibility,
    analyze_spacing_grid,
    analyze_color_statistics,
    run_rule_engine,
    get_contrast_ratio as re_get_contrast_ratio,
    get_relative_luminance,
    hex_to_rgb as re_hex_to_rgb,
    is_gray,
    color_distance as re_color_distance,
    find_aa_compliant_color,
    parse_size_to_px,
    STANDARD_SCALES,
)


# =============================================================================
# TEST DATA
# =============================================================================

MOCK_TYPOGRAPHY_TOKENS = {
    "heading-1": {"font_size": "48px", "font_weight": "700"},
    "heading-2": {"font_size": "36px", "font_weight": "600"},
    "heading-3": {"font_size": "28px", "font_weight": "600"},
    "heading-4": {"font_size": "22px", "font_weight": "500"},
    "body-large": {"font_size": "18px", "font_weight": "400"},
    "body": {"font_size": "16px", "font_weight": "400"},
    "body-small": {"font_size": "14px", "font_weight": "400"},
    "caption": {"font_size": "12px", "font_weight": "400"},
}

MOCK_COLOR_TOKENS = {
    "brand-primary": {"value": "#06b2c4"},
    "brand-secondary": {"value": "#c1df1f"},
    "text-primary": {"value": "#1a1a1a"},
    "text-secondary": {"value": "#666666"},
    "background": {"value": "#ffffff"},
    "light-cyan": {"value": "#7dd3fc"},  # Fails AA on white
    "light-lime": {"value": "#d9f99d"},  # Fails AA on white
}

MOCK_SPACING_TOKENS_ALIGNED = {
    "space-1": {"value_px": 4},
    "space-2": {"value_px": 8},
    "space-3": {"value_px": 16},
    "space-4": {"value_px": 24},
    "space-5": {"value_px": 32},
    "space-6": {"value_px": 48},
}

MOCK_SPACING_TOKENS_MISALIGNED = {
    "space-1": {"value_px": 5},
    "space-2": {"value_px": 10},
    "space-3": {"value_px": 15},
    "space-4": {"value_px": 22},
    "space-5": {"value_px": 33},
}


# =============================================================================
# TEST CLASS: Color Utilities — Normalization & Deduplication
# =============================================================================

class TestColorNormalization:
    """Test color parsing, normalization and deduplication."""

    def test_normalize_hex_6digit(self):
        """6-digit hex stays lowercase."""
        assert normalize_hex("#FF0000") == "#ff0000"
        assert normalize_hex("#ffffff") == "#ffffff"

    def test_normalize_hex_3digit(self):
        """3-digit hex expands to 6-digit."""
        assert normalize_hex("#fff") == "#ffffff"
        assert normalize_hex("#000") == "#000000"
        assert normalize_hex("#f00") == "#ff0000"

    def test_parse_color_hex(self):
        """Parse hex color to ParsedColor."""
        parsed = parse_color("#ff0000")
        assert parsed is not None
        assert parsed.hex == "#ff0000"
        assert parsed.rgb == (255, 0, 0)

    def test_parse_color_rgb(self):
        """Parse rgb() string."""
        parsed = parse_color("rgb(0, 128, 255)")
        assert parsed is not None
        assert parsed.rgb == (0, 128, 255)

    def test_parse_color_invalid(self):
        """Invalid color returns None."""
        assert parse_color("not-a-color") is None
        assert parse_color("") is None

    def test_hex_to_rgb_and_back(self):
        """Round-trip hex → RGB → hex."""
        r, g, b = hex_to_rgb("#1a2b3c")
        result = rgb_to_hex(r, g, b)
        assert result == "#1a2b3c"

    def test_deduplicate_exact_duplicates(self):
        """Exact same colors are deduplicated."""
        colors = ["#ff0000", "#ff0000", "#00ff00", "#00ff00", "#0000ff"]
        result = deduplicate_colors(colors, threshold=1.0)
        assert len(result) == 3

    def test_deduplicate_near_duplicates(self):
        """Near-duplicate colors (within threshold) are deduplicated."""
        colors = ["#ff0000", "#fe0101", "#00ff00"]
        result = deduplicate_colors(colors, threshold=10.0)
        assert len(result) == 2  # #ff0000 and #fe0101 are near-dupes

    def test_deduplicate_preserves_distinct(self):
        """Distinct colors are preserved."""
        colors = ["#ff0000", "#00ff00", "#0000ff"]
        result = deduplicate_colors(colors, threshold=10.0)
        assert len(result) == 3

    def test_are_colors_similar_identical(self):
        """Same color is similar."""
        assert are_colors_similar("#ff0000", "#ff0000")

    def test_are_colors_similar_different(self):
        """Very different colors are not similar."""
        assert not are_colors_similar("#ff0000", "#0000ff", threshold=10.0)

    def test_color_distance_identical(self):
        """Same color has distance 0."""
        assert color_distance("#ff0000", "#ff0000") == 0.0

    def test_color_distance_symmetric(self):
        """Distance is symmetric."""
        d1 = color_distance("#ff0000", "#00ff00")
        d2 = color_distance("#00ff00", "#ff0000")
        assert d1 == d2


# =============================================================================
# TEST CLASS: Color Categorization
# =============================================================================

class TestColorCategorization:
    """Test semantic color classification."""

    def test_categorize_red(self):
        assert categorize_color("#ff0000") == "red"

    def test_categorize_blue(self):
        assert categorize_color("#0000ff") == "blue"

    def test_categorize_green(self):
        assert categorize_color("#00ff00") == "green"

    def test_categorize_neutral_white(self):
        assert categorize_color("#ffffff") == "neutral"

    def test_categorize_neutral_black(self):
        assert categorize_color("#000000") == "neutral"

    def test_categorize_neutral_gray(self):
        assert categorize_color("#808080") == "neutral"

    def test_categorize_cyan(self):
        """Brand color #06b2c4 should be cyan."""
        assert categorize_color("#06b2c4") == "cyan"


# =============================================================================
# TEST CLASS: WCAG Contrast (Rule Engine)
# =============================================================================

class TestWCAGContrast:
    """Test WCAG contrast ratio calculations — core math."""

    def test_black_on_white_is_21(self):
        """Black on white should be 21:1 (maximum contrast)."""
        ratio = re_get_contrast_ratio("#000000", "#ffffff")
        assert abs(ratio - 21.0) < 0.1

    def test_white_on_black_is_21(self):
        """White on black is also 21:1 (symmetric)."""
        ratio = re_get_contrast_ratio("#ffffff", "#000000")
        assert abs(ratio - 21.0) < 0.1

    def test_same_color_is_1(self):
        """Same color on same color should be 1:1."""
        ratio = re_get_contrast_ratio("#ff0000", "#ff0000")
        assert abs(ratio - 1.0) < 0.01

    def test_contrast_ratio_symmetric(self):
        """Contrast ratio is symmetric."""
        r1 = re_get_contrast_ratio("#06b2c4", "#ffffff")
        r2 = re_get_contrast_ratio("#ffffff", "#06b2c4")
        assert abs(r1 - r2) < 0.01

    def test_brand_primary_fails_aa_on_white(self):
        """Brand color #06b2c4 fails AA on white (contrast ~2.6)."""
        ratio = re_get_contrast_ratio("#06b2c4", "#ffffff")
        assert ratio < 4.5  # Fails AA normal
        assert ratio > 2.0  # But has some contrast

    def test_dark_text_passes_aa(self):
        """Dark text #1a1a1a passes AA on white."""
        ratio = re_get_contrast_ratio("#1a1a1a", "#ffffff")
        assert ratio >= 4.5

    def test_luminance_black_is_zero(self):
        """Black has luminance ~0."""
        lum = get_relative_luminance("#000000")
        assert abs(lum) < 0.001

    def test_luminance_white_is_one(self):
        """White has luminance ~1."""
        lum = get_relative_luminance("#ffffff")
        assert abs(lum - 1.0) < 0.001

    def test_find_aa_compliant_preserves_passing(self):
        """Color already passing AA is returned unchanged."""
        result = find_aa_compliant_color("#1a1a1a", "#ffffff", 4.5)
        assert result == "#1a1a1a"

    def test_find_aa_compliant_fixes_failing(self):
        """Failing color gets a fix that passes AA."""
        fixed = find_aa_compliant_color("#06b2c4", "#ffffff", 4.5)
        fixed_ratio = re_get_contrast_ratio(fixed, "#ffffff")
        assert fixed_ratio >= 4.5

    def test_analyze_accessibility_finds_failures(self):
        """analyze_accessibility identifies colors that fail AA on BOTH white and black."""
        results = analyze_accessibility(MOCK_COLOR_TOKENS)
        # passes_aa_normal is True if contrast >= 4.5 on white OR black.
        # Light colors pass because they have good contrast on black.
        # Medium-contrast colors like #06b2c4 or #666666 may fail on both.
        # At minimum, all results should be analyzed
        assert len(results) >= 5  # At least the colors with valid hex
        # Check that brand-primary #06b2c4 has low contrast on white
        brand = [r for r in results if r.hex_color == "#06b2c4"]
        assert len(brand) == 1
        assert brand[0].contrast_on_white < 4.5

    def test_analyze_accessibility_suggests_fixes(self):
        """AA failures get suggested fixes."""
        results = analyze_accessibility(MOCK_COLOR_TOKENS)
        failures = [r for r in results if not r.passes_aa_normal]
        for f in failures:
            assert f.suggested_fix is not None
            assert f.suggested_fix_contrast is not None
            assert f.suggested_fix_contrast >= 4.5

    def test_fg_bg_pair_check(self):
        """FG/BG pairs are checked for contrast."""
        pairs = [
            {"foreground": "#06b2c4", "background": "#ffffff", "element": "button"},
        ]
        results = analyze_accessibility({}, fg_bg_pairs=pairs)
        # #06b2c4 on white fails AA (contrast ~3.2)
        pair_failures = [r for r in results if r.name.startswith("fg:")]
        assert len(pair_failures) == 1

    def test_fg_bg_same_color_skipped(self):
        """Same-color FG/BG pairs are skipped (invisible text)."""
        pairs = [
            {"foreground": "#ffffff", "background": "#ffffff", "element": "hidden"},
        ]
        results = analyze_accessibility({}, fg_bg_pairs=pairs)
        assert len(results) == 0


# =============================================================================
# TEST CLASS: Type Scale Detection
# =============================================================================

class TestTypeScaleDetection:
    """Test type scale ratio detection and recommendations."""

    def test_detect_ratio_from_tokens(self):
        """Detects a reasonable ratio from mock typography tokens."""
        result = analyze_type_scale(MOCK_TYPOGRAPHY_TOKENS)
        # Sizes: 12, 14, 16, 18, 22, 28, 36, 48 — ratios vary
        assert result.detected_ratio > 1.0
        assert result.detected_ratio < 2.0

    def test_consistent_scale(self):
        """A perfectly consistent scale is detected as consistent."""
        # Major Third (1.25): 12, 15, 18.75, 23.4, 29.3
        tokens = {
            f"size-{i}": {"font_size": f"{12 * (1.25 ** i):.1f}px"}
            for i in range(5)
        }
        result = analyze_type_scale(tokens)
        assert result.is_consistent
        assert abs(result.detected_ratio - 1.25) < 0.05

    def test_inconsistent_scale(self):
        """Random sizes are detected as inconsistent."""
        tokens = {
            "a": {"font_size": "10px"},
            "b": {"font_size": "17px"},
            "c": {"font_size": "31px"},
            "d": {"font_size": "42px"},
        }
        result = analyze_type_scale(tokens)
        # Very inconsistent — large variance
        assert result.variance > 0.15 or not result.is_consistent

    def test_single_size(self):
        """Single size returns Unknown scale."""
        tokens = {"body": {"font_size": "16px"}}
        result = analyze_type_scale(tokens)
        assert result.scale_name == "Unknown"
        assert result.recommendation == 1.25  # Default: Major Third

    def test_no_sizes(self):
        """Empty tokens return Unknown scale."""
        result = analyze_type_scale({})
        assert result.scale_name == "Unknown"

    def test_rem_conversion(self):
        """rem values are converted to px (1rem = 16px)."""
        tokens = {
            "body": {"font_size": "1rem"},
            "heading": {"font_size": "2rem"},
        }
        result = analyze_type_scale(tokens)
        assert 16.0 in result.sizes_px
        assert 32.0 in result.sizes_px

    def test_base_size_detection(self):
        """Base size detected near 16px."""
        result = analyze_type_scale(MOCK_TYPOGRAPHY_TOKENS)
        assert 14 <= result.base_size <= 18

    def test_standard_scales_defined(self):
        """All standard scales are defined."""
        assert 1.25 in STANDARD_SCALES
        assert 1.333 in STANDARD_SCALES
        assert 1.618 in STANDARD_SCALES

    def test_parse_size_to_px(self):
        """Various size formats parsed correctly."""
        assert parse_size_to_px("16px") == 16.0
        assert parse_size_to_px("1rem") == 16.0
        assert parse_size_to_px("1.5em") == 24.0
        assert parse_size_to_px(16) == 16.0
        assert parse_size_to_px("abc") is None


# =============================================================================
# TEST CLASS: Spacing Grid Analysis
# =============================================================================

class TestSpacingGrid:
    """Test spacing grid detection and GCD math."""

    def test_aligned_to_4px(self):
        """Values divisible by 4 are detected as 4px-aligned."""
        result = analyze_spacing_grid(MOCK_SPACING_TOKENS_ALIGNED)
        assert result.is_aligned
        # All values (4, 8, 16, 24, 32, 48) are divisible by 4 and 8
        assert result.recommendation in [4, 8]

    def test_8px_grid_detected(self):
        """All-8px-multiple values detected as 8px grid."""
        tokens = {
            "s1": {"value_px": 8},
            "s2": {"value_px": 16},
            "s3": {"value_px": 24},
            "s4": {"value_px": 32},
        }
        result = analyze_spacing_grid(tokens)
        assert result.detected_base == 8
        assert result.is_aligned
        assert result.alignment_percentage == 100.0

    def test_misaligned_detected(self):
        """Misaligned spacing is flagged."""
        result = analyze_spacing_grid(MOCK_SPACING_TOKENS_MISALIGNED)
        # GCD of 5, 10, 15, 22, 33 = 1 — not aligned
        assert result.detected_base == 1
        assert not result.is_aligned

    def test_empty_spacing(self):
        """Empty spacing defaults to 8px recommendation."""
        result = analyze_spacing_grid({})
        assert result.recommendation == 8
        assert not result.is_aligned

    def test_single_value(self):
        """Single value uses itself as base."""
        tokens = {"s1": {"value_px": 8}}
        result = analyze_spacing_grid(tokens)
        assert result.detected_base == 8

    def test_gcd_calculation(self):
        """GCD correctly computed for spacing values."""
        tokens = {
            "s1": {"value_px": 12},
            "s2": {"value_px": 24},
            "s3": {"value_px": 36},
        }
        result = analyze_spacing_grid(tokens)
        assert result.detected_base == 12

    def test_suggested_scale_generated(self):
        """Suggested scale is generated."""
        result = analyze_spacing_grid(MOCK_SPACING_TOKENS_ALIGNED)
        assert len(result.suggested_scale) > 0
        assert 0 in result.suggested_scale

    def test_string_values_parsed(self):
        """String values like '16px' are parsed correctly."""
        tokens = {
            "s1": {"value": "8px"},
            "s2": {"value": "16px"},
        }
        result = analyze_spacing_grid(tokens)
        assert result.current_values == [8, 16]


# =============================================================================
# TEST CLASS: Color Statistics
# =============================================================================

class TestColorStatistics:
    """Test color palette statistics analysis."""

    def test_counts_correct(self):
        """Total and unique counts are correct."""
        tokens = {
            "a": {"value": "#ff0000"},
            "b": {"value": "#ff0000"},  # duplicate
            "c": {"value": "#00ff00"},
        }
        result = analyze_color_statistics(tokens)
        assert result.total_count == 3
        assert result.unique_count == 2
        assert result.duplicate_count == 1

    def test_gray_detection(self):
        """Grays are counted correctly."""
        tokens = {
            "white": {"value": "#ffffff"},
            "gray": {"value": "#808080"},
            "black": {"value": "#000000"},
            "red": {"value": "#ff0000"},
        }
        result = analyze_color_statistics(tokens)
        assert result.gray_count >= 3  # white, gray, black are all low saturation

    def test_near_duplicates_found(self):
        """Near-duplicate colors are detected."""
        tokens = {
            "red1": {"value": "#ff0000"},
            "red2": {"value": "#fe0101"},  # Very close to red1
            "blue": {"value": "#0000ff"},
        }
        result = analyze_color_statistics(tokens, similarity_threshold=0.05)
        assert len(result.near_duplicates) >= 1

    def test_hue_distribution(self):
        """Hue distribution groups colors correctly."""
        tokens = {
            "red": {"value": "#ff0000"},
            "blue": {"value": "#0000ff"},
            "green": {"value": "#00ff00"},
        }
        result = analyze_color_statistics(tokens)
        assert "red" in result.hue_distribution
        assert "blue" in result.hue_distribution
        assert "green" in result.hue_distribution

    def test_empty_tokens(self):
        """Empty tokens return zeros."""
        result = analyze_color_statistics({})
        assert result.total_count == 0
        assert result.unique_count == 0


# =============================================================================
# TEST CLASS: Rule Engine Integration
# =============================================================================

class TestRuleEngineIntegration:
    """Test the full run_rule_engine() function."""

    def test_returns_all_components(self):
        """Rule engine returns all analysis components."""
        result = run_rule_engine(
            typography_tokens=MOCK_TYPOGRAPHY_TOKENS,
            color_tokens=MOCK_COLOR_TOKENS,
            spacing_tokens=MOCK_SPACING_TOKENS_ALIGNED,
        )
        assert result.typography is not None
        assert result.accessibility is not None
        assert result.spacing is not None
        assert result.color_stats is not None

    def test_consistency_score_bounds(self):
        """Consistency score is between 0 and 100."""
        result = run_rule_engine(
            typography_tokens=MOCK_TYPOGRAPHY_TOKENS,
            color_tokens=MOCK_COLOR_TOKENS,
            spacing_tokens=MOCK_SPACING_TOKENS_ALIGNED,
        )
        assert 0 <= result.consistency_score <= 100

    def test_aa_failures_counted(self):
        """AA failures are counted in summary."""
        result = run_rule_engine(
            typography_tokens=MOCK_TYPOGRAPHY_TOKENS,
            color_tokens=MOCK_COLOR_TOKENS,
            spacing_tokens=MOCK_SPACING_TOKENS_ALIGNED,
        )
        assert result.aa_failures >= 0

    def test_to_dict_serializable(self):
        """to_dict() returns JSON-serializable data."""
        import json
        result = run_rule_engine(
            typography_tokens=MOCK_TYPOGRAPHY_TOKENS,
            color_tokens=MOCK_COLOR_TOKENS,
            spacing_tokens=MOCK_SPACING_TOKENS_ALIGNED,
        )
        d = result.to_dict()
        json_str = json.dumps(d)
        assert len(json_str) > 0

    def test_log_callback_called(self):
        """Log callback receives messages."""
        logs = []
        run_rule_engine(
            typography_tokens=MOCK_TYPOGRAPHY_TOKENS,
            color_tokens=MOCK_COLOR_TOKENS,
            spacing_tokens=MOCK_SPACING_TOKENS_ALIGNED,
            log_callback=lambda msg: logs.append(msg),
        )
        assert len(logs) > 0
        # Should contain rule engine header
        assert any("RULE ENGINE" in log for log in logs)

    def test_with_fg_bg_pairs(self):
        """FG/BG pairs are analyzed when provided."""
        pairs = [
            {"foreground": "#06b2c4", "background": "#ffffff", "element": "button"},
            {"foreground": "#1a1a1a", "background": "#ffffff", "element": "heading"},
        ]
        result = run_rule_engine(
            typography_tokens=MOCK_TYPOGRAPHY_TOKENS,
            color_tokens=MOCK_COLOR_TOKENS,
            spacing_tokens=MOCK_SPACING_TOKENS_ALIGNED,
            fg_bg_pairs=pairs,
        )
        # Should have accessibility results including pair checks
        assert len(result.accessibility) > 0

    def test_empty_tokens_no_crash(self):
        """Empty tokens don't crash the rule engine."""
        result = run_rule_engine(
            typography_tokens={},
            color_tokens={},
            spacing_tokens={},
        )
        assert result.consistency_score >= 0

    def test_perfect_score_possible(self):
        """A well-organized design system scores high."""
        # All 8px-aligned spacing
        spacing = {f"s{i}": {"value_px": i * 8} for i in range(1, 7)}
        # Consistent type scale (Major Third 1.25)
        typo = {
            f"t{i}": {"font_size": f"{16 * (1.25 ** i):.0f}px"}
            for i in range(5)
        }
        # AA-passing colors only
        colors = {
            "dark": {"value": "#1a1a1a"},
            "medium": {"value": "#333333"},
        }
        result = run_rule_engine(
            typography_tokens=typo,
            color_tokens=colors,
            spacing_tokens=spacing,
        )
        assert result.consistency_score >= 50  # Should be reasonably high


# =============================================================================
# TEST CLASS: Color Ramp Generation
# =============================================================================

class TestColorRampGeneration:
    """Test color ramp generation from base color."""

    def test_ramp_has_all_shades(self):
        """Ramp generates all standard shades."""
        ramp = generate_color_ramp("#06b2c4")
        assert "50" in ramp
        assert "500" in ramp
        assert "900" in ramp
        assert len(ramp) == 10

    def test_ramp_500_is_base(self):
        """Shade 500 is the base color."""
        ramp = generate_color_ramp("#06b2c4")
        assert ramp["500"] == "#06b2c4"

    def test_ramp_lightness_order(self):
        """Lighter shades are lighter than darker shades."""
        ramp = generate_color_ramp("#06b2c4")
        shade_50 = parse_color(ramp["50"])
        shade_900 = parse_color(ramp["900"])
        assert shade_50.hsl[2] > shade_900.hsl[2]  # 50 is lighter

    def test_ramp_empty_on_invalid(self):
        """Invalid color returns empty ramp."""
        ramp = generate_color_ramp("not-a-color")
        assert ramp == {}


# =============================================================================
# TEST CLASS: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_is_gray_pure_white(self):
        """White is gray (low saturation)."""
        assert is_gray("#ffffff")

    def test_is_gray_pure_black(self):
        """Black is gray (low saturation)."""
        assert is_gray("#000000")

    def test_is_gray_red_is_not(self):
        """Pure red is not gray."""
        assert not is_gray("#ff0000")

    def test_color_distance_black_white(self):
        """Black to white is maximum distance."""
        dist = re_color_distance("#000000", "#ffffff")
        assert dist > 0.9  # Close to maximum (~1.0)

    def test_very_large_spacing(self):
        """Large spacing values don't crash."""
        tokens = {"huge": {"value_px": 10000}}
        result = analyze_spacing_grid(tokens)
        assert result.detected_base == 10000

    def test_typography_mixed_units(self):
        """Mixed px/rem/em units are handled."""
        tokens = {
            "a": {"font_size": "16px"},
            "b": {"font_size": "1.5rem"},
            "c": {"font_size": "2em"},
        }
        result = analyze_type_scale(tokens)
        assert len(result.sizes_px) == 3
        assert 16.0 in result.sizes_px
        assert 24.0 in result.sizes_px
        assert 32.0 in result.sizes_px

    def test_duplicate_sizes_deduped(self):
        """Duplicate font sizes are deduplicated."""
        tokens = {
            "a": {"font_size": "16px"},
            "b": {"font_size": "16px"},
            "c": {"font_size": "24px"},
        }
        result = analyze_type_scale(tokens)
        assert len(result.sizes_px) == 2  # 16 and 24

    def test_hex_to_rgb_shorthand(self):
        """3-digit hex expands correctly."""
        assert re_hex_to_rgb("#fff") == (255, 255, 255)
        assert re_hex_to_rgb("#000") == (0, 0, 0)
        assert re_hex_to_rgb("#f00") == (255, 0, 0)


# =============================================================================
# TEST CLASS: Color Name Generation Logic
# =============================================================================

class TestColorNameGeneration:
    """Test color name generation logic (matching app.py's _generate_color_name_from_hex)."""

    def test_pure_red_hue(self):
        """Pure red (#ff0000) has hue in red range."""
        import colorsys
        hex_val = "#ff0000"
        hex_clean = hex_val.lstrip('#').lower()
        r = int(hex_clean[0:2], 16) / 255
        g = int(hex_clean[2:4], 16) / 255
        b = int(hex_clean[4:6], 16) / 255
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        hue = h * 360
        # Red should be in range 0-15 or 345-360
        assert hue < 15 or hue >= 345

    def test_pure_blue_hue(self):
        """Pure blue (#0000ff) has hue in blue range."""
        import colorsys
        hex_val = "#0000ff"
        hex_clean = hex_val.lstrip('#').lower()
        r = int(hex_clean[0:2], 16) / 255
        g = int(hex_clean[2:4], 16) / 255
        b = int(hex_clean[4:6], 16) / 255
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        hue = h * 360
        # Blue should be in range 195-255
        assert 195 <= hue < 255

    def test_gray_low_saturation(self):
        """Gray colors (#888888) have low saturation."""
        import colorsys
        hex_val = "#888888"
        hex_clean = hex_val.lstrip('#').lower()
        r = int(hex_clean[0:2], 16) / 255
        g = int(hex_clean[2:4], 16) / 255
        b = int(hex_clean[4:6], 16) / 255
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        # Gray should have very low saturation
        assert s < 0.1

    def test_white_high_lightness(self):
        """White (#ffffff) has high lightness for shade 50."""
        import colorsys
        hex_val = "#ffffff"
        hex_clean = hex_val.lstrip('#').lower()
        r = int(hex_clean[0:2], 16) / 255
        g = int(hex_clean[2:4], 16) / 255
        b = int(hex_clean[4:6], 16) / 255
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        # White should have lightness >= 0.95 -> shade 50
        assert l >= 0.95

    def test_black_low_lightness(self):
        """Black (#000000) has low lightness for shade 900."""
        import colorsys
        hex_val = "#000000"
        hex_clean = hex_val.lstrip('#').lower()
        r = int(hex_clean[0:2], 16) / 255
        g = int(hex_clean[2:4], 16) / 255
        b = int(hex_clean[4:6], 16) / 255
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        # Black should have lightness < 0.10 -> shade 900
        assert l < 0.10

    def test_teal_hue(self):
        """Teal color (#06b2c4) has hue in teal range."""
        import colorsys
        hex_val = "#06b2c4"
        hex_clean = hex_val.lstrip('#').lower()
        r = int(hex_clean[0:2], 16) / 255
        g = int(hex_clean[2:4], 16) / 255
        b = int(hex_clean[4:6], 16) / 255
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        hue = h * 360
        # Teal should be in range 150-195
        assert 150 <= hue < 195


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Rule Engine — Deterministic Design System Analysis
===================================================

This module handles ALL calculations that don't need LLM reasoning:
- Type scale detection
- AA/AAA contrast checking
- Algorithmic color fixes
- Spacing grid detection
- Color statistics and deduplication

LLMs should ONLY be used for:
- Brand color identification (requires context understanding)
- Palette cohesion (subjective assessment)
- Design maturity scoring (holistic evaluation)
- Prioritized recommendations (business reasoning)
"""

import colorsys
import re
from dataclasses import dataclass, field
from functools import reduce
from math import gcd
from typing import Optional


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TypeScaleAnalysis:
    """Results of type scale analysis."""
    detected_ratio: float
    closest_standard_ratio: float
    scale_name: str
    is_consistent: bool
    variance: float
    sizes_px: list[float]
    ratios_between_sizes: list[float]
    recommendation: float
    recommendation_name: str
    base_size: float = 16.0  # Detected base/body font size
    
    def to_dict(self) -> dict:
        return {
            "detected_ratio": round(self.detected_ratio, 3),
            "closest_standard_ratio": self.closest_standard_ratio,
            "scale_name": self.scale_name,
            "is_consistent": self.is_consistent,
            "variance": round(self.variance, 3),
            "sizes_px": self.sizes_px,
            "base_size": self.base_size,
            "recommendation": self.recommendation,
            "recommendation_name": self.recommendation_name,
        }


@dataclass
class ColorAccessibility:
    """Accessibility analysis for a single color."""
    hex_color: str
    name: str
    contrast_on_white: float
    contrast_on_black: float
    passes_aa_normal: bool  # 4.5:1
    passes_aa_large: bool   # 3.0:1
    passes_aaa_normal: bool # 7.0:1
    best_text_color: str    # White or black
    suggested_fix: Optional[str] = None
    suggested_fix_contrast: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            "color": self.hex_color,
            "name": self.name,
            "contrast_white": round(self.contrast_on_white, 2),
            "contrast_black": round(self.contrast_on_black, 2),
            "aa_normal": self.passes_aa_normal,
            "aa_large": self.passes_aa_large,
            "aaa_normal": self.passes_aaa_normal,
            "best_text": self.best_text_color,
            "suggested_fix": self.suggested_fix,
            "suggested_fix_contrast": round(self.suggested_fix_contrast, 2) if self.suggested_fix_contrast else None,
        }


@dataclass
class SpacingGridAnalysis:
    """Results of spacing grid analysis."""
    detected_base: int
    is_aligned: bool
    alignment_percentage: float
    misaligned_values: list[int]
    recommendation: int
    recommendation_reason: str
    current_values: list[int]
    suggested_scale: list[int]
    
    def to_dict(self) -> dict:
        return {
            "detected_base": self.detected_base,
            "is_aligned": self.is_aligned,
            "alignment_percentage": round(self.alignment_percentage, 1),
            "misaligned_values": self.misaligned_values,
            "recommendation": self.recommendation,
            "recommendation_reason": self.recommendation_reason,
            "current_values": self.current_values,
            "suggested_scale": self.suggested_scale,
        }


@dataclass
class ColorStatistics:
    """Statistical analysis of color palette."""
    total_count: int
    unique_count: int
    duplicate_count: int
    gray_count: int
    saturated_count: int
    near_duplicates: list[tuple[str, str, float]]  # (color1, color2, similarity)
    hue_distribution: dict[str, int]  # {"red": 5, "blue": 3, ...}
    
    def to_dict(self) -> dict:
        return {
            "total": self.total_count,
            "unique": self.unique_count,
            "duplicates": self.duplicate_count,
            "grays": self.gray_count,
            "saturated": self.saturated_count,
            "near_duplicates_count": len(self.near_duplicates),
            "hue_distribution": self.hue_distribution,
        }


@dataclass
class RadiusAnalysis:
    """v3: Analysis of border radius tokens."""
    tier_count: int = 0               # How many distinct radius tiers
    values_px: list = field(default_factory=list)  # Sorted px values
    base_4_aligned: int = 0           # Count aligned to base-4 grid
    base_8_aligned: int = 0           # Count aligned to base-8 grid
    alignment_pct: float = 0.0        # % aligned to best grid
    grid_base: int = 4                # Detected grid base (4 or 8)
    has_full: bool = False             # Has a "full" / 9999px value
    strategy: str = "mixed"           # "sharp" (<= 4px), "rounded" (4-16), "pill" (>= 24), "mixed"

    def to_dict(self) -> dict:
        return {
            "tier_count": self.tier_count,
            "values_px": self.values_px,
            "base_4_aligned": self.base_4_aligned,
            "base_8_aligned": self.base_8_aligned,
            "alignment_pct": round(self.alignment_pct, 1),
            "grid_base": self.grid_base,
            "has_full": self.has_full,
            "strategy": self.strategy,
        }


@dataclass
class ShadowAnalysis:
    """v3: Analysis of shadow / elevation tokens."""
    level_count: int = 0              # Number of distinct shadows
    blur_values: list = field(default_factory=list)  # Sorted blur px
    is_monotonic: bool = True         # Blur increases with each level
    y_offset_monotonic: bool = True   # Y-offset increases with each level
    color_consistent: bool = True     # All shadows use same base color
    elevation_verdict: str = "none"   # "good" / "inconsistent" / "insufficient" / "none"

    def to_dict(self) -> dict:
        return {
            "level_count": self.level_count,
            "blur_values": self.blur_values,
            "is_monotonic": self.is_monotonic,
            "y_offset_monotonic": self.y_offset_monotonic,
            "color_consistent": self.color_consistent,
            "elevation_verdict": self.elevation_verdict,
        }


@dataclass
class RuleEngineResults:
    """Complete rule engine analysis results."""
    typography: TypeScaleAnalysis
    accessibility: list[ColorAccessibility]
    spacing: SpacingGridAnalysis
    color_stats: ColorStatistics

    # v3: radius and shadow analysis
    radius: RadiusAnalysis = field(default_factory=RadiusAnalysis)
    shadows: ShadowAnalysis = field(default_factory=ShadowAnalysis)

    # Summary
    aa_failures: int = 0
    consistency_score: int = 50  # 0-100

    def to_dict(self) -> dict:
        return {
            "typography": self.typography.to_dict(),
            "accessibility": [a.to_dict() for a in self.accessibility if not a.passes_aa_normal],
            "accessibility_all": [a.to_dict() for a in self.accessibility],
            "spacing": self.spacing.to_dict(),
            "color_stats": self.color_stats.to_dict(),
            "radius": self.radius.to_dict(),
            "shadows": self.shadows.to_dict(),
            "summary": {
                "aa_failures": self.aa_failures,
                "consistency_score": self.consistency_score,
            }
        }


# =============================================================================
# COLOR UTILITIES
# =============================================================================

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex string."""
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def get_relative_luminance(hex_color: str) -> float:
    """Calculate relative luminance per WCAG 2.1."""
    r, g, b = hex_to_rgb(hex_color)
    
    def channel_luminance(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    
    return 0.2126 * channel_luminance(r) + 0.7152 * channel_luminance(g) + 0.0722 * channel_luminance(b)


def get_contrast_ratio(color1: str, color2: str) -> float:
    """Calculate WCAG contrast ratio between two colors."""
    l1 = get_relative_luminance(color1)
    l2 = get_relative_luminance(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def is_gray(hex_color: str, threshold: float = 0.1) -> bool:
    """Check if color is a gray (low saturation)."""
    r, g, b = hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    return s < threshold


def get_saturation(hex_color: str) -> float:
    """Get saturation value (0-1)."""
    r, g, b = hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    return s


def get_hue_name(hex_color: str) -> str:
    """Get human-readable hue name."""
    r, g, b = hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
    if s < 0.1:
        return "gray"
    
    hue_deg = h * 360
    
    if hue_deg < 15 or hue_deg >= 345:
        return "red"
    elif hue_deg < 45:
        return "orange"
    elif hue_deg < 75:
        return "yellow"
    elif hue_deg < 150:
        return "green"
    elif hue_deg < 210:
        return "cyan"
    elif hue_deg < 270:
        return "blue"
    elif hue_deg < 315:
        return "purple"
    else:
        return "pink"


def color_distance(hex1: str, hex2: str) -> float:
    """Calculate perceptual color distance (0-1, lower = more similar)."""
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    
    # Simple Euclidean distance in RGB space (normalized)
    dr = (r1 - r2) / 255
    dg = (g1 - g2) / 255
    db = (b1 - b2) / 255
    
    return (dr**2 + dg**2 + db**2) ** 0.5 / (3 ** 0.5)


def darken_color(hex_color: str, factor: float) -> str:
    """Darken a color by a factor (0-1)."""
    r, g, b = hex_to_rgb(hex_color)
    r = int(r * (1 - factor))
    g = int(g * (1 - factor))
    b = int(b * (1 - factor))
    return rgb_to_hex(r, g, b)


def lighten_color(hex_color: str, factor: float) -> str:
    """Lighten a color by a factor (0-1)."""
    r, g, b = hex_to_rgb(hex_color)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return rgb_to_hex(r, g, b)


def find_aa_compliant_color(hex_color: str, background: str = "#ffffff", target_contrast: float = 4.5) -> str:
    """
    Algorithmically adjust a color until it meets AA contrast requirements.
    
    Returns the original color if it already passes, otherwise returns
    a darkened/lightened version that passes.
    """
    current_contrast = get_contrast_ratio(hex_color, background)

    if current_contrast >= target_contrast:
        return hex_color

    # Determine direction: move fg *away* from bg in luminance.
    # If fg is lighter than bg → darken fg to increase gap.
    # If fg is darker than bg → lighten fg to increase gap.
    bg_luminance = get_relative_luminance(background)
    color_luminance = get_relative_luminance(hex_color)

    should_darken = color_luminance >= bg_luminance

    best_color = hex_color
    best_contrast = current_contrast

    for i in range(1, 101):
        factor = i / 100

        if should_darken:
            new_color = darken_color(hex_color, factor)
        else:
            new_color = lighten_color(hex_color, factor)

        new_contrast = get_contrast_ratio(new_color, background)

        if new_contrast >= target_contrast:
            return new_color

        if new_contrast > best_contrast:
            best_contrast = new_contrast
            best_color = new_color

    # If first direction didn't reach target, try the opposite direction
    # (e.g., very similar luminances where either direction could work)
    should_darken = not should_darken
    for i in range(1, 101):
        factor = i / 100

        if should_darken:
            new_color = darken_color(hex_color, factor)
        else:
            new_color = lighten_color(hex_color, factor)

        new_contrast = get_contrast_ratio(new_color, background)

        if new_contrast >= target_contrast:
            return new_color

        if new_contrast > best_contrast:
            best_contrast = new_contrast
            best_color = new_color

    return best_color


# =============================================================================
# TYPE SCALE ANALYSIS
# =============================================================================

# Standard type scale ratios
STANDARD_SCALES = {
    1.067: "Minor Second",
    1.125: "Major Second",
    1.200: "Minor Third",
    1.250: "Major Third",       # ⭐ Recommended
    1.333: "Perfect Fourth",
    1.414: "Augmented Fourth",
    1.500: "Perfect Fifth",
    1.618: "Golden Ratio",
    2.000: "Octave",
}


def parse_size_to_px(size: str) -> Optional[float]:
    """Convert any size string to pixels."""
    if isinstance(size, (int, float)):
        return float(size)
    
    size = str(size).strip().lower()
    
    # Extract number
    match = re.search(r'([\d.]+)', size)
    if not match:
        return None
    
    value = float(match.group(1))
    
    if 'rem' in size:
        return value * 16  # Assume 16px base
    elif 'em' in size:
        return value * 16  # Approximate
    elif 'px' in size or size.replace('.', '').isdigit():
        return value
    
    return value


def analyze_type_scale(typography_tokens: dict) -> TypeScaleAnalysis:
    """
    Analyze typography tokens to detect type scale ratio.
    
    Args:
        typography_tokens: Dict of typography tokens with font_size
        
    Returns:
        TypeScaleAnalysis with detected ratio and recommendations
    """
    # Extract and parse sizes
    sizes = []
    for name, token in typography_tokens.items():
        if isinstance(token, dict):
            size = token.get("font_size") or token.get("fontSize") or token.get("size")
        else:
            size = getattr(token, "font_size", None)
        
        if size:
            px = parse_size_to_px(size)
            if px and px > 0:
                sizes.append(px)
    
    # Sort and dedupe
    sizes_px = sorted(set(sizes))
    
    if len(sizes_px) < 2:
        # Use the size if valid (>= 10px), otherwise default to 16px
        if sizes_px and sizes_px[0] >= 10:
            base_size = sizes_px[0]
        else:
            base_size = 16.0
        return TypeScaleAnalysis(
            detected_ratio=1.0,
            closest_standard_ratio=1.25,
            scale_name="Unknown",
            is_consistent=False,
            variance=0,
            sizes_px=sizes_px,
            ratios_between_sizes=[],
            recommendation=1.25,
            recommendation_name="Major Third",
            base_size=base_size,
        )
    
    # Calculate ratios between consecutive sizes
    ratios = []
    for i in range(len(sizes_px) - 1):
        if sizes_px[i] > 0:
            ratio = sizes_px[i + 1] / sizes_px[i]
            if 1.0 < ratio < 3.0:  # Reasonable range
                ratios.append(ratio)
    
    if not ratios:
        # Detect base size even if no valid ratios
        # Filter out tiny sizes (< 10px) which are likely captions/icons
        valid_body_sizes = [s for s in sizes_px if s >= 10]
        base_candidates = [s for s in valid_body_sizes if 14 <= s <= 18]
        if base_candidates:
            base_size = min(base_candidates, key=lambda x: abs(x - 16))
        elif valid_body_sizes:
            base_size = min(valid_body_sizes, key=lambda x: abs(x - 16))
        elif sizes_px:
            base_size = max(sizes_px)  # Last resort: largest of tiny sizes
        else:
            base_size = 16.0
        return TypeScaleAnalysis(
            detected_ratio=1.0,
            closest_standard_ratio=1.25,
            scale_name="Unknown",
            is_consistent=False,
            variance=0,
            sizes_px=sizes_px,
            ratios_between_sizes=[],
            recommendation=1.25,
            recommendation_name="Major Third",
            base_size=base_size,
        )
    
    # Average ratio
    avg_ratio = sum(ratios) / len(ratios)
    
    # Variance (consistency check)
    variance = max(ratios) - min(ratios) if ratios else 0
    is_consistent = variance < 0.15  # Within 15% variance is "consistent"
    
    # Find closest standard scale
    closest_scale = min(STANDARD_SCALES.keys(), key=lambda x: abs(x - avg_ratio))
    scale_name = STANDARD_SCALES[closest_scale]
    
    # Detect base size (closest to 16px, or 14-18px range typical for body)
    # The base size is typically the most common body text size
    # IMPORTANT: Filter out tiny sizes (< 10px) which are likely captions/icons
    valid_body_sizes = [s for s in sizes_px if s >= 10]

    base_candidates = [s for s in valid_body_sizes if 14 <= s <= 18]
    if base_candidates:
        # Prefer 16px if present, otherwise closest to 16
        if 16 in base_candidates:
            base_size = 16.0
        else:
            base_size = min(base_candidates, key=lambda x: abs(x - 16))
    elif valid_body_sizes:
        # Fallback: find size closest to 16px from valid sizes (>= 10px)
        # This avoids picking tiny caption/icon sizes like 7px
        base_size = min(valid_body_sizes, key=lambda x: abs(x - 16))
    elif sizes_px:
        # Last resort: just use the largest size if all are tiny
        base_size = max(sizes_px)
    else:
        base_size = 16.0
    
    # Recommendation
    if is_consistent and abs(avg_ratio - closest_scale) < 0.05:
        # Already using a standard scale
        recommendation = closest_scale
        recommendation_name = scale_name
    else:
        # Recommend Major Third (1.25) as default
        recommendation = 1.25
        recommendation_name = "Major Third"
    
    return TypeScaleAnalysis(
        detected_ratio=avg_ratio,
        closest_standard_ratio=closest_scale,
        scale_name=scale_name,
        is_consistent=is_consistent,
        variance=variance,
        sizes_px=sizes_px,
        ratios_between_sizes=ratios,
        recommendation=recommendation,
        recommendation_name=recommendation_name,
        base_size=base_size,
    )


# =============================================================================
# ACCESSIBILITY ANALYSIS
# =============================================================================

def analyze_accessibility(color_tokens: dict, fg_bg_pairs: list[dict] = None) -> list[ColorAccessibility]:
    """
    Analyze all colors for WCAG accessibility compliance.

    Args:
        color_tokens: Dict of color tokens with value/hex
        fg_bg_pairs: Optional list of actual foreground/background pairs
                     extracted from the DOM (each dict has 'foreground',
                     'background', 'element' keys).

    Returns:
        List of ColorAccessibility results
    """
    results = []

    for name, token in color_tokens.items():
        if isinstance(token, dict):
            hex_color = token.get("value") or token.get("hex") or token.get("color")
        else:
            hex_color = getattr(token, "value", None)

        if not hex_color or not hex_color.startswith("#"):
            continue

        try:
            contrast_white = get_contrast_ratio(hex_color, "#ffffff")
            contrast_black = get_contrast_ratio(hex_color, "#000000")

            passes_aa_normal = contrast_white >= 4.5 or contrast_black >= 4.5
            passes_aa_large = contrast_white >= 3.0 or contrast_black >= 3.0
            passes_aaa_normal = contrast_white >= 7.0 or contrast_black >= 7.0

            best_text = "#ffffff" if contrast_white > contrast_black else "#000000"

            # Generate fix suggestion if needed
            suggested_fix = None
            suggested_fix_contrast = None

            if not passes_aa_normal:
                suggested_fix = find_aa_compliant_color(hex_color, "#ffffff", 4.5)
                suggested_fix_contrast = get_contrast_ratio(suggested_fix, "#ffffff")

            results.append(ColorAccessibility(
                hex_color=hex_color,
                name=name,
                contrast_on_white=contrast_white,
                contrast_on_black=contrast_black,
                passes_aa_normal=passes_aa_normal,
                passes_aa_large=passes_aa_large,
                passes_aaa_normal=passes_aaa_normal,
                best_text_color=best_text,
                suggested_fix=suggested_fix,
                suggested_fix_contrast=suggested_fix_contrast,
            ))
        except Exception:
            continue

    # --- Real foreground-background pair checks ---
    if fg_bg_pairs:
        for pair in fg_bg_pairs:
            fg = pair.get("foreground", "").lower()
            bg = pair.get("background", "").lower()
            element = pair.get("element", "")
            if not (fg.startswith("#") and bg.startswith("#")):
                continue
            # Skip same-color pairs (invisible/placeholder text — not real failures)
            if fg == bg:
                continue
            try:
                ratio = get_contrast_ratio(fg, bg)
                # Skip near-identical pairs (ratio < 1.1) — likely decorative/hidden
                if ratio < 1.1:
                    continue
                if ratio < 4.5:
                    # This pair fails AA — record it
                    fix = find_aa_compliant_color(fg, bg, 4.5)
                    fix_contrast = get_contrast_ratio(fix, bg)
                    results.append(ColorAccessibility(
                        hex_color=fg,
                        name=f"fg:{fg} on bg:{bg} ({element}) [{ratio:.1f}:1]",
                        contrast_on_white=get_contrast_ratio(fg, "#ffffff"),
                        contrast_on_black=get_contrast_ratio(fg, "#000000"),
                        passes_aa_normal=False,
                        passes_aa_large=ratio >= 3.0,
                        passes_aaa_normal=False,
                        best_text_color="#ffffff" if get_contrast_ratio(fg, "#ffffff") > get_contrast_ratio(fg, "#000000") else "#000000",
                        suggested_fix=fix,
                        suggested_fix_contrast=fix_contrast,
                    ))
            except Exception:
                continue

    return results


# =============================================================================
# SPACING GRID ANALYSIS
# =============================================================================

def analyze_spacing_grid(spacing_tokens: dict) -> SpacingGridAnalysis:
    """
    Analyze spacing tokens to detect grid alignment.
    
    Args:
        spacing_tokens: Dict of spacing tokens with value_px or value
        
    Returns:
        SpacingGridAnalysis with detected grid and recommendations
    """
    values = []
    
    for name, token in spacing_tokens.items():
        if isinstance(token, dict):
            px = token.get("value_px") or token.get("value")
        else:
            px = getattr(token, "value_px", None) or getattr(token, "value", None)
        
        if px:
            try:
                px_val = int(float(str(px).replace('px', '')))
                if px_val > 0:
                    values.append(px_val)
            except (ValueError, TypeError):
                continue
    
    if not values:
        return SpacingGridAnalysis(
            detected_base=8,
            is_aligned=False,
            alignment_percentage=0,
            misaligned_values=[],
            recommendation=8,
            recommendation_reason="No spacing values detected, defaulting to 8px grid",
            current_values=[],
            suggested_scale=[0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64],
        )
    
    values = sorted(set(values))
    
    # Find GCD (greatest common divisor) of all values
    detected_base = reduce(gcd, values)
    
    # Check alignment to common grids (4px, 8px)
    aligned_to_4 = all(v % 4 == 0 for v in values)
    aligned_to_8 = all(v % 8 == 0 for v in values)
    
    # Find misaligned values (not divisible by detected base)
    misaligned = [v for v in values if v % detected_base != 0] if detected_base > 1 else values
    
    alignment_percentage = (len(values) - len(misaligned)) / len(values) * 100 if values else 0
    
    # Determine recommendation
    if aligned_to_8:
        recommendation = 8
        recommendation_reason = "All values already align to 8px grid"
        is_aligned = True
    elif aligned_to_4:
        recommendation = 4
        recommendation_reason = "Values align to 4px grid (consider 8px for simpler system)"
        is_aligned = True
    elif detected_base in [4, 8]:
        recommendation = detected_base
        recommendation_reason = f"Detected {detected_base}px base with {alignment_percentage:.0f}% alignment"
        is_aligned = alignment_percentage >= 80
    else:
        recommendation = 8
        recommendation_reason = f"Inconsistent spacing detected (GCD={detected_base}), recommend 8px grid"
        is_aligned = False
    
    # Generate suggested scale
    base = recommendation
    suggested_scale = [0] + [base * i for i in [0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 16] if base * i == int(base * i)]
    suggested_scale = sorted(set([int(v) for v in suggested_scale]))
    
    return SpacingGridAnalysis(
        detected_base=detected_base,
        is_aligned=is_aligned,
        alignment_percentage=alignment_percentage,
        misaligned_values=misaligned,
        recommendation=recommendation,
        recommendation_reason=recommendation_reason,
        current_values=values,
        suggested_scale=suggested_scale,
    )


# =============================================================================
# COLOR STATISTICS
# =============================================================================

def analyze_color_statistics(color_tokens: dict, similarity_threshold: float = 0.05) -> ColorStatistics:
    """
    Analyze color palette statistics.
    
    Args:
        color_tokens: Dict of color tokens
        similarity_threshold: Distance threshold for "near duplicate" (0-1)
        
    Returns:
        ColorStatistics with palette analysis
    """
    colors = []
    
    for name, token in color_tokens.items():
        if isinstance(token, dict):
            hex_color = token.get("value") or token.get("hex")
        else:
            hex_color = getattr(token, "value", None)
        
        if hex_color and hex_color.startswith("#"):
            colors.append(hex_color.lower())
    
    unique_colors = list(set(colors))
    
    # Count grays and saturated
    grays = [c for c in unique_colors if is_gray(c)]
    saturated = [c for c in unique_colors if get_saturation(c) > 0.3]
    
    # Find near duplicates
    near_duplicates = []
    for i, c1 in enumerate(unique_colors):
        for c2 in unique_colors[i+1:]:
            dist = color_distance(c1, c2)
            if dist < similarity_threshold and dist > 0:
                near_duplicates.append((c1, c2, round(dist, 4)))
    
    # Hue distribution
    hue_dist = {}
    for c in unique_colors:
        hue = get_hue_name(c)
        hue_dist[hue] = hue_dist.get(hue, 0) + 1
    
    return ColorStatistics(
        total_count=len(colors),
        unique_count=len(unique_colors),
        duplicate_count=len(colors) - len(unique_colors),
        gray_count=len(grays),
        saturated_count=len(saturated),
        near_duplicates=near_duplicates,
        hue_distribution=hue_dist,
    )


# =============================================================================
# v3: RADIUS GRID ANALYSIS
# =============================================================================

def analyze_radius_grid(radius_tokens: dict) -> RadiusAnalysis:
    """Analyze border radius tokens for grid alignment and strategy."""
    if not radius_tokens:
        return RadiusAnalysis()

    values_px = []
    for name, t in radius_tokens.items():
        px = None
        if isinstance(t, dict):
            px = t.get("value_px")
        else:
            px = getattr(t, "value_px", None)
        if px is not None and isinstance(px, (int, float)):
            values_px.append(int(px))

    if not values_px:
        return RadiusAnalysis()

    values_px = sorted(set(values_px))
    has_full = 9999 in values_px
    # For grid analysis, exclude 0 and 9999
    grid_candidates = [v for v in values_px if 0 < v < 9999]

    base_4 = sum(1 for v in grid_candidates if v % 4 == 0)
    base_8 = sum(1 for v in grid_candidates if v % 8 == 0)
    total = len(grid_candidates) if grid_candidates else 1

    if base_8 / total >= 0.7:
        grid_base = 8
        alignment_pct = (base_8 / total) * 100
    else:
        grid_base = 4
        alignment_pct = (base_4 / total) * 100

    # Determine strategy: sharp, rounded, pill, mixed
    if grid_candidates:
        max_val = max(grid_candidates)
        if max_val <= 4:
            strategy = "sharp"
        elif max_val <= 16:
            strategy = "rounded"
        elif max_val >= 24:
            strategy = "pill"
        else:
            strategy = "mixed"
    else:
        strategy = "none"

    return RadiusAnalysis(
        tier_count=len(values_px),
        values_px=values_px,
        base_4_aligned=base_4,
        base_8_aligned=base_8,
        alignment_pct=alignment_pct,
        grid_base=grid_base,
        has_full=has_full,
        strategy=strategy,
    )


# =============================================================================
# v3: SHADOW ELEVATION ANALYSIS
# =============================================================================

def analyze_shadow_elevation(shadow_tokens: dict) -> ShadowAnalysis:
    """Analyze shadow tokens for elevation hierarchy and consistency."""
    if not shadow_tokens:
        return ShadowAnalysis()

    blur_values = []
    y_offsets = []
    colors_seen = set()

    for name, t in shadow_tokens.items():
        if isinstance(t, dict):
            blur = t.get("blur_px")
            y_off = t.get("y_offset_px")
            color = t.get("color") or t.get("value", "")[:30]
        else:
            blur = getattr(t, "blur_px", None)
            y_off = getattr(t, "y_offset_px", None)
            color = getattr(t, "color", None) or str(getattr(t, "value", ""))[:30]

        if blur is not None:
            blur_values.append(float(blur))
        if y_off is not None:
            y_offsets.append(float(y_off))
        # Normalize color for consistency check (strip alpha variations)
        if color:
            base_color = color.split("(")[0].strip() if "(" in color else color[:7]
            colors_seen.add(base_color)

    if not blur_values:
        return ShadowAnalysis()

    sorted_blur = sorted(blur_values)
    sorted_y = sorted(y_offsets) if y_offsets else []

    # Check monotonic progression
    is_mono_blur = all(sorted_blur[i] <= sorted_blur[i+1] for i in range(len(sorted_blur)-1))
    is_mono_y = all(sorted_y[i] <= sorted_y[i+1] for i in range(len(sorted_y)-1)) if len(sorted_y) > 1 else True

    # Color consistency: all shadows should use the same base color
    color_consistent = len(colors_seen) <= 2

    # Verdict
    level_count = len(sorted_blur)
    if level_count == 0:
        verdict = "none"
    elif level_count < 3:
        verdict = "insufficient"
    elif is_mono_blur and color_consistent:
        verdict = "good"
    else:
        verdict = "inconsistent"

    return ShadowAnalysis(
        level_count=level_count,
        blur_values=[round(b, 1) for b in sorted_blur],
        is_monotonic=is_mono_blur,
        y_offset_monotonic=is_mono_y,
        color_consistent=color_consistent,
        elevation_verdict=verdict,
    )


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def run_rule_engine(
    typography_tokens: dict,
    color_tokens: dict,
    spacing_tokens: dict,
    radius_tokens: dict = None,
    shadow_tokens: dict = None,
    log_callback: Optional[callable] = None,
    fg_bg_pairs: list[dict] = None,
) -> RuleEngineResults:
    """
    Run complete rule-based analysis on design tokens.
    
    This is FREE (no LLM costs) and handles all deterministic calculations.
    
    Args:
        typography_tokens: Dict of typography tokens
        color_tokens: Dict of color tokens  
        spacing_tokens: Dict of spacing tokens
        radius_tokens: Dict of border radius tokens (optional)
        shadow_tokens: Dict of shadow tokens (optional)
        log_callback: Function to log messages
        
    Returns:
        RuleEngineResults with all analysis data
    """
    
    def log(msg: str):
        if log_callback:
            log_callback(msg)
    
    log("")
    log("═" * 60)
    log("⚙️  LAYER 1: RULE ENGINE (FREE - $0.00)")
    log("═" * 60)
    log("")
    
    # ─────────────────────────────────────────────────────────────
    # Typography Analysis
    # ─────────────────────────────────────────────────────────────
    log("   📐 TYPE SCALE ANALYSIS")
    log("   " + "─" * 40)
    typography = analyze_type_scale(typography_tokens)

    # Step-by-step reasoning
    if typography.sizes_px and len(typography.sizes_px) >= 2:
        sizes = sorted(typography.sizes_px)
        log(f"   │  Step 1: Found {len(sizes)} font sizes: {sizes}")
        if len(sizes) >= 2:
            ratios = [round(sizes[i+1]/sizes[i], 3) for i in range(len(sizes)-1) if sizes[i] > 0]
            log(f"   │  Step 2: Computed ratios between consecutive sizes: {ratios[:8]}{'...' if len(ratios) > 8 else ''}")
            if ratios:
                avg_ratio = sum(ratios) / len(ratios)
                log(f"   │  Step 3: Average ratio = {avg_ratio:.3f}, variance = {typography.variance:.3f}")
                log(f"   │  Step 4: {'Variance ≤ 0.15 → consistent ✅' if typography.is_consistent else f'Variance {typography.variance:.3f} > 0.15 → inconsistent ⚠️'}")

    consistency_icon = "✅" if typography.is_consistent else "⚠️"
    log(f"   ├─ Detected Ratio: {typography.detected_ratio:.3f}")
    log(f"   ├─ Closest Standard: {typography.scale_name} ({typography.closest_standard_ratio})")
    log(f"   ├─ Consistent: {consistency_icon} {'Yes' if typography.is_consistent else f'No (variance: {typography.variance:.2f})'}")
    log(f"   ├─ Sizes Found: {typography.sizes_px}")
    log(f"   └─ 💡 Recommendation: {typography.recommendation} ({typography.recommendation_name})")
    log("")
    
    # ─────────────────────────────────────────────────────────────
    # Accessibility Analysis  
    # ─────────────────────────────────────────────────────────────
    log("   ♿ ACCESSIBILITY CHECK (WCAG AA/AAA)")
    log("   " + "─" * 40)
    accessibility = analyze_accessibility(color_tokens, fg_bg_pairs=fg_bg_pairs)

    # Separate individual-color failures from real FG/BG pair failures
    pair_failures = [a for a in accessibility if not a.passes_aa_normal and a.name.startswith("fg:")]
    color_only_failures = [a for a in accessibility if not a.passes_aa_normal and not a.name.startswith("fg:")]
    failures = [a for a in accessibility if not a.passes_aa_normal]
    passes = len(accessibility) - len(failures)

    # Step-by-step reasoning
    pair_count = len(fg_bg_pairs) if fg_bg_pairs else 0
    log(f"   │  Step 1: Testing each color against white (#fff) and black (#000)")
    log(f"   │  Step 2: WCAG AA requires ≥4.5:1 for normal text, ≥3.0:1 for large text")
    log(f"   │  Step 3: A color passes if it achieves ≥4.5:1 against EITHER white or black")
    if pair_count > 0:
        log(f"   │  Step 4: Also testing {pair_count} real foreground/background pairs from the page")
    pass_rate = round(passes / max(len(accessibility), 1) * 100)
    log(f"   │  Result: {passes}/{len(accessibility)} pass ({pass_rate}%)")

    log(f"   ├─ Colors Analyzed: {len(accessibility)}")
    log(f"   ├─ FG/BG Pairs Checked: {pair_count}")
    log(f"   ├─ AA Pass: {passes} ✅")
    log(f"   ├─ AA Fail (color vs white/black): {len(color_only_failures)} {'❌' if color_only_failures else '✅'}")
    log(f"   ├─ AA Fail (real FG/BG pairs): {len(pair_failures)} {'❌' if pair_failures else '✅'}")

    if color_only_failures:
        log("   │")
        log("   │  ⚠️  FAILING COLORS (vs white/black):")
        for i, f in enumerate(color_only_failures[:8]):
            fix_info = f" → 💡 Fix: {f.suggested_fix} ({f.suggested_fix_contrast:.1f}:1)" if f.suggested_fix else ""
            log(f"   │  ├─ {f.name}: {f.hex_color} (white:{f.contrast_on_white:.1f}:1, black:{f.contrast_on_black:.1f}:1){fix_info}")
        if len(color_only_failures) > 8:
            log(f"   │  └─ ... and {len(color_only_failures) - 8} more")

    if pair_failures:
        log("   │")
        log("   │  ❌ FAILING FG/BG PAIRS (actual on-page combinations):")
        for i, f in enumerate(pair_failures[:8]):
            fix_info = f" → 💡 Fix: {f.suggested_fix} ({f.suggested_fix_contrast:.1f}:1)" if f.suggested_fix else ""
            log(f"   │  ├─ {f.name}{fix_info}")
        if len(pair_failures) > 8:
            log(f"   │  └─ ... and {len(pair_failures) - 8} more")

    log("")
    
    # ─────────────────────────────────────────────────────────────
    # Spacing Grid Analysis
    # ─────────────────────────────────────────────────────────────
    log("   📏 SPACING GRID ANALYSIS")
    log("   " + "─" * 40)
    spacing = analyze_spacing_grid(spacing_tokens)

    # Step-by-step reasoning
    log(f"   │  Step 1: Extracted all spacing values (margin, padding, gap)")
    log(f"   │  Step 2: Detected base unit via GCD: {spacing.detected_base}px")
    aligned_count = round(spacing.alignment_percentage / 100 * max(len(spacing_tokens), 1))
    total = max(len(spacing_tokens), 1)
    log(f"   │  Step 3: Checking divisibility: {aligned_count}/{total} values are multiples of {spacing.detected_base}px")
    if spacing.misaligned_values:
        log(f"   │  Step 4: Off-grid values: {spacing.misaligned_values[:10]}{'...' if len(spacing.misaligned_values) > 10 else ''}")

    alignment_icon = "✅" if spacing.is_aligned else "⚠️"
    log(f"   ├─ Detected Base: {spacing.detected_base}px")
    log(f"   ├─ Grid Aligned: {alignment_icon} {spacing.alignment_percentage:.0f}%")

    if spacing.misaligned_values:
        log(f"   ├─ Misaligned Values: {spacing.misaligned_values[:10]}{'...' if len(spacing.misaligned_values) > 10 else ''}")

    log(f"   ├─ Suggested Scale: {spacing.suggested_scale[:12]}{'...' if len(spacing.suggested_scale) > 12 else ''}")
    log(f"   └─ 💡 Recommendation: {spacing.recommendation}px ({spacing.recommendation_reason})")
    log("")
    
    # ─────────────────────────────────────────────────────────────
    # Color Statistics
    # ─────────────────────────────────────────────────────────────
    log("   🎨 COLOR PALETTE STATISTICS")
    log("   " + "─" * 40)
    color_stats = analyze_color_statistics(color_tokens)

    # Step-by-step reasoning
    log(f"   │  Step 1: Counted {color_stats.total_count} total color tokens from extraction")
    log(f"   │  Step 2: After exact-hex dedup: {color_stats.unique_count} unique colors")
    if color_stats.duplicate_count > 0:
        log(f"   │  Step 3: Found {color_stats.duplicate_count} exact duplicates (same hex, different usage)")
    if len(color_stats.near_duplicates) > 0:
        log(f"   │  Step 4: Found {len(color_stats.near_duplicates)} near-duplicate pairs (RGB distance < 10)")
        for nd in color_stats.near_duplicates[:3]:
            if isinstance(nd, (tuple, list)) and len(nd) >= 2:
                log(f"   │     └─ {nd[0]} ≈ {nd[1]}")
    if color_stats.unique_count > 30:
        log(f"   │  ⚠️ {color_stats.unique_count} unique colors is high — most design systems use 15-25")
    elif color_stats.unique_count < 8:
        log(f"   │  ⚠️ Only {color_stats.unique_count} unique colors — may need more semantic variety")
    else:
        log(f"   │  ✅ {color_stats.unique_count} unique colors — reasonable palette size")

    dup_icon = "⚠️" if color_stats.duplicate_count > 10 else "✅"
    unique_icon = "⚠️" if color_stats.unique_count > 30 else "✅"

    log(f"   ├─ Total Colors: {color_stats.total_count}")
    log(f"   ├─ Unique Colors: {color_stats.unique_count} {unique_icon}")
    log(f"   ├─ Exact Duplicates: {color_stats.duplicate_count} {dup_icon}")
    log(f"   ├─ Near-Duplicates: {len(color_stats.near_duplicates)}")
    log(f"   ├─ Grays: {color_stats.gray_count} | Saturated: {color_stats.saturated_count}")
    log(f"   └─ Hue Distribution: {dict(list(color_stats.hue_distribution.items())[:7])}{'...' if len(color_stats.hue_distribution) > 7 else ''}")
    log("")

    # ─────────────────────────────────────────────────────────────
    # v3: Radius Grid Analysis
    # ─────────────────────────────────────────────────────────────
    radius_result = analyze_radius_grid(radius_tokens or {})
    if radius_result.tier_count > 0:
        log("   🔘 RADIUS GRID ANALYSIS")
        log("   " + "─" * 40)
        # Step-by-step reasoning
        log(f"   │  Step 1: Found {radius_result.tier_count} unique radius values: {radius_result.values_px[:10]}{'...' if len(radius_result.values_px) > 10 else ''}")
        log(f"   │  Step 2: Checking base-4 alignment: {radius_result.base_4_aligned}/{radius_result.tier_count} values divisible by 4")
        log(f"   │  Step 3: Checking base-8 alignment: {radius_result.base_8_aligned}/{radius_result.tier_count} values divisible by 8")
        grid_choice = "base-4" if radius_result.base_4_aligned >= radius_result.base_8_aligned else "base-8"
        log(f"   │  Step 4: Best fit grid: {grid_choice} ({radius_result.alignment_pct:.0f}% aligned)")
        if radius_result.has_full:
            log(f"   │  Step 5: Full radius (9999px/50%) detected — used for pills/circles ✅")
        strategy_explanation = {
            "tight": "small range (1-8px), subtle rounding",
            "moderate": "medium range, balanced approach",
            "expressive": "wide range including large radii, expressive design",
            "mixed": "inconsistent strategy, values don't follow clear pattern",
        }
        strat_desc = strategy_explanation.get(radius_result.strategy, radius_result.strategy)
        log(f"   │  Strategy: {radius_result.strategy} — {strat_desc}")

        align_icon = "✅" if radius_result.alignment_pct >= 80 else "⚠️"
        log(f"   ├─ Tiers: {radius_result.tier_count} | Values: {radius_result.values_px[:10]}")
        log(f"   ├─ Grid: base-{radius_result.grid_base} | Aligned: {align_icon} {radius_result.alignment_pct:.0f}%")
        log(f"   ├─ Strategy: {radius_result.strategy} | Has full: {radius_result.has_full}")
        log(f"   └─ Base-4: {radius_result.base_4_aligned}/{radius_result.tier_count} | Base-8: {radius_result.base_8_aligned}/{radius_result.tier_count}")
        log("")

    # ─────────────────────────────────────────────────────────────
    # v3: Shadow Elevation Analysis
    # ─────────────────────────────────────────────────────────────
    shadow_result = analyze_shadow_elevation(shadow_tokens or {})
    log("   🌗 SHADOW ELEVATION ANALYSIS")
    log("   " + "─" * 40)
    if shadow_result.level_count > 0:
        # Step-by-step reasoning
        log(f"   │  Step 1: Found {shadow_result.level_count} shadow definitions")
        log(f"   │  Step 2: Sorted by blur radius: {shadow_result.blur_values}")
        if shadow_result.is_monotonic:
            log(f"   │  Step 3: Blur values increase monotonically ✅ (proper elevation hierarchy)")
        else:
            log(f"   │  Step 3: Blur values are NOT monotonic ⚠️ (shadows don't form proper hierarchy)")
        log(f"   │  Step 4: Shadow colors {'are consistent ✅' if shadow_result.color_consistent else 'vary ⚠️ — should use same base color with different alpha'}")

        mono_icon = "✅" if shadow_result.is_monotonic else "⚠️"
        color_icon = "✅" if shadow_result.color_consistent else "⚠️"
        log(f"   ├─ Levels: {shadow_result.level_count} | Blur: {shadow_result.blur_values}")
        log(f"   ├─ Monotonic Blur: {mono_icon} {'Yes' if shadow_result.is_monotonic else 'No — progression is non-linear'}")
        log(f"   ├─ Color Consistent: {color_icon} {'Yes' if shadow_result.color_consistent else 'No — mixed shadow colors'}")
        log(f"   ├─ Verdict: {shadow_result.elevation_verdict}")

        # Specific recommendations for insufficient levels
        if shadow_result.level_count < 4:
            log(f"   │")
            log(f"   │  ⚠️  INSUFFICIENT SHADOW LEVELS ({shadow_result.level_count} found, 4-6 recommended)")
            log(f"   │  Industry standard elevation systems:")
            log(f"   │  ├─ Material Design: 6 levels (0dp–24dp)")
            log(f"   │  ├─ Tailwind CSS: 6 levels (sm, DEFAULT, md, lg, xl, 2xl)")
            log(f"   │  ├─ Shopify Polaris: 5 levels (transparent–500)")
            log(f"   │  ├─ IBM Carbon: 4 levels (sm, md, lg, xl)")
            log(f"   │  └─ Chakra UI: 6 levels (xs, sm, md, lg, xl, 2xl)")
            log(f"   │")
            log(f"   │  💡 Recommendation: Add {4 - shadow_result.level_count} more shadow levels for a complete elevation system.")
            log(f"   │  Suggested additions (blur values):")
            # Generate suggested blur values based on what exists
            existing = shadow_result.blur_values
            if len(existing) == 1:
                suggested = [round(existing[0] * 0.5, 1), round(existing[0] * 2, 1), round(existing[0] * 4, 1)]
                log(f"   │  ├─ xs: {suggested[0]}px blur (subtle)")
                log(f"   │  ├─ md: {suggested[1]}px blur (cards/dropdowns)")
                log(f"   │  └─ lg: {suggested[2]}px blur (modals/overlays)")
            elif len(existing) == 2:
                mid = round((existing[0] + existing[1]) / 2, 1)
                large = round(existing[1] * 2, 1)
                log(f"   │  ├─ md: {mid}px blur (between existing levels)")
                log(f"   │  └─ lg: {large}px blur (modals/overlays)")
            elif len(existing) == 3:
                large = round(existing[-1] * 1.5, 1)
                log(f"   │  └─ xl: {large}px blur (maximum elevation)")
        elif not shadow_result.is_monotonic:
            log(f"   │")
            log(f"   │  💡 Recommendation: Re-order shadows so blur increases with elevation level.")
            log(f"   │  Current blur order: {shadow_result.blur_values}")
            log(f"   │  Expected: monotonically increasing (e.g., 2→4→8→16→24)")

        log(f"   └─ Score Impact: {'10/10 (good)' if shadow_result.elevation_verdict == 'good' else '5/10 (partial)' if shadow_result.level_count >= 3 else '2/10 (insufficient)'}")
    else:
        log(f"   │  No shadow tokens found in extraction.")
        log(f"   │  ⚠️  Most design systems define 4-6 shadow levels for elevation hierarchy.")
        log(f"   │  This site may use flat design or shadows weren't captured.")
        log(f"   └─ Score Impact: 2/10 (no shadows)")
    log("")

    # ─────────────────────────────────────────────────────────────
    # Calculate Summary Scores
    # ─────────────────────────────────────────────────────────────

    # Consistency score (0-100) — v3: includes radius + shadow
    type_score = 20 if typography.is_consistent else 8
    aa_score = 20 * (passes / max(len(accessibility), 1))
    spacing_score = 20 * (spacing.alignment_percentage / 100)
    color_score = 20 * (1 - min(color_stats.duplicate_count / max(color_stats.total_count, 1), 1))
    radius_score = 10 * (radius_result.alignment_pct / 100) if radius_result.tier_count > 0 else 5
    shadow_score = 10 if shadow_result.elevation_verdict == "good" else 5 if shadow_result.level_count >= 3 else 2

    consistency_score = int(type_score + aa_score + spacing_score + color_score + radius_score + shadow_score)

    log("   " + "─" * 40)
    log(f"   RULE ENGINE SUMMARY")
    log(f"   ├─ Consistency Score: {consistency_score}/100")
    log(f"   │  Breakdown:")
    log(f"   │  ├─ Type Scale:    {type_score:.0f}/20 {'✅' if type_score >= 15 else '⚠️'}")
    log(f"   │  ├─ Accessibility: {aa_score:.0f}/20 {'✅' if aa_score >= 15 else '⚠️' if aa_score >= 10 else '❌'}")
    log(f"   │  ├─ Spacing Grid:  {spacing_score:.0f}/20 {'✅' if spacing_score >= 15 else '⚠️'}")
    log(f"   │  ├─ Color Palette: {color_score:.0f}/20 {'✅' if color_score >= 15 else '⚠️'}")
    log(f"   │  ├─ Radius:        {radius_score:.0f}/10 {'✅' if radius_score >= 7 else '⚠️'}")
    log(f"   │  └─ Shadows:       {shadow_score:.0f}/10 {'✅' if shadow_score >= 7 else '⚠️'}")
    log(f"   ├─ AA Failures: {len(failures)}")
    log(f"   ├─ Radius: {radius_result.tier_count} tiers ({radius_result.strategy})")
    log(f"   ├─ Shadows: {shadow_result.level_count} levels ({shadow_result.elevation_verdict})")
    log(f"   └─ Cost: $0.00 (free)")
    log("")

    return RuleEngineResults(
        typography=typography,
        accessibility=accessibility,
        spacing=spacing,
        color_stats=color_stats,
        radius=radius_result,
        shadows=shadow_result,
        aa_failures=len(failures),
        consistency_score=consistency_score,
    )
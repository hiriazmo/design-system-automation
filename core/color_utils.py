"""
Color Utilities
Design System Extractor v2

Functions for color analysis, contrast calculation, and ramp generation.
"""

import re
import colorsys
from typing import Optional
from dataclasses import dataclass


# =============================================================================
# COLOR PARSING
# =============================================================================

@dataclass
class ParsedColor:
    """Parsed color with multiple representations."""
    hex: str
    rgb: tuple[int, int, int]
    hsl: tuple[float, float, float]
    oklch: Optional[tuple[float, float, float]] = None


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c * 2 for c in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex color."""
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Convert RGB to HSL."""
    r_norm, g_norm, b_norm = r / 255, g / 255, b / 255
    h, l, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)
    return (h * 360, s * 100, l * 100)


def hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    """Convert HSL to RGB."""
    h_norm, s_norm, l_norm = h / 360, s / 100, l / 100
    r, g, b = colorsys.hls_to_rgb(h_norm, l_norm, s_norm)
    return (int(r * 255), int(g * 255), int(b * 255))


def parse_color(color_string: str) -> Optional[ParsedColor]:
    """
    Parse any CSS color format to ParsedColor.
    
    Supports:
    - Hex: #fff, #ffffff
    - RGB: rgb(255, 255, 255)
    - RGBA: rgba(255, 255, 255, 0.5)
    - HSL: hsl(0, 100%, 50%)
    """
    color_string = color_string.strip().lower()
    
    # Hex format
    if color_string.startswith("#"):
        hex_color = color_string
        if len(hex_color) == 4:
            hex_color = f"#{hex_color[1]*2}{hex_color[2]*2}{hex_color[3]*2}"
        try:
            rgb = hex_to_rgb(hex_color)
            hsl = rgb_to_hsl(*rgb)
            return ParsedColor(hex=hex_color, rgb=rgb, hsl=hsl)
        except ValueError:
            return None
    
    # RGB/RGBA format
    rgb_match = re.match(r"rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", color_string)
    if rgb_match:
        r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
        hex_color = rgb_to_hex(r, g, b)
        hsl = rgb_to_hsl(r, g, b)
        return ParsedColor(hex=hex_color, rgb=(r, g, b), hsl=hsl)
    
    # HSL format
    hsl_match = re.match(r"hsl\s*\(\s*(\d+)\s*,\s*(\d+)%?\s*,\s*(\d+)%?", color_string)
    if hsl_match:
        h, s, l = float(hsl_match.group(1)), float(hsl_match.group(2)), float(hsl_match.group(3))
        rgb = hsl_to_rgb(h, s, l)
        hex_color = rgb_to_hex(*rgb)
        return ParsedColor(hex=hex_color, rgb=rgb, hsl=(h, s, l))
    
    return None


def normalize_hex(color: str) -> str:
    """Normalize hex color to lowercase 6-digit format."""
    parsed = parse_color(color)
    return parsed.hex if parsed else color


# =============================================================================
# CONTRAST CALCULATIONS (WCAG)
# =============================================================================

def get_luminance(r: int, g: int, b: int) -> float:
    """
    Calculate relative luminance according to WCAG 2.1.
    
    Formula: L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    where R, G, B are linearized values.
    """
    def linearize(c: int) -> float:
        c_norm = c / 255
        if c_norm <= 0.04045:
            return c_norm / 12.92
        return ((c_norm + 0.055) / 1.055) ** 2.4
    
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def get_contrast_ratio(color1: str, color2: str) -> float:
    """
    Calculate WCAG contrast ratio between two colors.
    
    Returns ratio from 1:1 to 21:1
    """
    parsed1 = parse_color(color1)
    parsed2 = parse_color(color2)
    
    if not parsed1 or not parsed2:
        return 1.0
    
    l1 = get_luminance(*parsed1.rgb)
    l2 = get_luminance(*parsed2.rgb)
    
    lighter = max(l1, l2)
    darker = min(l1, l2)
    
    return (lighter + 0.05) / (darker + 0.05)


def check_wcag_compliance(foreground: str, background: str) -> dict:
    """
    Check WCAG compliance for a color pair.
    
    Returns dict with AA and AAA compliance for normal and large text.
    """
    ratio = get_contrast_ratio(foreground, background)
    
    return {
        "contrast_ratio": round(ratio, 2),
        "aa_normal_text": ratio >= 4.5,      # AA for normal text
        "aa_large_text": ratio >= 3.0,       # AA for large text (18pt+ or 14pt+ bold)
        "aaa_normal_text": ratio >= 7.0,     # AAA for normal text
        "aaa_large_text": ratio >= 4.5,      # AAA for large text
    }


def get_contrast_with_white(color: str) -> float:
    """Get contrast ratio against white."""
    return get_contrast_ratio(color, "#ffffff")


def get_contrast_with_black(color: str) -> float:
    """Get contrast ratio against black."""
    return get_contrast_ratio(color, "#000000")


def get_best_text_color(background: str) -> str:
    """Determine whether white or black text works better on a background."""
    white_contrast = get_contrast_with_white(background)
    black_contrast = get_contrast_with_black(background)
    return "#ffffff" if white_contrast > black_contrast else "#000000"


# =============================================================================
# COLOR SIMILARITY & DEDUPLICATION
# =============================================================================

def color_distance(color1: str, color2: str) -> float:
    """
    Calculate perceptual distance between two colors.
    
    Uses simple Euclidean distance in RGB space.
    For more accuracy, consider using CIE Lab Delta E.
    """
    parsed1 = parse_color(color1)
    parsed2 = parse_color(color2)
    
    if not parsed1 or not parsed2:
        return float("inf")
    
    r1, g1, b1 = parsed1.rgb
    r2, g2, b2 = parsed2.rgb
    
    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5


def are_colors_similar(color1: str, color2: str, threshold: float = 10.0) -> bool:
    """Check if two colors are perceptually similar."""
    return color_distance(color1, color2) < threshold


def find_duplicate_colors(colors: list[str], threshold: float = 10.0) -> list[tuple[str, str]]:
    """
    Find pairs of colors that are potentially duplicates.
    
    Returns list of (color1, color2) tuples.
    """
    duplicates = []
    normalized = [normalize_hex(c) for c in colors]
    
    for i, color1 in enumerate(normalized):
        for color2 in normalized[i + 1:]:
            if are_colors_similar(color1, color2, threshold):
                duplicates.append((color1, color2))
    
    return duplicates


def deduplicate_colors(colors: list[str], threshold: float = 10.0) -> list[str]:
    """
    Remove duplicate colors, keeping the first occurrence.
    """
    result = []
    normalized = [normalize_hex(c) for c in colors]
    
    for color in normalized:
        is_duplicate = False
        for existing in result:
            if are_colors_similar(color, existing, threshold):
                is_duplicate = True
                break
        if not is_duplicate:
            result.append(color)
    
    return result


# =============================================================================
# COLOR RAMP GENERATION
# =============================================================================

def generate_color_ramp(
    base_color: str,
    shades: list[int] = None,
    method: str = "hsl"
) -> dict[str, str]:
    """
    Generate a color ramp from a base color.
    
    Args:
        base_color: The base color (typically becomes 500)
        shades: List of shade values (default: [50, 100, 200, 300, 400, 500, 600, 700, 800, 900])
        method: "hsl" (simple) or "oklch" (perceptually uniform, not implemented)
    
    Returns:
        Dict mapping shade to hex color.
    """
    if shades is None:
        shades = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]
    
    parsed = parse_color(base_color)
    if not parsed:
        return {}
    
    h, s, l = parsed.hsl
    ramp = {}
    
    # Base color is 500
    base_shade = 500
    
    for shade in shades:
        if shade == base_shade:
            ramp[str(shade)] = parsed.hex
            continue
        
        # Calculate lightness adjustment
        # Lighter shades (50-400): increase lightness
        # Darker shades (600-900): decrease lightness
        if shade < base_shade:
            # Lighter: interpolate toward white
            factor = (base_shade - shade) / base_shade
            new_l = l + (100 - l) * factor * 0.85
            # Slightly reduce saturation for very light shades
            new_s = s * (1 - factor * 0.3)
        else:
            # Darker: interpolate toward black
            factor = (shade - base_shade) / (900 - base_shade)
            new_l = l * (1 - factor * 0.85)
            # Increase saturation slightly for dark shades
            new_s = min(100, s * (1 + factor * 0.2))
        
        new_rgb = hsl_to_rgb(h, new_s, new_l)
        ramp[str(shade)] = rgb_to_hex(*new_rgb)
    
    return ramp


def generate_accessible_ramp(
    base_color: str,
    background: str = "#ffffff"
) -> dict[str, dict]:
    """
    Generate a color ramp with accessibility information.
    
    Returns dict with color values and their contrast ratios.
    """
    ramp = generate_color_ramp(base_color)
    result = {}
    
    for shade, color in ramp.items():
        compliance = check_wcag_compliance(color, background)
        result[shade] = {
            "value": color,
            "contrast_ratio": compliance["contrast_ratio"],
            "aa_text": compliance["aa_normal_text"],
            "best_text_color": get_best_text_color(color),
        }
    
    return result


# =============================================================================
# COLOR CATEGORIZATION
# =============================================================================

def categorize_color(color: str) -> str:
    """
    Categorize a color by its general hue.
    
    Returns: "red", "orange", "yellow", "green", "cyan", "blue", "purple", "pink", "neutral"
    """
    parsed = parse_color(color)
    if not parsed:
        return "unknown"
    
    h, s, l = parsed.hsl
    
    # Neutrals (low saturation or extreme lightness)
    if s < 10 or l < 5 or l > 95:
        return "neutral"
    
    # Categorize by hue
    if h < 15 or h >= 345:
        return "red"
    elif h < 45:
        return "orange"
    elif h < 70:
        return "yellow"
    elif h < 150:
        return "green"
    elif h < 190:
        return "cyan"
    elif h <= 240:
        return "blue"
    elif h < 295:
        return "purple"
    else:
        return "pink"


def suggest_color_name(color: str, role: str = None) -> str:
    """
    Suggest a semantic name for a color.
    
    Args:
        color: The color value
        role: Optional role hint ("primary", "background", "text", etc.)
    
    Returns suggested name like "blue-500" or "neutral-100"
    """
    parsed = parse_color(color)
    if not parsed:
        return "unknown"
    
    category = categorize_color(color)
    h, s, l = parsed.hsl
    
    # Determine shade level based on lightness
    if l >= 95:
        shade = "50"
    elif l >= 85:
        shade = "100"
    elif l >= 75:
        shade = "200"
    elif l >= 65:
        shade = "300"
    elif l >= 55:
        shade = "400"
    elif l >= 45:
        shade = "500"
    elif l >= 35:
        shade = "600"
    elif l >= 25:
        shade = "700"
    elif l >= 15:
        shade = "800"
    else:
        shade = "900"
    
    return f"{category}-{shade}"


def group_colors_by_category(colors: list[str]) -> dict[str, list[str]]:
    """
    Group colors by their category.
    
    Returns dict mapping category to list of colors.
    """
    groups: dict[str, list[str]] = {}
    
    for color in colors:
        category = categorize_color(color)
        if category not in groups:
            groups[category] = []
        groups[category].append(normalize_hex(color))
    
    return groups


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def sort_colors_by_hue(colors: list[str]) -> list[str]:
    """Sort colors by hue, then by lightness."""
    def sort_key(color: str):
        parsed = parse_color(color)
        if not parsed:
            return (0, 0, 0)
        h, s, l = parsed.hsl
        # Neutrals (low saturation) go at the end
        if s < 10:
            return (360 + l, s, l)
        return (h, s, l)
    
    return sorted([normalize_hex(c) for c in colors], key=sort_key)


def sort_colors_by_lightness(colors: list[str]) -> list[str]:
    """Sort colors from light to dark."""
    def sort_key(color: str):
        parsed = parse_color(color)
        return -parsed.hsl[2] if parsed else 0
    
    return sorted([normalize_hex(c) for c in colors], key=sort_key)


def is_dark_color(color: str) -> bool:
    """Check if a color is considered dark (for text on backgrounds)."""
    parsed = parse_color(color)
    if not parsed:
        return False
    return parsed.hsl[2] < 50


def is_light_color(color: str) -> bool:
    """Check if a color is considered light."""
    return not is_dark_color(color)

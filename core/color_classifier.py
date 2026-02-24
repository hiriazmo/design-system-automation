"""
Rule-Based Color Classifier
Design System Automation v3.1

100% deterministic color classification and naming.
NO LLM involved. Every decision logged with evidence.

The classifier:
1. Aggressively deduplicates similar colors (same role, RGB distance < 30)
2. Classifies by CSS evidence (property + element + hue)
3. Names with capped counts per category (no "nonary" ever again)
4. Supports user-selectable naming conventions (Tailwind, Material, Semantic, Custom)
5. Logs every decision with evidence trail
"""

import colorsys
from dataclasses import dataclass, field
from typing import Optional
from core.color_utils import parse_color, normalize_hex, categorize_color


# =============================================================================
# NAMING CONVENTIONS
# =============================================================================

CONVENTIONS = {
    "tailwind": {
        "separator": "-",       # blue-500
        "shade_format": "numeric",  # 50, 100, 200...900
        "prefix": "",
    },
    "material": {
        "separator": ".",       # blue.500
        "shade_format": "numeric",
        "prefix": "color.",
    },
    "semantic": {
        "separator": ".",       # color.brand.primary
        "shade_format": "role",  # primary, secondary, muted
        "prefix": "color.",
    },
}

# Role shade names for semantic convention
ROLE_SHADE_NAMES = {
    "brand": ["primary", "secondary", "accent"],
    "text": ["primary", "secondary", "muted"],
    "bg": ["primary", "secondary", "tertiary"],
    "border": ["primary", "secondary", "muted"],
    "feedback": ["error", "warning", "success", "info"],
}

# Feedback hue ranges (hue in degrees)
FEEDBACK_HUES = {
    "error": (345, 15),      # Red
    "warning": (15, 55),     # Orange/Yellow
    "success": (85, 155),    # Green
    "info": (175, 215),      # Cyan/Blue
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ClassifiedColor:
    """A color with its classification and evidence."""
    hex: str
    frequency: int
    category: str           # brand, text, bg, border, feedback, palette
    role: str               # primary, secondary, etc. OR numeric shade
    token_name: str         # Final token name (e.g., "color.brand.primary")
    evidence: list[str] = field(default_factory=list)
    confidence: str = "medium"  # high, medium, low
    css_properties: list[str] = field(default_factory=list)
    elements: list[str] = field(default_factory=list)
    contexts: list[str] = field(default_factory=list)
    merged_from: list[str] = field(default_factory=list)  # Hex values merged into this
    hue_family: str = "neutral"
    luminance: float = 0.5
    saturation: float = 0.0


@dataclass
class ClassificationResult:
    """Complete classification output with log."""
    colors: list[ClassifiedColor]
    log: list[str]          # Human-readable decision log
    convention: str         # Which convention was used
    stats: dict = field(default_factory=dict)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _rgb_distance(hex1: str, hex2: str) -> float:
    """Euclidean distance in RGB space."""
    p1 = parse_color(hex1)
    p2 = parse_color(hex2)
    if not p1 or not p2:
        return 999
    r1, g1, b1 = p1.rgb
    r2, g2, b2 = p2.rgb
    return ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** 0.5


def _get_luminance(hex_color: str) -> float:
    """Get perceptual luminance 0-1."""
    parsed = parse_color(hex_color)
    if not parsed:
        return 0.5
    r, g, b = parsed.rgb
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def _get_saturation(hex_color: str) -> float:
    """Get saturation 0-1."""
    parsed = parse_color(hex_color)
    if not parsed:
        return 0
    h, s, l = parsed.hsl
    return s / 100  # hsl returns 0-100


def _get_hue(hex_color: str) -> float:
    """Get hue in degrees 0-360."""
    parsed = parse_color(hex_color)
    if not parsed:
        return 0
    h, s, l = parsed.hsl
    return h


def _hue_in_range(hue: float, range_tuple: tuple) -> bool:
    """Check if hue is in range, handling wrap-around."""
    low, high = range_tuple
    if low < high:
        return low <= hue <= high
    else:  # Wraps around 360 (e.g., red: 345-15)
        return hue >= low or hue <= high


def _lightness_to_shade(lightness_pct: float) -> str:
    """Map HSL lightness (0-100) to numeric shade (50-900)."""
    if lightness_pct >= 95:
        return "50"
    elif lightness_pct >= 85:
        return "100"
    elif lightness_pct >= 75:
        return "200"
    elif lightness_pct >= 65:
        return "300"
    elif lightness_pct >= 55:
        return "400"
    elif lightness_pct >= 45:
        return "500"
    elif lightness_pct >= 35:
        return "600"
    elif lightness_pct >= 25:
        return "700"
    elif lightness_pct >= 15:
        return "800"
    else:
        return "900"


# =============================================================================
# MAIN CLASSIFIER
# =============================================================================

def classify_colors(
    colors_dict: dict,
    convention: str = "semantic",
    log_callback=None,
) -> ClassificationResult:
    """
    Classify and name all colors using 100% rule-based logic.

    Args:
        colors_dict: Dict of name -> ColorToken (from normalizer)
        convention: "tailwind", "material", or "semantic"
        log_callback: Optional callback for real-time logging

    Returns:
        ClassificationResult with classified colors and decision log
    """
    log_lines = []

    def log(msg):
        log_lines.append(msg)
        if log_callback:
            log_callback(msg)

    log("📊 COLOR CLASSIFICATION (Rule-Based v3.1)")
    log("─" * 50)

    if not colors_dict:
        log("⚠️ No colors to classify")
        return ClassificationResult(colors=[], log=log_lines, convention=convention)

    # =========================================================================
    # STEP 1: Build flat color list with metadata
    # =========================================================================
    raw_colors = []
    skipped_invalid = 0
    for name, c in colors_dict.items():
        hex_val = c.value if hasattr(c, 'value') else c.get('value', '')
        hex_val = normalize_hex(hex_val)

        # Validate hex: must be exactly #RRGGBB (7 chars) or #RGB (4 chars)
        if not hex_val or len(hex_val) not in (4, 7) or not hex_val.startswith('#'):
            skipped_invalid += 1
            continue
        # Verify all chars after # are hex digits
        hex_digits = hex_val[1:]
        if not all(ch in '0123456789abcdefABCDEF' for ch in hex_digits):
            skipped_invalid += 1
            continue

        freq = c.frequency if hasattr(c, 'frequency') else c.get('frequency', 0)
        css_props = c.css_properties if hasattr(c, 'css_properties') else c.get('css_properties', [])
        elements = c.elements if hasattr(c, 'elements') else c.get('elements', [])
        contexts = c.contexts if hasattr(c, 'contexts') else c.get('contexts', [])
        role_hint = c.role_hint if hasattr(c, 'role_hint') else c.get('role_hint', None)

        raw_colors.append({
            "hex": hex_val,
            "frequency": freq,
            "css_properties": [p.lower() for p in css_props],
            "elements": [e.lower() for e in elements],
            "contexts": [c.lower() for c in contexts],
            "role_hint": role_hint,
            "luminance": _get_luminance(hex_val),
            "saturation": _get_saturation(hex_val),
            "hue": _get_hue(hex_val),
            "hue_family": categorize_color(hex_val),
        })

    log(f"Input: {len(raw_colors)} unique colors" + (f" ({skipped_invalid} invalid hex values skipped)" if skipped_invalid else ""))

    # =========================================================================
    # STEP 2: Classify each color by CSS evidence
    # =========================================================================
    classified = []
    for c in raw_colors:
        category = _classify_single_color(c)
        c["category"] = category
        classified.append(c)

    # Count per category
    cat_counts = {}
    for c in classified:
        cat_counts[c["category"]] = cat_counts.get(c["category"], 0) + 1
    log(f"Pre-dedup classification: {cat_counts}")

    # =========================================================================
    # STEP 3: Aggressive dedup WITHIN each category
    # =========================================================================
    deduped = _aggressive_dedup(classified, log)

    cat_counts_after = {}
    for c in deduped:
        cat_counts_after[c["category"]] = cat_counts_after.get(c["category"], 0) + 1
    log(f"Post-dedup: {len(deduped)} colors — {cat_counts_after}")

    # =========================================================================
    # STEP 4: Cap and rank within each category
    # =========================================================================
    capped = _cap_per_category(deduped, log)

    # =========================================================================
    # STEP 5: Assign final names using chosen convention
    # =========================================================================
    result_colors = _assign_names(capped, convention, log)

    log(f"─" * 50)
    log(f"✅ Final: {len(result_colors)} color tokens using '{convention}' convention")

    stats = {
        "input_count": len(raw_colors),
        "output_count": len(result_colors),
        "merged_count": len(raw_colors) - len(deduped),
        "categories": cat_counts_after,
    }

    return ClassificationResult(
        colors=result_colors,
        log=log_lines,
        convention=convention,
        stats=stats,
    )


# =============================================================================
# STEP 2: CLASSIFY SINGLE COLOR
# =============================================================================

def _classify_single_color(c: dict) -> str:
    """
    Classify a single color into category based on CSS evidence.
    Returns: "brand", "text", "bg", "border", "feedback", "palette"
    """
    css_props = c["css_properties"]
    elements = c["elements"]
    all_context = " ".join(css_props + elements + c["contexts"])
    sat = c["saturation"]
    lum = c["luminance"]
    hue = c["hue"]
    freq = c["frequency"]

    # --- FEEDBACK: by hue + saturation (check FIRST, before brand) ---
    if sat > 0.4:
        # Check explicit feedback keywords in context
        feedback_keywords = ["error", "danger", "invalid", "success", "valid",
                            "warning", "caution", "alert", "info", "notice"]
        if any(kw in all_context for kw in feedback_keywords):
            return "feedback"

        # Check by hue if frequency is low (feedback colors are rarely used often)
        if freq < 15:
            for fb_type, hue_range in FEEDBACK_HUES.items():
                if _hue_in_range(hue, hue_range):
                    # Additional check: pure saturated colors with low freq = likely feedback
                    if sat > 0.6:
                        return "feedback"

    # --- BRAND: interactive elements + background-color + saturated ---
    interactive = ["button", "a", "input", "select", "submit", "btn", "cta", "link"]
    is_interactive = any(el in all_context for el in interactive)
    has_bg_prop = any("background" in p for p in css_props)

    if sat > 0.25 and is_interactive and has_bg_prop and freq > 5:
        return "brand"
    if sat > 0.3 and freq > 20:
        return "brand"

    # --- TEXT: "color" property on text elements + low saturation ---
    has_color_prop = any(p == "color" for p in css_props)
    text_els = ["p", "span", "h1", "h2", "h3", "h4", "h5", "h6", "label", "li", "td", "a"]
    is_text_el = any(el in all_context for el in text_els)

    if has_color_prop and (is_text_el or sat < 0.15):
        if sat < 0.2:
            return "text"

    # --- BACKGROUND: background-color on containers + light/neutral ---
    containers = ["div", "section", "main", "body", "article", "header", "footer", "card", "nav"]
    is_container = any(el in all_context for el in containers)

    if has_bg_prop and is_container and sat < 0.15:
        return "bg"
    if lum > 0.9 and sat < 0.1:
        return "bg"

    # --- BORDER: border properties ---
    has_border_prop = any("border" in p for p in css_props)
    if has_border_prop and sat < 0.2:
        return "border"

    # --- Neutral with high freq but no clear CSS evidence → likely text ---
    if sat < 0.1 and lum < 0.6 and freq > 10:
        return "text"
    if sat < 0.1 and lum > 0.8:
        return "bg"

    # --- Everything else → palette ---
    return "palette"


# =============================================================================
# STEP 3: AGGRESSIVE DEDUP
# =============================================================================

def _aggressive_dedup(colors: list[dict], log) -> list[dict]:
    """
    Aggressively merge similar colors WITHIN the same category.

    Thresholds:
    - Semantic categories (brand, text, bg, border, feedback): RGB distance < 30
    - Palette: RGB distance < 50 within same hue family (more aggressive)
    """
    # Group by category
    by_category = {}
    for c in colors:
        cat = c["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(c)

    result = []
    total_merged = 0

    for cat, cat_colors in by_category.items():
        if len(cat_colors) <= 1:
            result.extend(cat_colors)
            continue

        if cat == "palette":
            # For palette: dedup within each hue family with higher threshold
            by_hue = {}
            for c in cat_colors:
                hf = c["hue_family"]
                if hf not in by_hue:
                    by_hue[hf] = []
                by_hue[hf].append(c)

            for hue_fam, hue_colors in by_hue.items():
                merged_hue, merged_count = _dedup_group(hue_colors, threshold=50, label=f"palette/{hue_fam}", log=log)
                result.extend(merged_hue)
                total_merged += merged_count
        else:
            merged_cat, merged_count = _dedup_group(cat_colors, threshold=30, label=cat, log=log)
            result.extend(merged_cat)
            total_merged += merged_count

    if total_merged > 0:
        log(f"[DEDUP] Total: {total_merged} near-duplicate colors merged")

    return result


def _dedup_group(colors: list[dict], threshold: float, label: str, log) -> tuple[list[dict], int]:
    """Dedup a group of colors with given RGB distance threshold."""
    colors.sort(key=lambda x: -x["frequency"])
    merged = []
    used = set()
    merged_count = 0

    for i, c1 in enumerate(colors):
        if i in used:
            continue

        group = [c1]
        for j, c2 in enumerate(colors[i+1:], i+1):
            if j in used:
                continue
            dist = _rgb_distance(c1["hex"], c2["hex"])
            if dist < threshold:
                group.append(c2)
                used.add(j)

        primary = group[0]
        merged_hexes = []
        for other in group[1:]:
            primary["frequency"] += other["frequency"]
            primary["css_properties"] = list(set(primary["css_properties"] + other["css_properties"]))
            primary["elements"] = list(set(primary["elements"] + other["elements"]))
            primary["contexts"] = list(set(primary["contexts"] + other["contexts"]))
            merged_hexes.append(other["hex"])

        primary["merged_from"] = merged_hexes
        merged.append(primary)
        used.add(i)

        if merged_hexes:
            merged_count += len(merged_hexes)
            log(f"[DEDUP] {label}: {primary['hex']} absorbed {len(merged_hexes)} similar (dist<{threshold})")

    return merged, merged_count


# =============================================================================
# STEP 4: CAP PER CATEGORY
# =============================================================================

# Maximum colors per category
CATEGORY_CAPS = {
    "brand": 3,       # primary, secondary, accent
    "text": 3,        # primary, secondary, muted
    "bg": 3,          # primary, secondary, tertiary
    "border": 3,      # light, default, dark
    "feedback": 4,    # error, warning, success, info
    "palette": 999,   # palette cap is enforced per-hue-family below
}

# Maximum palette colors PER hue family (e.g., max 4 blues, max 4 reds)
PALETTE_PER_HUE_CAP = 4


def _cap_per_category(colors: list[dict], log) -> list[dict]:
    """
    Limit colors per category. Excess get dropped (not demoted).
    For palette: enforce a per-hue-family cap (max 4 per hue).
    Within each group, keep highest-frequency colors.
    """
    by_category = {}
    for c in colors:
        cat = c["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(c)

    result = []

    for cat, cat_colors in by_category.items():
        cat_colors.sort(key=lambda x: -x["frequency"])

        if cat == "palette":
            # Enforce per-hue-family cap
            by_hue = {}
            for c in cat_colors:
                hf = c["hue_family"]
                if hf not in by_hue:
                    by_hue[hf] = []
                by_hue[hf].append(c)

            for hue_fam, hue_colors in by_hue.items():
                hue_colors.sort(key=lambda x: -x["frequency"])
                kept = hue_colors[:PALETTE_PER_HUE_CAP]
                dropped = hue_colors[PALETTE_PER_HUE_CAP:]
                result.extend(kept)
                if dropped:
                    log(f"[CAP] {hue_fam}: kept top {len(kept)}, dropped {len(dropped)} low-freq palette colors")
        else:
            cap = CATEGORY_CAPS.get(cat, 3)
            kept = cat_colors[:cap]
            dropped = cat_colors[cap:]
            result.extend(kept)
            if dropped:
                log(f"[CAP] {cat}: kept {len(kept)}, dropped {len(dropped)} overflow colors")

    return result


# =============================================================================
# STEP 5: ASSIGN NAMES
# =============================================================================

def _assign_names(colors: list[dict], convention: str, log) -> list[ClassifiedColor]:
    """
    Assign final token names based on chosen convention.

    For palette colors: distributes across unique shade slots per hue family
    (no .2/.3 suffixes). If 4 blues exist, they get shades spread across the
    full 50-900 range based on relative lightness ordering.
    """
    conv = CONVENTIONS.get(convention, CONVENTIONS["semantic"])
    prefix = conv["prefix"]
    sep = conv["separator"]

    # Group by category for role assignment
    by_category = {}
    for c in colors:
        cat = c["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(c)

    result = []
    used_names = set()

    for cat in ["brand", "text", "bg", "border", "feedback", "palette"]:
        cat_colors = by_category.get(cat, [])
        if not cat_colors:
            continue

        # Sort by frequency for consistent ordering
        cat_colors.sort(key=lambda x: -x["frequency"])

        if cat == "palette":
            # PALETTE: Group by hue family, then distribute across shade slots
            result.extend(_assign_palette_names(cat_colors, convention, prefix, sep, used_names, log))
            continue

        for idx, c in enumerate(cat_colors):
            if cat == "feedback":
                role = _assign_feedback_role(c, idx, by_category.get("feedback", []))
            else:
                # Semantic / Tailwind / Material: use role names
                role_names = ROLE_SHADE_NAMES.get(c["category"], ["primary", "secondary", "tertiary"])
                if idx < len(role_names):
                    role = role_names[idx]
                else:
                    role = f"{idx + 1}"

            # Build token name
            if convention == "tailwind":
                token_name = f"{cat}{sep}{role}"
            else:
                token_name = f"{prefix}{cat}{sep}{role}"

            # Collision guard — skip duplicates instead of appending .N suffix
            # (the .N suffix creates invalid nested DTCG when _flat_key_to_nested splits by ".")
            if token_name in used_names:
                log(f"[SKIP] {c['hex']} → {token_name} collision, already taken — dropping")
                continue
            used_names.add(token_name)

            evidence = _build_evidence(c)
            log(f"[NAME] {c['hex']} → {token_name} ({c['category']}, freq={c['frequency']})")

            result.append(ClassifiedColor(
                hex=c["hex"],
                frequency=c["frequency"],
                category=c["category"],
                role=role,
                token_name=token_name,
                evidence=evidence,
                confidence="high" if c["frequency"] > 10 else "medium" if c["frequency"] > 3 else "low",
                css_properties=c["css_properties"],
                elements=c["elements"],
                contexts=c["contexts"],
                merged_from=c.get("merged_from", []),
                hue_family=c["hue_family"],
                luminance=c["luminance"],
                saturation=c["saturation"],
            ))

    return result


# Shade slots ordered by lightness (lightest first)
_SHADE_SLOTS = ["50", "100", "200", "300", "400", "500", "600", "700", "800", "900"]


def _assign_palette_names(
    palette_colors: list[dict],
    convention: str,
    prefix: str,
    sep: str,
    used_names: set,
    log,
) -> list[ClassifiedColor]:
    """
    Assign palette names by hue family with lightness-aware shade mapping.

    Each color gets a shade (50-900) based on its ACTUAL luminance, not a
    fixed slot.  Lightest colors → lowest shade numbers (50/100), darkest → 800/900.
    If two colors in the same hue map to the same shade, the less-frequent one
    is nudged to the nearest free shade.  No .2/.3 suffixes ever.
    """
    # Group by hue family
    by_hue = {}
    for c in palette_colors:
        hf = c["hue_family"]
        if hf not in by_hue:
            by_hue[hf] = []
        by_hue[hf].append(c)

    result = []

    for hue_fam, hue_colors in sorted(by_hue.items()):
        # Sort by luminance: lightest first
        hue_colors.sort(key=lambda x: -x["luminance"])

        # Map each color's luminance to the nearest shade slot.
        # Luminance 0.95+ → 50, 0.0 → 900.  Linear interpolation.
        def _luminance_to_shade(lum: float) -> str:
            # Clamp luminance to [0, 1]
            lum = max(0.0, min(1.0, lum))
            # Map: high luminance → low shade, low luminance → high shade
            # 50 ← 0.95+, 100 ← ~0.85, 200 ← ~0.72, ..., 900 ← 0.0-0.05
            shade_idx = int((1.0 - lum) * (len(_SHADE_SLOTS) - 1) + 0.5)
            shade_idx = max(0, min(len(_SHADE_SLOTS) - 1, shade_idx))
            return _SHADE_SLOTS[shade_idx]

        # Assign shades, resolving collisions within the same hue family
        used_shades_in_hue = set()
        assignments = []  # list of (color_dict, shade_str)

        for c in hue_colors:
            shade = _luminance_to_shade(c["luminance"])
            if shade in used_shades_in_hue:
                # Nudge to nearest free shade
                shade_int = _SHADE_SLOTS.index(shade)
                found = False
                for offset in range(1, len(_SHADE_SLOTS)):
                    for direction in (+1, -1):
                        cand = shade_int + offset * direction
                        if 0 <= cand < len(_SHADE_SLOTS) and _SHADE_SLOTS[cand] not in used_shades_in_hue:
                            shade = _SHADE_SLOTS[cand]
                            found = True
                            break
                    if found:
                        break
            used_shades_in_hue.add(shade)
            assignments.append((c, shade))

        for c, role in assignments:

            if convention == "tailwind":
                token_name = f"{hue_fam}{sep}{role}"
            else:
                token_name = f"{prefix}{hue_fam}{sep}{role}"

            # Name should be unique (cap guarantees max 4 per hue)
            used_names.add(token_name)

            evidence = _build_evidence(c)
            log(f"[NAME] {c['hex']} → {token_name} (palette/{hue_fam}, freq={c['frequency']})")

            result.append(ClassifiedColor(
                hex=c["hex"],
                frequency=c["frequency"],
                category="palette",
                role=role,
                token_name=token_name,
                evidence=evidence,
                confidence="high" if c["frequency"] > 10 else "medium" if c["frequency"] > 3 else "low",
                css_properties=c["css_properties"],
                elements=c["elements"],
                contexts=c["contexts"],
                merged_from=c.get("merged_from", []),
                hue_family=hue_fam,
                luminance=c["luminance"],
                saturation=c["saturation"],
            ))

    return result


def _assign_feedback_role(c: dict, idx: int, all_feedback: list) -> str:
    """Assign feedback role by hue matching."""
    hue = c["hue"]
    sat = c["saturation"]

    # Try to match by hue
    if _hue_in_range(hue, FEEDBACK_HUES["error"]) and sat > 0.4:
        return "error"
    if _hue_in_range(hue, FEEDBACK_HUES["warning"]) and sat > 0.4:
        return "warning"
    if _hue_in_range(hue, FEEDBACK_HUES["success"]) and sat > 0.4:
        return "success"
    if _hue_in_range(hue, FEEDBACK_HUES["info"]) and sat > 0.3:
        return "info"

    # Fallback: by index
    fallback_names = ["error", "warning", "success", "info"]
    return fallback_names[idx % len(fallback_names)]


def _build_evidence(c: dict) -> list[str]:
    """Build human-readable evidence list for classification."""
    ev = []
    if c["frequency"] > 0:
        ev.append(f"Used {c['frequency']}x")
    if c["css_properties"]:
        ev.append(f"CSS: {', '.join(c['css_properties'][:3])}")
    if c["elements"]:
        ev.append(f"Elements: {', '.join(c['elements'][:3])}")
    if c.get("merged_from"):
        ev.append(f"Merged {len(c['merged_from'])} similar colors")
    ev.append(f"Hue: {c['hue_family']}, Lum: {c['luminance']:.2f}, Sat: {c['saturation']:.2f}")
    return ev


# =============================================================================
# PREVIEW GENERATOR
# =============================================================================

def generate_classification_preview(result: ClassificationResult) -> str:
    """
    Generate a human-readable preview of the classification.
    Shows what the user will get before export.
    """
    lines = []
    lines.append(f"🎨 COLOR CLASSIFICATION PREVIEW ({result.convention} convention)")
    lines.append(f"{'=' * 60}")
    lines.append("")

    # Group by category
    by_cat = {}
    for c in result.colors:
        if c.category not in by_cat:
            by_cat[c.category] = []
        by_cat[c.category].append(c)

    cat_labels = {
        "brand": "🏷️  BRAND (from buttons/CTAs)",
        "text": "📝 TEXT (from color property)",
        "bg": "🖼️  BACKGROUND (from containers)",
        "border": "📐 BORDER (from border properties)",
        "feedback": "⚡ FEEDBACK (by hue convention)",
    }

    for cat in ["brand", "text", "bg", "border", "feedback"]:
        cat_colors = by_cat.get(cat, [])
        if not cat_colors:
            continue

        label = cat_labels.get(cat, f"📦 {cat.upper()}")
        lines.append(label)

        for c in cat_colors:
            ev_short = f"({c.frequency}x" + (f", merged {len(c.merged_from)}" if c.merged_from else "") + ")"
            lines.append(f"  ■ {c.hex}  →  {c.token_name}  {ev_short}")

        lines.append("")

    # Palette colors (group by hue family)
    palette = by_cat.get("palette", [])
    if palette:
        lines.append("🎨 PALETTE (remaining by hue)")
        hue_groups = {}
        for c in palette:
            if c.hue_family not in hue_groups:
                hue_groups[c.hue_family] = []
            hue_groups[c.hue_family].append(c)

        for hue_fam, hue_colors in sorted(hue_groups.items()):
            for c in hue_colors:
                lines.append(f"  ■ {c.hex}  →  {c.token_name}  ({c.frequency}x)")

        lines.append("")

    # Stats
    lines.append(f"{'─' * 60}")
    if result.stats:
        lines.append(f"Total: {result.stats.get('output_count', 0)} tokens")
        if result.stats.get("merged_count", 0) > 0:
            lines.append(f"⚠️  {result.stats['merged_count']} near-duplicate colors were merged")

    return "\n".join(lines)

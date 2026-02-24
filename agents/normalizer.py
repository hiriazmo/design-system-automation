"""
Agent 2: Token Normalizer & Structurer
Design System Automation v3

Persona: Design System Librarian

Responsibilities:
- Clean noisy extraction data
- Deduplicate similar tokens (colors within threshold, similar spacing)
- Assign ALL color names using NUMERIC shades only (50-900)
- Add role_hints based on CSS property/element context (absorbed from semantic_analyzer)
- Normalize radius values (parse, deduplicate, sort, name)
- Normalize shadow values (parse, sort by blur, name)
- Fix typography naming collisions (add weight suffix)
- Tag tokens as: detected | inferred | low-confidence
"""

import re
from typing import Optional
from collections import defaultdict

from core.token_schema import (
    ColorToken,
    TypographyToken,
    SpacingToken,
    RadiusToken,
    ShadowToken,
    ExtractedTokens,
    NormalizedTokens,
    Confidence,
    TokenSource,
)
from core.color_utils import (
    parse_color,
    normalize_hex,
    categorize_color,
)


class TokenNormalizer:
    """
    Normalizes and structures extracted tokens.

    This is Agent 2's job — taking raw extraction data and
    organizing it into a clean, deduplicated structure.

    v3 changes:
    - Color naming: ALWAYS numeric shades (50-900), NEVER words (light/dark/base)
    - Role hints: CSS-property-based metadata for AURORA to consume
    - Radius: Full normalization (parse, deduplicate, sort, name)
    - Shadows: Full normalization (parse, sort by blur, deduplicate, name)
    - Typography: Collision-proof naming with weight suffix
    """

    def __init__(self):
        # Thresholds for duplicate detection
        self.color_similarity_threshold = 10  # Delta in RGB space
        self.spacing_merge_threshold = 2  # px difference to merge

        # Radius semantic tiers (px -> name)
        self.radius_tiers = [
            (0, "none"),
            (2, "sm"),
            (4, "md"),
            (8, "lg"),
            (16, "xl"),
            (24, "2xl"),
            (9999, "full"),
        ]

        # Shadow elevation tiers (by count)
        self.shadow_tier_names = ["xs", "sm", "md", "lg", "xl", "2xl"]

    def normalize(self, extracted: ExtractedTokens) -> NormalizedTokens:
        """
        Normalize extracted tokens.

        Args:
            extracted: Raw extraction results from Agent 1

        Returns:
            NormalizedTokens with cleaned, deduplicated data
        """
        # Process each token type (returns lists)
        colors_list = self._normalize_colors(extracted.colors)
        typography_list = self._normalize_typography(extracted.typography)
        spacing_list = self._normalize_spacing(extracted.spacing)
        radius_list = self._normalize_radius(extracted.radius)
        shadows_list = self._normalize_shadows(extracted.shadows)

        # Convert to dicts keyed by suggested_name
        colors_dict = {}
        for c in colors_list:
            key = c.suggested_name or c.value
            # Handle duplicate names by appending a suffix
            if key in colors_dict:
                suffix = 2
                while f"{key}_{suffix}" in colors_dict:
                    suffix += 1
                key = f"{key}_{suffix}"
            colors_dict[key] = c

        typography_dict = {}
        for t in typography_list:
            key = t.suggested_name or f"{t.font_family}-{t.font_size}"
            if key in typography_dict:
                suffix = 2
                while f"{key}_{suffix}" in typography_dict:
                    suffix += 1
                key = f"{key}_{suffix}"
            typography_dict[key] = t

        spacing_dict = {}
        for s in spacing_list:
            key = s.suggested_name or s.value
            if key in spacing_dict:
                suffix = 2
                while f"{key}_{suffix}" in spacing_dict:
                    suffix += 1
                key = f"{key}_{suffix}"
            spacing_dict[key] = s

        # Radius and shadows are already properly named
        radius_dict = {}
        for r in radius_list:
            key = r.suggested_name or f"radius-{r.value}"
            if key in radius_dict:
                suffix = 2
                while f"{key}_{suffix}" in radius_dict:
                    suffix += 1
                key = f"{key}_{suffix}"
            radius_dict[key] = r

        shadows_dict = {}
        for s in shadows_list:
            key = s.suggested_name or f"shadow-{hash(s.value) % 1000}"
            if key in shadows_dict:
                suffix = 2
                while f"{key}_{suffix}" in shadows_dict:
                    suffix += 1
                key = f"{key}_{suffix}"
            shadows_dict[key] = s

        # Create normalized result
        normalized = NormalizedTokens(
            viewport=extracted.viewport,
            source_url=extracted.source_url,
            colors=colors_dict,
            typography=typography_dict,
            spacing=spacing_dict,
            radius=radius_dict,
            shadows=shadows_dict,
            font_families=extracted.font_families,
            detected_spacing_base=extracted.spacing_base,
            detected_naming_convention=extracted.naming_convention,
        )

        return normalized

    # =========================================================================
    # COLOR NORMALIZATION
    # =========================================================================

    def _normalize_colors(self, colors: list[ColorToken]) -> list[ColorToken]:
        """
        Normalize color tokens:
        - Deduplicate similar colors
        - Assign role_hints based on CSS context (absorbed from semantic_analyzer)
        - Assign suggested names using hue + NUMERIC shade (50-900)
        - Calculate confidence

        v3: Removed _infer_color_role() and _generate_color_name_from_value().
        ALL colors now get numeric shades via _generate_preliminary_name().
        Role hints are set for AURORA to consume (not used in naming).
        """
        if not colors:
            return []

        # Step 1: Deduplicate by exact hex value
        unique_colors = {}
        for color in colors:
            hex_val = normalize_hex(color.value)
            if hex_val in unique_colors:
                # Merge frequency and contexts
                existing = unique_colors[hex_val]
                existing.frequency += color.frequency
                existing.contexts = list(set(existing.contexts + color.contexts))
                existing.elements = list(set(existing.elements + color.elements))
                existing.css_properties = list(set(existing.css_properties + color.css_properties))
            else:
                color.value = hex_val
                unique_colors[hex_val] = color

        # Step 2: Merge visually similar colors
        merged_colors = self._merge_similar_colors(list(unique_colors.values()))

        # Step 3: Assign role_hints and preliminary names (ALL numeric)
        for color in merged_colors:
            # Set role_hint based on CSS property/element context
            color.role_hint = self._infer_role_hint(color)

            # Generate name: ALWAYS hue + numeric shade (50-900)
            color.suggested_name = self._generate_preliminary_name(color)

            # Update confidence based on frequency
            color.confidence = self._calculate_confidence(color.frequency)

        # Sort by frequency (most used first)
        merged_colors.sort(key=lambda c: -c.frequency)

        return merged_colors

    def _merge_similar_colors(self, colors: list[ColorToken]) -> list[ColorToken]:
        """Merge colors that are visually very similar."""
        if len(colors) <= 1:
            return colors

        merged = []
        used = set()

        for i, color1 in enumerate(colors):
            if i in used:
                continue

            # Find similar colors
            similar_group = [color1]
            for j, color2 in enumerate(colors[i+1:], i+1):
                if j in used:
                    continue
                if self._colors_are_similar(color1.value, color2.value):
                    similar_group.append(color2)
                    used.add(j)

            # Merge the group - keep the most frequent
            similar_group.sort(key=lambda c: -c.frequency)
            primary = similar_group[0]

            # Aggregate data from similar colors
            for other in similar_group[1:]:
                primary.frequency += other.frequency
                primary.contexts = list(set(primary.contexts + other.contexts))
                primary.elements = list(set(primary.elements + other.elements))
                primary.css_properties = list(set(primary.css_properties + other.css_properties))

            merged.append(primary)
            used.add(i)

        return merged

    def _colors_are_similar(self, hex1: str, hex2: str) -> bool:
        """Check if two colors are visually similar."""
        try:
            parsed1 = parse_color(hex1)
            parsed2 = parse_color(hex2)
            if parsed1 is None or parsed2 is None:
                return False
            if parsed1.rgb is None or parsed2.rgb is None:
                return False

            rgb1 = parsed1.rgb
            rgb2 = parsed2.rgb

            # Calculate Euclidean distance in RGB space
            distance = sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)) ** 0.5
            return distance < self.color_similarity_threshold
        except Exception:
            return False

    def _infer_role_hint(self, color: ColorToken) -> Optional[str]:
        """
        Infer a role_hint for AURORA based on CSS property and element context.

        This replaces the old _infer_color_role() (which was used for naming)
        and absorbs the useful heuristics from semantic_analyzer.py.

        Role hints are metadata for AURORA — they do NOT affect the color name.
        """
        css_props = [p.lower() for p in color.css_properties]
        elements = [e.lower() for e in color.elements]
        contexts = [c.lower() for c in color.contexts]
        all_context = " ".join(css_props + elements + contexts)

        # Calculate color properties for additional heuristics
        parsed = parse_color(color.value)
        if parsed and parsed.rgb:
            r, g, b = parsed.rgb
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            max_c = max(r, g, b)
            min_c = min(r, g, b)
            saturation = (max_c - min_c) / 255 if max_c > 0 else 0
        else:
            luminance = 0.5
            saturation = 0

        # --- BRAND/INTERACTIVE candidate ---
        interactive_elements = ["button", "a", "input", "select", "submit", "btn", "cta", "link"]
        is_interactive = any(el in all_context for el in interactive_elements)
        has_bg_prop = any("background" in p for p in css_props)

        # Interactive elements with background-color + saturated color
        if saturation > 0.25 and is_interactive and has_bg_prop:
            return "brand_candidate"
        # Highly saturated + high frequency
        if saturation > 0.35 and color.frequency > 15:
            return "brand_candidate"

        # --- TEXT candidate ---
        has_color_prop = any(
            p == "color" or (p.endswith("-color") and "background" not in p and "border" not in p)
            for p in css_props
        )
        text_elements = ["p", "span", "h1", "h2", "h3", "h4", "h5", "h6", "label", "text"]
        is_text_element = any(el in all_context for el in text_elements)

        if saturation < 0.15 and (has_color_prop or is_text_element):
            return "text_candidate"
        if saturation < 0.1 and luminance < 0.5 and color.frequency > 30:
            return "text_candidate"

        # --- BACKGROUND candidate ---
        container_elements = ["div", "section", "main", "body", "article", "header", "footer", "card"]
        is_container = any(el in all_context for el in container_elements)

        if has_bg_prop and is_container and saturation < 0.15:
            return "bg_candidate"
        if luminance > 0.9 and saturation < 0.1:
            return "bg_candidate"

        # --- BORDER candidate ---
        has_border_prop = any("border" in p for p in css_props)
        if has_border_prop or "border" in all_context:
            return "border_candidate"

        # --- FEEDBACK candidate ---
        # Check for error/success/warning keywords in context
        feedback_keywords = {
            "error": ["error", "danger", "invalid", "negative"],
            "success": ["success", "valid", "positive"],
            "warning": ["warning", "caution", "alert"],
            "info": ["info", "notice"],
        }
        for fb_type, keywords in feedback_keywords.items():
            if any(kw in all_context for kw in keywords):
                return "feedback_candidate"

        # --- Generic palette color (saturated but no clear role) ---
        if saturation > 0.2:
            return "palette"

        return None

    def _generate_preliminary_name(self, color: ColorToken) -> str:
        """
        Generate a preliminary name using hue family + numeric shade.

        This is the SINGLE naming path for ALL colors.
        Convention: color.{hue_family}.{shade}

        Shade is ALWAYS numeric (50-900) based on HSL lightness.
        NEVER uses words like light/dark/base.

        AURORA may later override these with semantic names (color.brand.primary),
        but the normalizer's job is just hue + shade.
        """
        category = categorize_color(color.value)
        parsed = parse_color(color.value)

        if parsed and parsed.hsl:
            h, s, l = parsed.hsl

            # Map lightness to shade number (50-900)
            # Uses HSL lightness which is more perceptually accurate than
            # the old luminance-based approach
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
        else:
            shade = "500"

        return f"color.{category}.{shade}"

    # =========================================================================
    # TYPOGRAPHY NORMALIZATION
    # =========================================================================

    def _normalize_typography(self, typography: list[TypographyToken]) -> list[TypographyToken]:
        """
        Normalize typography tokens:
        - Deduplicate identical styles
        - Infer type scale categories
        - Assign suggested names with weight suffix to prevent collisions
        """
        if not typography:
            return []

        # Deduplicate by unique style combination
        unique_typo = {}
        for typo in typography:
            key = f"{typo.font_family}|{typo.font_size}|{typo.font_weight}|{typo.line_height}"
            if key in unique_typo:
                existing = unique_typo[key]
                existing.frequency += typo.frequency
                existing.elements = list(set(existing.elements + typo.elements))
            else:
                unique_typo[key] = typo

        result = list(unique_typo.values())

        # Infer names based on size, elements, AND weight (v3: collision fix)
        for typo in result:
            typo.suggested_name = self._generate_typography_name(typo)
            typo.confidence = self._calculate_confidence(typo.frequency)

        # Sort by font size (largest first)
        result.sort(key=lambda t: -self._parse_font_size(t.font_size))

        return result

    def _generate_typography_name(self, typo: TypographyToken) -> str:
        """
        Generate a semantic name for typography.

        v3: Includes font weight in name to prevent collisions.
        Two styles at 24px with weight 700 and 400 now produce
        font.heading.lg.700 and font.heading.lg.400 instead of both being font.heading.lg.
        """
        size_px = self._parse_font_size(typo.font_size)
        elements = " ".join(typo.elements).lower()

        # Determine category from elements
        if any(h in elements for h in ["h1", "hero", "display"]):
            category = "display"
        elif any(h in elements for h in ["h2", "h3", "h4", "h5", "h6", "heading", "title"]):
            category = "heading"
        elif any(h in elements for h in ["label", "caption", "small", "meta"]):
            category = "label"
        elif any(h in elements for h in ["body", "p", "paragraph", "text"]):
            category = "body"
        else:
            category = "text"

        # Determine size tier
        if size_px >= 32:
            size_tier = "xl"
        elif size_px >= 24:
            size_tier = "lg"
        elif size_px >= 18:
            size_tier = "md"
        elif size_px >= 14:
            size_tier = "sm"
        else:
            size_tier = "xs"

        # v3: Include weight to prevent collisions
        weight = typo.font_weight
        return f"font.{category}.{size_tier}.{weight}"

    def _parse_font_size(self, size: str) -> float:
        """Parse font size string to pixels."""
        if not size:
            return 16

        size = size.lower().strip()

        # Handle px
        if "px" in size:
            try:
                return float(size.replace("px", ""))
            except ValueError:
                return 16

        # Handle rem (assume 16px base)
        if "rem" in size:
            try:
                return float(size.replace("rem", "")) * 16
            except ValueError:
                return 16

        # Handle em (assume 16px base)
        if "em" in size:
            try:
                return float(size.replace("em", "")) * 16
            except ValueError:
                return 16

        # Try plain number
        try:
            return float(size)
        except ValueError:
            return 16

    # =========================================================================
    # SPACING NORMALIZATION
    # =========================================================================

    def _normalize_spacing(self, spacing: list[SpacingToken]) -> list[SpacingToken]:
        """
        Normalize spacing tokens:
        - Merge similar values
        - Align to base-8 grid if close
        - Assign suggested names
        """
        if not spacing:
            return []

        # Deduplicate by value
        unique_spacing = {}
        for space in spacing:
            key = space.value
            if key in unique_spacing:
                existing = unique_spacing[key]
                existing.frequency += space.frequency
                existing.contexts = list(set(existing.contexts + space.contexts))
            else:
                unique_spacing[key] = space

        result = list(unique_spacing.values())

        # Merge very similar values
        result = self._merge_similar_spacing(result)

        # Assign names
        for space in result:
            space.suggested_name = self._generate_spacing_name(space)
            space.confidence = self._calculate_confidence(space.frequency)

        # Sort by value
        result.sort(key=lambda s: s.value_px)

        return result

    def _merge_similar_spacing(self, spacing: list[SpacingToken]) -> list[SpacingToken]:
        """Merge spacing values that are very close."""
        if len(spacing) <= 1:
            return spacing

        # Sort by pixel value
        spacing.sort(key=lambda s: s.value_px)

        merged = []
        i = 0

        while i < len(spacing):
            current = spacing[i]
            group = [current]

            # Find adjacent similar values
            j = i + 1
            while j < len(spacing):
                if abs(spacing[j].value_px - current.value_px) <= self.spacing_merge_threshold:
                    group.append(spacing[j])
                    j += 1
                else:
                    break

            # Merge group - prefer base-8 aligned value or most frequent
            group.sort(key=lambda s: (-s.fits_base_8, -s.frequency))
            primary = group[0]

            for other in group[1:]:
                primary.frequency += other.frequency
                primary.contexts = list(set(primary.contexts + other.contexts))

            merged.append(primary)
            i = j

        return merged

    def _generate_spacing_name(self, space: SpacingToken) -> str:
        """Generate a semantic name for spacing."""
        px = space.value_px

        # Map to t-shirt sizes based on value
        if px <= 2:
            size = "px"
        elif px <= 4:
            size = "0.5"
        elif px <= 8:
            size = "1"
        elif px <= 12:
            size = "1.5"
        elif px <= 16:
            size = "2"
        elif px <= 20:
            size = "2.5"
        elif px <= 24:
            size = "3"
        elif px <= 32:
            size = "4"
        elif px <= 40:
            size = "5"
        elif px <= 48:
            size = "6"
        elif px <= 64:
            size = "8"
        elif px <= 80:
            size = "10"
        elif px <= 96:
            size = "12"
        else:
            size = str(int(px / 4))

        return f"space.{size}"

    # =========================================================================
    # RADIUS NORMALIZATION (NEW in v3)
    # =========================================================================

    def _normalize_radius(self, radius_tokens: list[RadiusToken]) -> list[RadiusToken]:
        """
        Normalize border radius tokens.

        v3: Full processing instead of just storing raw values.
        - Parse multi-value shorthand (take max single value)
        - Convert percentage values (50% -> 9999px for "full")
        - Convert rem/em to px
        - Deduplicate by resolved px value
        - Sort by size
        - Assign semantic names (none, sm, md, lg, xl, 2xl, full)
        """
        if not radius_tokens:
            return []

        # Step 1: Parse each radius to a single px value
        parsed_radii = []
        for token in radius_tokens:
            px_value = self._parse_radius_value(token.value)
            if px_value is not None:
                token.value_px = int(px_value)
                token.value = f"{int(px_value)}px"
                # Set grid alignment flags
                token.fits_base_4 = (px_value % 4 == 0) if px_value > 0 else True
                token.fits_base_8 = (px_value % 8 == 0) if px_value > 0 else True
                parsed_radii.append(token)

        # Step 2: Deduplicate by px value
        unique_radii = {}
        for token in parsed_radii:
            key = token.value_px
            if key in unique_radii:
                existing = unique_radii[key]
                existing.frequency += token.frequency
                existing.elements = list(set(existing.elements + token.elements))
            else:
                unique_radii[key] = token

        result = list(unique_radii.values())

        # Step 3: Sort by px value
        result.sort(key=lambda r: r.value_px or 0)

        # Step 4: Assign semantic names
        for token in result:
            token.suggested_name = self._generate_radius_name(token)
            token.confidence = self._calculate_confidence(token.frequency)

        return result

    def _parse_radius_value(self, value: str) -> Optional[int]:
        """
        Parse a CSS border-radius value to a single integer px value.

        Handles:
        - Single values: "8px", "0.5rem", "1em"
        - Multi-value shorthand: "0px 0px 16px 16px" -> take max (16)
        - Percentage: "50%" -> 9999 (treated as "full")
        - "none" / "0" -> 0
        """
        if not value:
            return None

        value = value.strip().lower()

        # Handle "none"
        if value == "none" or value == "0":
            return 0

        # Handle percentage — 50% means fully round, map to 9999
        if "%" in value:
            try:
                pct = float(value.replace("%", "").strip())
                if pct >= 50:
                    return 9999
                # For lower percentages, approximate (not exact, but reasonable)
                # Most radius percentages in practice are 50% for circles
                return int(pct)
            except ValueError:
                return None

        # Handle multi-value shorthand: "0px 0px 16px 16px"
        # Split by spaces and take the max value
        parts = value.split()
        if len(parts) > 1:
            max_px = 0
            for part in parts:
                px = self._parse_single_length(part)
                if px is not None and px > max_px:
                    max_px = px
            return int(max_px) if max_px > 0 else 0

        # Single value
        px = self._parse_single_length(value)
        return int(round(px)) if px is not None else None

    def _parse_single_length(self, value: str) -> Optional[float]:
        """Parse a single CSS length value to px."""
        value = value.strip().lower()

        if "px" in value:
            try:
                return float(value.replace("px", ""))
            except ValueError:
                return None

        if "rem" in value:
            try:
                return float(value.replace("rem", "")) * 16
            except ValueError:
                return None

        if "em" in value:
            try:
                return float(value.replace("em", "")) * 16
            except ValueError:
                return None

        # Try plain number (treat as px)
        try:
            return float(value)
        except ValueError:
            return None

    def _generate_radius_name(self, token: RadiusToken) -> str:
        """
        Generate a semantic name for a border radius token.

        Maps px values to semantic tiers:
        - 0 -> radius.none
        - 1-3 -> radius.sm
        - 4-7 -> radius.md
        - 8-15 -> radius.lg
        - 16-23 -> radius.xl
        - 24-9998 -> radius.2xl
        - 9999 -> radius.full
        """
        px = token.value_px or 0

        if px == 0:
            return "radius.none"
        elif px >= 9999:
            return "radius.full"
        elif px <= 3:
            return "radius.sm"
        elif px <= 7:
            return "radius.md"
        elif px <= 15:
            return "radius.lg"
        elif px <= 23:
            return "radius.xl"
        else:
            return "radius.2xl"

    # =========================================================================
    # SHADOW NORMALIZATION (NEW in v3)
    # =========================================================================

    def _normalize_shadows(self, shadow_tokens: list[ShadowToken]) -> list[ShadowToken]:
        """
        Normalize box shadow tokens.

        v3: Full processing instead of hash-based keys.
        - Parse shadow CSS into components (if not already parsed)
        - Compute blur_px and y_offset_px for sorting
        - Filter out spread-only shadows (border simulations)
        - Separate inset shadows into their own category
        - Sort by blur radius (elevation)
        - Deduplicate visually similar shadows
        - Assign semantic names (xs, sm, md, lg, xl)
        """
        if not shadow_tokens:
            return []

        # Step 1: Parse and compute numeric values
        parsed_shadows = []
        for token in shadow_tokens:
            self._ensure_shadow_parsed(token)

            # Skip spread-only shadows (border simulations)
            if (token.blur_px is None or token.blur_px == 0) and token.spread and token.spread != "0px":
                continue

            # Skip inset shadows (different semantic — handle separately if needed)
            if token.inset:
                continue

            # Skip shadows with no meaningful blur
            if token.blur_px is not None and token.blur_px <= 0:
                continue

            parsed_shadows.append(token)

        if not parsed_shadows:
            return []

        # Step 2: Deduplicate by visual similarity (same blur + y-offset range)
        unique_shadows = []
        seen_blur_values = set()
        for token in parsed_shadows:
            blur = token.blur_px or 0
            # Round to nearest 2px for dedup
            blur_bucket = round(blur / 2) * 2
            if blur_bucket not in seen_blur_values:
                seen_blur_values.add(blur_bucket)
                unique_shadows.append(token)
            else:
                # Merge frequency with existing
                for existing in unique_shadows:
                    existing_blur = round((existing.blur_px or 0) / 2) * 2
                    if existing_blur == blur_bucket:
                        existing.frequency += token.frequency
                        existing.elements = list(set(existing.elements + token.elements))
                        break

        # Step 3: Sort by blur radius (ascending = increasing elevation)
        unique_shadows.sort(key=lambda s: s.blur_px or 0)

        # Step 4: Assign semantic names based on sort order
        for i, token in enumerate(unique_shadows):
            if i < len(self.shadow_tier_names):
                tier_name = self.shadow_tier_names[i]
            else:
                tier_name = f"{i + 1}xl"
            token.suggested_name = f"shadow.{tier_name}"
            token.confidence = self._calculate_confidence(token.frequency)

        return unique_shadows

    def _ensure_shadow_parsed(self, token: ShadowToken):
        """
        Ensure shadow token has parsed components and computed px values.

        If offset_x/offset_y/blur/spread/color are None, attempt to parse
        from the raw CSS value string.
        """
        # Compute blur_px from blur string
        if token.blur is not None and token.blur_px is None:
            px = self._parse_single_length(token.blur)
            token.blur_px = px if px is not None else 0

        # Compute y_offset_px from offset_y string
        if token.offset_y is not None and token.y_offset_px is None:
            px = self._parse_single_length(token.offset_y)
            token.y_offset_px = px if px is not None else 0

        # If components are all None, try to parse from CSS value
        if token.blur is None and token.offset_x is None:
            self._parse_shadow_css(token)

    def _parse_shadow_css(self, token: ShadowToken):
        """
        Parse a CSS box-shadow value into components.

        Format: [inset] <offset-x> <offset-y> [blur] [spread] <color>
        Example: "0px 4px 8px 0px rgba(0,0,0,0.1)"
        """
        value = token.value.strip()

        # Check for inset
        if value.startswith("inset"):
            token.inset = True
            value = value[5:].strip()

        # Extract color (rgba/rgb/hex at the end or beginning)
        color_match = re.search(
            r'(rgba?\s*\([^)]+\)|#[0-9a-fA-F]{3,8})\s*$',
            value
        )
        if color_match:
            token.color = color_match.group(1).strip()
            value = value[:color_match.start()].strip()
        else:
            # Try color at the beginning
            color_match = re.search(
                r'^(rgba?\s*\([^)]+\)|#[0-9a-fA-F]{3,8})\s+',
                value
            )
            if color_match:
                token.color = color_match.group(1).strip()
                value = value[color_match.end():].strip()

        # Parse remaining length values
        length_pattern = r'(-?\d+(?:\.\d+)?(?:px|rem|em|%)?)'
        lengths = re.findall(length_pattern, value)

        if len(lengths) >= 2:
            token.offset_x = lengths[0]
            token.offset_y = lengths[1]
            px = self._parse_single_length(lengths[1])
            token.y_offset_px = px if px is not None else 0

        if len(lengths) >= 3:
            token.blur = lengths[2]
            px = self._parse_single_length(lengths[2])
            token.blur_px = px if px is not None else 0

        if len(lengths) >= 4:
            token.spread = lengths[3]

        # Default blur_px to 0 if still None
        if token.blur_px is None:
            token.blur_px = 0
        if token.y_offset_px is None:
            token.y_offset_px = 0

    # =========================================================================
    # SHARED UTILITIES
    # =========================================================================

    def _calculate_confidence(self, frequency: int) -> Confidence:
        """Calculate confidence based on frequency."""
        if frequency >= 10:
            return Confidence.HIGH
        elif frequency >= 3:
            return Confidence.MEDIUM
        else:
            return Confidence.LOW


def normalize_tokens(extracted: ExtractedTokens) -> NormalizedTokens:
    """Convenience function to normalize tokens."""
    normalizer = TokenNormalizer()
    return normalizer.normalize(extracted)

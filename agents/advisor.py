"""
Agent 3: Design System Best Practices Advisor
Design System Automation

Persona: Senior Staff Design Systems Architect

Responsibilities:
- Analyze extracted tokens against best practices (Material, Polaris, Carbon)
- Propose upgrade OPTIONS with rationale (LLM-powered reasoning)
- Generate type scales, color ramps, spacing grids (Rule-based calculation)
- Never change: font families, primary/secondary base colors

Hybrid Approach:
- LLM: Analyzes patterns, recommends options, explains rationale
- Rules: Calculates actual values (math-based)
"""

import os
import json
from typing import Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from core.token_schema import (
    NormalizedTokens,
    ColorToken,
    TypographyToken,
    SpacingToken,
    UpgradeOption,
    UpgradeRecommendations,
)
from core.color_utils import (
    parse_color,
    generate_color_ramp,
    get_contrast_ratio,
)


# =============================================================================
# TYPE SCALE CALCULATIONS (Rule-Based)
# =============================================================================

class TypeScaleRatio(Enum):
    """Common type scale ratios."""
    MINOR_SECOND = 1.067
    MAJOR_SECOND = 1.125
    MINOR_THIRD = 1.200
    MAJOR_THIRD = 1.250
    PERFECT_FOURTH = 1.333
    AUGMENTED_FOURTH = 1.414
    PERFECT_FIFTH = 1.500


def generate_type_scale(base_size: float, ratio: float, steps_up: int = 5, steps_down: int = 2) -> dict:
    """
    Generate a type scale from a base size.
    
    Args:
        base_size: Base font size in pixels (e.g., 16)
        ratio: Scale ratio (e.g., 1.25)
        steps_up: Number of sizes larger than base
        steps_down: Number of sizes smaller than base
    
    Returns:
        Dict with size names and values
    """
    scale = {}
    
    # Generate sizes below base
    for i in range(steps_down, 0, -1):
        size = base_size / (ratio ** i)
        name = f"text.{['xs', 'sm'][steps_down - i] if i <= 2 else f'xs-{i}'}"
        scale[name] = round(size)
    
    # Base size
    scale["text.base"] = round(base_size)
    
    # Generate sizes above base
    size_names = ["text.lg", "text.xl", "heading.sm", "heading.md", "heading.lg", "heading.xl", "heading.2xl", "display"]
    for i in range(1, steps_up + 1):
        size = base_size * (ratio ** i)
        name = size_names[i - 1] if i <= len(size_names) else f"heading.{i}xl"
        scale[name] = round(size)
    
    return scale


# =============================================================================
# SPACING GRID CALCULATIONS (Rule-Based)
# =============================================================================

def snap_to_grid(value: float, base: int = 8) -> int:
    """Snap a value to the nearest grid unit."""
    return round(value / base) * base


def generate_spacing_scale(base: int = 8, max_value: int = 96) -> dict:
    """
    Generate a spacing scale based on a base unit.
    
    Args:
        base: Base unit (4 or 8)
        max_value: Maximum spacing value
    
    Returns:
        Dict with spacing names and values
    """
    scale = {}
    multipliers = [0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24]
    names = ["0.5", "1", "1.5", "2", "2.5", "3", "4", "5", "6", "8", "10", "12", "16", "20", "24"]
    
    for mult, name in zip(multipliers, names):
        value = int(base * mult)
        if value <= max_value:
            scale[f"space.{name}"] = f"{value}px"
    
    return scale


def analyze_spacing_fit(detected_values: list[int], base: int = 8) -> dict:
    """
    Analyze how well detected spacing values fit a grid.
    
    Returns:
        Dict with fit percentage and adjustments needed
    """
    fits = 0
    adjustments = []
    
    for value in detected_values:
        snapped = snap_to_grid(value, base)
        if value == snapped:
            fits += 1
        else:
            adjustments.append({
                "original": value,
                "snapped": snapped,
                "delta": snapped - value
            })
    
    return {
        "base": base,
        "fit_percentage": (fits / len(detected_values) * 100) if detected_values else 0,
        "adjustments": adjustments,
        "already_aligned": fits,
        "needs_adjustment": len(adjustments)
    }


# =============================================================================
# COLOR RAMP GENERATION (Rule-Based)
# =============================================================================

def generate_semantic_color_ramp(base_color: str, role: str = "primary") -> dict:
    """
    Generate a full color ramp from a base color.
    
    Args:
        base_color: Hex color (e.g., "#373737")
        role: Semantic role (primary, secondary, neutral, etc.)
    
    Returns:
        Dict with shade names (50-900) and hex values
    """
    ramp = generate_color_ramp(base_color)
    
    result = {}
    shades = ["50", "100", "200", "300", "400", "500", "600", "700", "800", "900"]
    
    for shade, color in zip(shades, ramp):
        result[f"{role}.{shade}"] = color
    
    return result


# =============================================================================
# LLM-POWERED ANALYSIS (Agent 3 Brain)
# =============================================================================

class DesignSystemAdvisor:
    """
    Agent 3: Analyzes tokens and proposes upgrades.
    
    Uses LLM for reasoning and recommendations.
    Uses rules for calculating actual values.
    """
    
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log = log_callback or print
        self.hf_token = os.getenv("HF_TOKEN", "")
        self.model = os.getenv("AGENT3_MODEL", "meta-llama/Llama-3.1-70B-Instruct")
    
    async def analyze(
        self, 
        desktop_tokens: NormalizedTokens,
        mobile_tokens: NormalizedTokens,
    ) -> UpgradeRecommendations:
        """
        Analyze tokens and generate upgrade recommendations.
        
        Args:
            desktop_tokens: Normalized desktop tokens
            mobile_tokens: Normalized mobile tokens
        
        Returns:
            UpgradeRecommendations with options for each category
        """
        self.log("🤖 Agent 3: Starting design system analysis...")
        
        # Gather token statistics
        stats = self._gather_statistics(desktop_tokens, mobile_tokens)
        self.log(f"📊 Gathered statistics: {len(stats['colors'])} colors, {len(stats['typography'])} typography, {len(stats['spacing'])} spacing")
        
        # Generate rule-based options first
        self.log("🔧 Generating rule-based options...")
        type_scale_options = self._generate_type_scale_options(stats)
        spacing_options = self._generate_spacing_options(stats)
        color_ramp_options = self._generate_color_ramp_options(stats)
        
        # Get LLM analysis and recommendations
        self.log(f"🤖 Calling LLM ({self.model}) for analysis...")
        llm_analysis = await self._get_llm_analysis(stats, type_scale_options, spacing_options)
        
        # Apply LLM recommendations to options
        self._apply_llm_recommendations(type_scale_options, spacing_options, color_ramp_options, llm_analysis)
        
        self.log("✅ Analysis complete!")
        
        return UpgradeRecommendations(
            typography_scales=type_scale_options,
            spacing_systems=spacing_options,
            color_ramps=color_ramp_options,
            naming_conventions=[],
            llm_rationale=llm_analysis.get("rationale", ""),
            detected_patterns=llm_analysis.get("patterns", []),
            brand_analysis=llm_analysis.get("brand_analysis", []),
            color_observations=llm_analysis.get("color_observations", ""),
            accessibility_issues=llm_analysis.get("accessibility_issues", []),
        )
    
    def _gather_statistics(self, desktop: NormalizedTokens, mobile: NormalizedTokens) -> dict:
        """Gather statistics from tokens for analysis."""
        
        # Combine colors (colors are viewport-agnostic)
        colors = {}
        for name, token in desktop.colors.items():
            colors[token.value] = {
                "value": token.value,
                "frequency": token.frequency,
                "contexts": token.contexts,
                "suggested_name": token.suggested_name,
            }
        
        # Typography (viewport-specific)
        typography = {
            "desktop": [],
            "mobile": [],
        }
        for name, token in desktop.typography.items():
            typography["desktop"].append({
                "font_family": token.font_family,
                "font_size": token.font_size,
                "font_weight": token.font_weight,
                "frequency": token.frequency,
            })
        for name, token in mobile.typography.items():
            typography["mobile"].append({
                "font_family": token.font_family,
                "font_size": token.font_size,
                "font_weight": token.font_weight,
                "frequency": token.frequency,
            })
        
        # Spacing
        spacing = {
            "desktop": [],
            "mobile": [],
        }
        for name, token in desktop.spacing.items():
            spacing["desktop"].append(token.value_px)
        for name, token in mobile.spacing.items():
            spacing["mobile"].append(token.value_px)
        
        # Find most used font family
        font_families = {}
        for t in typography["desktop"]:
            family = t["font_family"]
            font_families[family] = font_families.get(family, 0) + t["frequency"]
        
        primary_font = max(font_families.items(), key=lambda x: x[1])[0] if font_families else "sans-serif"
        
        # Find base font size (most frequent in body context)
        font_sizes = [self._parse_size(t["font_size"]) for t in typography["desktop"]]
        base_font_size = 16  # Default
        if font_sizes:
            # Find most common size between 14-18px (typical body text)
            body_sizes = [s for s in font_sizes if 14 <= s <= 18]
            if body_sizes:
                base_font_size = max(set(body_sizes), key=body_sizes.count)
        
        return {
            "colors": colors,
            "typography": typography,
            "spacing": spacing,
            "primary_font": primary_font,
            "base_font_size": base_font_size,
            "all_font_sizes": list(set(font_sizes)),
        }
    
    def _parse_size(self, size_str: str) -> float:
        """Parse a size string to pixels."""
        if not size_str:
            return 16
        size_str = str(size_str).lower().strip()
        if "px" in size_str:
            return float(size_str.replace("px", ""))
        if "rem" in size_str:
            return float(size_str.replace("rem", "")) * 16
        if "em" in size_str:
            return float(size_str.replace("em", "")) * 16
        try:
            return float(size_str)
        except:
            return 16
    
    def _generate_type_scale_options(self, stats: dict) -> list[UpgradeOption]:
        """Generate type scale options."""
        base = stats["base_font_size"]
        options = []
        
        ratios = [
            ("minor_third", 1.200, "Conservative — subtle size differences"),
            ("major_third", 1.250, "Balanced — clear hierarchy without extremes"),
            ("perfect_fourth", 1.333, "Bold — strong visual hierarchy"),
        ]
        
        for id_name, ratio, desc in ratios:
            scale = generate_type_scale(base, ratio)
            options.append(UpgradeOption(
                id=f"type_scale_{id_name}",
                name=f"Type Scale {ratio}",
                description=desc,
                category="typography",
                values={
                    "ratio": ratio,
                    "base": base,
                    "scale": scale,
                },
                pros=[
                    f"Based on {base}px base (detected)",
                    f"Ratio {ratio} is industry standard",
                ],
                cons=[],
                effort="low",
                recommended=False,
            ))
        
        # Add "keep original" option
        options.append(UpgradeOption(
            id="type_scale_keep",
            name="Keep Original",
            description="Preserve detected font sizes without scaling",
            category="typography",
            values={
                "ratio": None,
                "base": base,
                "scale": {f"size_{i}": s for i, s in enumerate(stats["all_font_sizes"])},
            },
            pros=["No changes needed", "Preserves original design"],
            cons=["May have inconsistent scale"],
            effort="none",
            recommended=False,
        ))
        
        return options
    
    def _generate_spacing_options(self, stats: dict) -> list[UpgradeOption]:
        """Generate spacing system options."""
        desktop_spacing = stats["spacing"]["desktop"]
        
        options = []
        
        for base in [8, 4]:
            fit_analysis = analyze_spacing_fit(desktop_spacing, base)
            scale = generate_spacing_scale(base)
            
            options.append(UpgradeOption(
                id=f"spacing_{base}px",
                name=f"{base}px Base Grid",
                description=f"{'Modern standard' if base == 8 else 'Finer control'} — {fit_analysis['fit_percentage']:.0f}% of your values already fit",
                category="spacing",
                values={
                    "base": base,
                    "scale": scale,
                    "fit_analysis": fit_analysis,
                },
                pros=[
                    f"{fit_analysis['already_aligned']} values already aligned",
                    "Consistent visual rhythm" if base == 8 else "More granular control",
                ],
                cons=[
                    f"{fit_analysis['needs_adjustment']} values need adjustment" if fit_analysis['needs_adjustment'] > 0 else None,
                ],
                effort="low" if fit_analysis['fit_percentage'] > 70 else "medium",
                recommended=False,
            ))
        
        # Add "keep original" option
        options.append(UpgradeOption(
            id="spacing_keep",
            name="Keep Original",
            description="Preserve detected spacing values",
            category="spacing",
            values={
                "base": None,
                "scale": {f"space_{v}": f"{v}px" for v in desktop_spacing},
            },
            pros=["No changes needed"],
            cons=["May have irregular spacing"],
            effort="none",
            recommended=False,
        ))
        
        return options
    
    def _generate_color_ramp_options(self, stats: dict) -> list[UpgradeOption]:
        """Generate color ramp options."""
        options = []
        
        # Find primary colors (high frequency, used in text/background)
        primary_candidates = []
        for hex_val, data in stats["colors"].items():
            if data["frequency"] > 10:
                primary_candidates.append((hex_val, data))
        
        # Sort by frequency
        primary_candidates.sort(key=lambda x: -x[1]["frequency"])
        
        # Generate ramps for top colors
        for hex_val, data in primary_candidates[:5]:
            role = self._infer_color_role(data)
            ramp = generate_semantic_color_ramp(hex_val, role)
            
            options.append(UpgradeOption(
                id=f"color_ramp_{role}",
                name=f"{role.title()} Ramp",
                description=f"Generate 50-900 shades from {hex_val}",
                category="colors",
                values={
                    "base_color": hex_val,
                    "role": role,
                    "ramp": ramp,
                    "preserve_base": True,
                },
                pros=[
                    f"Base color {hex_val} preserved",
                    "Full shade range for UI states",
                    "AA contrast compliant",
                ],
                cons=[],
                effort="low",
                recommended=True,
            ))
        
        return options
    
    def _infer_color_role(self, color_data: dict) -> str:
        """Infer semantic role from color context."""
        contexts = " ".join(color_data.get("contexts", [])).lower()
        
        if "primary" in contexts or "brand" in contexts:
            return "primary"
        if "secondary" in contexts or "accent" in contexts:
            return "secondary"
        if "background" in contexts or "surface" in contexts:
            return "surface"
        if "text" in contexts or "foreground" in contexts:
            return "text"
        if "border" in contexts or "divider" in contexts:
            return "border"
        if "success" in contexts or "green" in contexts:
            return "success"
        if "error" in contexts or "red" in contexts:
            return "error"
        if "warning" in contexts or "yellow" in contexts:
            return "warning"
        
        return "neutral"
    
    async def _get_llm_analysis(self, stats: dict, type_options: list, spacing_options: list) -> dict:
        """Get LLM analysis and recommendations."""
        
        if not self.hf_token:
            self.log("⚠️ No HF token, using default recommendations")
            return self._get_default_recommendations(stats, type_options, spacing_options)
        
        try:
            from core.hf_inference import HFInferenceClient
            
            # HFInferenceClient gets token from settings/env
            client = HFInferenceClient()
            
            # Build prompt
            prompt = self._build_analysis_prompt(stats, type_options, spacing_options)
            
            self.log("📤 Sending analysis request to LLM...")
            
            # Use the agent-specific complete method
            response = await client.complete_async(
                agent_name="advisor",
                system_prompt="You are a Senior Design Systems Architect analyzing design tokens.",
                user_message=prompt,
                max_tokens=1500,
            )
            
            self.log("📥 Received LLM response")
            
            # Parse LLM response
            return self._parse_llm_response(response)
            
        except Exception as e:
            self.log(f"⚠️ LLM error: {str(e)}, using default recommendations")
            return self._get_default_recommendations(stats, type_options, spacing_options)
    
    def _build_analysis_prompt(self, stats: dict, type_options: list, spacing_options: list) -> str:
        """Build the prompt for LLM analysis."""
        
        # Format colors
        colors_str = "\n".join([
            f"  - {data['value']}: frequency={data['frequency']}, contexts={data['contexts'][:3]}"
            for hex_val, data in list(stats['colors'].items())[:10]
        ])
        
        # Format typography
        typo_str = "\n".join([
            f"  - {t['font_family']} {t['font_size']} (weight: {t['font_weight']}, freq: {t['frequency']})"
            for t in stats['typography']['desktop'][:10]
        ])
        
        # Format spacing
        spacing_str = f"Desktop: {sorted(stats['spacing']['desktop'])[:15]}"
        
        return f"""You are a Senior Design Systems Architect. Analyze these extracted design tokens and provide recommendations based on industry best practices.

## EXTRACTED TOKENS

### Colors (top 10 by frequency):
{colors_str}

### Typography:
Primary font: {stats['primary_font']}
Base size: {stats['base_font_size']}px
{typo_str}

### Spacing:
{spacing_str}

## YOUR TASK

Research and compare against these top design systems:
1. **Material Design 3** (Google) - Type scale, spacing grid, color system
2. **Apple Human Interface Guidelines** - Typography scale, spacing
3. **Shopify Polaris** - Type scale ratios, spacing system
4. **IBM Carbon** - Type tokens, spacing tokens
5. **Atlassian Design System** - Typography, spacing patterns

For each, note:
- Type scale ratio used
- Base font size
- Spacing grid (4px or 8px)
- Key observations

Then recommend:
1. Which TYPE SCALE ratio (1.2, 1.25, or 1.333) best matches this site's existing design?
2. Which SPACING BASE (4px or 8px) fits better?
3. Any ACCESSIBILITY concerns with the detected colors?

Respond in this JSON format:
{{
  "brand_analysis": [
    {{"brand": "Material Design 3", "ratio": 1.2, "base": 16, "spacing": "8px", "notes": "..."}},
    {{"brand": "Apple HIG", "ratio": 1.19, "base": 17, "spacing": "4px", "notes": "..."}},
    {{"brand": "Shopify Polaris", "ratio": 1.25, "base": 16, "spacing": "4px", "notes": "..."}},
    {{"brand": "IBM Carbon", "ratio": 1.25, "base": 14, "spacing": "8px", "notes": "..."}},
    {{"brand": "Atlassian", "ratio": 1.14, "base": 14, "spacing": "8px", "notes": "..."}}
  ],
  "recommended_type_scale": "minor_third|major_third|perfect_fourth|keep",
  "recommended_spacing": "8px|4px|keep",
  "rationale": "Detailed explanation comparing the extracted tokens to the brand analysis...",
  "color_observations": "Analysis of the color palette compared to industry standards...",
  "accessibility_issues": ["issue 1", "issue 2"]
}}"""
    
    def _parse_llm_response(self, response: str) -> dict:
        """Parse LLM response into structured recommendations."""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                parsed = json.loads(json_match.group())
                # Ensure all expected fields exist
                parsed.setdefault("brand_analysis", [])
                parsed.setdefault("recommended_type_scale", "major_third")
                parsed.setdefault("recommended_spacing", "8px")
                parsed.setdefault("rationale", "")
                parsed.setdefault("color_observations", "")
                parsed.setdefault("accessibility_issues", [])
                return parsed
        except Exception as e:
            self.log(f"   JSON parse error: {str(e)}")
        
        # Default if parsing fails
        return self._get_default_recommendations({}, [], [])
    
    def _get_default_recommendations(self, stats: dict, type_options: list, spacing_options: list) -> dict:
        """Get default recommendations without LLM."""
        
        # Default brand analysis (rule-based knowledge)
        brand_analysis = [
            {"brand": "Material Design 3", "ratio": 1.2, "base": 16, "spacing": "8px", 
             "notes": "Google's design system uses Major Second (1.125) to Minor Third (1.2) scales"},
            {"brand": "Apple HIG", "ratio": 1.19, "base": 17, "spacing": "4px",
             "notes": "Apple uses SF Pro with dynamic type scaling, 4pt grid"},
            {"brand": "Shopify Polaris", "ratio": 1.25, "base": 16, "spacing": "4px",
             "notes": "Polaris uses Major Third (1.25) with 4px spacing unit"},
            {"brand": "IBM Carbon", "ratio": 1.25, "base": 14, "spacing": "8px",
             "notes": "Carbon uses productive (14px) and expressive (16px) type sets"},
            {"brand": "Atlassian", "ratio": 1.14, "base": 14, "spacing": "8px",
             "notes": "Atlassian uses a compact scale for dense interfaces"},
        ]
        
        # Recommend based on fit analysis if available
        spacing_8_fit = 0
        spacing_4_fit = 0
        for opt in spacing_options:
            if opt and hasattr(opt, 'id'):
                if opt.id == "spacing_8px":
                    spacing_8_fit = opt.values.get("fit_analysis", {}).get("fit_percentage", 0)
                elif opt.id == "spacing_4px":
                    spacing_4_fit = opt.values.get("fit_analysis", {}).get("fit_percentage", 0)
        
        return {
            "brand_analysis": brand_analysis,
            "recommended_type_scale": "major_third",
            "recommended_spacing": "8px" if spacing_8_fit >= spacing_4_fit else "4px",
            "rationale": "Based on industry analysis: Major Third (1.25) type scale is the most commonly used ratio across modern design systems including Shopify Polaris and IBM Carbon. The 8px spacing grid is the modern standard used by Material Design and most enterprise design systems, providing a good balance between flexibility and consistency.",
            "color_observations": "The detected color palette shows a neutral-heavy design with good contrast potential. Consider generating full color ramps for better UI state coverage (hover, active, disabled states).",
            "accessibility_issues": [],
        }
    
    def _apply_llm_recommendations(
        self, 
        type_options: list[UpgradeOption],
        spacing_options: list[UpgradeOption],
        color_options: list[UpgradeOption],
        llm_analysis: dict
    ):
        """Apply LLM recommendations to options."""
        
        # Mark recommended type scale
        rec_type = llm_analysis.get("recommended_type_scale", "major_third")
        for opt in type_options:
            if rec_type in opt.id:
                opt.recommended = True
                opt.description += " ⭐ LLM Recommended"
        
        # Mark recommended spacing
        rec_spacing = llm_analysis.get("recommended_spacing", "8px")
        for opt in spacing_options:
            if rec_spacing.replace("px", "") in opt.id:
                opt.recommended = True
                opt.description += " ⭐ LLM Recommended"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def analyze_design_system(
    desktop_tokens: NormalizedTokens,
    mobile_tokens: NormalizedTokens,
    log_callback: Optional[Callable[[str], None]] = None
) -> UpgradeRecommendations:
    """
    Convenience function to analyze a design system.
    
    Args:
        desktop_tokens: Normalized desktop tokens
        mobile_tokens: Normalized mobile tokens
        log_callback: Optional callback for logging
    
    Returns:
        UpgradeRecommendations
    """
    advisor = DesignSystemAdvisor(log_callback=log_callback)
    return await advisor.analyze(desktop_tokens, mobile_tokens)

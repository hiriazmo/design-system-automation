"""
Token Schema Definitions
Design System Automation v3

Pydantic models for all token types and extraction results.
These are the core data structures used throughout the application.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# ENUMS
# =============================================================================

class TokenSource(str, Enum):
    """Origin of a token value."""
    DETECTED = "detected"       # Directly found in CSS
    INFERRED = "inferred"       # Derived from patterns
    UPGRADED = "upgraded"       # User-selected improvement
    MANUAL = "manual"           # User manually added


class Confidence(str, Enum):
    """Confidence level for extracted tokens."""
    HIGH = "high"               # 10+ occurrences, consistent usage
    MEDIUM = "medium"           # 3-9 occurrences
    LOW = "low"                 # 1-2 occurrences or conflicting


class Viewport(str, Enum):
    """Viewport type."""
    DESKTOP = "desktop"         # 1440px width
    MOBILE = "mobile"           # 375px width


class PageType(str, Enum):
    """Type of page template."""
    HOMEPAGE = "homepage"
    LISTING = "listing"
    DETAIL = "detail"
    FORM = "form"
    MARKETING = "marketing"
    AUTH = "auth"
    CHECKOUT = "checkout"
    ABOUT = "about"
    CONTACT = "contact"
    OTHER = "other"


# =============================================================================
# BASE TOKEN MODEL
# =============================================================================

class BaseToken(BaseModel):
    """Base class for all tokens."""
    source: TokenSource = TokenSource.DETECTED
    confidence: Confidence = Confidence.MEDIUM
    frequency: int = 0
    suggested_name: Optional[str] = None
    
    # For tracking user decisions
    accepted: bool = True
    flagged: bool = False
    notes: Optional[str] = None


# =============================================================================
# COLOR TOKENS
# =============================================================================

class ColorToken(BaseToken):
    """Extracted color token."""
    value: str  # hex value (e.g., "#007bff")
    value_rgb: Optional[str] = None  # "rgb(0, 123, 255)"
    value_hsl: Optional[str] = None  # "hsl(211, 100%, 50%)"

    # Context information
    contexts: list[str] = Field(default_factory=list)  # ["background", "text", "border"]
    elements: list[str] = Field(default_factory=list)  # ["button", "header", "link"]
    css_properties: list[str] = Field(default_factory=list)  # ["background-color", "color"]

    # Role hint from normalizer (for AURORA to consume)
    # Values: "brand_candidate", "text_candidate", "bg_candidate", "border_candidate",
    #         "feedback_candidate", "palette" (generic colored), None (unclassified)
    role_hint: Optional[str] = None

    # Accessibility
    contrast_white: Optional[float] = None  # Contrast ratio against white
    contrast_black: Optional[float] = None  # Contrast ratio against black
    wcag_aa_large_text: bool = False
    wcag_aa_small_text: bool = False
    wcag_aaa_large_text: bool = False
    wcag_aaa_small_text: bool = False

    @field_validator("value")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        """Ensure hex color is properly formatted."""
        v = v.strip().lower()
        if not v.startswith("#"):
            v = f"#{v}"
        # Convert 3-digit hex to 6-digit
        if len(v) == 4:
            v = f"#{v[1]}{v[1]}{v[2]}{v[2]}{v[3]}{v[3]}"
        return v


class ColorRamp(BaseModel):
    """Generated color ramp with shades."""
    base_color: str  # Original extracted color
    name: str  # e.g., "primary", "neutral"
    shades: dict[str, str] = Field(default_factory=dict)  # {"50": "#e6f2ff", "500": "#007bff", ...}
    source: TokenSource = TokenSource.UPGRADED


# =============================================================================
# TYPOGRAPHY TOKENS
# =============================================================================

class TypographyToken(BaseToken):
    """Extracted typography token."""
    font_family: str
    font_size: str  # "16px" or "1rem"
    font_size_px: Optional[float] = None  # Computed px value
    font_weight: int = 400
    line_height: str = "1.5"  # "1.5" or "24px"
    line_height_computed: Optional[float] = None  # Computed ratio
    letter_spacing: Optional[str] = None
    text_transform: Optional[str] = None  # "uppercase", "lowercase", etc.
    
    # Context
    elements: list[str] = Field(default_factory=list)  # ["h1", "p", "button"]
    css_selectors: list[str] = Field(default_factory=list)  # [".heading", ".body-text"]


class TypeScale(BaseModel):
    """Typography scale configuration."""
    name: str  # "Major Third", "Perfect Fourth"
    ratio: float  # 1.25, 1.333
    base_size: int = 16  # px
    sizes: dict[str, str] = Field(default_factory=dict)  # {"xs": "12px", "sm": "14px", ...}
    source: TokenSource = TokenSource.UPGRADED


class FontFamily(BaseModel):
    """Font family information."""
    name: str  # "Inter"
    fallbacks: list[str] = Field(default_factory=list)  # ["system-ui", "sans-serif"]
    category: str = "sans-serif"  # "serif", "sans-serif", "monospace"
    frequency: int = 0
    usage: str = "primary"  # "primary", "secondary", "accent", "monospace"


# =============================================================================
# SPACING TOKENS
# =============================================================================

class SpacingToken(BaseToken):
    """Extracted spacing token."""
    value: str  # "16px"
    value_px: int  # 16
    
    # Context
    contexts: list[str] = Field(default_factory=list)  # ["margin", "padding", "gap"]
    properties: list[str] = Field(default_factory=list)  # ["margin-top", "padding-left"]
    
    # Analysis
    fits_base_4: bool = False  # Divisible by 4
    fits_base_8: bool = False  # Divisible by 8
    is_outlier: bool = False  # Doesn't fit common patterns


class SpacingScale(BaseModel):
    """Spacing scale configuration."""
    name: str  # "8px base"
    base: int  # 8
    scale: list[int] = Field(default_factory=list)  # [4, 8, 16, 24, 32, 48, 64]
    names: dict[int, str] = Field(default_factory=dict)  # {4: "xs", 8: "sm", 16: "md"}
    source: TokenSource = TokenSource.UPGRADED


# =============================================================================
# BORDER RADIUS TOKENS
# =============================================================================

class RadiusToken(BaseToken):
    """Extracted border radius token."""
    value: str  # "8px" or "50%"
    value_px: Optional[int] = None  # If px value
    
    # Context
    elements: list[str] = Field(default_factory=list)  # ["button", "card", "input"]
    
    # Analysis
    fits_base_4: bool = False
    fits_base_8: bool = False


# =============================================================================
# SHADOW TOKENS
# =============================================================================

class ShadowToken(BaseToken):
    """Extracted box shadow token."""
    value: str  # Full CSS shadow value

    # Parsed components
    offset_x: Optional[str] = None
    offset_y: Optional[str] = None
    blur: Optional[str] = None
    spread: Optional[str] = None
    color: Optional[str] = None
    inset: bool = False

    # Computed numeric values for sorting/analysis
    blur_px: Optional[float] = None
    y_offset_px: Optional[float] = None

    # Context
    elements: list[str] = Field(default_factory=list)


# =============================================================================
# PAGE & CRAWL MODELS
# =============================================================================

class DiscoveredPage(BaseModel):
    """A page discovered during crawling."""
    url: str
    title: Optional[str] = None
    page_type: PageType = PageType.OTHER
    depth: int = 0  # Distance from homepage
    selected: bool = True  # User can deselect pages
    
    # Crawl status
    crawled: bool = False
    error: Optional[str] = None


class CrawlResult(BaseModel):
    """Result of crawling a single page."""
    url: str
    viewport: Viewport
    success: bool
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    # Results
    colors_found: int = 0
    typography_found: int = 0
    spacing_found: int = 0
    
    # Errors
    error: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)


# =============================================================================
# EXTRACTION RESULT
# =============================================================================

class ExtractedTokens(BaseModel):
    """Complete extraction result for one viewport."""
    viewport: Viewport
    source_url: str
    pages_crawled: list[str] = Field(default_factory=list)
    
    # Extracted tokens
    colors: list[ColorToken] = Field(default_factory=list)
    typography: list[TypographyToken] = Field(default_factory=list)
    spacing: list[SpacingToken] = Field(default_factory=list)
    radius: list[RadiusToken] = Field(default_factory=list)
    shadows: list[ShadowToken] = Field(default_factory=list)
    
    # Detected patterns
    font_families: list[FontFamily] = Field(default_factory=list)
    base_font_size: Optional[str] = None
    spacing_base: Optional[int] = None  # Detected: 4 or 8
    naming_convention: Optional[str] = None  # "bem", "utility", "none"
    
    # Metadata
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    extraction_duration_ms: Optional[int] = None
    
    # Quality indicators
    total_elements_analyzed: int = 0
    unique_colors: int = 0
    unique_font_sizes: int = 0
    unique_spacing_values: int = 0
    
    # Issues
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    
    def summary(self) -> dict:
        """Get extraction summary."""
        return {
            "viewport": self.viewport.value,
            "pages_crawled": len(self.pages_crawled),
            "colors": len(self.colors),
            "typography": len(self.typography),
            "spacing": len(self.spacing),
            "radius": len(self.radius),
            "shadows": len(self.shadows),
            "font_families": len(self.font_families),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
        }


# =============================================================================
# NORMALIZED TOKENS (Agent 2 Output)
# =============================================================================

class NormalizedTokens(BaseModel):
    """Normalized and structured tokens from Agent 2."""
    viewport: Viewport
    source_url: str
    
    # Normalized tokens with suggested names
    colors: dict[str, ColorToken] = Field(default_factory=dict)  # {"primary-500": ColorToken, ...}
    typography: dict[str, TypographyToken] = Field(default_factory=dict)
    spacing: dict[str, SpacingToken] = Field(default_factory=dict)
    radius: dict[str, RadiusToken] = Field(default_factory=dict)
    shadows: dict[str, ShadowToken] = Field(default_factory=dict)
    
    # Detected info
    font_families: list[FontFamily] = Field(default_factory=list)
    detected_spacing_base: Optional[int] = None
    detected_naming_convention: Optional[str] = None
    
    # Duplicates & conflicts
    duplicate_colors: list[tuple[str, str]] = Field(default_factory=list)  # [("#1a1a1a", "#1b1b1b"), ...]
    conflicting_tokens: list[str] = Field(default_factory=list)
    
    # Metadata
    normalized_at: datetime = Field(default_factory=datetime.now)


# =============================================================================
# UPGRADE OPTIONS (Agent 3 Output)
# =============================================================================

class UpgradeOption(BaseModel):
    """A single upgrade option."""
    id: str
    name: str
    description: str
    category: str  # "typography", "spacing", "colors", "naming"
    
    # The actual values
    values: dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    effort: str = "low"  # "low", "medium", "high"
    recommended: bool = False
    
    # Selection state
    selected: bool = False


class UpgradeRecommendations(BaseModel):
    """All upgrade recommendations from Agent 3."""
    
    # Options by category
    typography_scales: list[UpgradeOption] = Field(default_factory=list)
    spacing_systems: list[UpgradeOption] = Field(default_factory=list)
    color_ramps: list[UpgradeOption] = Field(default_factory=list)
    naming_conventions: list[UpgradeOption] = Field(default_factory=list)
    
    # LLM analysis results
    llm_rationale: str = ""
    detected_patterns: list[str] = Field(default_factory=list)
    brand_analysis: list[dict] = Field(default_factory=list)  # From LLM research
    color_observations: str = ""
    
    # Accessibility
    accessibility_issues: list[str] = Field(default_factory=list)
    accessibility_fixes: list[UpgradeOption] = Field(default_factory=list)
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)


# =============================================================================
# FINAL OUTPUT (Agent 4 Output)
# =============================================================================

class TokenMetadata(BaseModel):
    """Metadata for exported tokens."""
    source_url: str
    extracted_at: datetime
    version: str
    viewport: Viewport
    generator: str = "Design System Automation v3"


class FinalTokens(BaseModel):
    """Final exported token set."""
    metadata: TokenMetadata
    
    # Token collections
    colors: dict[str, dict] = Field(default_factory=dict)
    typography: dict[str, dict] = Field(default_factory=dict)
    spacing: dict[str, dict] = Field(default_factory=dict)
    radius: dict[str, dict] = Field(default_factory=dict)
    shadows: dict[str, dict] = Field(default_factory=dict)
    
    def to_tokens_studio_format(self) -> dict:
        """Convert to Tokens Studio compatible format."""
        return {
            "$metadata": {
                "source": self.metadata.source_url,
                "version": self.metadata.version,
            },
            "color": self.colors,
            "typography": self.typography,
            "spacing": self.spacing,
            "borderRadius": self.radius,
            "boxShadow": self.shadows,
        }
    
    def to_css_variables(self) -> str:
        """Convert to CSS custom properties."""
        lines = [":root {"]
        
        for name, data in self.colors.items():
            value = data.get("value", data) if isinstance(data, dict) else data
            lines.append(f"  --color-{name}: {value};")
        
        for name, data in self.spacing.items():
            value = data.get("value", data) if isinstance(data, dict) else data
            lines.append(f"  --space-{name}: {value};")
        
        lines.append("}")
        return "\n".join(lines)


# =============================================================================
# LANGGRAPH STATE
# =============================================================================

class WorkflowState(BaseModel):
    """LangGraph workflow state."""
    
    # Input
    base_url: str
    
    # Discovery phase
    discovered_pages: list[DiscoveredPage] = Field(default_factory=list)
    confirmed_pages: list[str] = Field(default_factory=list)
    
    # Extraction phase
    desktop_tokens: Optional[ExtractedTokens] = None
    mobile_tokens: Optional[ExtractedTokens] = None
    
    # Normalization phase
    desktop_normalized: Optional[NormalizedTokens] = None
    mobile_normalized: Optional[NormalizedTokens] = None
    
    # Upgrade phase
    upgrade_recommendations: Optional[UpgradeRecommendations] = None
    selected_upgrades: dict[str, str] = Field(default_factory=dict)  # {"typography_scale": "major_third", ...}
    
    # Generation phase
    desktop_final: Optional[FinalTokens] = None
    mobile_final: Optional[FinalTokens] = None
    
    # Workflow status
    current_stage: str = "init"  # "init", "discover", "confirm", "extract", "normalize", "review", "upgrade", "generate", "export"
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True

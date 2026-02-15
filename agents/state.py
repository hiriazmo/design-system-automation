"""
LangGraph State Definitions
Design System Extractor v2

Defines the state schema and type hints for LangGraph workflow.
"""

from typing import TypedDict, Annotated, Sequence, Optional
from datetime import datetime
from langgraph.graph.message import add_messages

from core.token_schema import (
    DiscoveredPage,
    ExtractedTokens,
    NormalizedTokens,
    UpgradeRecommendations,
    FinalTokens,
    Viewport,
)


# =============================================================================
# STATE ANNOTATIONS
# =============================================================================

def merge_lists(left: list, right: list) -> list:
    """Merge two lists, avoiding duplicates."""
    seen = set()
    result = []
    for item in left + right:
        key = str(item) if not hasattr(item, 'url') else item.url
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def replace_value(left, right):
    """Replace left with right (simple override)."""
    return right if right is not None else left


# =============================================================================
# MAIN WORKFLOW STATE
# =============================================================================

class AgentState(TypedDict):
    """
    Main state for the LangGraph workflow.
    
    This state is passed between all agents and accumulates data
    as the workflow progresses through stages.
    """
    
    # -------------------------------------------------------------------------
    # INPUT
    # -------------------------------------------------------------------------
    base_url: str  # The website URL to extract from
    
    # -------------------------------------------------------------------------
    # DISCOVERY STAGE (Agent 1 - Part 1)
    # -------------------------------------------------------------------------
    discovered_pages: Annotated[list[DiscoveredPage], merge_lists]
    pages_to_crawl: list[str]  # User-confirmed pages
    
    # -------------------------------------------------------------------------
    # EXTRACTION STAGE (Agent 1 - Part 2)
    # -------------------------------------------------------------------------
    # Desktop extraction
    desktop_extraction: Optional[ExtractedTokens]
    desktop_crawl_progress: float  # 0.0 to 1.0
    
    # Mobile extraction
    mobile_extraction: Optional[ExtractedTokens]
    mobile_crawl_progress: float  # 0.0 to 1.0
    
    # -------------------------------------------------------------------------
    # NORMALIZATION STAGE (Agent 2)
    # -------------------------------------------------------------------------
    desktop_normalized: Optional[NormalizedTokens]
    mobile_normalized: Optional[NormalizedTokens]
    
    # User decisions from Stage 1 review
    accepted_colors: list[str]  # List of accepted color values
    rejected_colors: list[str]  # List of rejected color values
    accepted_typography: list[str]
    rejected_typography: list[str]
    accepted_spacing: list[str]
    rejected_spacing: list[str]
    
    # -------------------------------------------------------------------------
    # ADVISOR STAGE (Agent 3)
    # -------------------------------------------------------------------------
    upgrade_recommendations: Optional[UpgradeRecommendations]
    
    # User selections from Stage 2 playground
    selected_type_scale: Optional[str]  # ID of selected scale
    selected_spacing_system: Optional[str]
    selected_naming_convention: Optional[str]
    selected_color_ramps: dict[str, bool]  # {"primary": True, "secondary": False}
    selected_a11y_fixes: list[str]  # IDs of accepted fixes
    
    # -------------------------------------------------------------------------
    # GENERATION STAGE (Agent 4)
    # -------------------------------------------------------------------------
    desktop_final: Optional[FinalTokens]
    mobile_final: Optional[FinalTokens]
    
    # Version info
    version_label: str  # e.g., "v1-recovered", "v2-upgraded"
    
    # -------------------------------------------------------------------------
    # WORKFLOW METADATA
    # -------------------------------------------------------------------------
    current_stage: str  # "discover", "extract", "normalize", "advise", "generate", "export"
    
    # Human checkpoints
    awaiting_human_input: bool
    checkpoint_name: Optional[str]  # "confirm_pages", "review_tokens", "select_upgrades", "approve_export"
    
    # Errors and warnings (accumulated)
    errors: Annotated[list[str], merge_lists]
    warnings: Annotated[list[str], merge_lists]
    
    # Messages for LLM agents (if using chat-based agents)
    messages: Annotated[Sequence[dict], add_messages]
    
    # Timing
    started_at: Optional[datetime]
    stage_started_at: Optional[datetime]


# =============================================================================
# STAGE-SPECIFIC STATES (for parallel execution)
# =============================================================================

class DiscoveryState(TypedDict):
    """State for page discovery sub-graph."""
    base_url: str
    discovered_pages: list[DiscoveredPage]
    discovery_complete: bool
    error: Optional[str]


class ExtractionState(TypedDict):
    """State for extraction sub-graph (per viewport)."""
    viewport: Viewport
    pages_to_crawl: list[str]
    extraction_result: Optional[ExtractedTokens]
    progress: float
    current_page: Optional[str]
    error: Optional[str]


class NormalizationState(TypedDict):
    """State for normalization sub-graph."""
    raw_tokens: ExtractedTokens
    normalized_tokens: Optional[NormalizedTokens]
    duplicates_found: list[tuple[str, str]]
    error: Optional[str]


class AdvisorState(TypedDict):
    """State for advisor sub-graph."""
    normalized_desktop: NormalizedTokens
    normalized_mobile: Optional[NormalizedTokens]
    recommendations: Optional[UpgradeRecommendations]
    error: Optional[str]


class GenerationState(TypedDict):
    """State for generation sub-graph."""
    normalized_tokens: NormalizedTokens
    selected_upgrades: dict[str, str]
    final_tokens: Optional[FinalTokens]
    error: Optional[str]


# =============================================================================
# CHECKPOINT STATES (Human-in-the-loop)
# =============================================================================

class PageConfirmationState(TypedDict):
    """State for page confirmation checkpoint."""
    discovered_pages: list[DiscoveredPage]
    confirmed_pages: list[str]
    user_confirmed: bool


class TokenReviewState(TypedDict):
    """State for token review checkpoint (Stage 1 UI)."""
    desktop_tokens: NormalizedTokens
    mobile_tokens: Optional[NormalizedTokens]
    
    # User decisions
    color_decisions: dict[str, bool]  # {value: accepted}
    typography_decisions: dict[str, bool]
    spacing_decisions: dict[str, bool]
    
    user_confirmed: bool


class UpgradeSelectionState(TypedDict):
    """State for upgrade selection checkpoint (Stage 2 UI)."""
    recommendations: UpgradeRecommendations
    current_tokens: NormalizedTokens
    
    # User selections
    selected_options: dict[str, str]  # {category: option_id}
    
    user_confirmed: bool


class ExportApprovalState(TypedDict):
    """State for export approval checkpoint (Stage 3 UI)."""
    desktop_final: FinalTokens
    mobile_final: Optional[FinalTokens]
    
    version_label: str
    user_confirmed: bool


# =============================================================================
# STATE FACTORY FUNCTIONS
# =============================================================================

def create_initial_state(base_url: str) -> AgentState:
    """Create initial state for a new workflow."""
    return {
        # Input
        "base_url": base_url,
        
        # Discovery
        "discovered_pages": [],
        "pages_to_crawl": [],
        
        # Extraction
        "desktop_extraction": None,
        "desktop_crawl_progress": 0.0,
        "mobile_extraction": None,
        "mobile_crawl_progress": 0.0,
        
        # Normalization
        "desktop_normalized": None,
        "mobile_normalized": None,
        "accepted_colors": [],
        "rejected_colors": [],
        "accepted_typography": [],
        "rejected_typography": [],
        "accepted_spacing": [],
        "rejected_spacing": [],
        
        # Advisor
        "upgrade_recommendations": None,
        "selected_type_scale": None,
        "selected_spacing_system": None,
        "selected_naming_convention": None,
        "selected_color_ramps": {},
        "selected_a11y_fixes": [],
        
        # Generation
        "desktop_final": None,
        "mobile_final": None,
        "version_label": "v1-recovered",
        
        # Workflow
        "current_stage": "discover",
        "awaiting_human_input": False,
        "checkpoint_name": None,
        "errors": [],
        "warnings": [],
        "messages": [],
        
        # Timing
        "started_at": datetime.now(),
        "stage_started_at": datetime.now(),
    }


def get_stage_progress(state: AgentState) -> dict:
    """Get progress information for the current workflow."""
    stages = ["discover", "extract", "normalize", "advise", "generate", "export"]
    current_idx = stages.index(state["current_stage"]) if state["current_stage"] in stages else 0
    
    return {
        "current_stage": state["current_stage"],
        "stage_index": current_idx,
        "total_stages": len(stages),
        "progress_percent": (current_idx / len(stages)) * 100,
        "awaiting_human": state["awaiting_human_input"],
        "checkpoint": state["checkpoint_name"],
    }

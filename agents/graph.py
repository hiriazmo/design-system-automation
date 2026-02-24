"""
LangGraph Workflow Orchestration
Design System Automation

Defines the main workflow graph with agents, checkpoints, and transitions.
"""

from typing import Literal
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents.state import AgentState, create_initial_state, get_stage_progress
from core.token_schema import Viewport


# =============================================================================
# NODE FUNCTIONS (Agent Entry Points)
# =============================================================================

async def discover_pages(state: AgentState) -> AgentState:
    """
    Agent 1 - Part 1: Discover pages from base URL.
    
    This node:
    1. Takes the base URL
    2. Crawls to find linked pages
    3. Classifies page types (homepage, listing, detail, etc.)
    4. Returns discovered pages for user confirmation
    """
    from agents.crawler import PageDiscoverer
    
    state["current_stage"] = "discover"
    state["stage_started_at"] = datetime.now()
    
    try:
        discoverer = PageDiscoverer()
        pages = await discoverer.discover(state["base_url"])
        
        state["discovered_pages"] = pages
        state["awaiting_human_input"] = True
        state["checkpoint_name"] = "confirm_pages"
        
    except Exception as e:
        state["errors"].append(f"Discovery failed: {str(e)}")
    
    return state


async def extract_tokens_desktop(state: AgentState) -> AgentState:
    """
    Agent 1 - Part 2a: Extract tokens from desktop viewport.
    """
    from agents.extractor import TokenExtractor
    
    state["current_stage"] = "extract"
    
    try:
        extractor = TokenExtractor(viewport=Viewport.DESKTOP)
        result = await extractor.extract(
            pages=state["pages_to_crawl"],
            progress_callback=lambda p: state.update({"desktop_crawl_progress": p})
        )
        
        state["desktop_extraction"] = result
        
    except Exception as e:
        state["errors"].append(f"Desktop extraction failed: {str(e)}")
    
    return state


async def extract_tokens_mobile(state: AgentState) -> AgentState:
    """
    Agent 1 - Part 2b: Extract tokens from mobile viewport.
    """
    from agents.extractor import TokenExtractor
    
    try:
        extractor = TokenExtractor(viewport=Viewport.MOBILE)
        result = await extractor.extract(
            pages=state["pages_to_crawl"],
            progress_callback=lambda p: state.update({"mobile_crawl_progress": p})
        )
        
        state["mobile_extraction"] = result
        
    except Exception as e:
        state["errors"].append(f"Mobile extraction failed: {str(e)}")
    
    return state


async def normalize_tokens(state: AgentState) -> AgentState:
    """
    Agent 2: Normalize and structure extracted tokens.
    """
    from agents.normalizer import TokenNormalizer
    
    state["current_stage"] = "normalize"
    state["stage_started_at"] = datetime.now()
    
    try:
        normalizer = TokenNormalizer()
        
        if state["desktop_extraction"]:
            state["desktop_normalized"] = normalizer.normalize(state["desktop_extraction"])
        
        if state["mobile_extraction"]:
            state["mobile_normalized"] = normalizer.normalize(state["mobile_extraction"])
        
        # After normalization, wait for human review
        state["awaiting_human_input"] = True
        state["checkpoint_name"] = "review_tokens"
        
    except Exception as e:
        state["errors"].append(f"Normalization failed: {str(e)}")
    
    return state


async def generate_recommendations(state: AgentState) -> AgentState:
    """
    Agent 3: Generate upgrade recommendations.
    """
    from agents.advisor import DesignSystemAdvisor
    
    state["current_stage"] = "advise"
    state["stage_started_at"] = datetime.now()
    
    try:
        advisor = DesignSystemAdvisor()
        recommendations = await advisor.analyze_and_recommend(
            desktop=state["desktop_normalized"],
            mobile=state["mobile_normalized"],
        )
        
        state["upgrade_recommendations"] = recommendations
        
        # Wait for human to select upgrades
        state["awaiting_human_input"] = True
        state["checkpoint_name"] = "select_upgrades"
        
    except Exception as e:
        state["errors"].append(f"Recommendation generation failed: {str(e)}")
    
    return state


async def generate_final_tokens(state: AgentState) -> AgentState:
    """
    Agent 4: Generate final token JSON.
    """
    from agents.generator import TokenGenerator
    
    state["current_stage"] = "generate"
    state["stage_started_at"] = datetime.now()
    
    try:
        generator = TokenGenerator()
        
        # Build selection config from user choices
        selections = {
            "type_scale": state["selected_type_scale"],
            "spacing_system": state["selected_spacing_system"],
            "naming_convention": state["selected_naming_convention"],
            "color_ramps": state["selected_color_ramps"],
            "a11y_fixes": state["selected_a11y_fixes"],
        }
        
        if state["desktop_normalized"]:
            state["desktop_final"] = generator.generate(
                normalized=state["desktop_normalized"],
                selections=selections,
                version=state["version_label"],
            )
        
        if state["mobile_normalized"]:
            state["mobile_final"] = generator.generate(
                normalized=state["mobile_normalized"],
                selections=selections,
                version=state["version_label"],
            )
        
        # Wait for human to approve export
        state["awaiting_human_input"] = True
        state["checkpoint_name"] = "approve_export"
        
    except Exception as e:
        state["errors"].append(f"Token generation failed: {str(e)}")
    
    return state


async def complete_workflow(state: AgentState) -> AgentState:
    """
    Final node: Mark workflow as complete.
    """
    state["current_stage"] = "export"
    state["awaiting_human_input"] = False
    state["checkpoint_name"] = None
    
    return state


# =============================================================================
# HUMAN CHECKPOINT HANDLERS
# =============================================================================

def handle_page_confirmation(state: AgentState, confirmed_pages: list[str]) -> AgentState:
    """Handle human confirmation of pages to crawl."""
    state["pages_to_crawl"] = confirmed_pages
    state["awaiting_human_input"] = False
    state["checkpoint_name"] = None
    return state


def handle_token_review(
    state: AgentState,
    color_decisions: dict[str, bool],
    typography_decisions: dict[str, bool],
    spacing_decisions: dict[str, bool],
) -> AgentState:
    """Handle human review of extracted tokens."""
    state["accepted_colors"] = [k for k, v in color_decisions.items() if v]
    state["rejected_colors"] = [k for k, v in color_decisions.items() if not v]
    state["accepted_typography"] = [k for k, v in typography_decisions.items() if v]
    state["rejected_typography"] = [k for k, v in typography_decisions.items() if not v]
    state["accepted_spacing"] = [k for k, v in spacing_decisions.items() if v]
    state["rejected_spacing"] = [k for k, v in spacing_decisions.items() if not v]
    
    state["awaiting_human_input"] = False
    state["checkpoint_name"] = None
    return state


def handle_upgrade_selection(
    state: AgentState,
    type_scale: str | None,
    spacing_system: str | None,
    naming_convention: str | None,
    color_ramps: dict[str, bool],
    a11y_fixes: list[str],
) -> AgentState:
    """Handle human selection of upgrade options."""
    state["selected_type_scale"] = type_scale
    state["selected_spacing_system"] = spacing_system
    state["selected_naming_convention"] = naming_convention
    state["selected_color_ramps"] = color_ramps
    state["selected_a11y_fixes"] = a11y_fixes
    
    state["awaiting_human_input"] = False
    state["checkpoint_name"] = None
    return state


def handle_export_approval(state: AgentState, version_label: str) -> AgentState:
    """Handle human approval of final export."""
    state["version_label"] = version_label
    state["awaiting_human_input"] = False
    state["checkpoint_name"] = None
    return state


# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================

def route_after_discovery(state: AgentState) -> Literal["wait_for_pages", "extract"]:
    """Route after discovery: wait for human or continue."""
    if state["awaiting_human_input"]:
        return "wait_for_pages"
    return "extract"


def route_after_extraction(state: AgentState) -> Literal["normalize", "error"]:
    """Route after extraction: normalize or handle error."""
    if state["desktop_extraction"] is None and state["mobile_extraction"] is None:
        return "error"
    return "normalize"


def route_after_normalization(state: AgentState) -> Literal["wait_for_review", "advise"]:
    """Route after normalization: wait for review or continue."""
    if state["awaiting_human_input"]:
        return "wait_for_review"
    return "advise"


def route_after_recommendations(state: AgentState) -> Literal["wait_for_selection", "generate"]:
    """Route after recommendations: wait for selection or continue."""
    if state["awaiting_human_input"]:
        return "wait_for_selection"
    return "generate"


def route_after_generation(state: AgentState) -> Literal["wait_for_approval", "complete"]:
    """Route after generation: wait for approval or complete."""
    if state["awaiting_human_input"]:
        return "wait_for_approval"
    return "complete"


# =============================================================================
# GRAPH BUILDER
# =============================================================================

def build_workflow_graph() -> StateGraph:
    """
    Build the main LangGraph workflow.
    
    Flow:
    1. discover_pages -> [human confirms pages]
    2. extract_desktop + extract_mobile (parallel)
    3. normalize_tokens -> [human reviews tokens]
    4. generate_recommendations -> [human selects upgrades]
    5. generate_final_tokens -> [human approves export]
    6. complete
    """
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # -------------------------------------------------------------------------
    # ADD NODES
    # -------------------------------------------------------------------------
    
    # Discovery
    workflow.add_node("discover", discover_pages)
    
    # Extraction (will be parallel in subgraph)
    workflow.add_node("extract_desktop", extract_tokens_desktop)
    workflow.add_node("extract_mobile", extract_tokens_mobile)
    
    # Normalization
    workflow.add_node("normalize", normalize_tokens)
    
    # Advisor
    workflow.add_node("advise", generate_recommendations)
    
    # Generator
    workflow.add_node("generate", generate_final_tokens)
    
    # Completion
    workflow.add_node("complete", complete_workflow)
    
    # Human checkpoint placeholder nodes (these just pass through)
    workflow.add_node("wait_for_pages", lambda s: s)
    workflow.add_node("wait_for_review", lambda s: s)
    workflow.add_node("wait_for_selection", lambda s: s)
    workflow.add_node("wait_for_approval", lambda s: s)
    
    # -------------------------------------------------------------------------
    # ADD EDGES
    # -------------------------------------------------------------------------
    
    # Entry point
    workflow.set_entry_point("discover")
    
    # Discovery -> (wait or extract)
    workflow.add_conditional_edges(
        "discover",
        route_after_discovery,
        {
            "wait_for_pages": "wait_for_pages",
            "extract": "extract_desktop",
        }
    )
    
    # After human confirms pages -> extract
    workflow.add_edge("wait_for_pages", "extract_desktop")
    
    # Parallel extraction
    workflow.add_edge("extract_desktop", "extract_mobile")
    
    # After extraction -> normalize
    workflow.add_conditional_edges(
        "extract_mobile",
        route_after_extraction,
        {
            "normalize": "normalize",
            "error": END,
        }
    )
    
    # Normalization -> (wait or advise)
    workflow.add_conditional_edges(
        "normalize",
        route_after_normalization,
        {
            "wait_for_review": "wait_for_review",
            "advise": "advise",
        }
    )
    
    # After human reviews -> advise
    workflow.add_edge("wait_for_review", "advise")
    
    # Advisor -> (wait or generate)
    workflow.add_conditional_edges(
        "advise",
        route_after_recommendations,
        {
            "wait_for_selection": "wait_for_selection",
            "generate": "generate",
        }
    )
    
    # After human selects upgrades -> generate
    workflow.add_edge("wait_for_selection", "generate")
    
    # Generation -> (wait or complete)
    workflow.add_conditional_edges(
        "generate",
        route_after_generation,
        {
            "wait_for_approval": "wait_for_approval",
            "complete": "complete",
        }
    )
    
    # After human approves -> complete
    workflow.add_edge("wait_for_approval", "complete")
    
    # Complete -> END
    workflow.add_edge("complete", END)
    
    return workflow


# =============================================================================
# WORKFLOW RUNNER
# =============================================================================

class WorkflowRunner:
    """
    Manages workflow execution with human-in-the-loop support.
    """
    
    def __init__(self):
        self.graph = build_workflow_graph()
        self.checkpointer = MemorySaver()
        self.app = self.graph.compile(checkpointer=self.checkpointer)
        self.current_state: AgentState | None = None
        self.thread_id: str | None = None
    
    async def start(self, base_url: str, thread_id: str | None = None) -> AgentState:
        """Start a new workflow."""
        self.thread_id = thread_id or f"workflow_{datetime.now().timestamp()}"
        self.current_state = create_initial_state(base_url)
        
        config = {"configurable": {"thread_id": self.thread_id}}
        
        # Run until first human checkpoint
        async for event in self.app.astream(self.current_state, config):
            self.current_state = event
            if self.current_state.get("awaiting_human_input"):
                break
        
        return self.current_state
    
    async def resume(self, human_input: dict) -> AgentState:
        """Resume workflow after human input."""
        if not self.current_state or not self.thread_id:
            raise ValueError("No active workflow to resume")
        
        checkpoint = self.current_state.get("checkpoint_name")
        
        # Apply human input based on checkpoint
        if checkpoint == "confirm_pages":
            self.current_state = handle_page_confirmation(
                self.current_state,
                human_input.get("confirmed_pages", [])
            )
        elif checkpoint == "review_tokens":
            self.current_state = handle_token_review(
                self.current_state,
                human_input.get("color_decisions", {}),
                human_input.get("typography_decisions", {}),
                human_input.get("spacing_decisions", {}),
            )
        elif checkpoint == "select_upgrades":
            self.current_state = handle_upgrade_selection(
                self.current_state,
                human_input.get("type_scale"),
                human_input.get("spacing_system"),
                human_input.get("naming_convention"),
                human_input.get("color_ramps", {}),
                human_input.get("a11y_fixes", []),
            )
        elif checkpoint == "approve_export":
            self.current_state = handle_export_approval(
                self.current_state,
                human_input.get("version_label", "v1")
            )
        
        config = {"configurable": {"thread_id": self.thread_id}}
        
        # Continue until next checkpoint or completion
        async for event in self.app.astream(self.current_state, config):
            self.current_state = event
            if self.current_state.get("awaiting_human_input"):
                break
        
        return self.current_state
    
    def get_progress(self) -> dict:
        """Get current workflow progress."""
        if not self.current_state:
            return {"status": "not_started"}
        return get_stage_progress(self.current_state)
    
    def get_state(self) -> AgentState | None:
        """Get current state."""
        return self.current_state


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_workflow() -> WorkflowRunner:
    """Create a new workflow runner instance."""
    return WorkflowRunner()


async def run_discovery_only(base_url: str) -> list:
    """Run only the discovery phase (for testing)."""
    from agents.crawler import PageDiscoverer
    
    discoverer = PageDiscoverer()
    return await discoverer.discover(base_url)


async def run_extraction_only(pages: list[str], viewport: Viewport) -> dict:
    """Run only the extraction phase (for testing)."""
    from agents.extractor import TokenExtractor
    
    extractor = TokenExtractor(viewport=viewport)
    return await extractor.extract(pages)

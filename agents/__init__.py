"""
Agents for Design System Automation.

This package contains:
- Stage 1 Agents: Crawler, Extractor, Normalizer, Semantic Analyzer
- Stage 2 Agents: Rule Engine, Benchmark Researcher, LLM Analysis Agents
- Workflow Graphs: LangGraph orchestration
"""

# Stage 2 components (no langgraph dependency)
from agents.benchmark_researcher import (
    BenchmarkResearcher,
    BenchmarkCache,
    DESIGN_SYSTEM_SOURCES,
    FALLBACK_BENCHMARKS,
    get_available_benchmarks,
    get_benchmark_choices,
    BenchmarkData,
    BenchmarkComparison,
)

try:
    from agents.llm_agents import (
        BrandIdentifierAgent,
        BenchmarkAdvisorAgent,
        BestPracticesValidatorAgent,
        HeadSynthesizerAgent,
        BrandIdentification,
        BenchmarkAdvice,
        BestPracticesResult,
        HeadSynthesis,
    )
except ImportError:
    BrandIdentifierAgent = None
    BenchmarkAdvisorAgent = None
    BestPracticesValidatorAgent = None
    HeadSynthesizerAgent = None
    BrandIdentification = None
    BenchmarkAdvice = None
    BestPracticesResult = None
    HeadSynthesis = None

# Lazy imports for langgraph-dependent modules
def get_state_module():
    """Lazy import for state module (requires langgraph)."""
    from agents import state as state_module
    return state_module

def get_graph_module():
    """Lazy import for graph module (requires langgraph)."""
    from agents import graph as graph_module
    return graph_module

__all__ = [
    # Benchmark Research
    "BenchmarkResearcher",
    "BenchmarkCache",
    "DESIGN_SYSTEM_SOURCES",
    "FALLBACK_BENCHMARKS",
    "get_available_benchmarks",
    "get_benchmark_choices",
    "BenchmarkData",
    "BenchmarkComparison",
    # LLM Agents
    "BrandIdentifierAgent",
    "BenchmarkAdvisorAgent",
    "BestPracticesValidatorAgent",
    "HeadSynthesizerAgent",
    "BrandIdentification",
    "BenchmarkAdvice",
    "BestPracticesResult",
    "HeadSynthesis",
    # Lazy loaders
    "get_state_module",
    "get_graph_module",
]

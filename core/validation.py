"""
Agent Output Validation
========================

JSON schemas for validating LLM agent outputs.
Ensures data integrity between pipeline stages.
"""

from typing import Any, Optional

try:
    from jsonschema import validate, ValidationError

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

from core.logging import get_logger

logger = get_logger("validation")


# =============================================================================
# SCHEMAS
# =============================================================================

BRAND_IDENTIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "brand_primary": {"type": ["string", "null"]},
        "brand_secondary": {"type": ["string", "null"]},
        "brand_accent": {"type": ["string", "null"]},
        "palette_strategy": {"type": "string"},
        "cohesion_score": {"type": ["number", "integer"]},
        "cohesion_notes": {"type": "string"},
        "semantic_names": {"type": "object"},
        "self_evaluation": {"type": "object"},
    },
    "required": ["brand_primary", "palette_strategy"],
}

BENCHMARK_ADVICE_SCHEMA = {
    "type": "object",
    "properties": {
        "recommended_benchmark": {"type": "string"},
        "recommended_benchmark_name": {"type": "string"},
        "reasoning": {"type": "string"},
        "alignment_changes": {"type": "array"},
        "pros_of_alignment": {"type": "array"},
        "cons_of_alignment": {"type": "array"},
        "alternative_benchmarks": {"type": "array"},
        "self_evaluation": {"type": "object"},
    },
    "required": ["recommended_benchmark", "reasoning"],
}

BEST_PRACTICES_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_score": {"type": ["number", "integer"]},
        "checks": {"type": "array"},
        "priority_fixes": {"type": "array"},
        "passing_practices": {"type": "array"},
        "failing_practices": {"type": "array"},
        "self_evaluation": {"type": "object"},
    },
    "required": ["overall_score", "priority_fixes"],
}

HEAD_SYNTHESIS_SCHEMA = {
    "type": "object",
    "properties": {
        "executive_summary": {"type": "string"},
        "scores": {"type": "object"},
        "benchmark_fit": {"type": "object"},
        "brand_analysis": {"type": "object"},
        "top_3_actions": {"type": "array"},
        "color_recommendations": {"type": "array"},
        "type_scale_recommendation": {"type": "object"},
        "spacing_recommendation": {"type": "object"},
        "self_evaluation": {"type": "object"},
    },
    "required": ["executive_summary", "top_3_actions"],
}

# Map agent names to schemas
AGENT_SCHEMAS = {
    "aurora": BRAND_IDENTIFICATION_SCHEMA,
    "brand_identifier": BRAND_IDENTIFICATION_SCHEMA,
    "atlas": BENCHMARK_ADVICE_SCHEMA,
    "benchmark_advisor": BENCHMARK_ADVICE_SCHEMA,
    "sentinel": BEST_PRACTICES_SCHEMA,
    "best_practices": BEST_PRACTICES_SCHEMA,
    "nexus": HEAD_SYNTHESIS_SCHEMA,
    "head_synthesizer": HEAD_SYNTHESIS_SCHEMA,
}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_agent_output(data: Any, agent_name: str) -> tuple[bool, Optional[str]]:
    """
    Validate an agent's output against its expected schema.

    Args:
        data: The output data (dict or dataclass with to_dict())
        agent_name: Name of the agent (e.g., 'aurora', 'nexus')

    Returns:
        (is_valid, error_message) tuple
    """
    agent_key = agent_name.lower().strip()
    schema = AGENT_SCHEMAS.get(agent_key)

    if not schema:
        logger.warning(f"No schema found for agent: {agent_name}")
        return True, None  # No schema = pass (don't block)

    # Convert dataclass to dict if needed
    if hasattr(data, "to_dict"):
        data_dict = data.to_dict()
    elif hasattr(data, "__dataclass_fields__"):
        from dataclasses import asdict
        data_dict = asdict(data)
    elif isinstance(data, dict):
        data_dict = data
    else:
        return False, f"Cannot validate: unexpected type {type(data)}"

    if not HAS_JSONSCHEMA:
        # Fallback: manual required-field check
        return _manual_validate(data_dict, schema, agent_name)

    try:
        validate(instance=data_dict, schema=schema)
        logger.debug(f"Validation passed for {agent_name}")
        return True, None
    except ValidationError as e:
        error_msg = f"Validation failed for {agent_name}: {e.message}"
        logger.warning(error_msg)
        return False, error_msg


def _manual_validate(data: dict, schema: dict, agent_name: str) -> tuple[bool, Optional[str]]:
    """Fallback validation without jsonschema library."""
    required = schema.get("required", [])
    missing = [field for field in required if field not in data]

    if missing:
        error_msg = f"{agent_name} output missing required fields: {missing}"
        logger.warning(error_msg)
        return False, error_msg

    return True, None


def validate_all_agents(outputs: dict) -> dict[str, tuple[bool, Optional[str]]]:
    """
    Validate all agent outputs at once.

    Args:
        outputs: Dict mapping agent_name → output data

    Returns:
        Dict mapping agent_name → (is_valid, error_message)
    """
    results = {}
    for agent_name, data in outputs.items():
        results[agent_name] = validate_agent_output(data, agent_name)
    return results

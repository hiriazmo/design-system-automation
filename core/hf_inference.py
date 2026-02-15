"""
HuggingFace Inference Client
Design System Extractor v2

Handles all LLM inference calls using HuggingFace Inference API.
Supports diverse models from different providers for specialized tasks.
"""

import os
from typing import Optional, AsyncGenerator
from dataclasses import dataclass
from huggingface_hub import InferenceClient, AsyncInferenceClient

from config.settings import get_settings


@dataclass
class ModelInfo:
    """Information about a model."""
    model_id: str
    provider: str
    context_length: int
    strengths: list[str]
    best_for: str
    tier: str  # "free", "pro", "pro+"


# =============================================================================
# COMPREHENSIVE MODEL REGISTRY — Organized by Provider
# =============================================================================

AVAILABLE_MODELS = {
    # =========================================================================
    # META — Llama Family (Best for reasoning)
    # =========================================================================
    "meta-llama/Llama-3.1-405B-Instruct": ModelInfo(
        model_id="meta-llama/Llama-3.1-405B-Instruct",
        provider="Meta",
        context_length=128000,
        strengths=["Best reasoning", "Massive knowledge", "Complex analysis"],
        best_for="Agent 3 (Advisor) — PREMIUM CHOICE",
        tier="pro+"
    ),
    "meta-llama/Llama-3.1-70B-Instruct": ModelInfo(
        model_id="meta-llama/Llama-3.1-70B-Instruct",
        provider="Meta",
        context_length=128000,
        strengths=["Excellent reasoning", "Long context", "Design knowledge"],
        best_for="Agent 3 (Advisor) — RECOMMENDED",
        tier="pro"
    ),
    "meta-llama/Llama-3.1-8B-Instruct": ModelInfo(
        model_id="meta-llama/Llama-3.1-8B-Instruct",
        provider="Meta",
        context_length=128000,
        strengths=["Fast", "Good reasoning for size", "Long context"],
        best_for="Budget Agent 3 fallback",
        tier="free"
    ),
    
    # =========================================================================
    # MISTRAL — European Excellence
    # =========================================================================
    "mistralai/Mixtral-8x22B-Instruct-v0.1": ModelInfo(
        model_id="mistralai/Mixtral-8x22B-Instruct-v0.1",
        provider="Mistral",
        context_length=65536,
        strengths=["Large MoE", "Strong reasoning", "Efficient"],
        best_for="Agent 3 (Advisor) — Pro alternative",
        tier="pro"
    ),
    "mistralai/Mixtral-8x7B-Instruct-v0.1": ModelInfo(
        model_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
        provider="Mistral",
        context_length=32768,
        strengths=["Good MoE efficiency", "Solid reasoning"],
        best_for="Agent 3 (Advisor) — Free tier option",
        tier="free"
    ),
    "mistralai/Mistral-7B-Instruct-v0.3": ModelInfo(
        model_id="mistralai/Mistral-7B-Instruct-v0.3",
        provider="Mistral",
        context_length=32768,
        strengths=["Fast", "Good instruction following"],
        best_for="General fallback",
        tier="free"
    ),
    "mistralai/Codestral-22B-v0.1": ModelInfo(
        model_id="mistralai/Codestral-22B-v0.1",
        provider="Mistral",
        context_length=32768,
        strengths=["Code specialist", "JSON generation", "Structured output"],
        best_for="Agent 4 (Generator) — RECOMMENDED",
        tier="pro"
    ),
    
    # =========================================================================
    # COHERE — Command R Family (Analysis & Retrieval)
    # =========================================================================
    "CohereForAI/c4ai-command-r-plus": ModelInfo(
        model_id="CohereForAI/c4ai-command-r-plus",
        provider="Cohere",
        context_length=128000,
        strengths=["Excellent analysis", "RAG optimized", "Long context"],
        best_for="Agent 3 (Advisor) — Great for research tasks",
        tier="pro"
    ),
    "CohereForAI/c4ai-command-r-v01": ModelInfo(
        model_id="CohereForAI/c4ai-command-r-v01",
        provider="Cohere",
        context_length=128000,
        strengths=["Good analysis", "Efficient"],
        best_for="Agent 3 budget option",
        tier="free"
    ),
    
    # =========================================================================
    # GOOGLE — Gemma Family
    # =========================================================================
    "google/gemma-2-27b-it": ModelInfo(
        model_id="google/gemma-2-27b-it",
        provider="Google",
        context_length=8192,
        strengths=["Strong instruction following", "Good balance"],
        best_for="Agent 2 (Normalizer) — Quality option",
        tier="pro"
    ),
    "google/gemma-2-9b-it": ModelInfo(
        model_id="google/gemma-2-9b-it",
        provider="Google",
        context_length=8192,
        strengths=["Fast", "Good instruction following"],
        best_for="Agent 2 (Normalizer) — Balanced",
        tier="free"
    ),
    
    # =========================================================================
    # MICROSOFT — Phi Family (Small but Mighty)
    # =========================================================================
    "microsoft/Phi-3.5-mini-instruct": ModelInfo(
        model_id="microsoft/Phi-3.5-mini-instruct",
        provider="Microsoft",
        context_length=128000,
        strengths=["Very fast", "Great structured output", "Long context"],
        best_for="Agent 2 (Normalizer) — RECOMMENDED",
        tier="free"
    ),
    "microsoft/Phi-3-medium-4k-instruct": ModelInfo(
        model_id="microsoft/Phi-3-medium-4k-instruct",
        provider="Microsoft",
        context_length=4096,
        strengths=["Fast", "Good for simple tasks"],
        best_for="Simple naming tasks",
        tier="free"
    ),
    
    # =========================================================================
    # QWEN — Alibaba Family
    # =========================================================================
    "Qwen/Qwen2.5-72B-Instruct": ModelInfo(
        model_id="Qwen/Qwen2.5-72B-Instruct",
        provider="Alibaba",
        context_length=32768,
        strengths=["Strong reasoning", "Multilingual", "Good design knowledge"],
        best_for="Agent 3 (Advisor) — Alternative",
        tier="pro"
    ),
    "Qwen/Qwen2.5-32B-Instruct": ModelInfo(
        model_id="Qwen/Qwen2.5-32B-Instruct",
        provider="Alibaba",
        context_length=32768,
        strengths=["Good balance", "Multilingual"],
        best_for="Medium-tier option",
        tier="pro"
    ),
    "Qwen/Qwen2.5-Coder-32B-Instruct": ModelInfo(
        model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
        provider="Alibaba",
        context_length=32768,
        strengths=["Code specialist", "JSON/structured output"],
        best_for="Agent 4 (Generator) — Alternative",
        tier="pro"
    ),
    "Qwen/Qwen2.5-7B-Instruct": ModelInfo(
        model_id="Qwen/Qwen2.5-7B-Instruct",
        provider="Alibaba",
        context_length=32768,
        strengths=["Fast", "Good all-rounder"],
        best_for="General fallback",
        tier="free"
    ),
    
    # =========================================================================
    # DEEPSEEK — Code Specialists
    # =========================================================================
    "deepseek-ai/deepseek-coder-33b-instruct": ModelInfo(
        model_id="deepseek-ai/deepseek-coder-33b-instruct",
        provider="DeepSeek",
        context_length=16384,
        strengths=["Excellent code generation", "JSON specialist"],
        best_for="Agent 4 (Generator) — Code focused",
        tier="pro"
    ),
    "deepseek-ai/DeepSeek-V2.5": ModelInfo(
        model_id="deepseek-ai/DeepSeek-V2.5",
        provider="DeepSeek",
        context_length=32768,
        strengths=["Strong reasoning", "Good code"],
        best_for="Multi-purpose",
        tier="pro"
    ),
    
    # =========================================================================
    # BIGCODE — StarCoder Family
    # =========================================================================
    "bigcode/starcoder2-15b-instruct-v0.1": ModelInfo(
        model_id="bigcode/starcoder2-15b-instruct-v0.1",
        provider="BigCode",
        context_length=16384,
        strengths=["Code generation", "Multiple languages"],
        best_for="Agent 4 (Generator) — Open source code model",
        tier="free"
    ),
}


# =============================================================================
# RECOMMENDED CONFIGURATIONS BY TIER
# =============================================================================

MODEL_PRESETS = {
    "budget": {
        "name": "Budget (Free Tier)",
        "description": "Best free models for each task",
        "agent2": "microsoft/Phi-3.5-mini-instruct",
        "agent3": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "agent4": "bigcode/starcoder2-15b-instruct-v0.1",
        "fallback": "mistralai/Mistral-7B-Instruct-v0.3",
    },
    "balanced": {
        "name": "Balanced (Pro Tier)",
        "description": "Good quality/cost balance",
        "agent2": "google/gemma-2-9b-it",
        "agent3": "meta-llama/Llama-3.1-70B-Instruct",
        "agent4": "mistralai/Codestral-22B-v0.1",
        "fallback": "Qwen/Qwen2.5-7B-Instruct",
    },
    "quality": {
        "name": "Maximum Quality (Pro+)",
        "description": "Best models regardless of cost",
        "agent2": "google/gemma-2-27b-it",
        "agent3": "meta-llama/Llama-3.1-405B-Instruct",
        "agent4": "deepseek-ai/deepseek-coder-33b-instruct",
        "fallback": "meta-llama/Llama-3.1-8B-Instruct",
    },
    "diverse": {
        "name": "Diverse Providers",
        "description": "One model from each major provider",
        "agent2": "microsoft/Phi-3.5-mini-instruct",  # Microsoft
        "agent3": "CohereForAI/c4ai-command-r-plus",  # Cohere
        "agent4": "mistralai/Codestral-22B-v0.1",     # Mistral
        "fallback": "meta-llama/Llama-3.1-8B-Instruct",  # Meta
    },
}


# =============================================================================
# AGENT-SPECIFIC RECOMMENDATIONS
# =============================================================================

AGENT_MODEL_RECOMMENDATIONS = {
    "crawler": {
        "requires_llm": False,
        "notes": "Pure rule-based extraction using Playwright + CSS parsing"
    },
    "extractor": {
        "requires_llm": False,
        "notes": "Pure rule-based extraction using Playwright + CSS parsing"
    },
    "normalizer": {
        "requires_llm": True,
        "task": "Token naming, duplicate detection, pattern inference",
        "needs": ["Fast inference", "Good instruction following", "Structured output"],
        "recommended": [
            ("microsoft/Phi-3.5-mini-instruct", "BEST — Fast, great structured output"),
            ("google/gemma-2-9b-it", "Good balance of speed and quality"),
            ("Qwen/Qwen2.5-7B-Instruct", "Reliable all-rounder"),
        ],
        "temperature": 0.2,
    },
    "advisor": {
        "requires_llm": True,
        "task": "Design system analysis, best practice recommendations",
        "needs": ["Strong reasoning", "Design knowledge", "Creative suggestions"],
        "recommended": [
            ("meta-llama/Llama-3.1-70B-Instruct", "BEST — Excellent reasoning"),
            ("CohereForAI/c4ai-command-r-plus", "Great for analysis tasks"),
            ("Qwen/Qwen2.5-72B-Instruct", "Strong alternative"),
            ("mistralai/Mixtral-8x7B-Instruct-v0.1", "Best free option"),
        ],
        "temperature": 0.4,
    },
    "generator": {
        "requires_llm": True,
        "task": "Generate JSON tokens, CSS variables, structured output",
        "needs": ["Code generation", "JSON formatting", "Schema adherence"],
        "recommended": [
            ("mistralai/Codestral-22B-v0.1", "BEST — Mistral's code model"),
            ("deepseek-ai/deepseek-coder-33b-instruct", "Excellent code specialist"),
            ("Qwen/Qwen2.5-Coder-32B-Instruct", "Strong code model"),
            ("bigcode/starcoder2-15b-instruct-v0.1", "Best free option"),
        ],
        "temperature": 0.1,
    },
}


# =============================================================================
# INFERENCE CLIENT
# =============================================================================

class HFInferenceClient:
    """
    Wrapper around HuggingFace Inference API.
    
    Handles model selection, retries, and fallbacks.
    """
    
    def __init__(self):
        self.settings = get_settings()
        # Read token fresh from env — the Settings singleton may have been
        # created before the user entered their token via the Gradio UI.
        self.token = os.getenv("HF_TOKEN", "") or self.settings.hf.hf_token

        if not self.token:
            raise ValueError("HF_TOKEN is required for inference")

        # Let huggingface_hub route to the best available provider automatically.
        # Do NOT set base_url (overrides per-model routing) or
        # provider="hf-inference" (that provider no longer hosts most models).
        # The default provider="auto" picks the first available third-party
        # provider (novita, together, cerebras, etc.) for each model.
        self.sync_client = InferenceClient(token=self.token)
        self.async_client = AsyncInferenceClient(token=self.token)
    
    def get_model_for_agent(self, agent_name: str) -> str:
        """Get the appropriate model for an agent."""
        return self.settings.get_model_for_agent(agent_name)
    
    def get_temperature_for_agent(self, agent_name: str) -> float:
        """Get recommended temperature for an agent."""
        temps = {
            # Legacy agents
            "normalizer": 0.2,  # Consistent naming
            "advisor": 0.4,    # Creative recommendations
            "generator": 0.1,  # Precise formatting
            # Stage 2 agents — tuned per persona
            "brand_identifier": 0.4,          # AURORA — creative color reasoning
            "benchmark_advisor": 0.25,        # ATLAS — analytical comparison
            "best_practices_validator": 0.2,  # SENTINEL — precise rule-checking
            "head_synthesizer": 0.3,          # NEXUS — balanced synthesis
        }
        return temps.get(agent_name, 0.3)
    
    def _build_messages(
        self,
        system_prompt: str,
        user_message: str,
        examples: list[dict] = None
    ) -> list[dict]:
        """Build message list for chat completion."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if examples:
            for example in examples:
                messages.append({"role": "user", "content": example["user"]})
                messages.append({"role": "assistant", "content": example["assistant"]})
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def complete(
        self,
        agent_name: str,
        system_prompt: str,
        user_message: str,
        examples: list[dict] = None,
        max_tokens: int = None,
        temperature: float = None,
        json_mode: bool = False,
    ) -> str:
        """
        Synchronous completion.
        
        Args:
            agent_name: Which agent is making the call (for model selection)
            system_prompt: System instructions
            user_message: User input
            examples: Optional few-shot examples
            max_tokens: Max tokens to generate
            temperature: Sampling temperature (uses agent default if not specified)
            json_mode: If True, instruct model to output JSON
        
        Returns:
            Generated text
        """
        model = self.get_model_for_agent(agent_name)
        max_tokens = max_tokens or self.settings.hf.max_new_tokens
        temperature = temperature or self.get_temperature_for_agent(agent_name)
        
        # Build messages
        if json_mode:
            system_prompt = f"{system_prompt}\n\nYou must respond with valid JSON only. No markdown, no explanation, just JSON."
        
        messages = self._build_messages(system_prompt, user_message, examples)
        
        try:
            response = self.sync_client.chat_completion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content

        except Exception as e:
            error_msg = str(e)
            print(f"[HF] Primary model {model} failed: {error_msg[:120]}")
            fallback = self.settings.models.fallback_model
            if fallback and fallback != model:
                print(f"[HF] Trying fallback: {fallback}")
                try:
                    response = self.sync_client.chat_completion(
                        model=fallback,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    return response.choices[0].message.content
                except Exception as fallback_err:
                    print(f"[HF] Fallback {fallback} also failed: {str(fallback_err)[:120]}")
                    raise fallback_err
            raise e
    
    async def complete_async(
        self,
        agent_name: str,
        system_prompt: str,
        user_message: str,
        examples: list[dict] = None,
        max_tokens: int = None,
        temperature: float = None,
        json_mode: bool = False,
    ) -> str:
        """
        Asynchronous completion.
        
        Same parameters as complete().
        """
        model = self.get_model_for_agent(agent_name)
        max_tokens = max_tokens or self.settings.hf.max_new_tokens
        temperature = temperature or self.get_temperature_for_agent(agent_name)
        
        if json_mode:
            system_prompt = f"{system_prompt}\n\nYou must respond with valid JSON only. No markdown, no explanation, just JSON."
        
        messages = self._build_messages(system_prompt, user_message, examples)
        
        try:
            response = await self.async_client.chat_completion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content

        except Exception as e:
            error_msg = str(e)
            print(f"[HF] Primary model {model} failed: {error_msg[:120]}")
            fallback = self.settings.models.fallback_model
            if fallback and fallback != model:
                print(f"[HF] Trying fallback: {fallback}")
                try:
                    response = await self.async_client.chat_completion(
                        model=fallback,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    return response.choices[0].message.content
                except Exception as fallback_err:
                    print(f"[HF] Fallback {fallback} also failed: {str(fallback_err)[:120]}")
                    raise fallback_err
            raise e
    
    async def stream_async(
        self,
        agent_name: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int = None,
        temperature: float = None,
    ) -> AsyncGenerator[str, None]:
        """
        Async streaming completion.
        
        Yields tokens as they are generated.
        """
        model = self.get_model_for_agent(agent_name)
        max_tokens = max_tokens or self.settings.hf.max_new_tokens
        temperature = temperature or self.get_temperature_for_agent(agent_name)
        
        messages = self._build_messages(system_prompt, user_message)
        
        async for chunk in await self.async_client.chat_completion(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        ):
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# =============================================================================
# SINGLETON & CONVENIENCE FUNCTIONS
# =============================================================================

_client: Optional[HFInferenceClient] = None


def get_inference_client() -> HFInferenceClient:
    """Get or create the inference client singleton.

    Re-creates the client if the token has changed (e.g. user entered it
    via the Gradio UI after initial startup).
    """
    global _client
    current_token = os.getenv("HF_TOKEN", "")
    if _client is None or (_client.token != current_token and current_token):
        _client = HFInferenceClient()
    return _client


def complete(
    agent_name: str,
    system_prompt: str,
    user_message: str,
    **kwargs
) -> str:
    """Convenience function for sync completion."""
    client = get_inference_client()
    return client.complete(agent_name, system_prompt, user_message, **kwargs)


async def complete_async(
    agent_name: str,
    system_prompt: str,
    user_message: str,
    **kwargs
) -> str:
    """Convenience function for async completion."""
    client = get_inference_client()
    return await client.complete_async(agent_name, system_prompt, user_message, **kwargs)


def get_model_info(model_id: str) -> dict:
    """Get information about a specific model."""
    if model_id in AVAILABLE_MODELS:
        info = AVAILABLE_MODELS[model_id]
        return {
            "model_id": info.model_id,
            "provider": info.provider,
            "context_length": info.context_length,
            "strengths": info.strengths,
            "best_for": info.best_for,
            "tier": info.tier,
        }
    return {"model_id": model_id, "provider": "unknown"}


def get_models_by_provider() -> dict[str, list[str]]:
    """Get all models grouped by provider."""
    by_provider = {}
    for model_id, info in AVAILABLE_MODELS.items():
        if info.provider not in by_provider:
            by_provider[info.provider] = []
        by_provider[info.provider].append(model_id)
    return by_provider


def get_models_by_tier(tier: str) -> list[str]:
    """Get all models for a specific tier (free, pro, pro+)."""
    return [
        model_id for model_id, info in AVAILABLE_MODELS.items()
        if info.tier == tier
    ]


def get_preset_config(preset_name: str) -> dict:
    """Get a preset model configuration."""
    return MODEL_PRESETS.get(preset_name, MODEL_PRESETS["balanced"])

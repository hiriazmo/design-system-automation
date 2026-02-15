"""
Application Settings
Design System Extractor v2

Loads configuration from environment variables and YAML files.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
import yaml

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try loading from parent directory (for development)
    load_dotenv(Path(__file__).parent.parent / ".env")


@dataclass
class HFSettings:
    """Hugging Face configuration."""
    hf_token: str = field(default_factory=lambda: os.getenv("HF_TOKEN", ""))
    hf_space_name: str = field(default_factory=lambda: os.getenv("HF_SPACE_NAME", ""))
    use_inference_api: bool = field(default_factory=lambda: os.getenv("USE_HF_INFERENCE_API", "true").lower() == "true")
    inference_timeout: int = field(default_factory=lambda: int(os.getenv("HF_INFERENCE_TIMEOUT", "120")))
    max_new_tokens: int = field(default_factory=lambda: int(os.getenv("HF_MAX_NEW_TOKENS", "2048")))
    temperature: float = field(default_factory=lambda: float(os.getenv("HF_TEMPERATURE", "0.3")))


@dataclass
class ModelSettings:
    """Model configuration for each agent — Diverse providers."""
    # Agent 1: Rule-based, no LLM needed
    
    # Agent 2 (Normalizer): Fast structured output
    # Default: Microsoft Phi (fast, great structured output)
    agent2_model: str = field(default_factory=lambda: os.getenv("AGENT2_MODEL", "microsoft/Phi-3.5-mini-instruct"))
    
    # Agent 3 (Advisor): Strong reasoning - MOST IMPORTANT
    # Default: Qwen 2.5 72B (freely available on HF serverless, no gated access needed)
    # Alternative: meta-llama/Llama-3.1-70B-Instruct (requires Meta license acceptance)
    agent3_model: str = field(default_factory=lambda: os.getenv("AGENT3_MODEL", "Qwen/Qwen2.5-72B-Instruct"))
    
    # Agent 4 (Generator): Code/JSON specialist
    # Default: Mistral Codestral (code specialist)
    agent4_model: str = field(default_factory=lambda: os.getenv("AGENT4_MODEL", "mistralai/Codestral-22B-v0.1"))
    
    # Fallback (must be freely available on HF serverless inference)
    fallback_model: str = field(default_factory=lambda: os.getenv("FALLBACK_MODEL", "Qwen/Qwen2.5-7B-Instruct"))


@dataclass
class APISettings:
    """API key configuration (optional alternatives)."""
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))


@dataclass
class BrowserSettings:
    """Playwright browser configuration."""
    browser_type: str = field(default_factory=lambda: os.getenv("BROWSER_TYPE", "chromium"))
    headless: bool = field(default_factory=lambda: os.getenv("BROWSER_HEADLESS", "true").lower() == "true")
    timeout: int = field(default_factory=lambda: int(os.getenv("BROWSER_TIMEOUT", "30000")))
    network_idle_timeout: int = field(default_factory=lambda: int(os.getenv("NETWORK_IDLE_TIMEOUT", "5000")))


@dataclass
class CrawlSettings:
    """Website crawling configuration."""
    max_pages: int = field(default_factory=lambda: int(os.getenv("MAX_PAGES", "20")))
    min_pages: int = field(default_factory=lambda: int(os.getenv("MIN_PAGES", "10")))
    crawl_delay_ms: int = field(default_factory=lambda: int(os.getenv("CRAWL_DELAY_MS", "1000")))
    max_concurrent: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_CRAWLS", "3")))
    respect_robots_txt: bool = field(default_factory=lambda: os.getenv("RESPECT_ROBOTS_TXT", "true").lower() == "true")


@dataclass
class ViewportSettings:
    """Viewport configuration for extraction."""
    desktop_width: int = 1440
    desktop_height: int = 900
    mobile_width: int = 375
    mobile_height: int = 812


@dataclass
class StorageSettings:
    """Persistent storage configuration."""
    storage_path: str = field(default_factory=lambda: os.getenv("STORAGE_PATH", "/data"))
    enable_persistence: bool = field(default_factory=lambda: os.getenv("ENABLE_PERSISTENCE", "true").lower() == "true")
    max_versions: int = field(default_factory=lambda: int(os.getenv("MAX_VERSIONS", "10")))


@dataclass
class UISettings:
    """UI configuration."""
    server_port: int = field(default_factory=lambda: int(os.getenv("SERVER_PORT", "7860")))
    share: bool = field(default_factory=lambda: os.getenv("SHARE", "false").lower() == "true")
    theme: str = field(default_factory=lambda: os.getenv("UI_THEME", "soft"))


@dataclass
class FeatureFlags:
    """Feature toggles."""
    color_ramps: bool = field(default_factory=lambda: os.getenv("FEATURE_COLOR_RAMPS", "true").lower() == "true")
    type_scales: bool = field(default_factory=lambda: os.getenv("FEATURE_TYPE_SCALES", "true").lower() == "true")
    a11y_checks: bool = field(default_factory=lambda: os.getenv("FEATURE_A11Y_CHECKS", "true").lower() == "true")
    parallel_extraction: bool = field(default_factory=lambda: os.getenv("FEATURE_PARALLEL_EXTRACTION", "true").lower() == "true")


@dataclass
class Settings:
    """Main settings container."""
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    
    hf: HFSettings = field(default_factory=HFSettings)
    models: ModelSettings = field(default_factory=ModelSettings)
    api: APISettings = field(default_factory=APISettings)
    browser: BrowserSettings = field(default_factory=BrowserSettings)
    crawl: CrawlSettings = field(default_factory=CrawlSettings)
    viewport: ViewportSettings = field(default_factory=ViewportSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    ui: UISettings = field(default_factory=UISettings)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    
    # Agent configuration loaded from YAML
    agents_config: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Load agent configuration from YAML after initialization."""
        self.load_agents_config()
    
    def load_agents_config(self):
        """Load agent personas and settings from YAML file."""
        yaml_path = Path(__file__).parent / "agents.yaml"
        if yaml_path.exists():
            with open(yaml_path, "r") as f:
                self.agents_config = yaml.safe_load(f)
        else:
            print(f"Warning: agents.yaml not found at {yaml_path}")
            self.agents_config = {}
    
    def get_agent_persona(self, agent_name: str) -> str:
        """Get persona string for an agent."""
        agent_key = f"agent_{agent_name}"
        if agent_key in self.agents_config:
            return self.agents_config[agent_key].get("persona", "")
        return ""
    
    def get_agent_config(self, agent_name: str) -> dict:
        """Get full configuration for an agent."""
        agent_key = f"agent_{agent_name}"
        return self.agents_config.get(agent_key, {})
    
    def get_model_for_agent(self, agent_name: str) -> str:
        """Get the model ID for a specific agent."""
        model_map = {
            # Legacy agents
            "normalizer": self.models.agent2_model,
            "advisor": self.models.agent3_model,
            "generator": self.models.agent4_model,
            
            # Stage 2 New Architecture agents — optimized model per role
            # AURORA: Creative/visual reasoning for brand color analysis
            "brand_identifier": os.getenv("BRAND_IDENTIFIER_MODEL", "Qwen/Qwen2.5-72B-Instruct"),
            # ATLAS: 128K context for large benchmark data, strong comparative reasoning
            "benchmark_advisor": os.getenv("BENCHMARK_ADVISOR_MODEL", "meta-llama/Llama-3.3-70B-Instruct"),
            # SENTINEL: Methodical rule-following, precise judgment
            "best_practices_validator": os.getenv("BEST_PRACTICES_MODEL", "Qwen/Qwen2.5-72B-Instruct"),
            # NEXUS: 128K context for combined inputs, strong synthesis
            "head_synthesizer": os.getenv("HEAD_SYNTHESIZER_MODEL", "meta-llama/Llama-3.3-70B-Instruct"),
            "benchmark_extractor": self.models.agent2_model,  # Phi-3.5 - structured extraction
        }
        return model_map.get(agent_name, self.models.fallback_model)
    
    def validate(self) -> list[str]:
        """Validate settings and return list of errors."""
        errors = []
        
        if not self.hf.hf_token:
            errors.append("HF_TOKEN is required for model inference")
        
        if self.crawl.max_pages < self.crawl.min_pages:
            errors.append("MAX_PAGES must be >= MIN_PAGES")
        
        return errors


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment and config files."""
    global settings
    settings = Settings()
    return settings


# Convenience functions
def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return settings.debug


def get_hf_token() -> str:
    """Get HuggingFace token."""
    return settings.hf.hf_token


def get_agent_persona(agent_name: str) -> str:
    """Get persona for an agent."""
    return settings.get_agent_persona(agent_name)


def get_model_for_agent(agent_name: str) -> str:
    """Get model ID for an agent."""
    return settings.get_model_for_agent(agent_name)

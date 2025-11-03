"""Configuration management for mini-Atlas."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseModel):
    """Agent behavior configuration."""
    
    max_steps: int = Field(default=30, ge=1, le=100)
    allow_navigation: bool = True
    screenshot_every_step: bool = True
    vision_enabled: bool = True
    action_schema_strict: bool = True
    wait_after_action_ms: int = Field(default=500, ge=0, le=5000)


class ViewportConfig(BaseModel):
    """Browser viewport configuration."""
    
    width: int = Field(default=1366, ge=800, le=3840)
    height: int = Field(default=768, ge=600, le=2160)


class BrowserConfig(BaseModel):
    """Browser configuration."""
    
    default_timeout_ms: int = Field(default=15000, ge=1000, le=60000)
    navigation_timeout_ms: int = Field(default=30000, ge=5000, le=120000)
    storage_mode: str = Field(default="ephemeral", pattern="^(ephemeral|persistent)$")
    persistent_dir: str = "./storage"
    context_isolation: bool = True
    locale: str = "tr-TR"
    timezone: str = "Europe/Istanbul"
    viewport: ViewportConfig = Field(default_factory=ViewportConfig)


class NetworkConfig(BaseModel):
    """Network monitoring configuration."""
    
    record_responses: bool = True
    max_payload_kb: int = Field(default=256, ge=1, le=10240)
    verify_backend_success: bool = True


class SecurityConfig(BaseModel):
    """Security and safety configuration."""
    
    block_file_dialogs: bool = True
    block_downloads: bool = True
    confirm_sensitive_actions: bool = True


class TelemetryConfig(BaseModel):
    """Logging and telemetry configuration."""
    
    json_logging: bool = True
    redact_secrets: bool = True
    sink: str = Field(default="stdout", pattern="^(stdout|file|both)$")


class Settings(BaseSettings):
    """Main application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM Configuration
    llm_provider: str = Field(default="openai", pattern="^(openai|ollama|vllm)$")
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    
    # Agent Settings (can override from env)
    agent_max_steps: Optional[int] = None
    agent_step_timeout: int = 30
    agent_total_timeout: int = 300
    
    # Browser Configuration
    browser: str = Field(default="headless", pattern="^(headless|headed)$")
    proxy_url: Optional[str] = None
    user_agent: Optional[str] = None
    timezone: str = "Europe/Istanbul"
    
    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Optional Services
    redis_url: Optional[str] = None
    mongo_url: Optional[str] = None
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    
    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: Optional[str], info) -> Optional[str]:
        """Validate OpenAI API key if OpenAI provider is selected."""
        if info.data.get("llm_provider") == "openai" and not v:
            raise ValueError("OPENAI_API_KEY required when LLM_PROVIDER is 'openai'")
        return v


class Config:
    """Combined configuration from YAML and environment."""
    
    def __init__(self):
        self.settings = Settings()
        self._yaml_config = self._load_yaml_config()
        
        # Load component configs from YAML
        self.agent = AgentConfig(**self._yaml_config.get("agent", {}))
        self.browser = BrowserConfig(**self._yaml_config.get("browser", {}))
        self.network = NetworkConfig(**self._yaml_config.get("network", {}))
        self.security = SecurityConfig(**self._yaml_config.get("security", {}))
        self.telemetry = TelemetryConfig(**self._yaml_config.get("telemetry", {}))
        
        # Override from environment if specified
        if self.settings.agent_max_steps:
            self.agent.max_steps = self.settings.agent_max_steps
        if self.settings.timezone:
            self.browser.timezone = self.settings.timezone
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = Path(__file__).parent.parent / "configs" / "config.yaml"
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f) or {}
        return {}
    
    @property
    def is_headless(self) -> bool:
        """Check if browser should run in headless mode."""
        return self.settings.browser == "headless"
    
    @property
    def has_redis(self) -> bool:
        """Check if Redis is configured."""
        return bool(self.settings.redis_url)
    
    @property
    def has_mongo(self) -> bool:
        """Check if MongoDB is configured."""
        return bool(self.settings.mongo_url)


# Global config instance
config = Config()

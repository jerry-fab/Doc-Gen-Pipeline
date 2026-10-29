"""
analyzer.utils.config_loader
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Loads and validates settings from `config.json`.
Uses the explicit `"deployment_mode"` setting ('local' or 'production')
to select the corresponding profile.
"""

import os
import json
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ProfileConfig(BaseModel):
    """Configuration for an individual environment profile (local or production)."""
    provider: str = Field("gemini", description="Provider identifier (gemini, groq, mistral, claude)")
    description: Optional[str] = Field(None, description="Human readable description")
    enabled: bool = Field(False, description="Whether to invoke this LLM API")
    api_key: Optional[str] = Field("", description="API key for the designated provider")
    api_base: str = Field("https://generativelanguage.googleapis.com/v1beta/openai/", description="Endpoint base URL")
    model: str = Field("gemini-1.5-flash", description="Model identifier")
    temperature: float = Field(0.1, description="Sampling temperature")
    timeout_seconds: int = Field(30, description="Network timeout in seconds")


class GeneratorConfig(BaseModel):
    """Configuration for documentation output formatting."""
    output_dir: str = Field("docs", description="Directory where Markdown docs will be written")
    include_mermaid_diagrams: bool = Field(True, description="Whether to embed Mermaid class diagrams")
    max_fields_in_diagram: int = Field(5, description="Maximum fields displayed in Mermaid class boxes")


class ScannerConfig(BaseModel):
    """Configuration for repository file discovery."""
    supported_extensions: List[str] = Field(
        default_factory=lambda: [".py", ".cs", ".java"],
        description="Source code extensions to scan"
    )
    ignored_directories: List[str] = Field(
        default_factory=lambda: [
            ".git", ".github", "docs", "venv", ".venv",
            "bin", "obj", "node_modules", "__pycache__", "build", "dist"
        ],
        description="Directory names to skip during recursive search"
    )


class AppConfig(BaseModel):
    """Root configuration model representing config.json with deployment_mode."""
    deployment_mode: str = Field("local", description="Deployment mode: 'local' or 'production'")
    profiles: Dict[str, ProfileConfig] = Field(default_factory=dict, description="Configured environment profiles")
    generator: GeneratorConfig = Field(default_factory=GeneratorConfig)
    scanner: ScannerConfig = Field(default_factory=ScannerConfig)

    def get_active_profile(self) -> ProfileConfig:
        """
        Retrieves the profile directly designated by the `deployment_mode` in config.json.
        
        Returns:
            ProfileConfig instance for 'local' or 'production'.
        """
        mode = self.deployment_mode.lower().strip()
        if mode in self.profiles:
            return self.profiles[mode]
        
        # Fallback profile if key not matched
        return ProfileConfig()


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Loads and parses configuration from config.json.
    
    If config.json is not found or malformed, returns safe default configuration.
    
    Args:
        config_path: Path to config.json. If None, searches project root.
        
    Returns:
        AppConfig instance with validated settings.
    """
    if config_path is None:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(root_dir, "config.json")

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AppConfig(**data)
        except Exception as exc:
            print(f"[Warning] Failed to load '{config_path}': {exc}. Using default configuration.")
            return AppConfig()
    else:
        return AppConfig()

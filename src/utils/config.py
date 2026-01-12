"""Configuration loading utilities."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dictionary containing merged configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    # Load environment variables from .env file
    load_dotenv()

    # Load YAML configuration
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def get_api_key(provider: str) -> str:
    """Get API key for the specified provider from environment.

    Args:
        provider: LLM provider name ("anthropic" or "google")

    Returns:
        API key string

    Raises:
        ValueError: If API key is not set
    """
    key_mapping = {
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY"
    }

    env_var = key_mapping.get(provider.lower())
    if not env_var:
        raise ValueError(f"Unknown provider: {provider}")

    api_key = os.getenv(env_var)
    if not api_key:
        raise ValueError(
            f"API key not found. Please set {env_var} in your .env file."
        )

    return api_key

"""LLM client factory for provider selection."""

from typing import Any, Dict

from .base import BaseLLMClient
from .anthropic_client import AnthropicClient
from .google_client import GoogleClient


def create_llm_client(config: Dict[str, Any]) -> BaseLLMClient:
    """Create an LLM client based on configuration.

    Factory function that instantiates the appropriate LLM client
    based on the provider setting in config.

    Args:
        config: Full application config dict containing 'llm' section

    Returns:
        Configured LLM client instance

    Raises:
        ValueError: If provider is unknown or not configured
    """
    llm_config = config.get("llm", {})
    provider = llm_config.get("provider", "").lower()

    if not provider:
        raise ValueError(
            "No LLM provider configured. "
            "Set 'llm.provider' in config.yaml to 'anthropic' or 'google'."
        )

    # Get provider-specific config
    provider_config = llm_config.get(provider, {})

    if provider == "anthropic":
        return AnthropicClient(provider_config)
    elif provider == "google":
        return GoogleClient(provider_config)
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            "Supported providers: 'anthropic', 'google'"
        )

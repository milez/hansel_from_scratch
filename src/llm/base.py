"""Abstract base class for LLM clients."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseLLMClient(ABC):
    """Abstract base class for all LLM providers.

    Provides a unified interface for different LLM backends
    (Anthropic Claude, Google Gemini, etc.)
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the LLM client.

        Args:
            config: Provider-specific configuration dict
        """
        self.model = config.get("model", "")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.7)

    @abstractmethod
    async def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Send messages to LLM and get response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt

        Returns:
            Response text from LLM
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name for display purposes."""
        pass

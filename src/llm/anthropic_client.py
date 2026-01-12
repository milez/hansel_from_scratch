"""Anthropic Claude LLM client implementation."""

from typing import Any, Dict, List, Optional

import anthropic

from .base import BaseLLMClient


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client.

    Implements the BaseLLMClient interface for Claude models.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize Anthropic client.

        Args:
            config: Configuration dict with model, max_tokens, temperature
        """
        super().__init__(config)
        self.client = anthropic.AsyncAnthropic()
        # Default to Claude Sonnet if not specified
        if not self.model:
            self.model = "claude-sonnet-4-20250514"

    async def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Send messages to Claude and get response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt

        Returns:
            Response text from Claude
        """
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt or "",
            messages=messages
        )
        return response.content[0].text

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "Anthropic Claude"

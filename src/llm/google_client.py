"""Google Gemini LLM client implementation."""

import os
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from .base import BaseLLMClient


class GoogleClient(BaseLLMClient):
    """Google Gemini API client.

    Implements the BaseLLMClient interface for Gemini models.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize Google Gemini client.

        Args:
            config: Configuration dict with model, max_tokens, temperature
        """
        super().__init__(config)

        # Configure API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)

        # Default to Gemini Flash if not specified
        if not self.model:
            self.model = "gemini-2.0-flash"

        self.genai_model = genai.GenerativeModel(self.model)

    async def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Send messages to Gemini and get response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt

        Returns:
            Response text from Gemini
        """
        # Convert messages to Gemini format
        history = self._convert_history(messages[:-1], system_prompt)

        # Start chat with history
        chat = self.genai_model.start_chat(history=history)

        # Send the last message
        last_message = messages[-1]["content"] if messages else ""

        response = await chat.send_message_async(
            last_message,
            generation_config=genai.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=self.temperature
            )
        )

        return response.text

    def _convert_history(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Convert OpenAI/Anthropic message format to Gemini format.

        Args:
            messages: Messages in standard format
            system_prompt: Optional system prompt to prepend

        Returns:
            Messages in Gemini format
        """
        history = []

        # Add system prompt as first user message if provided
        if system_prompt:
            history.append({
                "role": "user",
                "parts": [f"System: {system_prompt}"]
            })
            history.append({
                "role": "model",
                "parts": ["Understood. I will follow these instructions."]
            })

        # Convert remaining messages
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            history.append({
                "role": role,
                "parts": [msg["content"]]
            })

        return history

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "Google Gemini"

"""Base Agent class for Hansel agents."""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from src.context.loader import AgentContextLoader, AgentContext


class BaseAgent(ABC):
    """Abstract base class for all Hansel agents."""

    def __init__(self):
        self._system_prompt: Optional[str] = None
        self._context: Optional[AgentContext] = None

    @property
    @abstractmethod
    def id(self) -> str:
        """Agent identifier (e.g., 'nora', 'arthur')."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent display name."""
        pass

    @property
    @abstractmethod
    def icon(self) -> str:
        """Agent emoji icon."""
        pass

    @property
    @abstractmethod
    def role(self) -> str:
        """Agent role description."""
        pass

    @property
    def commands(self) -> List[str]:
        """List of commands this agent supports."""
        return []

    @property
    def definition_file(self) -> Path:
        """Path to agent definition markdown file."""
        return Path(f"docs/agents/{self.id}.md")

    def load_system_prompt(self) -> str:
        """Load system prompt from agent definition file.

        Returns:
            System prompt string
        """
        if self._system_prompt is not None:
            return self._system_prompt

        if not self.definition_file.exists():
            self._system_prompt = self._get_default_prompt()
            return self._system_prompt

        content = self.definition_file.read_text(encoding="utf-8")

        # Extract YAML from code block
        yaml_match = re.search(r"```yaml\s*\n(.*?)\n```", content, re.DOTALL)
        if yaml_match:
            try:
                yaml_content = yaml.safe_load(yaml_match.group(1))
                instructions = yaml_content.get("instructions", {})

                # Build system prompt from instructions
                prompt_parts = [
                    f"Du bist {self.name}, {instructions.get('role', self.role)}.",
                    "",
                    f"**Persona:** {instructions.get('persona', '')}",
                    f"**Fokus:** {instructions.get('focus', '')}",
                    "",
                    "**Verhaltensregeln:**",
                    instructions.get('logic', ''),
                    "",
                    "**Verfügbare Commands:**"
                ]

                for cmd in instructions.get('commands', []):
                    prompt_parts.append(f"- {cmd}")

                prompt_parts.extend([
                    "",
                    "**Startup:**",
                    instructions.get('startup', '')
                ])

                self._system_prompt = "\n".join(prompt_parts)
            except yaml.YAMLError:
                self._system_prompt = self._get_default_prompt()
        else:
            self._system_prompt = self._get_default_prompt()

        # Append context if available
        context_summary = self.get_context_summary()
        if context_summary:
            self._system_prompt = self._system_prompt + "\n\n" + context_summary

        return self._system_prompt

    def _get_default_prompt(self) -> str:
        """Get default system prompt if definition file not found."""
        return f"""Du bist {self.name}, {self.role}.
Antworte freundlich und hilfreich auf Deutsch."""

    def load_context(self) -> AgentContext:
        """Load context for this agent using Just-In-Time loading.

        Returns:
            AgentContext with relevant artifacts and summary
        """
        if self._context is None:
            loader = AgentContextLoader(self.id)
            self._context = loader.load()
        return self._context

    def clear_context_cache(self) -> None:
        """Clear cached context to force reload on next access."""
        self._context = None
        self._system_prompt = None

    def get_context_summary(self) -> str:
        """Get formatted context summary for system prompt.

        Returns:
            Context summary string or empty if no context
        """
        context = self.load_context()
        return context.summary

    def get_agent_info(self) -> Dict[str, str]:
        """Get agent info for chat messages.

        Returns:
            Dict with agent, agent_icon, agent_name
        """
        return {
            "agent": self.id,
            "agent_icon": self.icon,
            "agent_name": self.name
        }

    def handle_command(self, command: str) -> Optional[str]:
        """Handle a command if supported.

        Args:
            command: The command string (e.g., '*status')

        Returns:
            Response string if command handled, None otherwise
        """
        return None

    def is_command(self, message: str) -> bool:
        """Check if message is a command.

        Args:
            message: User message

        Returns:
            True if message starts with *
        """
        return message.strip().startswith("*")

    def parse_switch_command(self, message: str) -> Optional[str]:
        """Parse a switch command and return target agent ID.

        Args:
            message: User message

        Returns:
            Target agent ID if valid switch command, None otherwise
        """
        msg = message.strip().lower()
        if msg.startswith("*wechsel "):
            target = msg.replace("*wechsel ", "").strip()
            return target if target else None
        return None

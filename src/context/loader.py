"""Context loader for Hansel agents - Just-In-Time loading of relevant artifacts."""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.discovery.models import ArtifactType, Artifact
from src.discovery.artifacts import load_artifacts


# Token budget per agent (approximate)
AGENT_TOKEN_BUDGETS = {
    "nora": 2000,
    "arthur": 8000,  # Increased for book knowledge
    "finn": 5000,
    "ida": 4000,
    "theo": 4000
}

# Knowledge files per agent (from the book)
AGENT_KNOWLEDGE_FILES: Dict[str, List[str]] = {
    "arthur": ["docs/knowledge/arthur-buch-kapitel.md"],
    "finn": [],  # TODO: Add chapter 4
    "ida": [],   # TODO: Add chapter 5
    "theo": [],  # TODO: Add chapter 6
    "nora": ["docs/knowledge/explorationsmodell.md"],
}

# Which artifact types are relevant for each agent
AGENT_ARTIFACT_RELEVANCE = {
    "nora": [ArtifactType.MANDAT],  # Overview only
    "arthur": [ArtifactType.MANDAT],  # Full details
    "finn": [ArtifactType.RESEARCH_QUESTION, ArtifactType.INSIGHT],
    "ida": [ArtifactType.HMW_CHALLENGE, ArtifactType.IDEA],
    "theo": [ArtifactType.TEST_CARD, ArtifactType.LEARNING_CARD]
}


@dataclass
class AgentContext:
    """Context loaded for an agent."""
    agent_id: str
    artifacts: List[Artifact]
    knowledge: str  # Book knowledge content
    summary: str
    token_estimate: int


class AgentContextLoader:
    """Loads context for agents using Just-In-Time loading."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.token_budget = AGENT_TOKEN_BUDGETS.get(agent_id, 3000)
        self.relevant_types = AGENT_ARTIFACT_RELEVANCE.get(agent_id, [])
        self.knowledge_files = AGENT_KNOWLEDGE_FILES.get(agent_id, [])

    def _load_knowledge(self) -> str:
        """Load knowledge files for the agent.

        Returns:
            Combined knowledge content as string
        """
        knowledge_parts = []

        for file_path in self.knowledge_files:
            full_path = Path(file_path)
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding="utf-8")
                    knowledge_parts.append(content)
                except Exception:
                    pass  # Skip unreadable files

        return "\n\n---\n\n".join(knowledge_parts)

    def load(self) -> AgentContext:
        """Load context for the agent.

        Returns:
            AgentContext with relevant artifacts, knowledge and summary
        """
        # Load knowledge from book chapters
        knowledge = self._load_knowledge()

        # Load all artifacts
        all_artifacts = load_artifacts()

        # Filter to relevant types
        relevant = [
            a for a in all_artifacts
            if a.type in self.relevant_types
        ]

        # Build context text (knowledge + artifacts)
        context_text = self._build_context_text(relevant, knowledge)
        token_estimate = self._estimate_tokens(context_text)

        # Truncate artifacts if over budget (keep knowledge)
        while token_estimate > self.token_budget and relevant:
            relevant = relevant[:-1]  # Remove last artifact
            context_text = self._build_context_text(relevant, knowledge)
            token_estimate = self._estimate_tokens(context_text)

        return AgentContext(
            agent_id=self.agent_id,
            artifacts=relevant,
            knowledge=knowledge,
            summary=context_text,
            token_estimate=token_estimate
        )

    def _build_context_text(self, artifacts: List[Artifact], knowledge: str = "") -> str:
        """Build context text from knowledge and artifacts.

        Args:
            artifacts: List of artifacts to include
            knowledge: Book knowledge content

        Returns:
            Formatted context string
        """
        parts = []

        # Add knowledge first (most important)
        if knowledge:
            parts.append("## Dein Fachwissen\n")
            parts.append(knowledge)
            parts.append("\n---\n")
            parts.append("*Nutze dieses Wissen um den User bei der Discovery zu unterstützen.*\n")

        # Add artifacts context
        if artifacts:
            parts.append("## Discovery Context\n")

            for artifact in artifacts:
                parts.append(f"### {artifact.type.value.upper()}: {artifact.title}")
                parts.append(f"Status: {artifact.status.value}")
                parts.append(f"Erstellt von: {artifact.created_by}")
                parts.append("")
                parts.append(artifact.content)
                parts.append("")
                parts.append("---")
                parts.append("")

            parts.append("*Beziehe dich auf diese Artefakte wenn der User nach dem Projekt, Auftrag oder bisherigen Erkenntnissen fragt.*")

        return "\n".join(parts)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Simple approximation: ~4 chars per token for German text.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4


def load_context_for_agent(agent_id: str) -> AgentContext:
    """Convenience function to load context for an agent.

    Args:
        agent_id: Agent identifier

    Returns:
        AgentContext with relevant artifacts
    """
    loader = AgentContextLoader(agent_id)
    return loader.load()


def get_context_summary(agent_id: str) -> str:
    """Get just the context summary text for an agent.

    Args:
        agent_id: Agent identifier

    Returns:
        Context summary string
    """
    context = load_context_for_agent(agent_id)
    return context.summary

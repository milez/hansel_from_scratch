"""Pydantic models for Discovery artifacts."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    """Types of Discovery artifacts."""
    MANDAT = "mandat"
    RESEARCH_QUESTION = "research_question"
    INSIGHT = "insight"
    HMW_CHALLENGE = "hmw_challenge"
    IDEA = "idea"
    TEST_CARD = "test_card"
    LEARNING_CARD = "learning_card"


class ArtifactStatus(str, Enum):
    """Status of an artifact."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


class Artifact(BaseModel):
    """A Discovery artifact."""
    id: str
    type: ArtifactType
    title: str
    content: str
    status: ArtifactStatus = ArtifactStatus.DRAFT
    created_by: str  # Agent ID (nora, arthur, finn, ida, theo)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    related_to: List[str] = Field(default_factory=list)

    def get_category(self) -> str:
        """Get the wall category for this artifact type."""
        type_to_category = {
            ArtifactType.MANDAT: "mandat",
            ArtifactType.RESEARCH_QUESTION: "problem",
            ArtifactType.INSIGHT: "problem",
            ArtifactType.HMW_CHALLENGE: "solution",
            ArtifactType.IDEA: "solution",
            ArtifactType.TEST_CARD: "test",
            ArtifactType.LEARNING_CARD: "test"
        }
        return type_to_category.get(self.type, "problem")

    def get_directory(self) -> str:
        """Get the subdirectory for this artifact type."""
        type_to_dir = {
            ArtifactType.MANDAT: "",
            ArtifactType.RESEARCH_QUESTION: "research",
            ArtifactType.INSIGHT: "research/insights",
            ArtifactType.HMW_CHALLENGE: "ideen",
            ArtifactType.IDEA: "ideen",
            ArtifactType.TEST_CARD: "tests",
            ArtifactType.LEARNING_CARD: "tests"
        }
        return type_to_dir.get(self.type, "")


class DiscoverySession(BaseModel):
    """A Discovery session containing artifacts."""
    id: str
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    current_agent: str = "nora"
    mandat_complete: bool = False

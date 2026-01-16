"""Artifact persistence - save/load artifacts to markdown files."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from src.discovery.models import Artifact, ArtifactType, ArtifactStatus


# Base directory for discovery output
DISCOVERY_DIR = Path("_hansel-output/discovery-wall")


def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        DISCOVERY_DIR,
        DISCOVERY_DIR / "research",
        DISCOVERY_DIR / "research" / "insights",
        DISCOVERY_DIR / "ideen",
        DISCOVERY_DIR / "tests"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def clear_all_artifacts():
    """Delete all artifact files from disk."""
    if not DISCOVERY_DIR.exists():
        return

    # Delete all markdown files in discovery wall
    for md_file in DISCOVERY_DIR.rglob("*.md"):
        md_file.unlink()

    # Also delete session file if exists
    session_file = DISCOVERY_DIR / "session-meta.yaml"
    if session_file.exists():
        session_file.unlink()


def save_artifact(artifact: Artifact) -> Path:
    """Save an artifact to a markdown file.

    Args:
        artifact: The artifact to save

    Returns:
        Path to the saved file
    """
    ensure_directories()

    # Determine file path
    subdir = artifact.get_directory()
    if subdir:
        file_dir = DISCOVERY_DIR / subdir
    else:
        file_dir = DISCOVERY_DIR

    # Generate filename
    if artifact.type == ArtifactType.MANDAT:
        filename = "mandat.md"
    else:
        filename = f"{artifact.id}.md"

    file_path = file_dir / filename

    # Build frontmatter
    frontmatter = {
        "id": artifact.id,
        "type": artifact.type.value,
        "status": artifact.status.value,
        "created_by": artifact.created_by,
        "created_at": artifact.created_at.isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    if artifact.related_to:
        frontmatter["related_to"] = artifact.related_to

    # Build markdown content
    yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
    content = f"---\n{yaml_str}---\n\n# {artifact.title}\n\n{artifact.content}\n"

    # Write file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path


def parse_frontmatter(content: str) -> tuple[Dict, str]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Raw markdown file content

    Returns:
        Tuple of (frontmatter dict, body content)
    """
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if match:
        yaml_str = match.group(1)
        body = match.group(2)
        try:
            frontmatter = yaml.safe_load(yaml_str) or {}
        except yaml.YAMLError:
            frontmatter = {}
        return frontmatter, body.strip()

    return {}, content.strip()


def load_artifact_from_file(file_path: Path) -> Optional[Artifact]:
    """Load an artifact from a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        Artifact or None if parsing fails
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        frontmatter, body = parse_frontmatter(content)

        if not frontmatter.get("id") or not frontmatter.get("type"):
            return None

        # Extract title from body (first # heading)
        title_match = re.match(r"^#\s+(.+)$", body, re.MULTILINE)
        title = title_match.group(1) if title_match else "Untitled"

        # Remove title from body
        body_content = re.sub(r"^#\s+.+\n*", "", body, count=1).strip()

        # Parse dates
        created_at = frontmatter.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()

        updated_at = frontmatter.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif not isinstance(updated_at, datetime):
            updated_at = datetime.now()

        return Artifact(
            id=frontmatter["id"],
            type=ArtifactType(frontmatter["type"]),
            title=title,
            content=body_content,
            status=ArtifactStatus(frontmatter.get("status", "draft")),
            created_by=frontmatter.get("created_by", "unknown"),
            created_at=created_at,
            updated_at=updated_at,
            related_to=frontmatter.get("related_to", [])
        )
    except Exception:
        return None


def load_artifacts() -> List[Artifact]:
    """Load all artifacts from the discovery wall directory.

    Returns:
        List of all artifacts
    """
    ensure_directories()
    artifacts = []

    # Walk through all markdown files
    for md_file in DISCOVERY_DIR.rglob("*.md"):
        artifact = load_artifact_from_file(md_file)
        if artifact:
            artifacts.append(artifact)

    return artifacts


def load_artifacts_by_type(artifact_type: ArtifactType) -> List[Artifact]:
    """Load artifacts of a specific type.

    Args:
        artifact_type: Type to filter by

    Returns:
        List of matching artifacts
    """
    all_artifacts = load_artifacts()
    return [a for a in all_artifacts if a.type == artifact_type]


def get_artifact_counts() -> Dict[str, int]:
    """Get counts of artifacts by wall category.

    Returns:
        Dict with category names and counts
    """
    artifacts = load_artifacts()

    counts = {
        "mandat": 0,
        "problem": 0,
        "solution": 0,
        "test": 0
    }

    for artifact in artifacts:
        category = artifact.get_category()
        if category in counts:
            counts[category] += 1

    return counts


def get_artifacts_for_wall() -> Dict[str, List[str]]:
    """Get artifact titles grouped by wall category.

    Returns:
        Dict with category names and list of artifact titles
    """
    artifacts = load_artifacts()

    wall_data = {
        "mandat": [],
        "problem": [],
        "solution": [],
        "test": []
    }

    for artifact in artifacts:
        category = artifact.get_category()
        if category in wall_data:
            wall_data[category].append(artifact.title)

    return wall_data

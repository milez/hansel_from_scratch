"""Session persistence - save/load chat history and session state."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# Session file location
SESSION_FILE = Path("_hansel-output/discovery-wall/session-meta.yaml")


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return f"session-{uuid.uuid4().hex[:8]}"


def save_session(
    messages: List[Dict[str, Any]],
    session_id: Optional[str] = None,
    session_name: str = "Meine Discovery",
    current_agent: str = "nora",
    mandat_complete: bool = False
) -> Path:
    """Save session state and chat history to YAML file.

    Args:
        messages: List of chat messages
        session_id: Optional session ID (generates new if None)
        session_name: Name of the discovery session
        current_agent: Currently active agent
        mandat_complete: Whether mandat phase is complete

    Returns:
        Path to the saved session file
    """
    # Ensure directory exists
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Load existing session to preserve ID and created_at
    existing = load_session_raw()

    if session_id is None:
        session_id = existing.get("session", {}).get("id") or generate_session_id()

    created_at = existing.get("session", {}).get("created_at") or datetime.now().isoformat()

    # Build session data
    session_data = {
        "session": {
            "id": session_id,
            "name": session_name,
            "created_at": created_at,
            "updated_at": datetime.now().isoformat(),
            "current_agent": current_agent,
            "mandat_complete": mandat_complete
        },
        "chat_history": [
            {
                "role": msg.get("role"),
                "content": msg.get("content"),
                "agent": msg.get("agent"),
                "agent_icon": msg.get("agent_icon"),
                "agent_name": msg.get("agent_name"),
                "timestamp": msg.get("timestamp") or datetime.now().isoformat()
            }
            for msg in messages
        ]
    }

    # Write to file
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        yaml.dump(session_data, f, default_flow_style=False, allow_unicode=True)

    return SESSION_FILE


def load_session_raw() -> Dict[str, Any]:
    """Load raw session data from YAML file.

    Returns:
        Raw session data dict or empty dict if file doesn't exist
    """
    if not SESSION_FILE.exists():
        return {}

    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def load_session() -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Load session state and chat history.

    Returns:
        Tuple of (messages list, session metadata dict)
    """
    data = load_session_raw()

    if not data:
        return [], {}

    # Extract messages
    messages = []
    for msg in data.get("chat_history", []):
        message = {
            "role": msg.get("role"),
            "content": msg.get("content")
        }
        # Add optional fields if present
        if msg.get("agent"):
            message["agent"] = msg["agent"]
        if msg.get("agent_icon"):
            message["agent_icon"] = msg["agent_icon"]
        if msg.get("agent_name"):
            message["agent_name"] = msg["agent_name"]
        if msg.get("timestamp"):
            message["timestamp"] = msg["timestamp"]

        messages.append(message)

    # Extract session metadata
    session_meta = data.get("session", {})

    return messages, session_meta


def clear_session() -> None:
    """Clear the current session (for starting fresh)."""
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def session_exists() -> bool:
    """Check if a session file exists."""
    return SESSION_FILE.exists()

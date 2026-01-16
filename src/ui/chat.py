"""Chat UI component for Hansel."""

from typing import Dict, List, Optional
import streamlit as st

from src.discovery.session import load_session, save_session, session_exists


def init_chat_state():
    """Initialize chat-related session state, loading from disk if available."""
    if "messages" not in st.session_state:
        # Try to load existing session
        if session_exists():
            messages, session_meta = load_session()
            st.session_state.messages = messages
            st.session_state.session_meta = session_meta
        else:
            st.session_state.messages = []
            st.session_state.session_meta = {}


def persist_chat():
    """Save current chat state to disk."""
    save_session(
        messages=st.session_state.messages,
        current_agent=st.session_state.get("current_agent", "nora"),
        mandat_complete=st.session_state.get("mandat_complete", False)
    )


def add_message(
    role: str,
    content: str,
    agent: Optional[str] = None,
    agent_icon: Optional[str] = None,
    agent_name: Optional[str] = None,
    auto_save: bool = True
):
    """Add a message to chat history.

    Args:
        role: 'user' or 'assistant'
        content: Message content
        agent: Agent ID (for assistant messages)
        agent_icon: Agent emoji icon
        agent_name: Agent display name
        auto_save: Whether to auto-save to disk (default True)
    """
    message = {
        "role": role,
        "content": content
    }

    if agent:
        message["agent"] = agent
    if agent_icon:
        message["agent_icon"] = agent_icon
    if agent_name:
        message["agent_name"] = agent_name

    st.session_state.messages.append(message)

    # Auto-save to disk
    if auto_save:
        persist_chat()


def get_chat_history() -> List[Dict[str, str]]:
    """Get chat history in LLM-compatible format.

    Returns:
        List of message dicts with 'role' and 'content' keys
    """
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages
    ]


def render_message(message: Dict):
    """Render a single chat message.

    Args:
        message: Message dict with role, content, and optional agent info
    """
    role = message["role"]

    if role == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
    else:
        # Assistant message - show agent info if available
        agent_icon = message.get("agent_icon", "🤖")
        agent_name = message.get("agent_name", "Assistant")

        with st.chat_message("assistant", avatar=agent_icon):
            # Show agent name as header
            st.caption(f"**{agent_name}**")
            st.markdown(message["content"])


def render_chat():
    """Render the chat interface with message history."""
    init_chat_state()

    # Render all messages
    for message in st.session_state.messages:
        render_message(message)

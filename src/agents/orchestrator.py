"""Agent Orchestrator - manages agent switching and routing."""

from typing import Dict, Optional
import streamlit as st

from src.agents.base import BaseAgent
from src.agents.nora import NoraAgent
from src.agents.arthur import ArthurAgent


# Agent registry
AGENTS: Dict[str, BaseAgent] = {
    "nora": NoraAgent(),
    "arthur": ArthurAgent()
}


def get_agent(agent_id: str) -> Optional[BaseAgent]:
    """Get an agent by ID.

    Args:
        agent_id: Agent identifier

    Returns:
        Agent instance or None
    """
    return AGENTS.get(agent_id)


def get_active_agent() -> BaseAgent:
    """Get the currently active agent.

    Returns:
        Active agent instance (defaults to Nora)
    """
    agent_id = st.session_state.get("current_agent", "nora")
    agent = get_agent(agent_id)

    if agent is None:
        # Fallback to Nora
        agent = AGENTS["nora"]
        st.session_state.current_agent = "nora"

    return agent


def set_active_agent(agent_id: str) -> bool:
    """Set the active agent.

    Args:
        agent_id: Agent identifier to activate

    Returns:
        True if successful, False if agent not found
    """
    if agent_id not in AGENTS:
        return False

    st.session_state.current_agent = agent_id
    return True


def get_available_agents() -> Dict[str, Dict]:
    """Get info about all available agents.

    Returns:
        Dict of agent_id -> agent info
    """
    return {
        agent_id: {
            "name": agent.name,
            "icon": agent.icon,
            "role": agent.role,
            "commands": agent.commands
        }
        for agent_id, agent in AGENTS.items()
    }


def init_orchestrator_state():
    """Initialize orchestrator state."""
    if "current_agent" not in st.session_state:
        st.session_state.current_agent = "nora"

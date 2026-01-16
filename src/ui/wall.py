"""Discovery Wall UI component for Hansel."""

from typing import Dict, List, Optional
import streamlit as st

from src.discovery.artifacts import get_artifacts_for_wall
from src.agents.orchestrator import get_available_agents


def render_wall_section(
    title: str,
    icon: str,
    count: int = 0,
    items: Optional[List[str]] = None
):
    """Render a single wall section.

    Args:
        title: Section title
        icon: Emoji icon
        count: Number of items
        items: Optional list of item names to display
    """
    with st.container():
        # Section header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{icon} {title}**")
        with col2:
            if count > 0:
                st.markdown(f"✅ {count}")
            else:
                st.markdown("○")

        # Show items if any
        if items:
            for item in items[:3]:  # Show max 3 items
                st.caption(f"  • {item}")

        st.divider()


def render_discovery_wall():
    """Render the Discovery Wall with all sections."""
    st.markdown("### 📋 Discovery Wall")

    # Get artifact counts from session state (will be populated by Story 1.4)
    artifacts = st.session_state.get("artifacts", {})

    mandat_count = len(artifacts.get("mandat", []))
    problem_count = len(artifacts.get("problem", []))
    solution_count = len(artifacts.get("solution", []))
    test_count = len(artifacts.get("test", []))

    # Mandat Section
    render_wall_section(
        title="Mandat",
        icon="🎖️",
        count=mandat_count,
        items=artifacts.get("mandat", [])
    )

    # Problem/Research Section
    render_wall_section(
        title="Problem",
        icon="🔍",
        count=problem_count,
        items=artifacts.get("problem", [])
    )

    # Solution/Ideen Section
    render_wall_section(
        title="Lösung",
        icon="💡",
        count=solution_count,
        items=artifacts.get("solution", [])
    )

    # Test/Validierung Section
    render_wall_section(
        title="Test",
        icon="🧪",
        count=test_count,
        items=artifacts.get("test", [])
    )


def render_agent_overview():
    """Render an overview of all available agents."""
    with st.expander("👥 Team Discovery", expanded=False):
        agents = get_available_agents()
        for agent_id, info in agents.items():
            st.markdown(f"**{info['icon']} {info['name']}** - {info['role']}")
            if info['commands']:
                st.caption(f"Commands: {', '.join(info['commands'])}")
            st.divider()


def init_wall_state():
    """Initialize Discovery Wall state by loading artifacts from disk."""
    if "artifacts" not in st.session_state:
        # Load artifacts from filesystem
        st.session_state.artifacts = get_artifacts_for_wall()


def refresh_wall_state():
    """Refresh wall state from disk (call after saving new artifacts)."""
    st.session_state.artifacts = get_artifacts_for_wall()

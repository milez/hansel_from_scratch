"""Hansel - Product Discovery AI Agent Team.

Main Streamlit application entry point.
"""

import asyncio
import re
from typing import Optional
import streamlit as st

from src.utils.config import load_config, get_api_key
from src.llm.factory import create_llm_client
from src.ui.chat import render_chat, add_message, get_chat_history, init_chat_state
from src.ui.wall import render_discovery_wall, init_wall_state, refresh_wall_state, render_agent_overview
from src.agents.orchestrator import get_active_agent, get_agent, set_active_agent, init_orchestrator_state
from src.discovery.session import clear_session
from src.discovery.artifacts import clear_all_artifacts


# Agent name to ID mapping for delegation detection
AGENT_NAME_MAP = {
    "arthur": "arthur",
    "nora": "nora",
    "finn": "finn",
    "ida": "ida",
    "theo": "theo",
}


def detect_delegation(response: str) -> Optional[str]:
    """Detect if LLM response contains a delegation to another agent.

    Looks for patterns like:
    - "Übergabe an Arthur"
    - "Arthur übernimmt"
    - "Wechsel zu Finn"

    Args:
        response: The LLM response text

    Returns:
        Agent ID if delegation detected, None otherwise
    """
    response_lower = response.lower()

    # Patterns that indicate delegation (handoff phrases only)
    delegation_patterns = [
        r"übergabe an (\w+)",
        r"(\w+),? übernimmst du",
        r"(\w+) übernimmt",
        r"wechsel zu (\w+)",
        r"weiterleiten.* an (\w+)",
        r"(\w+) betritt",
        r"zu (\w+) weiterleiten",
    ]

    for pattern in delegation_patterns:
        match = re.search(pattern, response_lower)
        if match:
            agent_name = match.group(1).lower()
            if agent_name in AGENT_NAME_MAP:
                return AGENT_NAME_MAP[agent_name]

    return None


def init_session_state():
    """Initialize Streamlit session state."""
    if "initialized" not in st.session_state:
        try:
            # Load configuration
            config = load_config()
            st.session_state.config = config

            # Validate API key exists
            provider = config.get("llm", {}).get("provider", "anthropic")
            get_api_key(provider)  # Raises if missing

            # Initialize LLM client
            st.session_state.llm_client = create_llm_client(config)
            st.session_state.error = None
            st.session_state.initialized = True

        except FileNotFoundError as e:
            st.session_state.error = f"Configuration error: {e}"
            st.session_state.initialized = False

        except ValueError as e:
            st.session_state.error = f"API Key error: {e}"
            st.session_state.initialized = False

        except Exception as e:
            st.session_state.error = f"Initialization error: {e}"
            st.session_state.initialized = False

    # Initialize chat state
    init_chat_state()

    # Initialize wall state
    init_wall_state()

    # Initialize orchestrator state
    init_orchestrator_state()

    # Show greeting if chat is empty
    show_greeting_if_needed()


def show_greeting_if_needed():
    """Show Nora's greeting if chat is empty."""
    if len(st.session_state.get("messages", [])) == 0:
        agent = get_active_agent()
        # Only Nora greets (she's the coordinator)
        if hasattr(agent, 'get_greeting'):
            greeting = agent.get_greeting()
            add_message(
                role="assistant",
                content=greeting,
                **agent.get_agent_info()
            )


def render_error():
    """Render error message if initialization failed."""
    st.error(f"⚠️ {st.session_state.error}")
    st.markdown("""
    ### Troubleshooting

    1. **Check `config.yaml`** - Ensure it exists and has valid YAML syntax
    2. **Check `.env`** - Ensure API key is set:
       - For Anthropic: `ANTHROPIC_API_KEY=sk-ant-...`
       - For Google: `GOOGLE_API_KEY=AIza...`
    3. **Check provider setting** - `config.yaml` should have `llm.provider` set to `anthropic` or `google`
    """)


async def get_llm_response(user_message: str) -> str:
    """Get response from LLM using active agent's persona.

    Args:
        user_message: User's message

    Returns:
        LLM response text
    """
    llm_client = st.session_state.llm_client
    chat_history = get_chat_history()

    # Get active agent's system prompt
    agent = get_active_agent()
    system_prompt = agent.load_system_prompt()

    response = await llm_client.complete(chat_history, system_prompt)
    return response


async def compile_mandat_from_chat() -> Optional[str]:
    """Use LLM to compile a mandat from the chat history.

    Returns:
        Compiled mandat content or None if extraction fails
    """
    llm_client = st.session_state.llm_client
    chat_history = get_chat_history()

    # Special system prompt for mandat extraction
    extraction_prompt = """Du bist Arthur, der Mandats-Architekt.

Deine Aufgabe: Extrahiere aus dem bisherigen Gespräch ein strukturiertes Mandat.

Formatiere das Mandat EXAKT so:

## Kontext
[Warum jetzt? Was ist der Auslöser?]

## My Intent
[Was soll konkret erreicht werden? Messbar!]

## Higher Intent
[Worauf zahlt das ein? Das größere Ziel?]

## Key Tasks
[Die 2-3 wesentlichen Schritte]

## Boundaries
[Was wird NICHT gemacht? Grenzen?]

---

WICHTIG:
- Extrahiere NUR was im Gespräch besprochen wurde
- Wenn ein Element fehlt, schreibe "[Noch zu klären]"
- Fasse zusammen, erfinde nichts dazu
- Antworte NUR mit dem formatierten Mandat, keine Einleitung"""

    # Add extraction request to history
    extraction_request = [{"role": "user", "content": "Fasse jetzt das Mandat aus unserem Gespräch zusammen."}]
    full_history = chat_history + extraction_request

    try:
        response = await llm_client.complete(full_history, extraction_prompt)
        # Check if we got a valid response with at least some content
        if response and len(response) > 50 and "Kontext" in response:
            return response
        return None
    except Exception:
        return None


def start_new_session():
    """Clear session and start fresh (keeps artifacts on disk)."""
    clear_session()
    st.session_state.messages = []
    # Remove artifacts from session state so they get reloaded from disk
    if "artifacts" in st.session_state:
        del st.session_state["artifacts"]
    st.rerun()


def reset_everything():
    """Clear session AND delete all artifacts."""
    clear_session()
    clear_all_artifacts()
    st.session_state.messages = []
    st.session_state.artifacts = {"mandat": [], "problem": [], "solution": [], "test": []}
    if "confirm_reset" in st.session_state:
        del st.session_state["confirm_reset"]
    st.rerun()


def render_app():
    """Render the main application."""
    llm_client = st.session_state.llm_client
    agent = get_active_agent()

    # Header with session controls
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.title("🧭 Hansel - Product Discovery")
    with header_col2:
        st.write("")  # Spacing
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Neuer Chat", help="Chat leeren"):
                start_new_session()
        with btn_col2:
            if st.button("Reset", type="primary", help="Alles löschen"):
                st.session_state.show_reset_confirm = True

    # Reset confirmation dialog
    if st.session_state.get("show_reset_confirm", False):
        st.warning("⚠️ **Alles löschen?** Dies löscht Chat UND alle Artifacts!")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Ja, löschen", type="primary"):
                st.session_state.show_reset_confirm = False
                reset_everything()
        with col2:
            if st.button("Abbrechen"):
                st.session_state.show_reset_confirm = False
                st.rerun()

    # Agent info bar (above tabs)
    st.markdown(f"### {agent.icon} **{agent.name}** - {agent.role}")
    st.caption(f"Commands: {', '.join(agent.commands)}")

    # Tabs layout: Chat | Wall | Team
    tab_chat, tab_wall, tab_team = st.tabs(["💬 Chat", "🗂️ Wall", "👥 Team"])

    with tab_chat:
        render_chat()

    with tab_wall:
        render_discovery_wall()

    with tab_team:
        render_agent_overview()

    # Chat input (below tabs)
    if user_input := st.chat_input("Schreib eine Nachricht..."):
        # Add user message
        add_message(role="user", content=user_input)

        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)

        # Check if it's a switch command
        target_agent_id = agent.parse_switch_command(user_input)
        if target_agent_id:
            target_agent = get_agent(target_agent_id)
            if target_agent:
                # Switch to target agent
                set_active_agent(target_agent_id)
                # Get greeting from new agent
                greeting = target_agent.get_greeting()
                add_message(
                    role="assistant",
                    content=greeting,
                    **target_agent.get_agent_info()
                )
                st.rerun()
            else:
                # Unknown agent
                error_msg = f"⚠️ Agent '{target_agent_id}' nicht gefunden. Verfügbar: nora, arthur"
                with st.chat_message("assistant", avatar=agent.icon):
                    st.markdown(error_msg)
                    add_message(
                        role="assistant",
                        content=error_msg,
                        **agent.get_agent_info()
                    )
                return

        # Global handler for *speichern (works from any agent)
        if user_input.strip().lower() == "*speichern":
            arthur = get_agent("arthur")
            # Switch to Arthur if not already
            if agent.id != "arthur":
                set_active_agent("arthur")

            # Arthur compiles mandat from chat history via LLM
            with st.chat_message("assistant", avatar=arthur.icon):
                with st.spinner("Arthur kompiliert das Mandat..."):
                    mandat_content = asyncio.run(compile_mandat_from_chat())

                    if mandat_content:
                        # Save the compiled mandat
                        response = arthur.save_mandat_from_content(mandat_content)
                        st.markdown(response)
                        add_message(
                            role="assistant",
                            content=response,
                            **arthur.get_agent_info()
                        )
                        refresh_wall_state()

                        # Switch back to Nora
                        set_active_agent("nora")
                        nora = get_agent("nora")
                        handback_msg = """*Nora nickt Arthur zu.*

Sehr gut! Das Mandat steht. Ich sehe es auf der **Discovery Wall**.

Jetzt hast du eine klare Basis. Was möchtest du als nächstes erkunden?

- **Problem verstehen** → `*wechsel finn`
- **Ideen entwickeln** → `*wechsel ida`
- **Annahmen testen** → `*wechsel theo`

*Tippe `*status` für den Überblick.*"""
                        add_message(
                            role="assistant",
                            content=handback_msg,
                            **nora.get_agent_info()
                        )
                        st.rerun()
                    else:
                        error_msg = """## ⚠️ Mandat nicht vollständig

Ich konnte kein vollständiges Mandat aus unserem Gespräch extrahieren.

Lass uns die 5 Elemente nochmal durchgehen:
1. **Kontext** - Warum jetzt?
2. **My Intent** - Was konkret erreichen?
3. **Higher Intent** - Worauf zahlt das ein?
4. **Key Tasks** - Welche 2-3 Schritte?
5. **Boundaries** - Was nicht?

*Erzähl mir mehr, dann versuchen wir es nochmal.*"""
                        st.markdown(error_msg)
                        add_message(
                            role="assistant",
                            content=error_msg,
                            **arthur.get_agent_info()
                        )
            return

        # Check if it's a regular command
        if agent.is_command(user_input):
            command_response = agent.handle_command(user_input)
            if command_response:
                with st.chat_message("assistant", avatar=agent.icon):
                    st.markdown(command_response)
                    add_message(
                        role="assistant",
                        content=command_response,
                        **agent.get_agent_info()
                    )
                # Refresh wall after command (status might have changed)
                refresh_wall_state()
                return

        # Get LLM response
        with st.chat_message("assistant", avatar=agent.icon):
            with st.spinner(f"{agent.name} denkt nach..."):
                try:
                    response = asyncio.run(get_llm_response(user_input))
                    st.markdown(response)

                    # Add to history with agent info
                    add_message(
                        role="assistant",
                        content=response,
                        **agent.get_agent_info()
                    )

                    # Auto-detect delegation in LLM response
                    delegation_target = detect_delegation(response)
                    if delegation_target and delegation_target != agent.id:
                        target_agent = get_agent(delegation_target)
                        if target_agent:
                            set_active_agent(delegation_target)
                            # Show target agent's greeting
                            greeting = target_agent.get_greeting()
                            add_message(
                                role="assistant",
                                content=greeting,
                                **target_agent.get_agent_info()
                            )
                            st.rerun()

                except Exception as e:
                    error_msg = f"Fehler bei LLM-Anfrage: {e}"
                    st.error(error_msg)
                    add_message(role="assistant", content=error_msg)


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Hansel - Product Discovery",
        page_icon="🧭",
        layout="wide"
    )

    # Initialize session
    init_session_state()

    # Render based on initialization status
    if st.session_state.get("error"):
        render_error()
    elif st.session_state.get("initialized"):
        render_app()
    else:
        st.error("Unknown initialization state")


if __name__ == "__main__":
    main()

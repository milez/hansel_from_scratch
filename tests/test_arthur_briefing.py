"""Tests for Arthur's briefing functionality (Story 3.3)."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.agents.arthur import (
    ArthurAgent,
    BriefingState,
    BriefingElement,
    VAGUE_KEYWORDS,
    FULL_BRIEFING_ORDER,
    QUICK_BRIEFING_ORDER,
    ELEMENT_QUESTIONS,
    ELEMENT_NAMES,
)


class TestBriefingState:
    """Tests for BriefingState dataclass."""

    def test_initial_state(self):
        """Test default initial state."""
        state = BriefingState()
        assert state.active is False
        assert state.mode == "full"
        assert state.current_element is None
        assert state.elements_completed == []
        assert state.collected_answers == {}
        assert state.awaiting_clarification is False

    def test_get_element_order_full(self):
        """Test full briefing order."""
        state = BriefingState(mode="full")
        order = state.get_element_order()
        assert order == FULL_BRIEFING_ORDER
        assert len(order) == 5

    def test_get_element_order_quick(self):
        """Test quick briefing order."""
        state = BriefingState(mode="quick")
        order = state.get_element_order()
        assert order == QUICK_BRIEFING_ORDER
        assert len(order) == 3

    def test_get_next_element_empty(self):
        """Test getting next element with none completed."""
        state = BriefingState(mode="full")
        assert state.get_next_element() == BriefingElement.KONTEXT

    def test_get_next_element_partial(self):
        """Test getting next element after some completed."""
        state = BriefingState(mode="full")
        state.elements_completed = [BriefingElement.KONTEXT, BriefingElement.MY_INTENT]
        assert state.get_next_element() == BriefingElement.HIGHER_INTENT

    def test_get_next_element_all_complete(self):
        """Test getting next element when all complete."""
        state = BriefingState(mode="full")
        state.elements_completed = list(FULL_BRIEFING_ORDER)
        assert state.get_next_element() is None

    def test_is_complete_false(self):
        """Test is_complete when not complete."""
        state = BriefingState(mode="full")
        state.elements_completed = [BriefingElement.KONTEXT]
        assert state.is_complete() is False

    def test_is_complete_true(self):
        """Test is_complete when all elements done."""
        state = BriefingState(mode="full")
        state.elements_completed = list(FULL_BRIEFING_ORDER)
        assert state.is_complete() is True

    def test_is_complete_quick(self):
        """Test is_complete for quick mode."""
        state = BriefingState(mode="quick")
        state.elements_completed = list(QUICK_BRIEFING_ORDER)
        assert state.is_complete() is True

    def test_reset(self):
        """Test reset clears all state."""
        state = BriefingState(
            active=True,
            mode="quick",
            current_element=BriefingElement.KONTEXT,
            elements_completed=[BriefingElement.KONTEXT],
            collected_answers={"kontext": "test"},
            awaiting_clarification=True,
            last_vague_answer="vague"
        )
        state.reset()
        assert state.active is False
        assert state.mode == "full"
        assert state.current_element is None
        assert state.elements_completed == []
        assert state.collected_answers == {}
        assert state.awaiting_clarification is False
        assert state.last_vague_answer is None


class TestArthurAgentBasic:
    """Tests for ArthurAgent basic properties."""

    def test_agent_properties(self):
        """Test Arthur's basic properties."""
        arthur = ArthurAgent()
        assert arthur.id == "arthur"
        assert arthur.name == "Arthur"
        assert arthur.icon == "🎖️"
        assert arthur.role == "Mandats-Architekt & Bungay-Experte"

    def test_commands_list(self):
        """Test Arthur's available commands."""
        arthur = ArthurAgent()
        commands = arthur.commands
        assert "*briefing" in commands
        assert "*schnellcheck" in commands
        assert "*backbriefing" in commands
        assert "*alignment-check" in commands


class TestArthurBriefingStart:
    """Tests for starting briefings (AC1, AC6)."""

    def test_start_full_briefing(self):
        """AC1: Test starting full briefing with *briefing."""
        arthur = ArthurAgent()
        response = arthur.handle_command("*briefing")

        assert "Briefing starten" in response
        assert "5 Elemente" in response
        assert arthur.briefing_state.active is True
        assert arthur.briefing_state.mode == "full"
        assert arthur.briefing_state.current_element == BriefingElement.KONTEXT

    def test_start_schnellcheck(self):
        """AC6: Test starting schnellcheck with *schnellcheck."""
        arthur = ArthurAgent()
        response = arthur.handle_command("*schnellcheck")

        assert "Schnellcheck" in response
        assert "3 kritischsten" in response
        assert arthur.briefing_state.active is True
        assert arthur.briefing_state.mode == "quick"
        assert arthur.briefing_state.current_element == BriefingElement.KONTEXT


class TestArthurVagueDetection:
    """Tests for vague answer detection (AC2)."""

    def test_vague_answer_detected(self):
        """AC2: Test that vague answers are detected."""
        arthur = ArthurAgent()

        # Test vague keywords without concrete indicators
        assert arthur._is_vague_answer("Wir wollen mehr Wachstum", BriefingElement.KONTEXT) is True
        assert arthur._is_vague_answer("Bessere Qualität", BriefingElement.MY_INTENT) is True
        assert arthur._is_vague_answer("Erfolg steigern", BriefingElement.HIGHER_INTENT) is True

    def test_concrete_answer_not_vague(self):
        """Test that concrete answers pass through."""
        arthur = ArthurAgent()

        # Answers with numbers/dates are concrete
        assert arthur._is_vague_answer("Wir wollen 20% mehr Umsatz in Q2", BriefingElement.KONTEXT) is False
        assert arthur._is_vague_answer("3 Enterprise-Kunden haben gefragt", BriefingElement.KONTEXT) is False
        assert arthur._is_vague_answer("Bis Januar 2025 liefern", BriefingElement.MY_INTENT) is False

    def test_long_answer_not_vague(self):
        """Test that long detailed answers pass through even with vague words."""
        arthur = ArthurAgent()

        long_answer = "Wir wollen das System verbessern, weil die aktuelle Performance problematisch ist. " * 3
        assert arthur._is_vague_answer(long_answer, BriefingElement.KONTEXT) is False

    def test_clarification_prompt_generated(self):
        """AC2: Test clarification prompts for vague answers."""
        arthur = ArthurAgent()

        prompt = arthur._get_clarification_prompt("bessere Qualität", BriefingElement.KONTEXT)
        assert "konkret" in prompt.lower() or "messbar" in prompt.lower()


class TestArthurBriefingFlow:
    """Tests for the complete briefing conversation flow (AC1)."""

    def test_full_briefing_flow(self):
        """AC1: Test complete flow through all 5 elements."""
        arthur = ArthurAgent()

        # Start briefing
        arthur.handle_command("*briefing")
        assert arthur.is_briefing_active() is True

        # Answer each element
        answers = [
            "Q2 Revenue-Ziel gefährdet, 3 Enterprise-Kunden fragen",  # Kontext
            "20% höhere Conversion in 6 Wochen",  # My Intent
            "Series A Readiness bis Q4",  # Higher Intent
            "1. User Research, 2. Prototyp, 3. Test",  # Key Tasks
            "Max 2 Devs, kein Backend-Refactor",  # Boundaries
        ]

        for i, answer in enumerate(answers):
            response = arthur.process_briefing_answer(answer)
            if i < 4:  # Not last element
                assert response is not None
                assert "Weiter" in response or "Zusammenfassung" in response
            else:  # Last element shows summary
                assert "Zusammenfassung" in response
                assert "Stimmt das so?" in response

        # Verify all answers collected
        assert len(arthur.briefing_state.collected_answers) == 5

    def test_quick_briefing_flow(self):
        """AC6: Test schnellcheck flow through 3 elements."""
        arthur = ArthurAgent()

        # Start schnellcheck
        arthur.handle_command("*schnellcheck")
        assert arthur.briefing_state.mode == "quick"

        # Answer only 3 elements
        answers = [
            "Q2 Revenue-Ziel gefährdet",  # Kontext
            "Series A Readiness",  # Higher Intent
            "Max 2 Devs",  # Boundaries
        ]

        for i, answer in enumerate(answers):
            response = arthur.process_briefing_answer(answer)
            if i < 2:
                assert "Weiter" in response or "Gut" in response
            else:
                assert "Zusammenfassung" in response

        # Verify only 3 answers collected
        assert len(arthur.briefing_state.collected_answers) == 3

    def test_vague_answer_triggers_clarification(self):
        """AC2: Test that vague answers trigger clarification request."""
        arthur = ArthurAgent()
        arthur.handle_command("*briefing")

        # Give vague answer
        response = arthur.process_briefing_answer("Ist halt wichtig")

        assert "konkret" in response.lower() or "messbar" in response.lower() or "unscharf" in response.lower()
        assert arthur.briefing_state.awaiting_clarification is True
        assert arthur.briefing_state.current_element == BriefingElement.KONTEXT  # Still on same element

    def test_clarification_advances_element(self):
        """Test that providing clarification advances to next element."""
        arthur = ArthurAgent()
        arthur.handle_command("*briefing")

        # Vague answer
        arthur.process_briefing_answer("Ist wichtig")
        assert arthur.briefing_state.awaiting_clarification is True

        # Clarification
        response = arthur.process_briefing_answer("3 Enterprise-Kunden haben gefragt")
        assert arthur.briefing_state.awaiting_clarification is False
        assert BriefingElement.KONTEXT in arthur.briefing_state.elements_completed


class TestArthurAlignmentCheck:
    """Tests for alignment check functionality (AC3)."""

    def test_alignment_check_no_mandat(self):
        """Test alignment check when no mandat exists."""
        arthur = ArthurAgent()

        with patch('src.agents.arthur.load_artifacts', return_value=[]):
            response = arthur.handle_command("*alignment-check")

        assert "kein dokumentiertes Mandat" in response
        assert "❓" in response

    def test_alignment_check_with_mandat(self):
        """Test alignment check when mandat exists."""
        arthur = ArthurAgent()

        mock_artifact = MagicMock()
        mock_artifact.type = MagicMock()
        mock_artifact.type.MANDAT = "mandat"

        # Need to mock the ArtifactType comparison
        with patch('src.agents.arthur.load_artifacts') as mock_load:
            with patch('src.agents.arthur.ArtifactType') as mock_type:
                mock_type.MANDAT = "mandat"
                mock_artifact.type = "mandat"
                mock_load.return_value = [mock_artifact]

                response = arthur.handle_command("*alignment-check")

        # Check for positive indicators
        assert "✅" in response or "Alignment" in response


class TestArthurConfirmation:
    """Tests for mandat confirmation and saving (AC4)."""

    def test_is_awaiting_confirmation(self):
        """Test awaiting confirmation state."""
        arthur = ArthurAgent()

        # Not awaiting initially
        assert arthur.is_awaiting_confirmation() is False

        # Simulate completed briefing
        arthur._briefing_state.active = False
        arthur._briefing_state.collected_answers = {"kontext": "test"}
        assert arthur.is_awaiting_confirmation() is True

    def test_confirmation_responses(self):
        """Test confirmation response detection."""
        arthur = ArthurAgent()

        # Positive confirmations
        assert arthur.is_confirmation_response("ja") is True
        assert arthur.is_confirmation_response("Ja") is True
        assert arthur.is_confirmation_response("yes") is True
        assert arthur.is_confirmation_response("bestätigt") is True
        assert arthur.is_confirmation_response("ok") is True
        assert arthur.is_confirmation_response("passt") is True

        # Negative / other responses
        assert arthur.is_confirmation_response("nein") is False
        assert arthur.is_confirmation_response("das stimmt nicht") is False
        assert arthur.is_confirmation_response("ändern") is False

    def test_confirm_mandat_saves_artifact(self):
        """AC4: Test that confirming saves artifact to Discovery Wall."""
        arthur = ArthurAgent()

        # Setup completed briefing state
        arthur._briefing_state.mode = "full"
        arthur._briefing_state.collected_answers = {
            "kontext": "Test kontext",
            "my_intent": "Test intent",
            "higher_intent": "Test higher",
            "key_tasks": "Test tasks",
            "boundaries": "Test boundaries",
        }

        with patch('src.agents.arthur.save_artifact') as mock_save:
            response, should_handback = arthur.confirm_mandat("Test Projekt")

            # Verify save was called
            mock_save.assert_called_once()
            saved_artifact = mock_save.call_args[0][0]

            assert saved_artifact.type.value == "mandat"
            assert saved_artifact.created_by == "arthur"
            assert "Test Projekt" in saved_artifact.title

        # Verify response
        assert "gespeichert" in response
        assert should_handback is True

        # Verify state reset
        assert arthur._briefing_state.active is False
        assert arthur._briefing_state.collected_answers == {}


class TestArthurHandback:
    """Tests for handback to Nora (AC5)."""

    def test_confirm_returns_handback_flag(self):
        """AC5: Test that confirmation returns handback flag."""
        arthur = ArthurAgent()
        arthur._briefing_state.collected_answers = {"kontext": "test"}

        with patch('src.agents.arthur.save_artifact'):
            response, should_handback = arthur.confirm_mandat()

        assert should_handback is True
        assert "Nora" in response


class TestArthurIntegration:
    """Integration tests for complete flows."""

    def test_complete_briefing_to_save_flow(self):
        """Test complete flow from briefing start to save."""
        arthur = ArthurAgent()

        # Start
        arthur.handle_command("*briefing")

        # Answer all elements with concrete answers
        concrete_answers = [
            "3 Kunden haben Feature X angefragt letzte Woche",
            "20% mehr Umsatz in Q2 2025",
            "Series A mit 5M Bewertung",
            "1. Discovery, 2. Design, 3. MVP bauen",
            "Kein iOS, nur Web. Max 50k Budget.",
        ]

        for answer in concrete_answers:
            arthur.process_briefing_answer(answer)

        # Should now be awaiting confirmation
        assert arthur.is_awaiting_confirmation() is True

        # Confirm
        with patch('src.agents.arthur.save_artifact') as mock_save:
            response, handback = arthur.confirm_mandat("Feature X")
            mock_save.assert_called_once()

        assert handback is True
        assert arthur.is_awaiting_confirmation() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

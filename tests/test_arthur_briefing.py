"""Tests for Arthur agent (Story 3.3 - LLM-based coaching)."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.agents.arthur import ArthurAgent
from src.discovery.models import ArtifactType, ArtifactStatus


class TestArthurAgentProperties:
    """Tests for ArthurAgent basic properties."""

    def test_agent_id(self):
        """Test Arthur's ID."""
        arthur = ArthurAgent()
        assert arthur.id == "arthur"

    def test_agent_name(self):
        """Test Arthur's name."""
        arthur = ArthurAgent()
        assert arthur.name == "Arthur"

    def test_agent_icon(self):
        """Test Arthur's icon."""
        arthur = ArthurAgent()
        assert arthur.icon == "🎖️"

    def test_agent_role(self):
        """Test Arthur's role."""
        arthur = ArthurAgent()
        assert arthur.role == "Mandats-Architekt & Bungay-Experte"

    def test_commands_list(self):
        """Test Arthur's available commands."""
        arthur = ArthurAgent()
        commands = arthur.commands
        assert "*briefing" in commands
        assert "*schnellcheck" in commands
        assert "*backbriefing" in commands
        assert "*alignment-check" in commands
        assert "*speichern" in commands


class TestArthurGreeting:
    """Tests for Arthur's greeting."""

    def test_greeting_content(self):
        """Test that greeting introduces Arthur."""
        arthur = ArthurAgent()
        greeting = arthur.get_greeting()

        assert "Arthur" in greeting
        assert "mandat" in greeting.lower()

    def test_greeting_mentions_speichern(self):
        """Test that greeting mentions *speichern command."""
        arthur = ArthurAgent()
        greeting = arthur.get_greeting()

        assert "*speichern" in greeting


class TestArthurCommands:
    """Tests for Arthur's command handling."""

    def test_briefing_command(self):
        """Test *briefing command."""
        arthur = ArthurAgent()
        response = arthur.handle_command("*briefing")

        assert response is not None
        assert "Briefing" in response
        assert "5 Elemente" in response

    def test_backbriefing_command(self):
        """Test *backbriefing command."""
        arthur = ArthurAgent()
        response = arthur.handle_command("*backbriefing")

        assert response is not None
        assert "Backbriefing" in response
        assert "eigenen Worten" in response

    def test_speichern_command(self):
        """Test *speichern command."""
        arthur = ArthurAgent()
        response = arthur.handle_command("*speichern")

        assert response is not None
        assert "speichern" in response.lower()
        assert "Kontext" in response

    def test_unknown_command(self):
        """Test that unknown commands return None."""
        arthur = ArthurAgent()
        response = arthur.handle_command("*unknown")

        assert response is None


class TestArthurSchnellcheck:
    """Tests for Schnellcheck functionality (Story 3-3b)."""

    def test_schnellcheck_command(self):
        """AC1: Test *schnellcheck command starts quick dialogue."""
        arthur = ArthurAgent()
        response = arthur.handle_command("*schnellcheck")

        assert response is not None
        assert "Schnellcheck" in response
        assert "3 kritischsten" in response

    def test_schnellcheck_mentions_three_elements(self):
        """AC1: Test schnellcheck mentions only 3 elements."""
        arthur = ArthurAgent()
        response = arthur.handle_command("*schnellcheck")

        assert "Kontext" in response
        assert "Higher Intent" in response
        assert "Boundaries" in response
        # Should NOT mention My Intent and Key Tasks in quick mode
        assert "My Intent" not in response
        assert "Key Tasks" not in response

    def test_schnellcheck_mentions_speichern(self):
        """AC2: Test schnellcheck mentions *speichern for saving."""
        arthur = ArthurAgent()
        response = arthur.handle_command("*schnellcheck")

        assert "*speichern" in response

    def test_save_quick_mandat_with_prefix(self):
        """AC3: Test saving quick mandat with QUICK: prefix."""
        arthur = ArthurAgent()

        quick_content = "QUICK: Kontext: Deadline naht. Higher Intent: MVP launchen. Boundaries: Nur Web."

        with patch('src.agents.arthur.save_artifact') as mock_save:
            response = arthur.save_mandat_from_content(quick_content, "Test Projekt")

            mock_save.assert_called_once()
            saved_artifact = mock_save.call_args[0][0]

            # Verify QUICK flag in title
            assert "Quick" in saved_artifact.title or "⚡" in saved_artifact.title
            # Verify SCHNELLCHECK marker in content
            assert "SCHNELLCHECK" in saved_artifact.content

        # Verify response mentions quick
        assert "Quick" in response or "⚡" in response

    def test_save_quick_mandat_lowercase_prefix(self):
        """AC3: Test QUICK prefix is case-insensitive."""
        arthur = ArthurAgent()

        quick_content = "quick: Test content"

        with patch('src.agents.arthur.save_artifact') as mock_save:
            response = arthur.save_mandat_from_content(quick_content)

            saved_artifact = mock_save.call_args[0][0]
            assert "Quick" in saved_artifact.title or "⚡" in saved_artifact.title

    def test_regular_mandat_no_quick_flag(self):
        """Test that regular mandat without QUICK: prefix has no quick marker."""
        arthur = ArthurAgent()

        regular_content = "Kontext: Normal. Ziel: Normal."

        with patch('src.agents.arthur.save_artifact') as mock_save:
            response = arthur.save_mandat_from_content(regular_content)

            saved_artifact = mock_save.call_args[0][0]
            assert "Quick" not in saved_artifact.title
            assert "SCHNELLCHECK" not in saved_artifact.content

    def test_speichern_prompt_mentions_quick(self):
        """Test that *speichern prompt mentions QUICK: option."""
        arthur = ArthurAgent()
        response = arthur.handle_command("*speichern")

        assert "QUICK:" in response


class TestArthurAlignmentCheck:
    """Tests for alignment check functionality."""

    def test_alignment_check_no_mandat(self):
        """Test alignment check when no mandat exists."""
        arthur = ArthurAgent()

        with patch('src.discovery.artifacts.load_artifacts', return_value=[]):
            response = arthur.handle_command("*alignment-check")

        assert "kein dokumentiertes Mandat" in response

    def test_alignment_check_with_mandat(self):
        """Test alignment check when mandat exists."""
        arthur = ArthurAgent()

        mock_artifact = MagicMock()
        mock_artifact.type = ArtifactType.MANDAT

        with patch('src.discovery.artifacts.load_artifacts', return_value=[mock_artifact]):
            response = arthur.handle_command("*alignment-check")

        assert "✅" in response
        assert "Mandat" in response


class TestArthurSaveMandat:
    """Tests for mandat saving functionality."""

    def test_save_mandat_from_content(self):
        """Test saving mandat from provided content."""
        arthur = ArthurAgent()

        mandat_content = """
        Kontext: PMs machen schlechte Discovery
        Ziel: 10 User in 2 Monaten
        Higher Intent: Startup aufbauen
        Key Tasks: Nutzertests durchführen
        Boundaries: 2 Monate Zeit
        """

        with patch('src.agents.arthur.save_artifact') as mock_save:
            response = arthur.save_mandat_from_content(mandat_content, "Discovery Coach")

            # Verify save was called
            mock_save.assert_called_once()
            saved_artifact = mock_save.call_args[0][0]

            assert saved_artifact.type == ArtifactType.MANDAT
            assert saved_artifact.created_by == "arthur"
            assert "Discovery Coach" in saved_artifact.title
            assert saved_artifact.status == ArtifactStatus.COMPLETE

        # Verify response
        assert "gespeichert" in response
        assert "Discovery Wall" in response

    def test_save_mandat_default_project_name(self):
        """Test saving with default project name."""
        arthur = ArthurAgent()

        with patch('src.agents.arthur.save_artifact') as mock_save:
            arthur.save_mandat_from_content("Test content")

            saved_artifact = mock_save.call_args[0][0]
            assert "Mein Projekt" in saved_artifact.title


class TestArthurIntegration:
    """Integration tests."""

    def test_full_command_cycle(self):
        """Test that all commands work without errors."""
        arthur = ArthurAgent()

        # All commands should return strings
        greeting = arthur.get_greeting()
        assert isinstance(greeting, str)

        briefing = arthur.handle_command("*briefing")
        assert isinstance(briefing, str)

        schnellcheck = arthur.handle_command("*schnellcheck")
        assert isinstance(schnellcheck, str)

        backbriefing = arthur.handle_command("*backbriefing")
        assert isinstance(backbriefing, str)

        speichern = arthur.handle_command("*speichern")
        assert isinstance(speichern, str)

        with patch('src.discovery.artifacts.load_artifacts', return_value=[]):
            alignment = arthur.handle_command("*alignment-check")
            assert isinstance(alignment, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

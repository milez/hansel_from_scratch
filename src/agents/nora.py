"""Nora - Die Navigatorin agent for Hansel."""

from typing import List, Optional

from src.agents.base import BaseAgent
from src.discovery.artifacts import get_artifact_counts, load_artifacts
from src.discovery.models import ArtifactType


class NoraAgent(BaseAgent):
    """Nora - Die Navigatorin.

    Central coordinator of the Discovery team. She stands at the "Squash Point"
    and keeps track of all four fields of Product Discovery.
    """

    @property
    def id(self) -> str:
        return "nora"

    @property
    def name(self) -> str:
        return "Nora"

    @property
    def icon(self) -> str:
        return "🔭"

    @property
    def role(self) -> str:
        return "Navigatorin & Squash-Point-Masterin"

    @property
    def commands(self) -> List[str]:
        return ["*status", "*check", "*agent", "*mandat"]

    def _get_mandat_content(self) -> Optional[str]:
        """Load the current mandat content from disk.

        Used for *mandat command. Context loading for system prompt
        is handled by BaseAgent via AgentContextLoader.

        Returns:
            Mandat content string or None if no mandat exists
        """
        artifacts = load_artifacts()
        for artifact in artifacts:
            if artifact.type == ArtifactType.MANDAT:
                return f"**{artifact.title}**\n\n{artifact.content}"
        return None

    def handle_command(self, command: str) -> Optional[str]:
        """Handle Nora's commands.

        Args:
            command: The command string

        Returns:
            Response string if command handled
        """
        cmd = command.strip().lower()

        if cmd == "*status":
            return self._generate_status()
        elif cmd == "*check":
            return self._generate_check()
        elif cmd == "*agent":
            return self._suggest_agent()
        elif cmd == "*mandat":
            return self._show_mandat()

        return None

    def _show_mandat(self) -> str:
        """Show current mandat content."""
        mandat = self._get_mandat_content()
        if mandat:
            return f"## 🎖️ Aktuelles Mandat\n\n{mandat}"
        else:
            return "## 🎖️ Mandat\n\n*Noch kein Mandat vorhanden. Sprich mit Arthur um eines zu erstellen.*"

    def _generate_status(self) -> str:
        """Generate discovery status report."""
        counts = get_artifact_counts()

        status_parts = [
            "## 📊 Discovery Status\n",
            f"🎖️ **Mandat:** {counts['mandat']} Artefakt(e)",
            f"🔍 **Problem:** {counts['problem']} Artefakt(e)",
            f"💡 **Lösung:** {counts['solution']} Artefakt(e)",
            f"🧪 **Test:** {counts['test']} Artefakt(e)",
            ""
        ]

        total = sum(counts.values())
        if total == 0:
            status_parts.append("*Noch keine Artefakte. Lass uns mit dem Mandat beginnen!*")
        elif counts['mandat'] == 0:
            status_parts.append("⚠️ *Kein Mandat vorhanden. Wir sollten zuerst mit Arthur sprechen.*")
        else:
            status_parts.append("✅ *Mandat vorhanden. Wir können explorieren!*")

        return "\n".join(status_parts)

    def _generate_check(self) -> str:
        """Generate squash point reflection."""
        return """## 🔄 Squash-Punkt Reflexion

**Was haben wir gelernt?**
- Welche neuen Erkenntnisse haben wir gewonnen?
- Was wissen wir jetzt, was wir vorher nicht wussten?

**Wissen wir genug für den nächsten Schritt?**
- Haben wir validierte Fakten oder nur Annahmen?
- Passt unser Vorgehen noch zum Mandat?

*Erzähl mir, was du gelernt hast, dann entscheiden wir gemeinsam den nächsten Schritt.*"""

    def _suggest_agent(self) -> str:
        """Suggest next agent based on current state."""
        counts = get_artifact_counts()

        if counts['mandat'] == 0:
            return """## 👤 Nächster Agent: Arthur

Das Mandat fehlt noch! Ich empfehle, zuerst mit **Arthur** 🎖️ zu sprechen.
Er hilft dir, ein klares Mandat zu formulieren - das ist die Grundlage für alles weitere.

*Tippe `*wechsel arthur` um zu ihm zu wechseln.*"""

        elif counts['problem'] == 0:
            return """## 👤 Nächster Agent: Finn

Das Mandat steht! Jetzt sollten wir das **Problem** besser verstehen.
**Finn** 🔍 hilft dir bei der Bedarfsanalyse und Nutzerforschung.

*Finn ist noch nicht implementiert. Bleib bei mir oder geh zurück zu Arthur.*"""

        elif counts['solution'] == 0:
            return """## 👤 Nächster Agent: Ida

Wir haben Insights! Zeit für **Lösungsideen**.
**Ida** 💡 hilft dir mit How-Might-We Fragen und Brainstorming.

*Ida ist noch nicht implementiert. Bleib bei mir oder geh zurück zu Arthur.*"""

        else:
            return """## 👤 Nächster Agent: Theo

Wir haben Ideen! Zeit zum **Testen**.
**Theo** 🧪 hilft dir, Annahmen zu validieren mit Test Cards.

*Theo ist noch nicht implementiert. Bleib bei mir oder geh zurück zu Arthur.*"""

    def get_greeting(self) -> str:
        """Generate greeting message for new users.

        Returns:
            Greeting message with context-aware hints
        """
        counts = get_artifact_counts()

        greeting_parts = [
            f"Hallo! Ich bin **{self.name}** {self.icon}, deine Navigatorin.",
            "",
            "Ich stehe am Squash-Punkt in der Mitte unseres Discovery-Modells und behalte den Überblick über alle vier Felder:",
            "- 🎖️ **Mandat** - Was ist unser Auftrag?",
            "- 🔍 **Problem** - Was ist der Bedarf?",
            "- 💡 **Lösung** - Welche Ideen haben wir?",
            "- 🧪 **Test** - Was haben wir validiert?",
            ""
        ]

        # Add context-aware hint
        if counts['mandat'] == 0:
            greeting_parts.extend([
                "Ich sehe, wir haben noch kein **Mandat**. Das ist der wichtigste erste Schritt!",
                "",
                "Sag mir: *Was führt dich her?* Oder tippe `*status` für eine Übersicht.",
                "",
                "💡 *Tipp: Sobald du mir dein Vorhaben erzählst, kann ich dich zu **Arthur** weiterleiten - er hilft dir beim Mandat.*"
            ])
        else:
            greeting_parts.extend([
                f"Schön, dass du wieder da bist! Wir haben bereits {sum(counts.values())} Artefakt(e).",
                "",
                "Tippe `*status` für eine Übersicht oder erzähl mir, wo du weitermachen möchtest."
            ])

        return "\n".join(greeting_parts)

"""Arthur - Der Mandats-Architekt agent for Hansel."""

from typing import List, Optional

from src.agents.base import BaseAgent
from src.discovery.artifacts import load_artifacts
from src.discovery.models import ArtifactType


class ArthurAgent(BaseAgent):
    """Arthur - Der Mandats-Architekt.

    Strategic mentor and clarification instance based on Stephen Bungay's
    "Art of Action". He ensures the team starts with clear, shared understanding.
    """

    @property
    def id(self) -> str:
        return "arthur"

    @property
    def name(self) -> str:
        return "Arthur"

    @property
    def icon(self) -> str:
        return "🎖️"

    @property
    def role(self) -> str:
        return "Mandats-Architekt & Bungay-Experte"

    @property
    def commands(self) -> List[str]:
        return ["*briefing", "*backbriefing", "*alignment-check"]

    def handle_command(self, command: str) -> Optional[str]:
        """Handle Arthur's commands.

        Args:
            command: The command string

        Returns:
            Response string if command handled
        """
        cmd = command.strip().lower()

        if cmd == "*briefing":
            return self._start_briefing()
        elif cmd == "*backbriefing":
            return self._request_backbriefing()
        elif cmd == "*alignment-check":
            return self._check_alignment()

        return None

    def _start_briefing(self) -> str:
        """Start the structured briefing dialogue."""
        return """## 🎖️ Briefing starten

*Arthur lehnt sich vor, Notizblock bereit.*

Gut. Lass uns das Mandat klären. Ich werde dich durch die **5 Elemente** führen:

### 1. Kontext
Warum machen wir das **gerade jetzt**? Was ist passiert, das dieses Vorhaben ausgelöst hat?

*Erzähl mir den Kontext. Ich höre zu.*"""

    def _request_backbriefing(self) -> str:
        """Request backbriefing from user."""
        return """## 🔄 Backbriefing

*Arthur schiebt den Notizblock zur Seite.*

Jetzt **du**. Ich will hören, wie du das Mandat verstanden hast.

Formuliere in **deinen eigenen Worten**:

1. **Was** ist das Ziel?
2. **Warum** ist es wichtig?
3. **Woran** erkennen wir Erfolg?
4. **Was** sind die Grenzen?

*Ich werde aufmerksam zuhören und Unklarheiten aufdecken.*"""

    def _check_alignment(self) -> str:
        """Check if all 5 elements are clarified."""
        # Check if we have a mandat
        artifacts = load_artifacts()
        has_mandat = any(a.type == ArtifactType.MANDAT for a in artifacts)

        if has_mandat:
            return """## ✅ Alignment-Check

*Arthur nickt langsam.*

Wir haben ein dokumentiertes Mandat. Lass mich prüfen:

| Element | Status |
|---------|--------|
| **Kontext** | ✅ Dokumentiert |
| **My Intent** | ✅ Klar formuliert |
| **Higher Intent** | ✅ Übergeordnetes Ziel definiert |
| **Key Tasks** | ✅ Wesentliche Aufgaben bekannt |
| **Boundaries** | ✅ Grenzen gesetzt |

**Das Mandat steht.** Du kannst jetzt mit dem Team explorieren.

*Tippe `*status` bei Nora für den nächsten Schritt.*"""

        else:
            return """## ⚠️ Alignment-Check

*Arthur hebt eine Augenbraue.*

Wir haben **kein dokumentiertes Mandat**. Lass uns prüfen, was fehlt:

| Element | Status |
|---------|--------|
| **Kontext** | ❓ Unklar |
| **My Intent** | ❓ Noch nicht formuliert |
| **Higher Intent** | ❓ Übergeordnetes Ziel fehlt |
| **Key Tasks** | ❓ Aufgaben nicht definiert |
| **Boundaries** | ❓ Grenzen nicht gesetzt |

**Ohne klares Mandat kein klares Handeln.**

Tippe `*briefing` um den strukturierten Dialog zu starten."""

    def get_greeting(self) -> str:
        """Generate greeting when Arthur is activated.

        Returns:
            Arthur's characteristic greeting
        """
        return """*Arthur lehnt sich zurück, die Arme verschränkt.*

Ich bin **Arthur** 🎖️. Wir fangen erst an, wenn wir uns wirklich verstehen.

Strategie ist nicht das, was im Plan steht - sondern das, was **getan** wird. Und ohne klares Mandat wird zufällig gehandelt.

Lass uns das **Briefing** starten. Meine erste Frage:

> **Warum machen wir das gerade jetzt?** Was ist der Kontext?

*Ich höre zu.*"""

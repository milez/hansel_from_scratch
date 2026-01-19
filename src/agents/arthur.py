"""Arthur - Der Mandats-Architekt agent for Hansel.

Arthur is a coaching agent that helps users clarify their mandate using
the Bungay Briefing method. He uses his book knowledge to guide the
conversation naturally, not with a rigid form.
"""

from datetime import datetime
from typing import List, Optional

from src.agents.base import BaseAgent
from src.discovery.artifacts import save_artifact
from src.discovery.models import Artifact, ArtifactType, ArtifactStatus


class ArthurAgent(BaseAgent):
    """Arthur - Der Mandats-Architekt.

    Strategic mentor and clarification instance based on Stephen Bungay's
    "Art of Action". He helps users formulate a clear mandate through
    natural coaching conversation, not rigid forms.
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
        return ["*briefing", "*schnellcheck", "*backbriefing", "*alignment-check", "*speichern"]

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
        elif cmd == "*schnellcheck":
            return self._start_schnellcheck()
        elif cmd == "*backbriefing":
            return self._request_backbriefing()
        elif cmd == "*alignment-check":
            return self._check_alignment()
        elif cmd == "*speichern":
            return self._save_mandat_prompt()

        return None

    def _start_briefing(self) -> str:
        """Start the structured briefing dialogue."""
        return """## 🎖️ Briefing starten

*Arthur lehnt sich vor, Notizblock bereit.*

Gut. Lass uns das Mandat klären. Ich werde dir helfen, die **5 Elemente** zu formulieren:

1. **Kontext** - Warum jetzt? Was ist der Auslöser?
2. **My Intent** - Was willst du konkret erreichen?
3. **Higher Intent** - Worauf zahlt das ein?
4. **Key Tasks** - Was sind die wesentlichen Schritte?
5. **Boundaries** - Was machen wir NICHT?

---

**Erzähl mir:** Was führt dich her? Was möchtest du erreichen?

*Ich werde dir helfen, das zu strukturieren und konkret zu machen.*"""

    def _start_schnellcheck(self) -> str:
        """Start the quick 3-element check dialogue."""
        return """## ⚡ Schnellcheck starten

*Arthur schaut auf die Uhr, dann zu dir.*

Wenig Zeit? Kein Problem. Lass uns die **3 kritischsten Elemente** klären:

1. **Kontext** - Warum jetzt? Was ist der Auslöser?
2. **Higher Intent** - Worauf zahlt das ein? Das größere Bild?
3. **Boundaries** - Was machen wir NICHT? Grenzen?

---

**Los geht's:** Erzähl mir kurz - warum jetzt, was ist das große Ziel, und wo sind die Grenzen?

*5 Minuten. Fokussiert. Dann `*speichern` mit "QUICK:" am Anfang.*"""

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
        """Check if we have a saved mandat."""
        from src.discovery.artifacts import load_artifacts

        artifacts = load_artifacts()
        has_mandat = any(a.type == ArtifactType.MANDAT for a in artifacts)

        if has_mandat:
            return """## ✅ Alignment-Check

*Arthur nickt langsam.*

Wir haben ein dokumentiertes Mandat auf der Discovery Wall.

**Das Mandat steht.** Du kannst jetzt mit dem Team explorieren.

*Tippe `*status` bei Nora für den nächsten Schritt.*"""

        else:
            return """## ⚠️ Alignment-Check

*Arthur hebt eine Augenbraue.*

Wir haben **kein dokumentiertes Mandat** auf der Discovery Wall.

**Ohne klares Mandat kein klares Handeln.**

Erzähl mir von deinem Vorhaben - ich helfe dir, ein klares Mandat zu formulieren.

Wenn wir alle 5 Elemente geklärt haben, tippe `*speichern`."""

    def _save_mandat_prompt(self) -> str:
        """Prompt user to provide the mandat summary for saving."""
        return """## 💾 Mandat speichern

*Arthur nimmt den Stift.*

Um das Mandat zu speichern, fasse es bitte kurz zusammen. Ich brauche:

**Kontext:** Warum jetzt?
**Ziel:** Was willst du erreichen?
**Higher Intent:** Worauf zahlt das ein?
**Key Tasks:** Die 2-3 wesentlichen Schritte?
**Boundaries:** Was machen wir NICHT?

---

Schreib das zusammen in einer Nachricht - ich speichere es dann auf der Discovery Wall.

💡 *Tipp: Für ein Quick-Mandat (nach `*schnellcheck`) starte mit `QUICK:` am Anfang.*

*Oder tippe `*briefing` wenn wir das noch klären müssen.*"""

    def save_mandat_from_content(self, content: str, project_name: str = "Mein Projekt") -> str:
        """Save a mandat from provided content.

        Detects QUICK: prefix for schnellcheck mandats.

        Args:
            content: The mandat content to save (prefix with "QUICK:" for schnellcheck)
            project_name: Name for the project/mandat

        Returns:
            Confirmation message
        """
        # Check for QUICK prefix
        is_quick = content.strip().upper().startswith("QUICK:")
        if is_quick:
            content = content.strip()[6:].strip()  # Remove "QUICK:" prefix
            title = f"⚡ Quick-Mandat: {project_name}"
            mandat_content = f"## ⚡ SCHNELLCHECK-MANDAT\n\n*Kompakte Version - nur kritische Elemente*\n\n---\n\n{content}"
        else:
            title = f"Mandat: {project_name}"
            mandat_content = content

        # Create artifact
        artifact = Artifact(
            id="mandat",
            type=ArtifactType.MANDAT,
            title=title,
            content=mandat_content,
            status=ArtifactStatus.COMPLETE,
            created_by="arthur",
            created_at=datetime.now(),
        )

        # Save to Discovery Wall
        save_artifact(artifact)

        if is_quick:
            return """## ⚡ Quick-Mandat gespeichert

*Arthur nickt knapp.*

Schnellcheck abgeschlossen. Quick-Mandat ist auf der **Discovery Wall**.

⚠️ *Für ein vollständiges Mandat später `*briefing` nutzen.*

---

**Nächster Schritt:** Nora übernimmt.

*Schnell, aber solide. Weiter geht's.*"""
        else:
            return """## ✅ Mandat gespeichert

*Arthur lächelt zufrieden.*

Das Mandat steht. Es wurde auf der **Discovery Wall** gespeichert.

---

**Nächster Schritt:** Nora übernimmt und zeigt dir den Weg.

*Die Basis ist gelegt. Jetzt geht die echte Arbeit los.*"""

    def get_greeting(self) -> str:
        """Generate greeting when Arthur is activated.

        Returns:
            Arthur's characteristic greeting
        """
        return """*Arthur lehnt sich zurück, die Arme verschränkt.*

Ich bin **Arthur** 🎖️. Wir fangen erst an, wenn wir uns wirklich verstehen.

Strategie ist nicht das, was im Plan steht - sondern das, was **getan** wird. Und ohne klares Mandat wird zufällig gehandelt.

---

**Erzähl mir:** Was führt dich her? Was möchtest du erreichen?

Ich werde dir helfen, daraus ein klares Mandat zu formulieren. Wenn wir fertig sind, tippe `*speichern`.

*Ich höre zu.*"""

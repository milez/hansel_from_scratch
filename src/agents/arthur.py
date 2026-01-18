"""Arthur - Der Mandats-Architekt agent for Hansel."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from src.agents.base import BaseAgent
from src.discovery.artifacts import load_artifacts, save_artifact
from src.discovery.models import Artifact, ArtifactType, ArtifactStatus


class BriefingElement(str, Enum):
    """The 5 elements of a Bungay Briefing."""
    KONTEXT = "kontext"
    MY_INTENT = "my_intent"
    HIGHER_INTENT = "higher_intent"
    KEY_TASKS = "key_tasks"
    BOUNDARIES = "boundaries"


# Order of elements in full briefing
FULL_BRIEFING_ORDER = [
    BriefingElement.KONTEXT,
    BriefingElement.MY_INTENT,
    BriefingElement.HIGHER_INTENT,
    BriefingElement.KEY_TASKS,
    BriefingElement.BOUNDARIES,
]

# Order for quick check (only critical 3)
QUICK_BRIEFING_ORDER = [
    BriefingElement.KONTEXT,
    BriefingElement.HIGHER_INTENT,
    BriefingElement.BOUNDARIES,
]

# Questions for each element
ELEMENT_QUESTIONS: Dict[BriefingElement, str] = {
    BriefingElement.KONTEXT: "Warum machen wir das **gerade jetzt**? Was ist passiert, das dieses Vorhaben ausgelöst hat?",
    BriefingElement.MY_INTENT: "Was willst **du** erreichen? Was ist dein konkretes Ziel?",
    BriefingElement.HIGHER_INTENT: "Was ist das **übergeordnete Ziel**? Worauf zahlt das ein?",
    BriefingElement.KEY_TASKS: "Was sind die **wesentlichen Aufgaben**? Was muss konkret getan werden?",
    BriefingElement.BOUNDARIES: "Was sind die **Grenzen**? Was ist explizit nicht Teil des Vorhabens?",
}

# Element display names
ELEMENT_NAMES: Dict[BriefingElement, str] = {
    BriefingElement.KONTEXT: "Kontext",
    BriefingElement.MY_INTENT: "My Intent",
    BriefingElement.HIGHER_INTENT: "Higher Intent",
    BriefingElement.KEY_TASKS: "Key Tasks",
    BriefingElement.BOUNDARIES: "Boundaries",
}

# Keywords that indicate vague answers (need clarification)
VAGUE_KEYWORDS = [
    "besser", "mehr", "gut", "schneller", "einfacher",
    "qualität", "erfolg", "wachstum", "optimieren",
    "verbessern", "steigern", "wichtig", "relevant",
]


@dataclass
class BriefingState:
    """State machine for briefing conversation flow."""
    active: bool = False
    mode: str = "full"  # "full" or "quick"
    current_element: Optional[BriefingElement] = None
    elements_completed: List[BriefingElement] = field(default_factory=list)
    collected_answers: Dict[str, str] = field(default_factory=dict)
    awaiting_clarification: bool = False
    last_vague_answer: Optional[str] = None

    def get_element_order(self) -> List[BriefingElement]:
        """Get the order of elements based on mode."""
        return QUICK_BRIEFING_ORDER if self.mode == "quick" else FULL_BRIEFING_ORDER

    def get_next_element(self) -> Optional[BriefingElement]:
        """Get the next element to ask about."""
        order = self.get_element_order()
        for element in order:
            if element not in self.elements_completed:
                return element
        return None

    def is_complete(self) -> bool:
        """Check if all required elements are completed."""
        order = self.get_element_order()
        return all(e in self.elements_completed for e in order)

    def reset(self):
        """Reset the briefing state."""
        self.active = False
        self.mode = "full"
        self.current_element = None
        self.elements_completed = []
        self.collected_answers = {}
        self.awaiting_clarification = False
        self.last_vague_answer = None


class ArthurAgent(BaseAgent):
    """Arthur - Der Mandats-Architekt.

    Strategic mentor and clarification instance based on Stephen Bungay's
    "Art of Action". He ensures the team starts with clear, shared understanding.
    """

    def __init__(self):
        super().__init__()
        self._briefing_state = BriefingState()

    @property
    def briefing_state(self) -> BriefingState:
        """Get the current briefing state."""
        return self._briefing_state

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
        return ["*briefing", "*schnellcheck", "*backbriefing", "*alignment-check"]

    def handle_command(self, command: str) -> Optional[str]:
        """Handle Arthur's commands.

        Args:
            command: The command string

        Returns:
            Response string if command handled
        """
        cmd = command.strip().lower()

        if cmd == "*briefing":
            return self._start_briefing(mode="full")
        elif cmd == "*schnellcheck":
            return self._start_briefing(mode="quick")
        elif cmd == "*backbriefing":
            return self._request_backbriefing()
        elif cmd == "*alignment-check":
            return self._check_alignment()

        return None

    def _start_briefing(self, mode: str = "full") -> str:
        """Start the structured briefing dialogue.

        Args:
            mode: "full" for all 5 elements, "quick" for 3 critical elements
        """
        self._briefing_state.reset()
        self._briefing_state.active = True
        self._briefing_state.mode = mode
        self._briefing_state.current_element = self._briefing_state.get_next_element()

        if mode == "quick":
            return self._format_schnellcheck_start()
        else:
            return self._format_full_briefing_start()

    def _format_full_briefing_start(self) -> str:
        """Format the full briefing start message."""
        return """## 🎖️ Briefing starten

*Arthur lehnt sich vor, Notizblock bereit.*

Gut. Lass uns das Mandat klären. Ich werde dich durch die **5 Elemente** führen:

1. **Kontext** - Warum jetzt?
2. **My Intent** - Was willst du erreichen?
3. **Higher Intent** - Übergeordnetes Ziel?
4. **Key Tasks** - Wesentliche Aufgaben?
5. **Boundaries** - Grenzen?

---

### 1. Kontext

Warum machen wir das **gerade jetzt**? Was ist passiert, das dieses Vorhaben ausgelöst hat?

*Erzähl mir den Kontext. Ich höre zu.*"""

    def _format_schnellcheck_start(self) -> str:
        """Format the schnellcheck start message."""
        return """## ⚡ Schnellcheck starten

*Arthur schaut auf die Uhr, dann zu dir.*

Wenig Zeit? Kein Problem. Lass uns die **3 kritischsten Elemente** klären:

1. **Kontext** - Warum jetzt?
2. **Higher Intent** - Übergeordnetes Ziel?
3. **Boundaries** - Grenzen?

---

### 1. Kontext

Warum machen wir das **gerade jetzt**?

*Kurz und knackig.*"""

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

    def is_briefing_active(self) -> bool:
        """Check if a briefing is currently in progress."""
        return self._briefing_state.active

    def process_briefing_answer(self, answer: str) -> Optional[str]:
        """Process a user's answer during an active briefing.

        Args:
            answer: The user's answer to the current briefing question

        Returns:
            Response string (next question, clarification request, or summary)
            None if no briefing is active
        """
        if not self._briefing_state.active:
            return None

        current = self._briefing_state.current_element
        if current is None:
            return None

        # Check if awaiting clarification
        if self._briefing_state.awaiting_clarification:
            # User provided clarification, combine with previous answer
            combined = f"{self._briefing_state.last_vague_answer} → {answer}"
            self._briefing_state.collected_answers[current.value] = combined
            self._briefing_state.awaiting_clarification = False
            self._briefing_state.last_vague_answer = None
            self._briefing_state.elements_completed.append(current)
            return self._advance_to_next_element()

        # Check if answer is vague
        if self._is_vague_answer(answer, current):
            self._briefing_state.awaiting_clarification = True
            self._briefing_state.last_vague_answer = answer
            return self._get_clarification_prompt(answer, current)

        # Answer is good, save and advance
        self._briefing_state.collected_answers[current.value] = answer
        self._briefing_state.elements_completed.append(current)
        return self._advance_to_next_element()

    def _is_vague_answer(self, answer: str, element: BriefingElement) -> bool:
        """Check if an answer is too vague and needs clarification.

        Args:
            answer: The user's answer
            element: The element being answered

        Returns:
            True if answer is vague and needs clarification
        """
        answer_lower = answer.lower()

        # Check for vague keywords
        has_vague_keyword = any(kw in answer_lower for kw in VAGUE_KEYWORDS)

        # Check for concrete indicators (numbers, dates, percentages)
        has_concrete = bool(re.search(r'\d+[%]?|\d{4}|q[1-4]|januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember', answer_lower))

        # Answer is vague if it has vague keywords but no concrete indicators
        # and is relatively short (less than 100 chars)
        if has_vague_keyword and not has_concrete and len(answer) < 100:
            return True

        return False

    def _get_clarification_prompt(self, vague_answer: str, element: BriefingElement) -> str:
        """Generate a clarification prompt for a vague answer.

        Args:
            vague_answer: The vague answer given
            element: The element being discussed

        Returns:
            Clarification prompt
        """
        element_name = ELEMENT_NAMES[element]

        # Find which vague keyword was used
        answer_lower = vague_answer.lower()
        used_keywords = [kw for kw in VAGUE_KEYWORDS if kw in answer_lower]
        keyword_str = used_keywords[0] if used_keywords else "das"

        prompts = {
            BriefingElement.KONTEXT: f"""*Arthur hebt eine Augenbraue.*

"{keyword_str.capitalize()}" - das ist noch zu unscharf.

**Was bedeutet das konkret?** Gib mir:
- Ein Ereignis oder Auslöser
- Einen Zeitpunkt oder Zeitraum
- Oder messbare Fakten

*Was ist wirklich passiert?*""",
            BriefingElement.MY_INTENT: f"""*Arthur klopft auf den Tisch.*

"{keyword_str.capitalize()}" ist kein Ziel. Das ist ein Wunsch.

**Mach es messbar:**
- Was genau willst du erreichen?
- Bis wann?
- Woran erkennst du, dass es funktioniert hat?

*Versuch's nochmal - konkreter.*""",
            BriefingElement.HIGHER_INTENT: f"""*Arthur lehnt sich zurück.*

"{keyword_str.capitalize()}" - das sagt jeder. Was ist das **wirkliche** Ziel dahinter?

Wenn dieses Projekt zu Ende ist, welches größere Ziel wird dadurch erreicht?

*Denk eine Ebene höher.*""",
            BriefingElement.KEY_TASKS: f"""*Arthur schüttelt den Kopf.*

"{keyword_str.capitalize()}" ist keine Aufgabe. Das ist eine Absicht.

**Was muss konkret getan werden?**
- Liste 2-3 wesentliche Schritte
- Keine Buzzwords, sondern Verben

*Was steht auf der To-Do-Liste?*""",
            BriefingElement.BOUNDARIES: f"""*Arthur runzelt die Stirn.*

"{keyword_str.capitalize()}" ist keine Grenze.

**Was ist explizit NICHT Teil des Vorhabens?**
- Welche Bereiche fassen wir nicht an?
- Welche Ressourcen haben wir nicht?
- Was machen wir definitiv nicht?

*Wo ist der Zaun?*""",
        }

        return prompts.get(element, f"*Arthur wartet.* Kannst du das konkretisieren?")

    def _advance_to_next_element(self) -> str:
        """Advance to the next briefing element or complete the briefing.

        Returns:
            Response for next element or completion summary
        """
        next_element = self._briefing_state.get_next_element()

        if next_element is None:
            # Briefing complete
            return self._generate_summary()

        self._briefing_state.current_element = next_element
        return self._format_next_question(next_element)

    def _format_next_question(self, element: BriefingElement) -> str:
        """Format the question for the next element.

        Args:
            element: The element to ask about

        Returns:
            Formatted question
        """
        order = self._briefing_state.get_element_order()
        idx = order.index(element) + 1
        total = len(order)
        element_name = ELEMENT_NAMES[element]
        question = ELEMENT_QUESTIONS[element]

        # Progress indicator
        completed = len(self._briefing_state.elements_completed)
        progress = "✅ " * completed + "⬜ " * (total - completed)

        return f"""*Arthur nickt und macht sich eine Notiz.*

Gut. Weiter.

---

### {idx}. {element_name}

{progress}

{question}

*Ich höre zu.*"""

    def _generate_summary(self) -> str:
        """Generate the briefing summary for confirmation.

        Returns:
            Formatted summary asking for confirmation
        """
        state = self._briefing_state
        answers = state.collected_answers
        is_quick = state.mode == "quick"

        mode_label = "⚡ Schnellcheck" if is_quick else "🎖️ Vollständiges Briefing"

        # Build summary sections
        sections = []
        for element in state.get_element_order():
            name = ELEMENT_NAMES[element]
            answer = answers.get(element.value, "—")
            sections.append(f"**{name}:**\n{answer}")

        sections_text = "\n\n".join(sections)

        self._briefing_state.active = False  # Mark as pending confirmation

        return f"""## {mode_label} - Zusammenfassung

*Arthur legt den Stift hin und schaut dich an.*

---

{sections_text}

---

**Stimmt das so?**

Antworte mit:
- **"Ja"** oder **"Bestätigt"** → Mandat wird gespeichert
- **"Nein"** oder Korrektur → Wir passen an

*Dein Mandat, deine Entscheidung.*"""

    def confirm_mandat(self, project_name: str = "Mein Projekt") -> tuple[str, bool]:
        """Save the mandat after user confirmation.

        Args:
            project_name: Name for the project/mandat

        Returns:
            Tuple of (response message, should_handback_to_nora)
        """
        state = self._briefing_state
        answers = state.collected_answers
        is_quick = state.mode == "quick"

        # Build mandat content
        content_parts = []
        for element in FULL_BRIEFING_ORDER:
            name = ELEMENT_NAMES[element]
            answer = answers.get(element.value, "—" if element in state.get_element_order() else "*Nicht im Schnellcheck enthalten*")
            content_parts.append(f"## {name}\n\n{answer}")

        content = "\n\n".join(content_parts)

        # Create artifact
        artifact = Artifact(
            id="mandat",
            type=ArtifactType.MANDAT,
            title=f"Mandat: {project_name}",
            content=content,
            status=ArtifactStatus.COMPLETE,
            created_by="arthur",
            created_at=datetime.now(),
        )

        # Save to Discovery Wall
        save_artifact(artifact)

        # Reset state
        state.reset()

        quick_note = "\n\n*Schnellcheck-Mandat - für vollständiges Briefing nutze `*briefing`*" if is_quick else ""

        response = f"""## ✅ Mandat gespeichert

*Arthur lächelt zufrieden.*

Das Mandat steht. Es wurde auf der **Discovery Wall** gespeichert.{quick_note}

---

**Nächster Schritt:** Nora übernimmt und zeigt dir den Weg.

*Die Basis ist gelegt. Jetzt geht die echte Arbeit los.*"""

        return response, True  # True = handback to Nora

    def is_awaiting_confirmation(self) -> bool:
        """Check if waiting for user to confirm the mandat summary."""
        state = self._briefing_state
        # We're awaiting confirmation if:
        # - Not active (briefing questions done)
        # - But we have collected answers (summary was shown)
        return not state.active and len(state.collected_answers) > 0

    def is_confirmation_response(self, message: str) -> bool:
        """Check if message is a confirmation response.

        Args:
            message: User message

        Returns:
            True if message confirms the mandat
        """
        confirm_keywords = ["ja", "yes", "bestätigt", "bestätigen", "ok", "okay", "passt", "stimmt", "korrekt", "richtig"]
        msg_lower = message.strip().lower()
        return any(kw == msg_lower or msg_lower.startswith(kw + " ") or msg_lower.startswith(kw + ",") for kw in confirm_keywords)

    def get_pending_confirmation_answers(self) -> Dict[str, str]:
        """Get the answers pending confirmation.

        Returns:
            Dict of element name to answer, or empty if not awaiting confirmation
        """
        if not self.is_awaiting_confirmation():
            return {}
        return self._briefing_state.collected_answers.copy()

# BMAD-Prinzipien für Hansel

## Die Kern-Prinzipien, die BMAD erfolgreich machen

### 1. Just-In-Time Loading (Lazy Loading)

**Prinzip:** Lade nur das, was gerade gebraucht wird - niemals alles auf einmal.

```
❌ FALSCH: Lade das gesamte Handbuch (500+ Seiten) in den Context
✅ RICHTIG: Lade nur das Kapitel "Mandat klären" wenn Arthur aktiv ist
```

**Für Hansel:**
- Jeder Agent lädt nur seine relevanten Kapitel aus dem Handbuch
- Arthur lädt: `knowledge/mandat-klaeren.md`
- Finn lädt: `knowledge/bedarf-verstehen.md`
- Etc.

### 2. Micro-File Architecture (Document Sharding)

**Prinzip:** Große Dokumente in kleine, fokussierte Dateien aufteilen.

```
❌ FALSCH: Eine 8MB Markdown-Datei
✅ RICHTIG: 20 kleine Dateien à 10-50KB
```

**Für Hansel - Handbuch sharден:**
```
docs/knowledge/
├── index.md                      # Übersicht & Navigation
├── 01-einfuehrung.md
├── 02-explorationsmodell.md
├── 03-mandat-klaeren/
│   ├── index.md
│   ├── auftragsklärung.md
│   └── bungay-briefing.md
├── 04-bedarf-verstehen/
│   ├── index.md
│   ├── forschungsfragen.md
│   ├── interviews.md
│   └── hypothesen.md
├── 05-ideen-entwickeln/
│   ├── index.md
│   ├── how-might-we.md
│   └── methoden.md
└── 06-loesungen-testen/
    ├── index.md
    ├── test-cards.md
    └── truth-curve.md
```

### 3. Step-File Architecture für Workflows

**Prinzip:** Workflows in sequenzielle Schritte aufteilen, nur einen Step gleichzeitig im Kontext.

```
workflows/briefing/
├── workflow.md           # Übersicht & Regeln
└── steps/
    ├── step-01-kontext.md
    ├── step-02-intent.md
    ├── step-03-higher-intent.md
    ├── step-04-key-tasks.md
    └── step-05-boundaries.md
```

**Regeln:**
- 🛑 NIEMALS mehrere Steps gleichzeitig laden
- 📖 IMMER den kompletten Step lesen vor Ausführung
- 🚫 NIEMALS Steps überspringen
- ⏸️ IMMER auf User-Input warten wenn gefordert

### 4. Agent-Manifest für Multi-Agent-Orchestrierung

**Prinzip:** Zentrale CSV/YAML-Datei mit allen Agent-Metadaten für schnelles Laden.

```csv
name,displayName,icon,role,module,path
nora,Nora,🔭,Navigatorin & Squash-Point-Masterin,hansel,agents/nora.md
arthur,Arthur,🎖️,Mandats-Architekt (Bungay-Experte),hansel,agents/arthur.md
finn,Finn,🔍,User Research & JTBD Experte,hansel,agents/finn.md
ida,Ida,💡,Ideation & Design Moderatorin,hansel,agents/ida.md
theo,Theo,🧪,Experiment-Designer & Test-Experte,hansel,agents/theo.md
```

**Vorteil:** Der Orchestrator muss nicht alle Agent-Dateien laden, um zu wissen, wer verfügbar ist.

### 5. State-Tracking in Frontmatter

**Prinzip:** Dokumenten-Status im YAML-Frontmatter tracken.

```yaml
---
type: mandat
status: in_progress
created: 2025-01-10
stepsCompleted: [1, 2, 3]
currentAgent: arthur
lastUpdate: 2025-01-10T21:30:00
---
```

**Für Hansel Discovery Wall:**
- Jedes Artefakt hat Frontmatter mit Status
- Ermöglicht Nora, den Gesamtstatus zu verstehen ohne alles zu lesen

### 6. Persona-Driven Agents

**Prinzip:** Jeder Agent hat eine klare Persona mit:
- `role` - Was macht der Agent?
- `identity` - Wer ist der Agent?
- `communication_style` - Wie kommuniziert er?
- `principles` - Nach welchen Regeln handelt er?

**Für Hansel bereits definiert:**
- Arthur: "Präzise, unnachgiebig, fokussiert auf die Art of Action"
- Finn: "Neugierig, analytisch, datenzentriert"
- Etc.

### 7. Commands & Triggers

**Prinzip:** Klare Trigger für Agent-Aktionen.

```yaml
commands:
  - trigger: "*status"
    action: "Zeigt den Fortschritt in allen 4 Feldern"
  - trigger: "*check"
    action: "Führt die Squash-Punkt-Reflektion durch"
```

**Vorteil:** User kann gezielt Funktionen aufrufen, Agent weiß genau was zu tun ist.

### 8. Shared Output Folder

**Prinzip:** Alle Artefakte an einem zentralen Ort.

```
_hansel-output/
├── discovery-wall/
│   ├── mandat.md           # Arthur's Output
│   ├── research/           # Finn's Outputs
│   │   ├── forschungsfragen.md
│   │   └── insights.md
│   ├── ideen/              # Ida's Outputs
│   │   └── how-might-we.md
│   └── tests/              # Theo's Outputs
│       ├── test-card-001.md
│       └── learning-card-001.md
└── status.yaml             # Nora's Gesamtübersicht
```

---

## Architektur-Vorschlag für Hansel

```
hansel/
├── config.yaml                 # Globale Konfiguration
├── agent-manifest.csv          # Agent-Registry
│
├── agents/                     # Agent-Definitionen
│   ├── nora.md
│   ├── arthur.md
│   ├── finn.md
│   ├── ida.md
│   └── theo.md
│
├── knowledge/                  # Geshardetes Handbuch
│   ├── index.md
│   ├── explorationsmodell.md
│   ├── mandat/
│   ├── bedarf/
│   ├── ideen/
│   └── test/
│
├── workflows/                  # Step-basierte Workflows
│   ├── briefing/
│   │   ├── workflow.md
│   │   └── steps/
│   ├── research/
│   ├── ideation/
│   └── validation/
│
├── templates/                  # Artefakt-Templates
│   ├── mandat.md
│   ├── test-card.md
│   └── learning-card.md
│
└── _output/                    # Discovery Wall
    └── discovery-wall/
```

---

## Context-Budget pro Agent

| Agent | Lädt beim Start | Max Context |
|-------|-----------------|-------------|
| Nora | `status.yaml`, `agent-manifest.csv` | ~2K tokens |
| Arthur | `knowledge/mandat/*.md`, `templates/mandat.md` | ~5K tokens |
| Finn | `knowledge/bedarf/*.md`, `templates/research/*.md` | ~5K tokens |
| Ida | `knowledge/ideen/*.md`, `templates/hmw.md` | ~4K tokens |
| Theo | `knowledge/test/*.md`, `templates/test-card.md` | ~4K tokens |

**Prinzip:** Kein Agent braucht mehr als ~5K tokens Kontext aus dem Handbuch.

---

## Nächste Schritte

1. Handbuch in kleine Dateien sharден
2. Agent-Dateien mit korrekten Load-Instruktionen erstellen
3. Workflow-Steps für jeden Agenten definieren
4. Templates für Artefakte erstellen
5. Orchestrator (Nora) implementieren

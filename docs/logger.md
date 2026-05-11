# Intelligence Trace — "Mission Control" Logger Design

## Vision

The Orchestration Trace sidebar is not a status bar — it is a **window into the AI's reasoning**. Every line should reveal friction, correction, or data-driven decision-making that a judge or technical reviewer can follow step-by-step.

---

## The Five-Agent Pipeline (Visual Map)

```
USER REQUEST
     │
     ▼ (Python mode selection in streamer.py)
     │
     ├──► [SCOUT]       → biometric cluster-match across 14 archetypes
     │         │
     │         └──► [LOGGER]  → logs centroid distances & keyword match
     │
     ├──► [NARRATOR]    → personalizes Scout output into 2-4 para story
     │         │
     │         └──► [LOGGER]  → logs story elements woven in
     │
     ├──► [COMPLIANCE]  → enforces IOC brand rules, tone, parity
     │         │
     │         └──► [LOGGER]  → logs violations found/fixed or clean pass
     │
     ├──► [EVAL]        → scores result across 6 dimensions (assessment only)
     │         │
     │         └──► [LOGGER]  → logs dimension scores
     │
     └──► FINAL JSON → SSE → Frontend
```

> Note: The Supervisor Agent was removed in v2. Mode selection is now handled in Python (`streamer.py`). See [`ARCHITECTURE_EVOLUTION.md`](ARCHITECTURE_EVOLUTION.md) for the full history.

---

## Logger Agent: Rules & Output Spec

The Logger Agent receives a context dump from the Supervisor after each pipeline step and must output a **single-line, data-specific trace** — maximum 150 characters.

### Anti-Patterns (Banned Boilerplate)

| ❌ Forbidden                                        | ✅ Required Instead                                         |
|----------------------------------------------------|-------------------------------------------------------------|
| "The Narrator Agent is reviewing the conversation" | "Narrative woven around tennis background, Elite Peak age." |
| "Scout Agent is analyzing..."                       | "Profile #7 (Versatile Decathlete) matched. Δh=6.2cm."    |
| "Compliance check complete."                        | "Clean pass — IOC brand labels verified across 2 profiles." |
| "Processing your request..."                        | (never acceptable)                                          |

---

## Trace Anatomy

Each SSE trace event has:
```json
{
  "type": "trace",
  "agent": "scout_agent | narrator_agent | compliance_agent | supervisor_agent | logger_agent",
  "event": "Thought | RequestReceived | AssemblingContext | ...",
  "timestamp": "HH:MM:SS",
  "detail": "<the actual intelligence trace — this is the primary text>"
}
```

The `detail` field from the **Logger Agent** is the human-readable intelligence trace. The `event` name from other agents is a raw ADK event class name used for secondary display only.

---

## Phase-Specific Trace Templates

### SCOUT Phase
```
Profile #[id] ([name]) → Δh:[X]cm Δw:[Y]kg Δa:[Z]yrs. Keywords: [top 2 matched]. [Standing path].
```
Example:
```
Profile #7 (Versatile Decathlete) matched. Δh:6.2cm Δw:0.6kg. Keywords: all-rounder, tenacity. Elite Decathlon pathway.
```

### NARRATOR Phase
```
Narrative woven around [user activity]. [life_stage] window. [tone] voice. [path type] story completed.
```
Example:
```
Narrative woven around tennis + yoga. Elite Peak window. Adaptable voice. Standing pathway story completed.
```

### COMPLIANCE Phase (violation found)
```
[VIOLATION] [violation type] → fixed. e.g. "Standalone 'Olympic' → 'elite sport pathway' in question."
```

### COMPLIANCE Phase (clean)
```
Clean pass — [summary of content type] approved. [Any parity note].
```
Example:
```
Clean pass — 2 standing + adaptive narratives approved. Equal prominence confirmed.
```

### INTERVIEW Phase
```
Q[N]: [topic summary]. [READY] option [included / not yet — min 3 required].
```
Example:
```
Q2: Training frequency + team sport background. [READY] not yet (minimum 3 required).
```

---

## Frontend Color Coding

| Agent       | Color     | Hex       | Meaning              |
|-------------|-----------|-----------|----------------------|
| Scout       | Gold      | `#c5a44e` | Data analysis        |
| Narrator    | Amber     | `#e3ce6f` | Storytelling         |
| Compliance  | Red       | `#f87171` | Quality gate / risk  |
| Supervisor  | Purple    | `#a78bfa` | Orchestration        |
| Logger      | Green     | `#34d399` | System trace         |
| System      | Slate     | `#94a3b8` | Internal events      |

---

## Auto-Scroll Behavior

The trace panel uses **sticky auto-scroll**: `scrollTop = scrollHeight` fires on every `AfterViewChecked` cycle. The newest trace is always pinned to the bottom of the viewport. The scrollbar is thin and styled to match the dark terminal aesthetic (4px gold-tinted thumb).

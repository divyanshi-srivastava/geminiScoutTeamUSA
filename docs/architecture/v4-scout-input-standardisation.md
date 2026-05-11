# v4 — Scout Input Standardisation (Proposed)

## The Problem

Scout is a math agent doing a non-math job.

Its current instruction contains a qualitative judgment layer bolted on top of biometric distance scoring:

> *"If `injury_mentioned` → increase adaptive pathway weight. If `training_gap` → shift the effective competitive window later. If `active_training` → reinforce the primary archetype with more confidence."*

These are not distance calculations. They are biographical interpretations — the kind of reasoning that requires understanding context, intent, and nuance. Scout is being asked to do both: compute Euclidean distances against 14 profiles AND make judgment calls about how a knee surgery or a career break should affect an archetype recommendation.

This mixed responsibility is a direct cause of Scout's hallucination problem. More context → longer reasoning chain → more opportunity for the model to interpolate rather than select. The invented archetype names ("Tactical Scholar", "The Strategist") appeared precisely when Scout was working through ambiguous, multi-signal inputs. The ERA headers added even more ambiguity surface.

There is also a second, quieter problem: Scout receiving ERA context breaks the clean separation between what the agents *do*. Narrator ran the era interview. It holds the user's journey. It knows what the user said about their knee surgery or career break — in the user's own words. Having Narrator hand a structured summary to the streamer, which then hands it to Scout as signal tags, which Scout then re-interprets — is three translations of the same information, each introducing noise.

---

## The Proposed Change

**Scout should only receive standardised inputs it would receive on any normal scouting run:**

- Biometrics (height, weight, age, gender)
- A conversation history containing interview signals

**All era-specific context stays with the Narrator and the streamer's Python layer.**

The Narrator already does the era mini-interview. It produces `era_context_summary` with signal tags (`injury_mentioned`, `training_gap`, `competitive`, etc.). Instead of passing those tags to Scout and asking Scout to interpret them, the streamer translates them into interview-signal-style keywords — the same format the manifest's `interview_signals.strong_match` and `interview_signals.weak_match` fields already use — and appends them to the conversation history before the scouting pipeline fires.

Scout sees a slightly longer conversation history. It does not know whether a signal came from the main interview or from an era mini-interview. It runs the same math it always runs.

---

## Implementation: Option B — Python Translation in Streamer

The translation happens in `streamer.py`, inside `_build_system_header()` or just before the scouting pipeline is invoked. No LLM synthesis required. No pipeline reordering. No frontend changes.

### Signal tag → keyword mapping

A lookup table maps ERA_CONTEXT signal tags to interview-signal keywords that align with the manifest's existing `interview_signals` schema:

| ERA signal tag | Injected as conversation turn |
|---|---|
| `active_training` | `"I've been training consistently and staying competitive."` |
| `competitive` | `"I'm actively competing and pushing my performance limits."` |
| `recreational` | `"I keep active but sport is more for enjoyment than competition."` |
| `training_gap` | `"I had a significant gap away from structured training."` |
| `returning_to_sport` | `"I'm getting back into sport after time away from it."` |
| `injury_mentioned` | `"I've been managing a physical setback that affected my training."` |
| `recovery_mode` | `"My body has been in recovery and I've had to adapt my movement."` |
| `peak_fitness` | `"I'm in the best physical shape of my life right now."` |
| `career_shift` | `"A major life change shifted my time and energy away from sport."` |
| `family_milestone` | `"Family commitments became the main focus of that chapter of my life."` |
| `student_era` | `"I was studying full-time and sport fit around that."` |

These are injected as a synthetic `user` turn in the conversation history with a label like `[ERA CONTEXT — synthesised from era interview]` so the logger can surface it as a trace event rather than hiding the translation.

### AGE_OVERRIDE stays Python

`AGE_OVERRIDE` (user's age at the destination Games) is already computed as pure arithmetic: `target_game_year - birth_year`. It continues to be injected by the streamer. Scout reads it in Step 1 and uses it for Step 5 peak_range alignment only. This is deterministic math, not interpretation — it stays.

### What Scout's context looks like after this change

**Before (current):**
```
[SYSTEM: MODE | SCOUTING]
[SYSTEM: BIOMETRIC_DATA | Height: 178cm | Weight: 72kg | Age: 41 | Gender: F]
[SYSTEM: TIME_TRAVEL | Destination: The Brisbane 2032 Games | User age at destination: 26 | Life stage: Elite Peak]
[SYSTEM: AGE_OVERRIDE | 26 (at The Brisbane 2032 Games)]
[SYSTEM: ERA_HISTORY]
  ...
[SYSTEM: ERA_CONTEXT]
  Life context: Was finishing a competitive rowing career while starting a graduate programme.
  Physical context: Knee injury in 2029, 14-month recovery, returning to sport.
  Athletic engagement: Recreational after injury, now rebuilding.
  Signals: injury_mentioned, recovery_mode, returning_to_sport, student_era
[SYSTEM: CONVERSATION_HISTORY]
  NARRATOR: What drives you most in movement?
  USER: Precision and technical control over raw speed.
  ...
```

**After (proposed):**
```
[SYSTEM: MODE | SCOUTING]
[SYSTEM: BIOMETRIC_DATA | Height: 178cm | Weight: 72kg | Age: 41 | Gender: F]
[SYSTEM: TIME_TRAVEL | Destination: The Brisbane 2032 Games | User age at destination: 26 | Life stage: Elite Peak]
[SYSTEM: AGE_OVERRIDE | 26 (at The Brisbane 2032 Games)]
[SYSTEM: CONVERSATION_HISTORY]
  NARRATOR: What drives you most in movement?
  USER: Precision and technical control over raw speed.
  ...
  USER [ERA CONTEXT — synthesised from era interview]: I've been managing a physical setback that affected my training.
  USER [ERA CONTEXT — synthesised from era interview]: My body has been in recovery and I've had to adapt my movement.
  USER [ERA CONTEXT — synthesised from era interview]: I'm getting back into sport after time away from it.
  USER [ERA CONTEXT — synthesised from era interview]: I was studying full-time and sport fit around that.
```

Scout still scores `recovery_mode`, `injury_mentioned`, `returning_to_sport`, and `student_era` signals — but via the same interview signal keyword matching it uses for all other answers. No special-case ERA handling. No new logic branch.

---

## What Changes Per Component

### `scout.md`
Remove entirely:
- The ERA_CONTEXT handling block in Step 1 (the "qualitative nudge modifiers" section)
- All references to signal tags and how they affect scoring

Scout becomes: biometrics → distance → interview signals → dimension enforcement → output verification. No exceptions.

### `streamer.py`
Add a small translation block in `_build_system_header()` (or just before the scouting pipeline fires):
- If `era_context_summary` is present and `mode == "SCOUTING"`, iterate over its `signals` array and append the corresponding synthetic conversation turns to `conversation_history` before building the header
- `ERA_CONTEXT` and `ERA_HISTORY` headers are no longer injected into the scouting system message (they can still be injected for Narrator in the narrative-writing phase, since Narrator uses them for biographical framing)

Note: the distinction between what Scout and Narrator receive is not trivial with the current SequentialAgent setup — all agents in the pipeline see the same initial user message. One clean resolution: continue injecting `ERA_CONTEXT` and `ERA_HISTORY` into the shared header (Narrator uses them), but add a `[SCOUT: IGNORE ERA_CONTEXT]` instruction to `scout.md` telling it to skip those headers entirely and rely only on `CONVERSATION_HISTORY`. This avoids pipeline restructuring while still achieving the isolation. The translated signals are already in conversation history so Scout has everything it needs.

### `narrator.md`
No changes to the interview or narrative modes.

Narrator already uses `ERA_CONTEXT` and `ERA_HISTORY` for biographical framing in SCOUTING mode — this continues unchanged. The change is that Scout stops consuming those headers, not that they disappear.

### `pipeline.py`
No changes. `Scout → Narrator → Compliance` order is unchanged.

### Frontend / models
No changes. The `StoryRequest` shape is unchanged. `era_context_summary` continues to be sent by the frontend on time-travel scouting requests — it is now consumed by the streamer's translation step rather than being forwarded to Scout directly.

### Logger
Improved. The synthetic ERA turns appended to conversation history are labelled `[ERA CONTEXT — synthesised from era interview]`, so the logger can emit a dedicated trace event: "Streamer synthesised 4 ERA signals into conversation history before scouting." This makes the translation visible in the Intelligence Trace sidebar rather than hidden inside Scout's reasoning.

---

## What This Fixes

| Problem | Current behaviour | After v4 |
|---|---|---|
| Scout hallucinating archetypes | Complex ERA input expands reasoning surface, model interpolates | Standardised input, shorter reasoning chain, less drift |
| Scout doing biographical judgment | ERA signal tags require qualitative interpretation | Signals translated to keywords before Scout runs; Scout just counts matches |
| ERA context translated three times | User words → Narrator summary → signal tags → Scout interpretation | User words → Narrator summary → Python keyword injection → Scout counts |
| Scout instruction complexity | ERA section adds a conditional logic branch to an already-complex step | Removed entirely; instruction is pure scoring logic |
| Auditability of ERA influence | ERA effects happen inside Scout's opaque reasoning | Translation is explicit Python; logged as a trace event |

## What This Does Not Change

- Scout's core scoring algorithm (Steps 2–6 are unchanged)
- The benchmark score history — this is a forward change, not a rewrite of prior results
- The user-facing experience — the time travel flow, era interview, and final report are identical
- Narrator's ability to write era-contextualised narratives (it still receives ERA_CONTEXT for the narrative phase)
- Compliance, Eval, pipeline ordering

---

## Open Questions Before Implementation

1. **Keyword mapping fidelity**: Do the synthesised keyword phrases actually trigger the manifest's `interview_signals.strong_match` patterns reliably? Should be validated against the manifest before shipping.
2. **Multiple hops**: When ERA_HISTORY contains multiple prior hops, do we synthesise signals from all of them or only the current hop? Likely current hop only — earlier hops are already baked into the main interview context.
3. **Conflicting signals**: If a user has both `active_training` and `injury_mentioned` (they're training through an injury), both synthetic turns are injected. Scout's scoring handles conflicting signals by net count — this is probably correct behaviour, but worth a benchmark run to confirm.

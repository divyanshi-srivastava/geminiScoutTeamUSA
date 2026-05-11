# Time Travel Feature — Implementation Spec

## Overview

When a user clicks a timeline pill after seeing their result, they don't get an instant cold re-scout. They get a **mini-interview** where the Narrator asks 1–2 era-bridging questions, then a full scout runs with the accumulated context. The result reflects both the age change AND the user's new answers.

---

## System Headers

The streamer injects these headers to communicate era context to the agents:

```
[SYSTEM: MODE | TIME_TRAVEL_INTERVIEW]
[SYSTEM: BIOMETRIC_DATA | Height: 183cm | Weight: 78kg | Age: 22]
[SYSTEM: TIME_TRAVEL | Destination: The 2032 Games | User age at destination: 26 | Life stage: Elite Peak]
[SYSTEM: AGE_OVERRIDE | 26 (at The 2032 Games)]
[SYSTEM: ERA_HISTORY | 2028 Games (age 22): User said they started competitive swimming and reduced gym work after a shoulder strain.]
[SYSTEM: CONVERSATION_HISTORY]
  USER: I train twice a week...
  NARRATOR: {"type": "interview", ...}
  ...
[END CONVERSATION_HISTORY]
```

When `is_ready_to_scout: false` AND `target_game_year` is set → `TIME_TRAVEL_INTERVIEW` mode.
When `is_ready_to_scout: true` AND `target_game_year` is set → `SCOUTING` mode (with `AGE_OVERRIDE`).

---

## Pipeline Routing

Mode selection is done in Python (`streamer.py`), not by a routing LLM.

```
TIME_TRAVEL_INTERVIEW:
  SequentialAgent: narrator_agent (era mode) → compliance_agent
  Returns: compliance-approved question JSON

SCOUTING (with AGE_OVERRIDE):
  SequentialAgent: scout_agent → narrator_agent → compliance_agent → eval_agent
  Scout receives AGE_OVERRIDE and uses it for peak_range alignment (Step 5).
  Narrator receives scout output + full conversation history + ERA_HISTORY.
```

> The Supervisor Agent was removed in v2. See [`architecture-evolution.md`](architecture-evolution.md).

---

## Narrator Mode C: Time Travel Interview

### Trigger
The streamer's system header contains `[SYSTEM: MODE | TIME_TRAVEL_INTERVIEW]` and `[SYSTEM: TIME_TRAVEL]`. Mode resolution is done in Python (`event_generator()` in `streamer.py`) — there is no LLM routing.

### Rules
1. Read the `TIME_TRAVEL` header to understand the destination era and life stage
2. Read `ERA_HISTORY` to see what was already said in previous time travel stops
3. Ask exactly **1 question** bridging the user from their current time to the destination era
4. The question should reference:
   - The specific Games destination ("At The 2032 Games, you'd be 26...")
   - The life stage transition if relevant ("You'd be entering your Elite Peak window...")
   - Any relevant ERA_HISTORY if available ("Given what you shared about 2028...")
5. Provide empathetic feedback on the user's previous answer (from conversation history) before asking
6. After the user answers, the `[READY]` trigger is automatic — no need to ask for permission
7. **Forbidden words**: Same as base interview — no "Olympic" or "Paralympic"

### Output Format
Same as base interview:
```json
{
  "type": "interview",
  "feedback": "<reaction to last answer, or era transition greeting>",
  "question": "<1 era-bridging question>",
  "options": ["<option 1>", "<option 2>", "<option 3>"]
}
```

---

## Frontend Flow

```
User clicks 2032 pill
  → timeline sends: { is_ready_to_scout: false, target_game_year: 2032, conversation_history: [...] }
  → state: SCOUTING (loading) → receives question → state: TIME_TRAVEL_INTERVIEW
  → interview component shows era context header + 1 question
  → user answers
  → timeline sends: { is_ready_to_scout: true, target_game_year: 2032, story: <answer>, conversation_history: [...] }
  → full scout pipeline runs with AGE_OVERRIDE
  → result appears with updated archetype + life stage badge
  → era answer saved to eraHistory map in state service
```

---

## State Service ERA History

```typescript
// In StateService
eraHistory: Map<number, string> = new Map();

saveEraAnswer(year: number, summary: string) {
  this.eraHistory.set(year, summary);
}

getEraHistoryBlock(): string {
  if (this.eraHistory.size === 0) return '';
  let block = '[SYSTEM: ERA_HISTORY]\n';
  this.eraHistory.forEach((summary, year) => {
    block += `  ${year} Games: ${summary}\n`;
  });
  return block;
}
```

The era summary stored is the user's answer to the time travel question (truncated to ~200 chars) plus the resulting archetype name. This gives the Narrator enough context without flooding the prompt.

---

## Life Stage Labels

Timeline pills display the life stage label below the city name:

```
[ 2032 ]
[ Paris ]
[ Elite Peak ]   ← colored text matching the pill border color
```

Color mapping:
- Rising Star (< 20): `#34d399` (green)
- Elite Peak (20–32): `#facc15` (yellow-gold)
- Veteran (33–45): `#60a5fa` (blue)
- Legacy Coach (> 45): `#a78bfa` (purple)

---

## Result Page Updates for Time Travel

When a time travel result arrives (i.e., `target_game_year` was set):
- The Scout Verdict panel shows an era banner: "AT THE 2032 GAMES · ELITE PEAK · AGE 26"
- The life stage badge on each card reflects the era age, not the current age
- The Judge's Vault footer shows: "Time travel active — age override: 26 at The 2032 Games"

---

## What Does NOT Change

- Scout, Compliance: completely unchanged — they just receive a different age
- The locked fields (`matched_profile_id`, `matched_profile_name`, `pathway_standing`, `pathway_adaptive`): never modified
- The base interview flow: completely unchanged
- The logger: operates identically across all modes

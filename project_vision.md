# Gemini Scout: The Living Legacy Vision

## The Core Philosophy
Gemini Scout is not a calculator — it is a **Time-Traveling Talent Scout**. It doesn't just categorize an athlete; it discovers a legacy. By blending high-fidelity biometric logic with a conversational, personalized narrative, we bridge the gap between "what you are" and "who you can become" within the Team USA ecosystem.

The experience has three acts:
1. **The Great Interview** — the Narrator learns who you are today
2. **The Scout Report** — five agents analyze and produce your archetype result
3. **The Time Machine** — you jump to different Games eras and discover how your story would have unfolded

---

## Act 1: The Great Interview

The Narrator Agent leads a conversational onboarding. No cold forms.

- Asks 3–5 targeted questions mixing multiple-choice chips and free-text inputs
- Provides empathetic feedback on every answer ("Training twice a week? That's a solid foundation!")
- After minimum 3 questions, offers the `[READY]` option to proceed to scouting
- **Forbidden words during interview**: "Olympic", "Paralympic" — replaced with "elite sport", "high-performance athletics", "elite athletic pathway"

---

## Act 2: The Scout Report

A 4-agent pipeline runs after the interview:

| Agent | Role |
|---|---|
| **Scout** | Maps biometrics to the closest archetype from a 12-profile manifest using Euclidean distance + keyword matching |
| **Narrator** | Rewrites Scout's technical verdict into a personalized 2–4 paragraph story using the user's interview answers |
| **Compliance** | Silently fixes any IOC brand violations (standalone "Olympic", NIL references, parity gaps) |
| **Logger** | Interprets each agent's internal reasoning in real-time, translating thought tokens into plain English for the judge's sidebar |

The result page shows:
- **Scout Verdict** — the Narrator's personalized story (top panel)
- **Pathway Cards** — archetype name, life stage badge, and discipline label (no prose) for both Elite and Adaptive pathways
- **Judge's Vault** — collapsible terminal panel showing full technical analysis

---

## Act 3: The Time Machine

This is the signature feature. After seeing their result, the user can jump to any Games year where they would have been eligible (age 16–55). Each jump is not a cold re-scout — it's a **mini-interview followed by a new result**.

### The Life Stage System
Each Games year is color-coded based on the user's age at that time:

| Life Stage | Age Range | Color | What It Means |
|---|---|---|---|
| Rising Star | Under 20 | Green `#34d399` | Early potential, raw talent |
| Elite Peak | 20–32 | Gold `#facc15` | Prime competitive window |
| Veteran | 33–45 | Blue `#60a5fa` | Experience-driven excellence |
| Legacy Coach | Over 45 | Purple `#a78bfa` | Mastery and mentorship arc |

### The Time Travel Flow

1. User sees their current result with the timeline bar
2. User clicks a Games year pill (e.g., "2032 · Paris")
3. The Narrator enters **Time Travel Interview Mode** — it asks 1–2 era-bridging questions:
   - "You'd be 26 at The 2032 Games. Were there any major shifts in your training or life goals between now and then?"
   - These questions are informed by the user's base interview answers
4. User answers → full scout pipeline runs with the era age + new answers
5. New result appears — archetype may shift, life stage badge changes, Scout Verdict references the era

### Cross-Era Memory
As the user visits multiple eras, the Narrator **accumulates context** across all jumps. If the user mentioned a knee injury in 2028, the 2032 mini-interview can reference it: "Knowing your knee recovery in 2028, how did that shape your approach heading into the 2032 cycle?"

The era history is passed as `[SYSTEM: ERA_HISTORY]` blocks alongside the base conversation history.

---

## The Logger: Mission Control

The logger sidebar is a **real-time window into agent reasoning** — not a status bar. It runs continuously during the pipeline, translating each agent's internal thinking into plain English.

Each agent's thought tokens are captured by the streamer and immediately passed to the Logger LLM after the agent finishes. The Logger produces 2–3 sentences explaining what that agent just did and why.

The sidebar accumulates logs across the entire session — interview, scouting, and time travel jumps. Judges can scroll back through the full reasoning history.

See `docs/logger.md` for the full Logger architecture spec.
See `docs/time_travel.md` for the full Time Travel implementation spec.

---

## Technical Architecture

```
Frontend (Angular 19)
  ├── InterviewComponent  — base interview + time travel mini-interview
  ├── ReportComponent     — result display with vault
  ├── TimelineComponent   — life stage pills + time travel trigger
  └── LoggerComponent     — real-time agent trace sidebar

Backend (FastAPI + Google ADK)
  ├── streamer.py         — SSE event generator, Python mode selection, pipeline orchestration
  ├── pipeline.py         — SequentialAgent assembly for INTERVIEW / SCOUTING / TIME_TRAVEL_INTERVIEW
  ├── scout_agent.py      — Scout: biometric archetype matching
  ├── narrator_agent.py   — Narrator: personalization + era questions
  ├── compliance_agent.py — Compliance: IOC brand enforcement
  ├── eval_agent.py       — Eval: post-scout quality scoring (6 dimensions)
  └── logger_agent.py     — Logger: thought interpretation (called directly by streamer)
```

### Pipeline Modes (Python-selected in streamer.py)
| Header | Mode | Pipeline |
|---|---|---|
| `[SYSTEM: MODE \| INTERVIEW]` | Base interview | Narrator → Compliance → return question |
| `[SYSTEM: MODE \| SCOUTING]` | Full scout | Scout → Narrator → Compliance → Eval → return result |
| `[SYSTEM: MODE \| TIME_TRAVEL_INTERVIEW]` | Era mini-interview | Narrator (era mode) → Compliance → return question |

### Key Invariants
- Scout and Compliance are never modified for time travel — only Narrator and Supervisor
- `matched_profile_id`, `matched_profile_name`, `pathway_standing`, `pathway_adaptive` are always locked fields — never rewritten by downstream agents
- The Logger never goes through Compliance — it's internal/judge-facing content
- Phase 0 docs (this file + `docs/time_travel.md` + agent `.md` instructions) are the source of truth — code must match them, not the other way around

# v3 — Instruction Tuning (Days 4–5)

## Changes from v2

**1. Pathway Manifest — gender-specific adaptive fields**

Added `adaptive_M` and `adaptive_F` fields to every profile's `pathways` object. Examples:
- Profile 6 (Mat Technician): `adaptive_M` = "Powerlifting (e.g., Men's +100 kg)" | `adaptive_F` = "Powerlifting (e.g., Women's -67 kg)"
- Profile 8 (Streamline): `adaptive_M` = "Adaptive Swimming (e.g., Men's 400 m Freestyle S10)" | `adaptive_F` = "Adaptive Swimming (e.g., Women's 400 m Freestyle S10)"

**2. Pathway Manifest — explicit dimension tags**

Added a `dimension` field to every profile: `"Power/Strength"`, `"Endurance"`, or `"Precision/Technical"`.

**3. Scout instruction — Step 0 rewritten**

Old Step 0 tried to *filter out* wrong-gender profiles from candidate scoring. This was brittle — a profile could be selected for its standing pathway and then have its gendered adaptive field copied verbatim.

New Step 0: resolve the correct gender field (`adaptive_M` or `adaptive_F`) *before* scoring starts, apply it unconditionally to whatever profile is ultimately selected.

**4. Scout instruction — dimension enforcement uses manifest tags**

Old distinctness enforcement: the scout was asked to *classify* dimensions from keywords (unreliable LLM inference).

New: `scout.md` Step 6 reads the `dimension` field from the manifest directly and requires the two picks to differ. No inference required.

**5. Scout instruction — AGE_OVERRIDE for peak_range alignment**

For time-travel personas, `BIOMETRIC_DATA Age` is the user's current age (e.g., 68 for a 1958-born user). But `peak_range` alignment for a time-travel result should use the user's age *at the destination Games* (e.g., 26 at the 1984 Games). The `AGE_OVERRIDE` header (already injected by the streamer during scouting) is now explicitly read in Step 1 and used for Step 5.

**6. Compliance — adaptive parity is now a rewrite rule**

Changed from "flag insufficient parity" to: if `scout_verdict` (object 2) is absent, <60 words, or <50% the length of object 1 → rewrite it to full narrative depth before passing. This eliminated all compliance failures in the benchmark.

**7. Narrator — option fork enforcement**

Added Rule 8: banned catch-all options ("balanced mix", "both equally", "open to anything"). Every option must represent a genuine biomechanical or lifestyle fork. If three genuinely distinct options can't be written, use free-text instead.

**8. Narrator — Narrative Contrast rule**

Added: object 1 (standing) must emphasise the user's PRIMARY physical dimension. Object 2 (adaptive) must emphasise a *different* dimension. Narrator is instructed to read both verdicts back before outputting and rewrite the adaptive if they make the same core argument.

**9. Eval Agent added**

A new `eval_agent` runs after compliance on every scouting result. It scores six dimensions: Authenticity, Personalization, Interview Quality, Pathway Distinctness, Life-Stage Coherence, and Compliance. Scores appear in the Judge's Vault and feed the benchmark master evaluator.

**10. Benchmark system built**

15 pre-written personas run through the live backend end-to-end. Produces timestamped reports with dimension averages, per-persona scorecards, and master LLM analysis. Score history tracked in `history.jsonl` for trend monitoring.

**11. Scout instruction — manifest-only constraint and output verification**

Scout was hallucinating profile names not present in the manifest (e.g., "Tactical Scholar", "The Strategist", "Rising Star Analyst") when a clean biometric match was ambiguous. Two changes stopped this:

- Added a `MANDATORY CONSTRAINT` block at the top of `scout.md` explicitly listing example invented names and stating that the 14 manifest profiles are the only valid source — no inference, no interpolation, regardless of additional context.
- Added Step 7 (Output Verification): before generating any JSON, the scout must verify that `matched_profile_id` is an integer between 1 and 14, `matched_profile_name` is copied character-for-character from that profile's `name` field, and pathway fields are exact strings from the manifest — not placeholders like "Standing" or "Adaptive". If any field fails, it must be rewritten before output.

---

## Sub-version Breakdown

### v3a — Gender resolution + dimension enforcement

- Added `adaptive_M` and `adaptive_F` fields to all 14 manifest profiles. Scout Step 0 now resolves the correct gender field before scoring — female athletes never get "Men's +100kg Powerlifting" events.
- Added explicit `dimension` field to every profile (`Power/Strength`, `Endurance`, `Precision/Technical`). Scout Step 6 reads the field directly and enforces that standing and adaptive picks have different dimension values.
- Added `AGE_OVERRIDE` awareness to Scout Step 1 so time-travel personas use their era age for peak_range alignment, not their current age.
- **Result**: +0.5 overall, compliance failures dropped from 3 → 0.

### v3b — Softened enforcement + compliance city fix + adaptive narrative rule

- The v3a dimension enforcement was too rigid — "always pick different dimension regardless of score gap" forced physically contradictory adaptive picks (Decathlon for a 48yo SCI rower who asked for "singular signature movement"), hurting authenticity. Added a 15-point score threshold and an interview signal gate (S ≥ W required) before overriding dimension.
- Added a full year→city lookup table (1960–2044) to the compliance instruction so the agent can fix bare year references like "The 2028 Games" → "The LA28 Games" without guessing.
- Added Narrator Rule 6: when `pathway_adaptive` contains a sport classification code (T44, S10, F56, etc.), the verdict must name the classification, explain what it covers, and connect it to the user's specific adaptive profile.
- **Result**: +0.5 overall, distinctness +0.9, compliance fully clean.

### v3c — Eval calibration fix

- Removed eval penalty for seasonal sport mismatches. The archetypes represent athletic dimensions, not season-specific sports — "Edge Carver" is about precision edge control at velocity, whether that maps to Alpine Skiing or Speed Skating is irrelevant to the archetype fit. Penalising for Brisbane (Summer) + Alpine Skiing was incorrect.
- **Result**: +0.9 overall, distinctness jumped to 8.2 (from 6.5), authenticity to 7.6.

---

## Pipeline Quality — Full Benchmark History

Each row is a benchmark run (15 personas × 3 rounds = 45 total runs from the multi-round era).

| Run | Overall | Auth | Pers | IQ | Distinct | Pass | Key change |
|---|---|---|---|---|---|---|---|
| Baseline (v2, single round) | 5.5 | 5.4 | 8.0 | 6.7 | 4.4 | 15/15 | SequentialAgent replaces Supervisor |
| v3a (gender fix) | 6.0 | 6.3 | 8.3 | 7.3 | 5.2 | 15/15 | `adaptive_M`/`adaptive_F` + `dimension` tags |
| v3a multi-round | 5.5 | 6.0 | 7.7 | 7.1 | 4.6 | 45/45 | 3 rounds per persona (variance now visible) |
| v3b | 6.5 | 5.9 | 7.9 | 7.6 | 6.1 | 45/45 | Softened distinctness threshold, compliance city lookup, Narrator adaptive classification rule |
| v3b (second run) | 6.5 | 6.6 | 7.7 | 7.7 | 6.5 | 43/45 | Same code, 2 backend timeouts on hostile persona |
| **v3c (latest)** | **7.4** | **7.6** | **8.0** | **7.6** | **8.2** | **45/45** | Eval agent no longer penalises seasonality; further instruction tuning |

**Baseline → latest: +1.9 overall, +2.2 authenticity, +3.8 distinctness, +0.9 interview quality. Zero compliance failures.**

---

## Agent Context Reference

`streamer.py` builds one system header per request (`_build_system_header()`) and passes it as the first message to the entire pipeline. Every in-pipeline agent sees this shared header. The table below maps every context item to the agents that receive it.

### Shared system header

| Header | Present when | What it contains |
|---|---|---|
| `[SYSTEM: MODE]` | Always | `INTERVIEW`, `SCOUTING`, or `TIME_TRAVEL_INTERVIEW` |
| `[SYSTEM: BIOMETRIC_DATA]` | Always | Height (cm), weight (kg), current age, gender |
| `[SYSTEM: TIME_TRAVEL]` | Target game year set | Destination Games name, user's age at that Games, life stage label |
| `[SYSTEM: AGE_OVERRIDE]` | SCOUTING + time travel | User's age at the destination Games — consumed by Scout for peak_range alignment |
| `[SYSTEM: ERA_HISTORY]` | Prior time-travel hops exist | Structured summaries of what user shared at each previously visited Games year |
| `[SYSTEM: ERA_CONTEXT]` | Era interview complete | Life context, physical context, athletic engagement, signal tags (e.g., `injury_mentioned`, `training_gap`) |
| `[SYSTEM: CONVERSATION_HISTORY]` | Prior turns exist | All narrator questions and user answers from the main interview |
| `[SYSTEM: CONTENT_RULES]` | Always | `FORBIDDEN_TERMS` list; `EVAL_CRITERIA` IDs added on SCOUTING runs |

### What each agent sees

| Context | Scout | Narrator<br>(INTERVIEW) | Narrator<br>(SCOUTING) | Narrator<br>(TIME_TRAVEL_INTERVIEW) | Compliance | Eval |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Pipeline mode | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Biometrics (height / weight / age / gender) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Conversation history (all prior Q&A turns) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `TIME_TRAVEL` (destination, user age there, life stage) | ◐ | — | ◐ | ✓ | ◐ | ◐ |
| `AGE_OVERRIDE` (user's age at destination Games) | ◐ | — | ◐ | — | ◐ | — |
| `ERA_HISTORY` (prior hop summaries) | ◐ | — | ◐ | ◐ | ◐ | — |
| `ERA_CONTEXT` (era mini-interview summary) | ◐ | — | ◐ | — | ◐ | — |
| `FORBIDDEN_TERMS` / `EVAL_CRITERIA` | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Pathway manifest (14 profiles, baked into instruction) | ✓ | — | — | — | — | — |
| Scout's JSON output (ADK session state `{scout_report}`) | — | — | ✓ | — | — | — |
| Compliance-approved result JSON | — | — | — | — | — | ✓ |
| Prior agent's output (as conversation turn to review) | — | — | — | — | ✓ | — |

**✓ = always present · ◐ = present when feature is active · — = not available**

**Notes:**
- **Pathway manifest** is appended directly to Scout's instruction string at startup (`scout_agent.py`) — no other agent sees it.
- **Narrator (SCOUTING)** has a `{scout_report}` placeholder in its instruction template. ADK fills this from session state after Scout writes its `output_key`.
- **Narrator (INTERVIEW)** also has `{scout_report}` in its template; the streamer pre-seeds it as an empty string so the placeholder never appears literally in output.
- **Narrator (TIME_TRAVEL_INTERVIEW)** does not receive `ERA_CONTEXT` because it is the agent responsible for building it — the summary is produced only when the narrator signals `era_ready_to_scout: true`.
- **`AGE_OVERRIDE`** is present in the system header for any SCOUTING + time travel run, making it technically visible to Narrator and Compliance in that mode. Only Scout reads it (Step 1 / Step 5 peak_range alignment).
- **Eval** is called outside ADK entirely via a direct API call (`call_eval()` in `eval_agent.py`). Its prompt is hand-assembled from request parameters. It evaluates the final output without access to how the pipeline constructed it — no ERA headers, no content rules, no pathway manifest.

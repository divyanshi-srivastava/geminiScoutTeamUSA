# v4 — Hallucination Defenses (Days 6–7)

The benchmark for v3c held steady at 7.4/10, but two failure modes still leaked through under live use:

1. **Scout** occasionally invented archetype names that did not exist in the 14-profile manifest ("Tactical Scholar", "The Strategist") when biometric matches were ambiguous, and occasionally recommended weight classes that were physically impossible for the user (a 55 kg woman receiving "Men's +100 kg Powerlifting").
2. **Compliance** occasionally hallucinated entirely new content in time-travel interview mode — transforming a Narrator-authored era question into a fabricated scout-array result, which then surfaced to the user as a scouting report on what should have been an interview turn.

v4 is the package of defenses that closed both holes. There is no new agent and no pipeline restructure — every fix is either an instruction constraint on an existing agent or a Python check around the agent's output.

---

## Defense 1 — Scout Output Verification (`scout.md`)

### MANDATORY CONSTRAINT block

A new section was added at the top of `scout.md`, before any scoring steps:

> The manifest embedded in your context contains **exactly 14 profiles**. You MUST select ONLY from these profiles. […]
> NEVER invent a profile name that does not appear in the manifest (e.g., "Tactical Scholar", "The Strategist", "Rising Star Analyst" are invented — do not use them).

Listing the actual invented names that Scout had previously produced is intentional. Negative examples appear to be more effective than abstract prohibitions for this class of failure.

### Step 0 — Weight class filter

After gender resolution, Scout checks every pathway label for an explicit weight class (`+100 kg`, `-60 kg`, etc.). If the class is physically implausible for the user's weight, Scout swaps in the next-best-scoring profile whose weight class is compatible. This is deterministic instruction-driven filtering, not LLM inference — the manifest contains the class strings, the BIOMETRIC_DATA header contains the user weight, and the check is a comparison.

### Step 7 — Output verification

A new mandatory step runs before Scout emits JSON. For each of the two profiles being returned, Scout verifies:

1. `matched_profile_id` is an integer between 1 and 14 that appears in the manifest.
2. `matched_profile_name` is a character-for-character copy from that profile's `name` field — not paraphrased, not summarised.
3. `pathway_standing` is the exact string from `pathways.standing` — not "Standing", not "Olympic", not a placeholder.
4. `pathway_adaptive` is the exact gender-resolved string — not "Adaptive", not "Paralympic", not "para-sport".

If any field fails verification, Scout rewrites it before output. The combination of the MANDATORY CONSTRAINT block (telling Scout what *not* to produce) and Step 7 (forcing a manifest cross-check before emitting) eliminated invented archetype names in the benchmark.

---

## Defense 2 — Compliance Shape Validation (`streamer.py`)

The harder failure was Compliance occasionally inventing new content. In `TIME_TRAVEL_INTERVIEW` mode, Narrator would produce a valid era question, and Compliance — invoked to enforce brand terminology on the same JSON — would sometimes return a completely fabricated `[{matched_profile_id, scout_verdict, …}, …]` scout-array instead. The Narrator's question was destroyed; the user saw a fake scouting report mid-interview.

Two complementary checks were added to `streamer.py`:

### `_output_shape()` — shape classifier

Every JSON output is classified into one of: `question`, `era-signal`, `scout-array`, `scout-object`, `array`, `object`, `non-json`, `empty`, `scalar`. Compliance is contractually required to preserve the shape it received from the previous agent. After Compliance runs, the streamer compares Narrator's pre-compliance shape against Compliance's output shape.

If the shapes differ — for example Narrator emitted a `question` and Compliance returned a `scout-array` — Compliance is treated as having hallucinated. The Compliance output is **discarded entirely**, and the Narrator's pre-compliance draft is used as the final response. A trace event tagged `compliance_agent / Hallucination` is emitted to the Intelligence Trace sidebar so the recovery is visible to the user and to judges, including the `before`/`after` payloads for inspection.

This is a safety net, not a fix — Compliance should never hallucinate, and Narrator's pre-compliance draft is still subject to the agent instructions that already enforce brand rules. But the fallback ensures a single bad Compliance call cannot trigger a fabricated scouting report.

### `_PIPELINE_EMIT_TYPE` — pipeline contract as source of truth

The earlier streamer derived the SSE event type (`interview` vs `result`) from the **shape** of the final response. This is the bug. A hallucinated scout-array from `time_travel_pipeline` would be classified as a result and emitted with `type:"result"` — exactly the wrong outcome.

v4 introduces a single source of truth:

```python
_PIPELINE_EMIT_TYPE = {
    "scouting_pipeline":     "result",
    "interview_pipeline":    "interview",
    "time_travel_pipeline":  "interview",
}
```

The SSE event type is now determined by which pipeline ran, never by what the output looks like. A `time_travel_pipeline` run always emits `type:"interview"`, even if its output is malformed. The frontend's defensive `looksLikeResult()` parser (described below) still distinguishes question payloads from result payloads inside the `interview` channel, but a hallucinated result can no longer leak into the result channel by mimicking its shape.

---

## Defense 3 — Frontend Defensive Parsing (`stream.service.ts`)

Even after the backend defenses, the frontend treats incoming chunks as untrusted:

- **`looksLikeResult()`** — a strict shape detector that returns `true` only for unambiguous scouting results: payloads with both `matched_profile_name` and `scout_verdict`, or `olympic`/`paralympic` keys, or an array of profile objects. A payload with a `question` field is never classified as a result. This catches the rare case where a hallucinated result reaches the `interview` channel; instead of rendering it as a question, the frontend reroutes it to the result handler.
- **`era_ready_to_scout` discrimination** — when Narrator emits `{ era_ready_to_scout: true, era_context_summary: {…} }` mid-stream during a time-travel interview, the frontend treats it as a signal (not a question) and triggers the era scout transition, accumulating the context summary as the next request's input.

Both detectors run before any state mutation, so an unexpected payload shape never updates the UI to the wrong screen.

---

## Defense 4 — Era Result Caching (frontend `state.service.ts`)

A user clicking the same Games year twice should not trigger a second backend round trip. Beyond the cost, the second run produces a slightly different narrative (LLM nondeterminism), which is jarring after the user has already absorbed the first.

The state service now keeps an `eraResultCache: Map<number, {result, evalResult}>`. When a year is revisited:

1. `hasVisitedYear(year)` short-circuits the click handler.
2. `restoreFromCache(year)` replays the cached result + eval into the application state without an HTTP call.
3. The timeline pill shows a coloured visited dot so users can see which eras they have already explored.

The cache lives in memory only — there is no persistence — so refreshing the page resets everything, consistent with the no-PII / per-session-state principle.

---

## Defense 5 — `CONTENT_RULES` Header (`content_rules.json`)

Forbidden terms and eval criteria are now read at startup from `backend/agents/data/content_rules.json` and injected into every agent's system header as a `[SYSTEM: CONTENT_RULES]` block. Previously each agent's instruction file had its own duplicated list of forbidden terms; a change in one place did not propagate.

The single source of truth lets the Eval Agent and the Compliance Agent score and rewrite against the same canonical list, and lets us add a forbidden term in one place rather than three.

---

## Defense 6 — Canonical Games Name Lookup (`_games_name`)

Compliance was inconsistently rewriting bare year references ("The 2028 Games") to canonical Games names ("The LA28 Games"). The lookup is deterministic — given a year, the canonical name is fixed — so the streamer now resolves it in Python and injects the canonical name directly into `[SYSTEM: TIME_TRAVEL]` and `[SYSTEM: AGE_OVERRIDE]` headers. Compliance no longer has to do this rewrite; the agent layer always sees the correct name.

`_GAMES_DISPLAY_NAME` covers 1960 through 2044 — every Games year the timeline can target.

---

## What Was Considered but NOT Shipped — Scout Input Standardisation

An earlier proposal (the original content of this document) suggested removing ERA_CONTEXT from Scout's input entirely, on the theory that Scout is a math agent and biographical context is what was expanding its reasoning surface. The plan was to translate ERA signal tags (`injury_mentioned`, `training_gap`, etc.) into synthetic conversation turns inside `streamer.py` before Scout ran, so Scout would only see standardised biometric + interview input.

This was not shipped. Two reasons:

1. **The hardening above closed the hallucination problem without removing context.** Once Step 7 verification and the Compliance shape check were in place, the benchmark stopped surfacing invented archetypes — and ERA_CONTEXT continued to produce *better* scouting results (more accurate life-stage alignment, more nuanced adaptive pathway selection) than the standardised-input alternative did in spot checks.
2. **The translation introduced its own loss surface.** Mapping `Signals: injury_mentioned, recovery_mode, returning_to_sport` to four synthetic English sentences would require the manifest's `interview_signals.strong_match` keywords to reliably match those phrasings — and the manifest signals are tuned for free-form user answers, not for the rigid Python-generated phrasings. The translation step would silently weaken signal scoring.

The instinct that "Scout is a math agent doing a non-math job" was probably still partly correct, but the right fix turned out to be making the math agent more rigid in its output (Step 7), not in its input. ERA_CONTEXT stays in Scout's context.

---

## What Changed — Files Touched

| File | Change |
|---|---|
| `backend/agents/instructions/scout.md` | MANDATORY CONSTRAINT block, Step 0 weight class filter, Step 7 output verification |
| `backend/api/streamer.py` | `_output_shape()`, compliance shape comparison + revert, `_PIPELINE_EMIT_TYPE` contract, `_games_name()` lookup, `[SYSTEM: CONTENT_RULES]` header |
| `backend/agents/data/content_rules.json` | New file — single source of truth for forbidden terms and eval criteria |
| `frontend/src/app/services/stream.service.ts` | `looksLikeResult()` strict shape detector, `era_ready_to_scout` signal discrimination |
| `frontend/src/app/services/state.service.ts` | `eraResultCache` + `restoreFromCache()`, `visitedYears$` stream, atomic clears in `setResult()`, loading-state clear inside `setActiveQuestion()` so torn-down stream observers can't leave a frozen spinner |
| `frontend/src/app/components/timeline.component.ts` | Cache-first click handler, visited-dot rendering |
| `backend/benchmark/run_benchmark.py` | `--regenerate <run>` flag to re-run the master evaluator on a completed run without re-running personas |
| `backend/.gcloudignore` + `backend/.dockerignore` | Excludes `benchmark/`, credentials, caches from the deployment image |

---

## Benchmark Impact

v4 did not chase a higher overall pipeline score — by v3c the score was already at 7.4 with zero compliance failures, and the defenses target hallucinations that the benchmark's eval criteria did not score harshly enough to surface in the aggregate number. The signal that v4 worked is qualitative:

- The "invented archetype name" failure mode was eliminated in the benchmark's per-persona JSONs (previously visible 1–2 times per 45-run sweep).
- The "compliance hallucination → wrong screen" failure mode was never observed in live use after the shape check was added; the trace sidebar shows the recovery event when it does fire.
- Time travel revisits became instant (no LLM round-trip on a previously visited year), which made the multi-era exploration loop usable as a demo feature rather than a 30-second-per-click test.

The first run that included the v4 changes (`2026-05-11_15-05-29`) scored 7.2 overall with `life_stage_coherence_tt = 8.4` across time travel hops. The slight overall dip versus 7.4 reflects the master evaluator catching premature interview truncation on three personas — a separate finding, captured as a follow-up improvement in the run's `report.md`.

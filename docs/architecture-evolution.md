# Architecture Evolution — v1 to v4

This document traces how the Gemini Scout pipeline changed across four architectural generations. Each change was driven by a concrete failure mode discovered in the live system.

---

## v1 — Supervisor Agent (Days 1–2)

The first design put a single LLM agent at the center of everything. It was the orchestrator, the router, and the decision-maker — calling sub-agents via ADK's `transfer_to_agent` whenever it needed to hand off work.

It failed almost immediately on any pipeline requiring more than one hop. SCOUTING needs scout → narrator → compliance in sequence; the supervisor called scout and then stopped. The user got raw JSON with no narrative. INTERVIEW worked only because it happened to need just one hop.

The root cause turned out to be a subtle ADK constraint: `transfer_to_agent` is a schema-only declaration, not a Python callable. ADK's Automatic Function Calling loop requires actual callables to keep executing. Without one, it runs the first sub-agent and treats the result as final.

Full investigation: [v1 detail](architecture/v1-supervisor-agent.md) · [Supervisor postmortem](supervisor-agent-postmortem.md)

---

## v2 — SequentialAgent (Day 3)

The fix was to stop asking an LLM to do a job Python could do in three lines. The Supervisor was removed entirely. Mode selection moved to `streamer.py`. Agent ordering moved to ADK's `SequentialAgent` — a deterministic Python loop with no LLM routing and no AFC.

This made the pipeline reliable. Every scouting run now executed all three agents in order, every time. Latency dropped (one fewer LLM call per request). Session state bugs from the supervisor era disappeared.

But reliability just revealed the next layer of problems. The first benchmark run against 15 personas surfaced gender hallucinations (wrong-gender adaptive events), duplicate standing/adaptive narratives, thin adaptive verdicts, and interview options that were functionally identical regardless of which one a user chose.

Full detail: [v2 detail](architecture/v2-sequential-agent.md)

---

## v3 — Instruction Tuning (Days 4–5)

v3 is not a new architecture — it's the same SequentialAgent pipeline with a series of targeted fixes applied to the agent instructions and the pathway manifest. Each fix addressed a specific failure mode surfaced by the benchmark.

The biggest structural change was adding gender-specific adaptive fields (`adaptive_M`/`adaptive_F`) and explicit `dimension` tags to the pathway manifest. These gave the Scout concrete values to copy instead of things to infer — and that distinction matters enormously for output correctness.

The other significant additions: a Compliance rewrite rule for thin adaptive narratives (previously advisory, now enforced), a Narrator constraint requiring the two pathways to argue from genuinely different athletic angles, and an Eval Agent that scores every scouting result across six dimensions and feeds a benchmark system for trend tracking.

Three sub-versions (v3a → v3b → v3c) each moved the benchmark meaningfully: from 5.5 overall at the v2 baseline to 7.4 at v3c, with distinctness going from 4.4 to 8.2.

Full detail: [v3 detail](architecture/v3-instruction-tuning.md)

---

## v4 — Hallucination Defenses (Days 6–7)

By v3c the benchmark was at 7.4 with zero compliance failures, but two failure modes still leaked through under live use that the scalar score did not penalise heavily:

- **Scout** occasionally invented archetype names not in the 14-profile manifest ("Tactical Scholar", "The Strategist") when biometric matches were ambiguous, and occasionally recommended weight classes physically incompatible with the user's weight.
- **Compliance** occasionally hallucinated entirely new content in time-travel interview mode — replacing a Narrator-authored era question with a fabricated scout-array, which the streamer then emitted to the frontend as a scouting result.

v4 closed both holes with a package of defenses rather than a new agent or pipeline restructure:

- **Scout output verification** — a MANDATORY CONSTRAINT block, a weight-class plausibility check at Step 0, and a Step 7 that verifies every output field character-for-character against the manifest before emitting JSON.
- **Compliance shape validation in `streamer.py`** — every JSON output is classified into a shape (`question`, `scout-array`, `era-signal`, etc.). Compliance is required to preserve the shape it received from Narrator. If shapes diverge, the Compliance output is discarded and Narrator's pre-compliance draft is used.
- **Pipeline emit contract** — the SSE event type (`result` vs `interview`) is now derived from the pipeline name, never from the output shape. A hallucinated scout-array inside `time_travel_pipeline` can no longer reach the result channel by mimicking its shape.
- **Frontend defensive parsing** — `looksLikeResult()` in `stream.service.ts` is a strict shape detector. `era_ready_to_scout` mid-stream signals are discriminated from question payloads before any state mutation.
- **Era result caching** — revisiting a Games year is instant; no second LLM round-trip, no narrative drift from LLM nondeterminism.
- **`CONTENT_RULES` header + canonical Games name lookup** — single source of truth for forbidden terms / eval criteria; `_games_name(year)` injects canonical Games names so Compliance no longer has to rewrite "The 2028 Games" → "The LA28 Games".

The instinct from an earlier proposal — "remove ERA_CONTEXT from Scout's input entirely" — was tried on paper and discarded. Hardening Scout's output verification (Step 7) closed the hallucination gap without giving up the additional context. The discarded proposal and the reasoning for not shipping it are documented in [v4 detail](architecture/v4-scout-input-standardisation.md).

The first benchmark run after v4 (`2026-05-11_15-05-29`) scored 7.2 overall with `life_stage_coherence` of 8.4 on time travel hops. The slight dip from v3c's 7.4 reflects the master evaluator surfacing a separate finding — premature interview truncation on three personas — that v4 did not target.

Full detail: [v4 detail](architecture/v4-scout-input-standardisation.md)

---

## Principles

A few things became clear across this process:

**LLM routing for deterministic pipelines is the wrong tool.** When you know the order at design time, enforce it in code.

**Schema-only tools disable the AFC loop.** `transfer_to_agent` is a FunctionDeclaration, not a callable. This is the root cause of every multi-hop failure in v1.

**Quality regressions need a measurement system, not intuition.** Without the benchmark, instruction changes would be invisible. With it, every change has a score delta attached.

**Structural constraints beat prompt instructions for correctness.** The gender hallucination wasn't fixable with a better filter instruction. It was fixed by putting the right value in the manifest so the agent could copy it rather than infer it.

**Session isolation matters.** `InMemorySessionService` accumulates function calls across requests. Fresh session IDs per request are required for stateless API behavior.

**Output verification beats output trust.** Once a benchmark caught Scout inventing archetype names, the fix that stuck was not a softer instruction — it was a hard `Step 7` that re-reads every output field against the manifest before allowing JSON emission. Instructing the model not to hallucinate is weaker than instructing it to verify.

**Defend at every layer.** The Compliance shape check, the pipeline emit contract, and the frontend's `looksLikeResult()` parser are three independent defenses against the same class of failure (a hallucinated payload reaching the user as the wrong screen). Each is cheap; together they make the failure structurally impossible. When the cost of a defense is low and the cost of the failure is high, redundancy is the right call.

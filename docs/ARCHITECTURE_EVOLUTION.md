# Architecture Evolution — v1 to v3

This document traces how the Gemini Scout pipeline changed from the initial design through three architectural generations. Each change was driven by a concrete failure mode discovered in the live system.

---

## v1 — Supervisor Agent (Days 1–2)

### Design

A single "Supervisor" LLM agent was the central orchestrator. It held all mode logic and called sub-agents via ADK's `transfer_to_agent` tool.

```
Request
  └── supervisor_agent
        ├── transfer_to_agent("narrator_agent")
        ├── transfer_to_agent("compliance_agent")
        └── [for SCOUTING]: transfer_to_agent("scout_agent")
                             transfer_to_agent("narrator_agent")
                             transfer_to_agent("compliance_agent")
```

### What Broke

SCOUTING required three sequential hops (scout → narrator → compliance). The pipeline always terminated after the first hop. The event trace always looked like:

```
supervisor → supervisor → scout_agent  [STOPPED]
```

Narrator was never called. The user received raw scout JSON with no narrative.

**Root cause:** ADK's `transfer_to_agent` is a `FunctionDeclaration` (schema-only), not a Python callable. Google ADK's Automatic Function Calling (AFC) loop requires Python callables to execute. With a schema-only tool, AFC was disabled — the supervisor made one transfer, the sub-agent ran and returned, and ADK treated that return as the final answer.

INTERVIEW worked coincidentally because it only required one real hop (narrator). Compliance was being called by the streamer as a post-loop synthetic step, not by the supervisor.

### What Was Tried

Eight approaches were exhausted before reaching this diagnosis. Full decision log: [`supervisor_agent_postmortem.md`](supervisor_agent_postmortem.md).

The key insight: `transfer_to_agent` is designed for *handoff* (permanent transfer of control), not *orchestration* (return result to caller, chain next step).

---

## v2 — SequentialAgent (Day 3)

### Design

Removed the Supervisor LLM entirely. Mode selection (which pipeline to run) moved to Python in `streamer.py`. Agent ordering moved to ADK's `SequentialAgent`, which uses a deterministic Python loop — no LLM routing, no AFC.

```
Python mode selection (streamer.py)
  ├── INTERVIEW:              SequentialAgent([narrator_agent, compliance_agent])
  ├── SCOUTING:               SequentialAgent([scout_agent, narrator_agent, compliance_agent])
  └── TIME_TRAVEL_INTERVIEW:  SequentialAgent([narrator_agent, compliance_agent])
```

Between agents, `output_key` on each `LlmAgent` writes its result to the ADK session state. The next agent reads it via `{output_key}` placeholders in its instruction template.

### What Improved

- SCOUTING pipeline now reliably executes all three agents in order, every time
- Removed one full LLM call per request (the supervisor), reducing latency
- Eliminated the session state accumulation bug (old supervisor replayed routing decisions from prior requests via `InMemorySessionService`; each request now runs a fresh session)
- Compliance correctly reviews the full narrated output, not raw scout JSON

### New Failure Modes Discovered (via benchmark)

With the pipeline now reliable, the first benchmark run (15 personas) revealed quality issues inside the agents themselves:

- **Gender hallucinations**: Scout was recommending "Men's +100kg Powerlifting" to 60kg female athletes. Root cause: `pathway_manifest.json` had gendered event examples hardcoded in the `adaptive` field; scout copied them verbatim.
- **Duplicate pathways**: Standing and adaptive results told the same story with different sport names. Root cause: no structural enforcement of dimension distinctness.
- **Thin adaptive narratives**: Some adaptive `scout_verdict` fields were 20 words vs 300-word standing verdicts. Root cause: compliance parity rule was advisory, not rewrite-on-violation.
- **Catch-all interview options**: Options like "balanced mix", "open to anything" produced interview data that couldn't meaningfully differentiate archetypes.

---

## v3 — Current (Days 4–5)

### Changes from v2

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

### Pipeline Quality — Full Benchmark History

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

### What each version changed

**v3a — Gender resolution + dimension enforcement**
- Added `adaptive_M` and `adaptive_F` fields to all 14 manifest profiles. Scout Step 0 now resolves the correct gender field before scoring — female athletes never get "Men's +100kg Powerlifting" events.
- Added explicit `dimension` field to every profile (`Power/Strength`, `Endurance`, `Precision/Technical`). Scout Step 6 reads the field directly and enforces that standing and adaptive picks have different dimension values.
- Added `AGE_OVERRIDE` awareness to Scout Step 1 so time-travel personas use their era age for peak_range alignment, not their current age.
- **Result**: +0.5 overall, compliance failures dropped from 3 → 0.

**v3b — Softened enforcement + compliance city fix + adaptive narrative rule**
- The v3a dimension enforcement was too rigid — "always pick different dimension regardless of score gap" forced physically contradictory adaptive picks (Decathlon for a 48yo SCI rower who asked for "singular signature movement"), hurting authenticity. Added a 15-point score threshold and an interview signal gate (S ≥ W required) before overriding dimension.
- Added a full year→city lookup table (1960–2044) to the compliance instruction so the agent can fix bare year references like "The 2028 Games" → "The LA28 Games" without guessing.
- Added Narrator Rule 6: when `pathway_adaptive` contains a sport classification code (T44, S10, F56, etc.), the verdict must name the classification, explain what it covers, and connect it to the user's specific adaptive profile.
- **Result**: +0.5 overall, distinctness +0.9, compliance fully clean.

**v3c — Eval calibration fix**
- Removed eval penalty for seasonal sport mismatches. The archetypes represent athletic dimensions, not season-specific sports — "Edge Carver" is about precision edge control at velocity, whether that maps to Alpine Skiing or Speed Skating is irrelevant to the archetype fit. Penalising for Brisbane (Summer) + Alpine Skiing was incorrect.
- **Result**: +0.9 overall, distinctness jumped to 8.2 (from 6.5), authenticity to 7.6.

---

## Architectural Principles Learned

**1. LLM routing for deterministic pipelines is the wrong tool.**
When you know the order at design time, enforce it in code. The Supervisor consumed one full LLM call per request to make a decision that could be expressed in three lines of Python.

**2. Schema-only tools disable the AFC loop.**
`transfer_to_agent` is a FunctionDeclaration, not a Python callable. AFC requires callables. This is the root cause of every multi-hop failure in v1.

**3. Quality regressions need a measurement system, not intuition.**
The benchmark system made quality changes measurable. Without it, improvements to the instruction files would be invisible — we'd be guessing. With it, each change has a score delta attached.

**4. Structural constraints beat prompt instructions for correctness.**
The gender hallucination problem wasn't fixable with a better filter instruction (we tried). It was fixed by adding `adaptive_M`/`adaptive_F` to the manifest so the correct value was *there to be copied* rather than *inferred*. Similarly, dimension distinctness is enforced by a manifest field, not LLM judgment.

**5. Session isolation matters.**
`InMemorySessionService` accumulates function calls across requests. This caused the supervisor to replay prior routing decisions, bypassing the LLM entirely on subsequent requests. Fresh session IDs per request are required for stateless API behavior.

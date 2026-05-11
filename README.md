# Gemini Scout — The Time-Traveling Talent Scout

> *Where do you fit in the Team USA story — and who could you have been across every era of the Games?*

A conversational AI scouting experience powered by Google Gemini and the Agent Development Kit. Built for the Team USA × Google Cloud Hackathon — **submitted for Challenge 5: Choose Your Own Fan-Centric Challenge**.

**Live app:** [gemini-scout.web.app](https://gemini-scout.web.app)

---

## The Experience — Three Acts

**Act 1 — The Great Interview**
A Narrator agent opens a warm, adaptive conversation. It asks 3–5 targeted questions about how you move, compete, and train — providing empathetic feedback on every answer. No form. No dropdown. A real conversation that builds a picture of your athleticism before any scouting begins.

**Act 2 — The Scout Report**
A 5-agent AI pipeline analyses your biometrics and interview answers against 14 named athletic archetypes derived from 120 years of Olympic history and Paralympic classification data. Two pathway cards are always returned: a **standing pathway** (conventional discipline) and an **adaptive pathway** (para-sport equivalent) — with equal narrative depth and prominence, always.

**Act 3 — The Time Machine**
After your result, a timeline bar shows every Games year where you'd have been eligible. Click any year and a Narrator asks one era-bridging biographical question — then a full new scout runs with your age at that time. The 1984 version of you gets a different result than the 2032 version. Cross-era memory accumulates so earlier hops inform later ones.

---

## Data Foundation — 120 Years of Olympic and Paralympic History

The 14 athletic archetypes at the heart of Gemini Scout were produced by running **K-means clustering** on **120 years of Olympic history (1896–2024)** and **International Paralympic Committee athlete classification data**. The clustering was performed offline on the full dataset to identify stable, physically meaningful athlete groupings — the 14 profiles are the direct output of that analysis, then named, enriched, and made narratable.

Each archetype profile encodes:
- **Biometric centroids** — height and weight cluster centres calibrated separately for male and female athletes from the historical dataset
- **Peak competitive age ranges** — derived from when athletes in each cluster family have historically peaked across the 120-year record
- **Interview signal keywords** — behavioural and lifestyle markers that distinguish one cluster from another in the real record
- **Gender-specific adaptive events** — `adaptive_M` and `adaptive_F` fields on every profile mapped to IPC classification standards, so recommended para-sport events are always correct for the user's gender

The deliberate choice to run clustering offline rather than at runtime is what makes the narrative experience possible. A runtime cluster number cannot have a name, a tone, a voice, or an equal adaptive pathway. Pre-derived, named archetypes can — and that is what allows the Narrator to write a personalised 2–4 paragraph story about *you*, not a data printout about cluster membership.

| Archetype | Dimension | Peak Age Range |
|---|---|---|
| Air Sculptor | Precision / Technical | 14 – 26 |
| Block Starter | Power / Strength | 18 – 28 |
| Bar Raiser | Power / Strength | 19 – 30 |
| Streamline | Endurance | 16 – 27 |
| Edge Carver | Precision / Technical | 16 – 32 |
| Net Presence | Precision / Technical | 18 – 33 |
| Mat Technician | Power / Strength | 18 – 33 |
| Swiss Army | Endurance | 21 – 32 |
| Boat Run | Endurance | 20 – 35 |
| Launch Force | Power / Strength | 22 – 36 |
| Road Machine | Endurance | 22 – 38 |
| Long Haul | Endurance | 20 – 38 |
| Iron Shoulder | Power / Strength | 22 – 40 |
| Steady Hand | Precision / Technical | 25 – 52 |

---

## What Makes Gemini Scout Different

### 1. A Real Multi-Agent Pipeline — Not a Single LLM Call

Five Gemini agents run in strict sequence on every scouting request, orchestrated by **Google ADK `SequentialAgent`** — deterministic Python execution with no LLM routing and no flaky orchestration.

```
browser (Angular 19)
    │  SSE stream
    ▼
FastAPI /scout endpoint — mode resolved in Python
    ▼
ADK SequentialAgent
    ├── INTERVIEW mode:              narrator_agent → compliance_agent
    ├── SCOUTING mode:               scout_agent → narrator_agent → compliance_agent → eval_agent
    └── TIME_TRAVEL_INTERVIEW mode:  narrator_agent (era mode) → compliance_agent

each step → logger_agent → Intelligence Trace sidebar
```

| Agent | Model | Role |
|---|---|---|
| **Scout** | `gemini-3.1-flash-lite` | Euclidean biometric matching + interview signal scoring against 14-profile manifest. Gender-resolves adaptive pathway. Enforces dimension distinctness. Step 7 output verification rejects manifest-invalid output before emit. |
| **Narrator** | `gemini-3.1-flash-lite` | Personalises scout output into a 2–4 paragraph narrative using the user's specific answers and profile tone. Runs era mini-interview in Time Travel mode. |
| **Compliance** | `gemini-3.1-flash-lite` | Enforces NIL rules, IOC brand terminology, and adaptive parity. Rewrites violations silently — users never see non-compliant output. Output shape is validated against Narrator's pre-compliance draft; if shapes diverge, the Compliance output is discarded and Narrator's draft is used. |
| **Eval** | `gemini-3.1-pro-preview` | Scores the completed result across 6 quality dimensions. Never modifies output — assessment only. Scores appear in the Judge's Vault. |
| **Logger** | `gemini-3.1-flash-lite` | Translates each agent's internal reasoning steps into plain English trace lines for the real-time sidebar. |

### 2. Paralympic Parity — Built Into the System, Not Bolted On

Every single scouting result returns two pathways of equal depth. This is not a design principle — it is a hard enforcement rule:

- The **Compliance agent** measures word count of both verdicts. If the adaptive pathway is absent, under 60 words, or less than 50% the length of the standing verdict, it **rewrites the adaptive narrative to full depth** before anything reaches the user.
- The **pathway manifest** has `adaptive_M` and `adaptive_F` fields on every profile. The Scout resolves the correct gender field before scoring begins — a 60kg female athlete never receives a "Men's +100kg Powerlifting" recommendation.
- The **Narrator** is explicitly instructed that when an adaptive pathway contains a sport classification code (T44, S10, F56, etc.), it must name the classification, explain what it covers, and connect it to the user's specific profile — the disability context is never a footnote.
- **8 of 15 benchmark personas are adaptive or para athletes** — including congenital limb difference, visual impairment, above-knee amputation, ALS, SCI wheelchair racing, Deafness, and goalball. Paralympic quality is measured, tracked, and scored on every pipeline run.

### 3. Time Travel — A Full Biographical Arc

No other submission lets a fan live their athletic story across time. The time travel feature:

- Shows the user every Games year they'd have been eligible for, coloured by life stage (Rising Star / Elite Peak / Veteran / Legacy)
- Triggers a biographical mini-interview before each era scout — questions about what life was asking of them in that era
- Applies an **AGE_OVERRIDE** so the archetype matching and narrative reflect who they were at that age, not who they are now
- Accumulates **cross-era memory** (`ERA_HISTORY`) — what the user shared at the 1992 Games informs the conversation at the 1996 Games
- Covers 1960 through 2044 — the full arc from Rome to Istanbul

### 4. Intelligence Trace — The AI's Reasoning Made Visible

A real-time sidebar shows every agent's internal reasoning as plain English. Not a status bar. Judges can follow the exact logical thread: which archetype scored highest and why, which interview signals reinforced it, whether compliance found a violation and what it rewrote, and what the eval agent scored the final result. This is a window into the pipeline, not a spinner.

### 5. Continuous Quality Measurement — A Benchmark Built for Regression Detection

Most hackathon projects have no way to know if a change improved or broke quality. Gemini Scout has a benchmark system that runs **15 pre-written personas** through the full live backend (real HTTP calls, not mocked), 3 rounds each, and produces a scored report with dimension averages and per-persona scorecards.

The Eval Agent scores every result across 6 dimensions: Authenticity, Personalization, Interview Quality, Pathway Distinctness, Life-Stage Coherence, and Compliance. Scores are tracked in `history.jsonl` across versions.

**Benchmark score progression:**

| Version | Overall | Authenticity | Personalization | Interview Quality | Distinctness | Compliance |
|---|---|---|---|---|---|---|
| v2 baseline | 5.5 | 5.4 | 8.0 | 6.7 | 4.4 | 15/15 |
| v3a | 6.0 | 6.3 | 8.3 | 7.3 | 5.2 | 15/15 |
| v3b | 6.5 | 5.9 | 7.9 | 7.6 | 6.1 | 45/45 |
| v3c | 7.4 | 7.6 | 8.0 | 7.6 | 8.2 | 45/45 |
| **v4 (current)** | **7.2** | **7.5** | **7.9** | **6.8** | **8.2** | **15/15** |

Baseline → current: **+1.7 overall · +2.1 authenticity · +3.8 distinctness · zero compliance failures.** v4's dip in interview quality reflects a new finding the master evaluator surfaced (premature interview truncation on three personas) — captured as a follow-up; the hallucination defenses introduced in v4 are not measured by the scalar score.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Angular 19, TypeScript, CSS custom properties |
| **Backend** | FastAPI (Python), Server-Sent Events (SSE) |
| **AI / Agents** | Google ADK `SequentialAgent` + `LlmAgent`, `gemini-3.1-flash-lite` (Scout, Narrator, Compliance, Logger) + `gemini-3.1-pro-preview` (Eval) |
| **Hosting** | Firebase Hosting (frontend), Google Cloud Run (backend) |
| **Auth** | Google Application Default Credentials via Vertex AI |

---

## Compliance

| Rule | Status | How it's enforced |
|---|---|---|
| No NIL (individual athlete names / likenesses) | ✓ PASS | Archetype-only output; Compliance agent blocks any name reference |
| No IOC branding ("Olympic", "Paralympic" as standalone terms) | ✓ PASS | Compliance instruction + word-level replacement |
| Games format ("The [City] [Year] Games") | ✓ PASS | Narrator instruction + Compliance catches violations; 30-year lookup table covers 1960–2044 |
| Adaptive / standing parity | ✓ PASS | Compliance rewrites adaptive verdict if absent, <60 words, or <50% standing length |
| Gender-correct adaptive events | ✓ PASS | `adaptive_M` / `adaptive_F` resolved at Scout Step 0 before scoring begins |
| No finish times or specific scoring data | ✓ PASS | Placements and medals only in all legacy references |
| No PII stored | ✓ PASS | No database; all conversation state is per-session in memory only |

---

## Architecture Documentation

The engineering decisions behind Gemini Scout are fully documented — including failures, root causes, and what was learned.

| Document | What It Covers |
|---|---|
| [`docs/for-judges.md`](docs/for-judges.md) | Direct mapping of every feature to judging criteria |
| [`docs/architecture-evolution.md`](docs/architecture-evolution.md) | How the pipeline evolved from v1 (Supervisor LLM) → v4 (hallucination defenses) |
| [`docs/architecture/v1-supervisor-agent.md`](docs/architecture/v1-supervisor-agent.md) | Why the Supervisor failed — the ADK `transfer_to_agent` root cause |
| [`docs/architecture/v2-sequential-agent.md`](docs/architecture/v2-sequential-agent.md) | SequentialAgent design and the failure modes it exposed |
| [`docs/architecture/v3-instruction-tuning.md`](docs/architecture/v3-instruction-tuning.md) | All 11 instruction changes with benchmark score deltas + agent context reference table |
| [`docs/architecture/v4-scout-input-standardisation.md`](docs/architecture/v4-scout-input-standardisation.md) | Hallucination defenses — Scout output verification, Compliance shape validation, frontend defensive parsing, era result caching |
| [`docs/supervisor-agent-postmortem.md`](docs/supervisor-agent-postmortem.md) | Full postmortem on 8 failed approaches before the Supervisor was removed |
| [`docs/time-travel.md`](docs/time-travel.md) | Time travel — headers, flow, era memory, state management |
| [`docs/logger.md`](docs/logger.md) | Intelligence Trace — design and trace format spec |
| [`backend/benchmark/README.md`](backend/benchmark/README.md) | Benchmark system — personas, running, output format |

---

## Running Locally

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
ng serve
```

**Benchmark** (requires backend running):
```bash
cd backend
source venv/bin/activate
python -m benchmark.run_benchmark
```

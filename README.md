# Gemini Scout — Time-Traveling Talent Scout

A conversational AI sports scouting experience powered by Google Gemini and the Agent Development Kit. Built for the Team USA × Google Cloud Hackathon.

**Live app:** [gemini-scout.web.app](https://gemini-scout.web.app)

---

## What It Does

Gemini Scout discovers what kind of athlete you are — and who you could have been across every era of the Games. In three acts:

**Act 1 — The Great Interview**
A Narrator agent leads a warm, adaptive conversation. It asks 3–5 targeted questions, provides empathetic feedback, and builds a picture of your athleticism before any scouting begins.

**Act 2 — The Scout Report**
A 5-agent pipeline analyzes your biometrics and interview answers against a 14-profile athletic archetype manifest. Two pathways are always returned: a **standing pathway** (conventional discipline) and an **adaptive pathway** (para-sport equivalent) — with equal narrative depth and prominence.

**Act 3 — The Time Machine**
After seeing your result, a timeline bar shows every Games year where you'd have been eligible. Click any year and the Narrator asks one era-bridging question before running a new full scout with your age at that time. Cross-era memory accumulates — your 2028 context informs your 2032 conversation.

---

## Key Features

| Feature | Description |
|---|---|
| **14-Profile Archetype Manifest** | Physics-grounded profiles (Air Sculptor, Long Haul, Block Starter, etc.) with Euclidean centroid matching + interview signal scoring |
| **Gender-Resolved Adaptive Pathways** | Every profile has `adaptive_M` and `adaptive_F` variants — no wrong-gender event recommendations |
| **Dimension Enforcement** | Each profile has an explicit `dimension` tag (Power/Strength, Endurance, Precision/Technical). Standing and adaptive picks are always from different dimensions. |
| **Time Travel** | Full biographic arc — user can jump to past and future eras, each triggering a new mini-interview + scout with AGE_OVERRIDE |
| **Cross-Era Memory** | `ERA_HISTORY` system header accumulates context across time travel stops |
| **Intelligence Trace** | Real-time sidebar showing each agent's internal reasoning as plain English |
| **Eval Agent** | Post-scouting evaluation agent scores every result on Authenticity, Personalization, Interview Quality, Pathway Distinctness, Life-Stage Coherence, and Compliance |
| **Pipeline Benchmark** | 15 pre-written personas run through the live backend end-to-end; produces timestamped score reports and trend history for continuous improvement |
| **Compliance Gate** | Silently enforces NIL rules, IOC brand terminology, and adaptive/standing parity on every response before it reaches the user |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Angular 19, TypeScript, CSS custom properties |
| **Backend** | FastAPI (Python), Server-Sent Events (SSE) |
| **AI / Agents** | Google ADK `SequentialAgent` + `LlmAgent`, Gemini 2.5 Flash / Pro |
| **Hosting** | Firebase Hosting (frontend), Google Cloud Run (backend) |
| **Credentials** | Google Application Default Credentials via Vertex AI |

---

## Architecture

```
Browser (Angular 19)
  │  SSE stream
  ▼
FastAPI /scout endpoint
  │  mode resolved in Python (INTERVIEW / SCOUTING / TIME_TRAVEL_INTERVIEW)
  ▼
ADK SequentialAgent Pipeline
  ├── INTERVIEW mode:      narrator_agent → compliance_agent
  ├── SCOUTING mode:       scout_agent → narrator_agent → compliance_agent → eval_agent
  └── TIME_TRAVEL_INTERVIEW: narrator_agent (era mode) → compliance_agent

Each agent step streams a trace event → Logger Agent → Intelligence Trace sidebar
```

### Agent Responsibilities

| Agent | Role |
|---|---|
| **Scout** | Euclidean distance matching across 14 archetype profiles. Gender-resolves adaptive pathway. Enforces dimension distinctness. |
| **Narrator** | Personalizes scout output into 2–4 paragraph stories using interview answers and profile tone. In time travel mode, asks one era-bridging question. |
| **Compliance** | Enforces NIL rules, IOC brand terminology, and adaptive parity. Rewrites violations silently. |
| **Eval** | Scores the completed pipeline result across 6 dimensions. Never modifies output — assessment only. |
| **Logger** | Translates each agent's internal steps into human-readable trace lines for the sidebar. |

---

## Data Model

- **`pathway_manifest.json`** — 14 athletic archetypes, each with biometric centroids (M/F split), keyword signals, and gender-specific adaptive pathway examples
- **`games_manifest.json`** — Games years, host cities, and era metadata for the timeline
- **`legacy_facts.json`** — Historical achievement context used by Narrator
- **`system_constraints.json`** — Compliance reference data

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

**Pipeline Benchmark** (backend running required):
```bash
cd backend
source venv/bin/activate
python -m benchmark.run_benchmark
```
See `backend/benchmark/README.md` for full benchmark documentation.

---

## Pipeline Quality

The benchmark system runs 15 diverse personas (including adaptive athletes, time-travel edge cases, and hostile inputs) through the full live pipeline — 3 rounds each, 45 total runs. Current scores (latest run, 45/45 succeeded):

| Dimension | Score | Baseline | Change |
|---|---|---|---|
| Authenticity | 7.6 / 10 | 5.4 | +2.2 |
| Personalization | 8.0 / 10 | 8.0 | — |
| Interview Quality | 7.6 / 10 | 6.7 | +0.9 |
| Pathway Distinctness | 8.2 / 10 | 4.4 | +3.8 |
| **Overall Pipeline** | **7.4 / 10** | **5.5** | **+1.9** |

Score history is tracked in `backend/benchmark/results/history.jsonl`. The benchmark is run after every significant change to detect regressions.

---

## Compliance

- No individual athlete names, images, or likenesses anywhere in the pipeline
- Games always referenced as "The [City] [Year] Games" — never "Olympic" or "Paralympic" as standalone terms
- Standing and adaptive pathways always receive equal narrative depth
- No finish times or specific scoring — placements and medals only
- No PII collected or stored

---

## Docs

| Document | What It Covers |
|---|---|
| [`docs/FOR_JUDGES.md`](docs/FOR_JUDGES.md) | Direct mapping of features to hackathon judging criteria |
| [`docs/ARCHITECTURE_EVOLUTION.md`](docs/ARCHITECTURE_EVOLUTION.md) | How the architecture changed from v1 (Supervisor) to v3 (SequentialAgent + Eval) |
| [`docs/LIVING_LEGACY_ARCH.md`](docs/LIVING_LEGACY_ARCH.md) | Current multi-agent architecture reference |
| [`docs/supervisor_agent_postmortem.md`](docs/supervisor_agent_postmortem.md) | Why the Supervisor LLM was removed — engineering postmortem |
| [`docs/time_travel.md`](docs/time_travel.md) | Time travel feature — headers, flow, state management |
| [`docs/logger.md`](docs/logger.md) | Intelligence Trace logger — design and trace format spec |
| [`backend/benchmark/README.md`](backend/benchmark/README.md) | Benchmark system — personas, running, output format |

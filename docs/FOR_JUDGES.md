# Gemini Scout — For Judges

This document maps the project directly to the hackathon judging criteria and points you to the most interesting parts of the codebase.

---

## Judging Criteria Breakdown

### 1. Impact (40%)

**Fan-Centric problem being solved:**
Most sports fan engagement tools are passive — stats, standings, recaps. Gemini Scout answers a question fans actually ask: *"Where do I fit in the Team USA story?"* It makes every person the protagonist of their own athletic legacy, regardless of ability or age.

**Paralympic parity (enforced at the system level):**
This is not a checkbox. The Compliance agent has a hard rule: if the adaptive `scout_verdict` is absent, under 60 words, or less than 50% the length of the standing verdict, it *rewrites the adaptive narrative to full depth* before anything reaches the user. See [`backend/agents/instructions/compliance.md`](../backend/agents/instructions/compliance.md) Rule 4.

Every scout result always returns exactly two pathway cards — standing and adaptive — with equal narrative richness. The pathway manifest has 14 profiles, each with gender-specific adaptive event examples (`adaptive_M` and `adaptive_F` fields) so the recommended event is always the right gender for the user.

**Visionary element — The Time Machine:**
The timeline feature lets users explore their entire athletic arc across Games history and into the future. This isn't a re-run of the same query — each era jump triggers a mini-interview, accumulates cross-era context, and applies an age override so the scout result genuinely reflects that life stage. A 22-year-old seeing themselves as a 45-year-old Veteran at the 2048 Games is a meaningfully different result, not just a relabeled copy.

---

### 2. Technical Depth & Execution (30%)

**Functionality — 15-persona pipeline benchmark:**
The project includes an automated benchmark system that runs 15 diverse pre-written personas through the full live backend (HTTP, not mocked) and produces a scored report. This is our primary regression guard. See `backend/benchmark/README.md`.

Latest benchmark run: 15 personas × 3 rounds = 45 runs. Overall pipeline score: 6.0/10. Score history is tracked in `backend/benchmark/results/history.jsonl`.

**Gemini integration — multi-agent reasoning chain:**
Five Gemini agents run in sequence on every scouting request:

```
scout_agent → narrator_agent → compliance_agent → eval_agent
                                                       ↑
                                    (+ logger_agent called after each step)
```

- **Scout** uses `gemini-2.5-flash` to perform structured biometric matching with a 14-profile manifest
- **Narrator** uses `gemini-2.5-flash` to personalize the scout's technical output into a compelling 2–4 paragraph narrative
- **Compliance** uses `gemini-2.5-flash` to enforce IOC brand rules and adaptive parity silently
- **Eval** uses `gemini-2.5-pro-preview` to score the completed result across 6 dimensions — it never modifies output
- **Logger** uses `gemini-3.1-flash-lite` to translate internal agent reasoning into plain English for the sidebar

All agents run via **Google ADK `SequentialAgent`** — deterministic Python sequencing with `output_key` passing between agents. No LLM routing; no flaky orchestration.

Key files:
- [`backend/agents/pipeline.py`](../backend/agents/pipeline.py) — pipeline assembly
- [`backend/api/streamer.py`](../backend/api/streamer.py) — SSE orchestration and mode selection
- [`backend/agents/instructions/`](../backend/agents/instructions/) — all agent instructions as Markdown

**Google Cloud deployment:**
- Backend: Google Cloud Run (containerized FastAPI)
- Frontend: Firebase Hosting
- Auth: Google Application Default Credentials via Vertex AI

**Innovation — Dimension-enforced pathway matching:**
The pathway manifest has an explicit `dimension` field on every profile (`Power/Strength`, `Endurance`, or `Precision/Technical`). The scout instruction reads these fields directly to enforce that standing and adaptive picks are always from *different* dimensions. This is structural — no LLM judgment call involved. See [`backend/agents/data/pathway_manifest.json`](../backend/agents/data/pathway_manifest.json).

**Innovation — Gender-resolved adaptive pathways:**
The same manifest has `adaptive_M` and `adaptive_F` fields on every profile. Step 0 of the scout resolves the correct field before any scoring happens, so a 60kg female athlete never gets assigned a "Men's +100kg Powerlifting" event. This was the most critical quality fix identified by the benchmark system. See [`backend/agents/instructions/scout.md`](../backend/agents/instructions/scout.md).

**Innovation — Eval agent as continuous quality feedback:**
The eval agent runs on every scouting result and scores across 6 dimensions. These scores appear in the frontend Judge's Vault and feed the benchmark master evaluator. The benchmark system tracks score history across runs, making quality regressions visible. See [`backend/agents/instructions/eval.md`](../backend/agents/instructions/eval.md).

---

### 3. Presentation Quality (30%)

**UX flow:**
1. Landing → enter biometrics (height, weight, birth year, gender — optional)
2. Conversational interview (3–5 questions with multiple-choice chips and free-text)
3. Scout result with two pathway cards, life stage badge, and Judge's Vault
4. Timeline bar with Games years colored by life stage
5. Click any year → era question → new result

**Intelligence Trace sidebar:**
Every agent step produces a human-readable trace line in the sidebar. This is a window into the pipeline's reasoning, not a status bar. Judges can follow the exact logical thread: which archetype was matched and why, what interview signals reinforced it, whether compliance found a violation and what it did about it. See [`docs/logger.md`](logger.md).

**Compliance — what the user never sees:**
The compliance agent silently rewrites violations before output reaches the frontend. Standalone "Olympic" → "elite sport pathway". Thin adaptive verdict → full rewrite to match standing depth. The user always gets clean, compliant output; the Judge's Vault shows the diff.

---

## Where to Find What

| What you want to see | Where to look |
|---|---|
| Agent instruction prompts (the real work) | `backend/agents/instructions/*.md` |
| Agent Python wrappers | `backend/agents/*.py` |
| Sequential pipeline assembly | `backend/agents/pipeline.py` |
| SSE streaming + mode selection | `backend/api/streamer.py` |
| 14-profile archetype manifest | `backend/agents/data/pathway_manifest.json` |
| Benchmark personas (15 edge cases) | `backend/benchmark/personas/*.json` |
| Benchmark report (latest run) | `backend/benchmark/results/` (most recent folder) |
| Score history | `backend/benchmark/results/history.jsonl` |
| Frontend components | `frontend/src/app/components/` |
| Architecture postmortem (Supervisor removal) | `docs/supervisor_agent_postmortem.md` |
| Architecture evolution (v1 → v3) | `docs/ARCHITECTURE_EVOLUTION.md` |

---

## Compliance Checklist

| Rule | Status | Implementation |
|---|---|---|
| No NIL (individual athletes) | PASS | Archetype-only results; compliance agent blocks name references |
| No IOC branding | PASS | No rings, torch, or logos anywhere in codebase or output |
| Terminology ("The [City] [Year] Games") | PASS | Narrator instruction enforced + compliance agent catches violations |
| No "Former/Past Olympian/Paralympian" | PASS | Compliance instruction explicitly blocks this phrase |
| Adaptive parity (equal depth) | PASS | Compliance agent enforces 60-word minimum + 50% length parity |
| No finish times / specific scoring | PASS | Only placements and medals in legacy references |
| No PII stored | PASS | No database; conversation state is per-session in memory only |
| Gender-correct adaptive events | PASS | `adaptive_M`/`adaptive_F` fields resolve at scout Step 0 |

# Pipeline Benchmark

Runs a set of pre-written user personas through the **live backend** end-to-end:
interview → scouting → eval. Produces a timestamped report and tracks the
pipeline score across runs so you can see quality change as the code evolves.

---

## Prerequisites

1. The backend server must be running before you start.
2. All normal backend dependencies must be installed (`pip install -r requirements.txt`).
3. Credentials must be in place (`scout-credentials.json` or `GOOGLE_APPLICATION_CREDENTIALS`).
4. **Use the project venv** — the benchmark uses `httpx` which is installed there, not in the system Python.

---

## Starting the backend

From the `backend/` directory:

```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Leave it running, then open a second terminal for the benchmark.

---

## Running the benchmark

All commands run from the `backend/` directory with the venv active.

```bash
source venv/bin/activate
```

### Full run — all personas, 1 round each (default)

```bash
python -m benchmark.run_benchmark
```

### Multiple rounds per persona

```bash
# 3 rounds each — surfaces reliability issues and question variance
python -m benchmark.run_benchmark --rounds 3

# Single persona, 5 rounds — deep dive on one edge case
python -m benchmark.run_benchmark --persona 03_adaptive --rounds 5
```

Each round gets a different narrator question set (LLM is non-deterministic). The report shows average scores and the min–max range per persona, making inconsistency visible.

Output files are named `{persona_id}_r1.json`, `{persona_id}_r2.json`, etc.

### Control concurrency

```bash
# 3 concurrent runs (default is all at once)
python -m benchmark.run_benchmark --rounds 3 --parallel 3
```

### Single persona (faster — good for debugging one edge case)

```bash
python -m benchmark.run_benchmark --persona 03_adaptive
python -m benchmark.run_benchmark --persona 05_youth
```

The `--persona` flag matches by substring against the persona `id` field.

### Custom backend URL

```bash
python -m benchmark.run_benchmark --url http://localhost:8080
```

---

## Output

Every run creates a timestamped folder inside `benchmark/results/`:

```
benchmark/results/
  2026-05-10_14-32-01/
    01_young_female_swimmer.json      ← conversation log + scouting result + eval scores
    02_tall_power_athlete.json
    03_adaptive_visual_impairment.json
    04_veteran_endurance_runner.json
    05_youth_time_travel_2032.json
    summary.json                      ← all results + master LLM analysis
    report.md                         ← human-readable report (paste into Slack / show at demo)
  history.jsonl                       ← one line per run for trend tracking
```

Per-persona files are written immediately as each persona completes, so a partial
run is always recoverable.

### Reading the report

Open `results/TIMESTAMP/report.md`. It contains:

- **Overall pipeline score** (1–10, holistic LLM judgment)
- **Dimension averages** — Authenticity, Personalization, Interview Quality, Pathway Distinctness
- **Per-persona scorecard** — one row per persona with all dimension scores
- **Strengths / Weaknesses / Critical Issues** — cited by persona ID
- **Suggested improvements** — actionable, specific

### Tracking score over time

`results/history.jsonl` has one JSON line per run:

```json
{"timestamp": "2026-05-10_14-32-01", "pipeline_score": 7.2, "authenticity": 8.1, "personalization": 6.3, "interview_quality": 4.8, "distinctness": 7.5, "persona_count": 5, "success_count": 5}
```

Quick score history in the terminal:

```bash
cat benchmark/results/history.jsonl | python -c "
import sys, json
for line in sys.stdin:
    r = json.loads(line)
    ps = r.get('pipeline_score')
    score = f'{ps:.1f}' if ps else 'N/A'
    print(f\"{r['timestamp']}  score={score}  IQ={r.get('interview_quality', '—')}  auth={r.get('authenticity', '—')}\")
"
```

---

## Personas

| # | File | Label | Age | Disability / Edge Case | Time Travel |
|---|------|-------|-----|----------------------|-------------|
| 01 | `01_young_female_swimmer.json` | Young female swimmer | 17 | — | — |
| 02 | `02_tall_power_athlete.json` | Tall male power athlete | 24 | — | — |
| 03 | `03_adaptive_visual_impairment.json` | Partial visual impairment | 28 | Partial blindness (right eye) | — |
| 04 | `04_veteran_endurance_runner.json` | Veteran ultramarathon runner | 42 | — | — |
| 05 | `05_youth_time_travel_2032.json` | Youth gymnast | 16 | — | 2032 (future, age 22) |
| 06 | `06_hostile_ex_boxer.json` | Hostile ex-boxer | 31 | **Badmouths Olympics + Google** | — |
| 07 | `07_congenitally_blind_goalball.json` | Goalball / tandem cyclist | 34 | **Totally blind since birth** | — |
| 08 | `08_above_knee_amputee_sprinter.json` | Para-sprinter | 26 | **Above-knee amputee (right leg)** | — |
| 09 | `09_congenital_limb_difference_swimmer.json` | Adaptive swimmer | 29 | **Missing left forearm (congenital)** | — |
| 10 | `10_early_stage_als.json` | Former tennis player | 45 | **Early-stage ALS** | — |
| 11 | `11_retired_gymnast_time_travel_1984.json` | Retired gymnastics coach | 68 | — | **1984 PAST (age 26)** |
| 12 | `12_para_rower_time_travel_2036.json` | Para-rower (SCI) | 38 | T6 spinal cord injury | **2036 FUTURE (age 48)** |
| 13 | `13_wheelchair_racer_paraplegic.json` | Wheelchair racer | 22 | **T4 complete paraplegia** | — |
| 14 | `14_deaf_sprinter.json` | 400m sprinter | 25 | **Profoundly deaf** | — |
| 15 | `15_powerlifter_high_bmi.json` | Competitive powerlifter | 35 | High BMI (142 kg, mostly muscle) | — |

### Adding a new persona

Create a JSON file in `benchmark/personas/` following this schema:

```json
{
  "id": "06_my_new_persona",
  "label": "Short human-readable label",
  "description": "Detailed character description — background, sport history, preferences, how they answer questions. The more specific, the more authentic the simulated answers.",
  "height_cm": 170,
  "weight_kg": 68,
  "birth_year": 1995,
  "gender": "F",
  "target_game_year": null,
  "max_questions": 4
}
```

For a time travel persona, add:

```json
  "target_game_year": 2032,
  "time_travel_trigger_after": 2
```

This tells the runner to do `time_travel_trigger_after` normal interview questions,
then one TIME_TRAVEL_INTERVIEW question for the target year, then scout.

---

## How a run works

```
All personas run in parallel (asyncio.gather):

  Each persona independently:
  1. POST /scout  (biometrics, no history)           → narrator asks Q1
  2. Answer LLM picks an answer for this persona
  3. POST /scout  (history: Q1+A1)                   → narrator asks Q2
  4. ... repeat up to max_questions ...
  5. POST /scout  (is_ready_to_scout: true)           → scouting pipeline runs
                                                        eval agent runs (same as real user)
  6. Write persona result file immediately on completion

After all personas finish:
  7. Master evaluator LLM reads all eval results
  8. Writes summary.json + report.md
  9. Appends one line to history.jsonl
```

Within a single persona the turns are still sequential (each question depends on the
previous answer). Parallelism is across personas, not within one.

The **answer LLM** (`gemini-3.1-flash-lite`) reads the narrator's actual question
and options, then picks the most authentic answer for the persona's description.
Everything else is the real pipeline — no mocking.

---

## Recommended workflow

**Before a demo:**
```bash
python -m benchmark.run_benchmark
# Review report.md — fix any critical issues before presenting
```

**After a significant code change:**
```bash
python -m benchmark.run_benchmark
# Compare pipeline_score to previous run in history.jsonl
```

**Quick sanity check (one persona, ~3 min):**
```bash
python -m benchmark.run_benchmark --persona 01_young
```

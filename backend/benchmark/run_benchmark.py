"""
Gemini Scout Pipeline Benchmark
================================
Runs every persona in benchmark/personas/ through the live backend, collects
eval results, and writes a timestamped report to benchmark/results/.

Usage (from the backend/ directory):
    python -m benchmark.run_benchmark
    python -m benchmark.run_benchmark --url http://localhost:8000
    python -m benchmark.run_benchmark --persona 03_adaptive_visual_impairment

The backend server must be running before you start the benchmark.
Each run appends one line to benchmark/results/history.jsonl for trend tracking.
"""
import os
import sys
import json
import glob
import asyncio
import logging
import argparse
import datetime

# ── Bootstrap: ensure backend/ is on the path and env vars are set ──
_BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR   = os.path.dirname(_BENCHMARK_DIR)
sys.path.insert(0, _BACKEND_DIR)

os.environ.setdefault("GOOGLE_GENAI_USE_ENTERPRISE", "true")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "geminiscoutteamusa")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")

_creds = os.path.join(_BACKEND_DIR, "scout-credentials.json")
if os.path.isfile(_creds):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _creds

from benchmark.session_runner import run_persona          # noqa: E402
from benchmark.master_evaluator import (                  # noqa: E402
    generate_master_report,
    generate_markdown_report,
    _dim_avg,
    _dim_avg_tt,
)

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("benchmark")


def _load_personas(personas_dir: str, filter_id: str | None = None) -> list:
    files = sorted(glob.glob(os.path.join(personas_dir, "*.json")))
    if not files:
        raise FileNotFoundError(f"No persona files found in {personas_dir}")
    personas = []
    for f in files:
        with open(f) as fp:
            p = json.load(fp)
        if filter_id and filter_id not in p.get("id", ""):
            continue
        personas.append(p)
    if filter_id and not personas:
        raise ValueError(f"No persona matched filter '{filter_id}'")
    return personas


async def _run(backend_url: str, personas: list, results_dir: str, parallel: int = 0, rounds: int = 1) -> str:
    run_ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = os.path.join(results_dir, run_ts)
    os.makedirs(run_dir, exist_ok=True)

    # 0 means "all at once"; semaphore is per (persona × round) task
    total_tasks = len(personas) * rounds
    concurrency = total_tasks if parallel == 0 else max(1, parallel)
    mode_label = "all parallel" if concurrency >= total_tasks else f"{concurrency} at a time"

    logger.info("")
    logger.info("╔══════════════════════════════════════════════╗")
    logger.info("║  GEMINI SCOUT PIPELINE BENCHMARK             ║")
    logger.info("╚══════════════════════════════════════════════╝")
    logger.info("  Backend     : %s", backend_url)
    logger.info("  Personas    : %d  ×  %d round%s  =  %d total runs",
                len(personas), rounds, "s" if rounds != 1 else "", total_tasks)
    logger.info("  Concurrency : %s", mode_label)
    logger.info("  Output      : %s", run_dir)
    logger.info("")

    semaphore = asyncio.Semaphore(concurrency)

    async def _run_one(persona: dict, round_num: int) -> dict:
        async with semaphore:
            round_label = f"r{round_num}/{rounds}" if rounds > 1 else ""
            logger.info("━━━ START  %s  %s(%s) ━━━", persona["id"], f"[{round_label}] " if round_label else "", persona["label"])
            try:
                result = await run_persona(persona, backend_url)
            except Exception as exc:
                logger.error("FAILED  persona=%s  round=%d  error=%s", persona["id"], round_num, exc, exc_info=True)
                result = {
                    "persona_id": persona["id"],
                    "persona_label": persona["label"],
                    "error": str(exc),
                    "conversation_log": [],
                    "scouting_result": None,
                    "eval_result": None,
                }

            result["round"] = round_num

            suffix = f"_r{round_num}" if rounds > 1 else ""
            out_path = os.path.join(run_dir, f"{persona['id']}{suffix}.json")
            with open(out_path, "w") as f:
                json.dump(result, f, indent=2, default=str)
            logger.info("━━━ DONE   %s  [r%d]  → wrote %s", persona["id"], round_num, out_path)
            return result

    tasks = [
        _run_one(p, r)
        for p in personas
        for r in range(1, rounds + 1)
    ]
    results = list(await asyncio.gather(*tasks))

    # ── Master report ──
    logger.info("Generating master report…")
    successful = [r for r in results if not r.get("error") and r.get("eval_result")]
    if not successful:
        logger.warning("No successful persona results — skipping master evaluator LLM call")
        master = {
            "pipeline_score": None,
            "run_summary": "All personas failed or returned no eval.",
            "strengths": [], "weaknesses": [],
            "critical_issues": [], "suggested_improvements": [],
            "dimension_analysis": {},
        }
    else:
        master = await generate_master_report(successful)

    # Write summary.json
    summary = {
        "run_timestamp": run_ts,
        "backend_url": backend_url,
        "persona_count": len(personas),
        "rounds": rounds,
        "total_runs": total_tasks,
        "success_count": len(successful),
        "master": master,
        "results": results,
    }
    with open(os.path.join(run_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)

    # Write report.md
    report_md = generate_markdown_report(results, master, run_ts)
    report_path = os.path.join(run_dir, "report.md")
    with open(report_path, "w") as f:
        f.write(report_md)

    # Append to history.jsonl (one line per run for trend tracking)
    history_entry: dict = {
        "timestamp": run_ts,
        "pipeline_score": master.get("pipeline_score"),
        "persona_count": len(personas),
        "rounds": rounds,
        "total_runs": total_tasks,
        "success_count": len(successful),
    }
    for dim in ["authenticity", "personalization", "interview_quality", "distinctness"]:
        history_entry[dim] = _dim_avg(successful, dim)
    history_entry["life_stage_coherence_tt"] = _dim_avg_tt(successful, "life_stage_coherence")

    history_path = os.path.join(results_dir, "history.jsonl")
    with open(history_path, "a") as f:
        f.write(json.dumps(history_entry) + "\n")

    # ── Final summary ──
    ps = master.get("pipeline_score")
    logger.info("")
    logger.info("╔══════════════════════════════════════════════╗")
    score_line = f"  Pipeline score: {ps:.1f} / 10" if ps is not None else "  Pipeline score: N/A"
    logger.info("║  %-44s║", score_line)
    runs_label = f"{total_tasks} runs ({len(personas)}p × {rounds}r) — {len(successful)} succeeded"
    logger.info("║  %-44s║", f"  {runs_label}")
    logger.info("╠══════════════════════════════════════════════╣")
    logger.info("║  report.md  → %s", report_path)
    logger.info("║  history    → %s", history_path)
    logger.info("╚══════════════════════════════════════════════╝")

    return report_md


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gemini Scout Pipeline Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--url", default="http://localhost:8000",
        help="Backend base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--personas", default=os.path.join(_BENCHMARK_DIR, "personas"),
        help="Directory containing persona JSON files",
    )
    parser.add_argument(
        "--results", default=os.path.join(_BENCHMARK_DIR, "results"),
        help="Directory to write run results into",
    )
    parser.add_argument(
        "--persona", default=None,
        help="Run a single persona by ID substring (e.g. '03_adaptive')",
    )
    parser.add_argument(
        "--parallel", type=int, default=0,
        help="Max concurrent runs. 0 (default) = all in parallel. 1 = sequential.",
    )
    parser.add_argument(
        "--rounds", type=int, default=1,
        help="How many times to run each persona (default 1). Each round gets different narrator questions.",
    )
    args = parser.parse_args()

    os.makedirs(args.results, exist_ok=True)
    personas = _load_personas(args.personas, filter_id=args.persona)
    asyncio.run(_run(args.url, personas, args.results, parallel=args.parallel, rounds=args.rounds))


if __name__ == "__main__":
    main()

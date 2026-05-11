"""
Master Evaluator — aggregates all per-persona eval results and generates a narrative report.
Called once per benchmark run after all personas complete.
"""
import re
import json
import logging
from google import genai
from google.genai import types

MODEL = "gemini-3.1-pro-preview"

_client: genai.Client | None = None
logger = logging.getLogger("benchmark.master_evaluator")


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client()
    return _client


def _extract_json(raw: str) -> str:
    """Strip markdown fences, find the outermost object, fix trailing commas."""
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end > start:
        raw = raw[start:end + 1]
    raw = re.sub(r",\s*([}\]])", r"\1", raw)
    return raw


_SYSTEM = """You are a quality assurance engineer for an AI sports scouting pipeline.

You receive per-persona eval results from a batch test run. Each result includes biometrics,
initial eval scores, compliance status, and time travel hop evals (where applicable).

Return ONLY this JSON (no prose, no markdown fences):
{
  "pipeline_score": 7.2,
  "run_summary": "One sentence: overall health of this pipeline run.",
  "strengths": ["Specific strength citing persona IDs"],
  "weaknesses": ["Specific failure citing persona IDs and which dimension"],
  "critical_issues": ["Any score ≤3 or compliance failure — empty array if none"],
  "suggested_improvements": [
    {"area": "Interview Quality", "suggestion": "Specific actionable change"}
  ],
  "dimension_analysis": {
    "authenticity": "One sentence pattern across all personas",
    "personalization": "One sentence",
    "interview_quality": "One sentence",
    "distinctness": "One sentence",
    "life_stage_coherence": "One sentence on time travel result quality (or 'No time travel runs' if none)"
  }
}

Rules:
- pipeline_score is your holistic 1-10 judgment, not a simple average
- Cite specific persona IDs when calling out issues
- suggested_improvements: max 4, must be actionable
- critical_issues: empty array [] if everything passed"""


async def generate_master_report(persona_results: list) -> dict:
    """Calls the master evaluator LLM and returns the structured analysis dict."""
    summaries = []
    for r in persona_results:
        ev = r.get("eval_result") or {}
        entry = {
            "persona_id": r.get("persona_id"),
            "persona_label": r.get("persona_label"),
            "biometrics": r.get("biometrics"),
            "conversation_turns": len(r.get("conversation_log", [])),
            "overall": ev.get("overall"),
            "summary": ev.get("summary"),
            "authenticity": (ev.get("authenticity") or {}).get("score"),
            "authenticity_reasoning": (ev.get("authenticity") or {}).get("reasoning"),
            "personalization": (ev.get("personalization") or {}).get("score"),
            "personalization_reasoning": (ev.get("personalization") or {}).get("reasoning"),
            "interview_quality": (ev.get("interview_quality") or {}).get("score"),
            "interview_quality_reasoning": (ev.get("interview_quality") or {}).get("reasoning"),
            "distinctness": (ev.get("distinctness") or {}).get("score"),
            "life_stage_coherence": (ev.get("life_stage_coherence") or {}).get("score"),
            "life_stage_coherence_reasoning": (ev.get("life_stage_coherence") or {}).get("reasoning"),
            "compliance_passed": (ev.get("compliance") or {}).get("passed"),
            "compliance_note": (ev.get("compliance") or {}).get("note"),
        }

        # Include time travel hop eval summaries
        tt_results = r.get("time_travel_results", [])
        if tt_results:
            entry["time_travel_hops"] = []
            for hop in tt_results:
                hop_ev = hop.get("eval_result") or {}
                entry["time_travel_hops"].append({
                    "year": hop.get("target_game_year"),
                    "overall": hop_ev.get("overall"),
                    "life_stage_coherence": (hop_ev.get("life_stage_coherence") or {}).get("score"),
                    "life_stage_coherence_reasoning": (hop_ev.get("life_stage_coherence") or {}).get("reasoning"),
                    "authenticity": (hop_ev.get("authenticity") or {}).get("score"),
                    "personalization": (hop_ev.get("personalization") or {}).get("score"),
                    "compliance_passed": (hop_ev.get("compliance") or {}).get("passed"),
                    "backend_error": hop.get("backend_error"),
                })

        summaries.append(entry)

    prompt = (
        f"Persona eval results from this benchmark run ({len(summaries)} personas):\n\n"
        f"{json.dumps(summaries, indent=2)}\n\n"
        "Generate the master pipeline analysis."
    )

    _fallback = {
        "pipeline_score": None,
        "run_summary": "Master evaluator failed — see benchmark logs.",
        "strengths": [],
        "weaknesses": [],
        "critical_issues": [],
        "suggested_improvements": [],
        "dimension_analysis": {},
    }

    for attempt in range(2):
        try:
            call_prompt = prompt if attempt == 0 else (
                prompt + "\n\nCRITICAL: Your previous response was not valid JSON. "
                "Output ONLY a raw JSON object. No markdown, no trailing commas, no comments."
            )
            response = await _get_client().aio.models.generate_content(
                model=MODEL,
                contents=call_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM,
                    max_output_tokens=8192,
                    temperature=0.1 if attempt == 1 else 0.2,
                ),
            )
            raw = response.text.strip() if response.text else "{}"
            raw = _extract_json(raw)
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning("Master evaluator JSON parse error (attempt %d): %s", attempt + 1, e)
        except Exception as e:
            logger.error("Master evaluator call failed (attempt %d): %s", attempt + 1, e, exc_info=True)
            break

    return _fallback


def _bar(score, width: int = 10) -> str:
    if score is None:
        return "░" * width + "  N/A"
    filled = round(float(score) / 10 * width)
    return "█" * filled + "░" * (width - filled) + f"  {float(score):.1f}"


def _dim_avg(results: list, key: str) -> float | None:
    """Average a dimension score across initial scouting evals."""
    scores = [
        (r.get("eval_result") or {}).get(key, {})
        for r in results
        if r.get("eval_result")
    ]
    scores = [
        s.get("score") if isinstance(s, dict) else None
        for s in scores
    ]
    scores = [s for s in scores if s is not None]
    return round(sum(scores) / len(scores), 1) if scores else None


def _dim_avg_tt(results: list, key: str) -> float | None:
    """Average a dimension score across all time travel hop evals."""
    scores = []
    for r in results:
        for hop in r.get("time_travel_results", []):
            ev = hop.get("eval_result") or {}
            val = ev.get(key, {})
            score = val.get("score") if isinstance(val, dict) else None
            if score is not None:
                scores.append(score)
    return round(sum(scores) / len(scores), 1) if scores else None


def generate_markdown_report(persona_results: list, master: dict, run_timestamp: str) -> str:
    lines = []

    pipeline_score = master.get("pipeline_score")
    score_str = f"{pipeline_score:.1f}" if pipeline_score is not None else "N/A"

    lines += [
        f"# PIPELINE BENCHMARK — {run_timestamp}",
        "",
        f"## Overall Pipeline Score: {score_str} / 10",
        "",
        f"> {master.get('run_summary', '')}",
        "",
    ]

    # ── Dimension averages (initial scouting) ──
    dim_keys = [
        ("authenticity",      "Authenticity"),
        ("personalization",   "Personalization"),
        ("interview_quality", "Interview Quality"),
        ("distinctness",      "Pathway Distinctness"),
    ]

    lines.append("### Dimension Averages (Initial Scouting)")
    lines.append("```")
    for key, label in dim_keys:
        avg = _dim_avg(persona_results, key)
        lines.append(f"  {label:<24} {_bar(avg)}")
    lines.append("```")
    lines.append("")

    # ── Time travel averages ──
    tt_results_exist = any(r.get("time_travel_results") for r in persona_results)
    tt_dim_keys = [
        ("life_stage_coherence", "Life Stage Coherence"),
        ("authenticity",         "Authenticity"),
        ("personalization",      "Personalization"),
        ("distinctness",         "Pathway Distinctness"),
    ]
    if tt_results_exist:
        lines.append("### Dimension Averages (Time Travel Hops)")
        lines.append("```")
        for key, label in tt_dim_keys:
            avg = _dim_avg_tt(persona_results, key)
            lines.append(f"  {label:<24} {_bar(avg)}")
        lines.append("```")
        lines.append("")

    # ── Per-persona scorecard ──
    from collections import defaultdict
    persona_groups: dict = defaultdict(list)
    for r in persona_results:
        persona_groups[r.get("persona_id", "?")].append(r)

    multi_round = any(len(v) > 1 for v in persona_groups.values())

    if multi_round:
        lines += [
            "### Per-Persona Scorecard (avg ± variance across rounds)",
            "",
            "| Persona | Rounds | Overall | Auth | Pers | IQ | Distinct | TT Hops | Compliance |",
            "|---------|:------:|:-------:|:----:|:----:|:--:|:--------:|:-------:|:----------:|",
        ]
    else:
        lines += [
            "### Per-Persona Scorecard",
            "",
            "| Persona | Overall | Auth | Pers | IQ | Distinct | TT Hops | Compliance |",
            "|---------|:-------:|:----:|:----:|:--:|:--------:|:-------:|:----------:|",
        ]

    for pid, group in persona_groups.items():
        label = (group[0].get("persona_label") or pid)[:38]
        n_ok = [r for r in group if not r.get("error") and r.get("eval_result")]
        n_err = len(group) - len(n_ok)

        if not n_ok:
            err_note = f"ERROR×{len(group)}" if len(group) > 1 else "ERROR"
            if multi_round:
                lines.append(f"| {label:<38} | {len(group)} | {err_note} | — | — | — | — | — | — |")
            else:
                lines.append(f"| {label:<38} | {err_note} | — | — | — | — | — | — |")
            continue

        def _avg_dim(key: str) -> str:
            scores = [(r.get("eval_result") or {}).get(key, {}) for r in n_ok]
            scores = [s.get("score") if isinstance(s, dict) else None for s in scores]
            scores = [s for s in scores if s is not None]
            if not scores:
                return "—"
            avg = sum(scores) / len(scores)
            if multi_round and len(scores) > 1:
                lo, hi = min(scores), max(scores)
                return f"{avg:.1f} ({lo}–{hi})" if lo != hi else f"{avg:.1f}"
            return str(round(avg, 1))

        overall_scores = [(r.get("eval_result") or {}).get("overall") for r in n_ok]
        overall_scores = [s for s in overall_scores if s is not None]
        if overall_scores:
            ov_avg = sum(overall_scores) / len(overall_scores)
            if multi_round and len(overall_scores) > 1:
                lo, hi = min(overall_scores), max(overall_scores)
                overall_str = f"**{ov_avg:.1f}** ({lo}–{hi})" if lo != hi else f"**{ov_avg:.1f}**"
            else:
                overall_str = f"**{round(ov_avg, 1)}**"
        else:
            overall_str = "—"

        comp_results = [(r.get("eval_result") or {}).get("compliance", {}).get("passed") for r in n_ok]
        comp_results = [c for c in comp_results if c is not None]
        if comp_results:
            n_pass = sum(1 for c in comp_results if c)
            comp_str = f"{n_pass}/{len(comp_results)}✓" if multi_round else ("✓" if comp_results[0] else "✗")
        else:
            comp_str = "—"

        # Time travel hop summary: "2/2✓" = 2 hops, both have evals
        tt_hops_all = []
        for r in n_ok:
            tt_hops_all.extend(r.get("time_travel_results", []))
        if tt_hops_all:
            tt_with_eval = sum(1 for h in tt_hops_all if h.get("eval_result"))
            tt_str = f"{tt_with_eval}/{len(tt_hops_all)}"
        else:
            tt_str = "—"

        err_suffix = f" +{n_err}err" if n_err else ""
        rounds_str = f"{len(n_ok)}{err_suffix}"

        if multi_round:
            row = (
                f"| {label:<38} | {rounds_str} | {overall_str} | {_avg_dim('authenticity')} | "
                f"{_avg_dim('personalization')} | {_avg_dim('interview_quality')} | "
                f"{_avg_dim('distinctness')} | {tt_str} | {comp_str} |"
            )
        else:
            row = (
                f"| {label:<38} | {overall_str} | {_avg_dim('authenticity')} | "
                f"{_avg_dim('personalization')} | {_avg_dim('interview_quality')} | "
                f"{_avg_dim('distinctness')} | {tt_str} | {comp_str} |"
            )
        lines.append(row)

    lines.append("")

    # ── Time travel scorecard ──
    if tt_results_exist:
        lines += [
            "### Time Travel Scorecard",
            "",
            "| Persona | Year | Overall | Life Stage | Auth | Pers | Compliance |",
            "|---------|:----:|:-------:|:----------:|:----:|:----:|:----------:|",
        ]
        for r in persona_results:
            p_label = (r.get("persona_label") or r.get("persona_id", "?"))[:30]
            for hop in r.get("time_travel_results", []):
                year = hop.get("target_game_year", "?")
                hop_ev = hop.get("eval_result") or {}
                if hop.get("backend_error"):
                    lines.append(
                        f"| {p_label:<30} | {year} | ERROR | — | — | — | — |"
                    )
                    continue
                if not hop_ev:
                    lines.append(
                        f"| {p_label:<30} | {year} | N/A | — | — | — | — |"
                    )
                    continue

                def _hs(key: str) -> str:
                    v = hop_ev.get(key, {})
                    s = v.get("score") if isinstance(v, dict) else None
                    return str(s) if s is not None else "—"

                ov = hop_ev.get("overall")
                ov_str = f"**{ov}**" if ov is not None else "—"
                comp = (hop_ev.get("compliance") or {}).get("passed")
                comp_str = "✓" if comp else ("✗" if comp is False else "—")
                lines.append(
                    f"| {p_label:<30} | {year} | {ov_str} | {_hs('life_stage_coherence')} | "
                    f"{_hs('authenticity')} | {_hs('personalization')} | {comp_str} |"
                )
        lines.append("")

    def _section(title: str, items: list) -> None:
        if not items:
            return
        lines.append(f"### {title}")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    _section("What's Working Well", master.get("strengths", []))
    _section("What Needs Improvement", master.get("weaknesses", []))
    _section("⚠ Critical Issues", master.get("critical_issues", []))

    suggestions = master.get("suggested_improvements", [])
    if suggestions:
        lines.append("### Suggested Improvements")
        for s in suggestions:
            lines.append(f"**{s.get('area', 'Area')}**: {s.get('suggestion', '')}")
            lines.append("")

    dim_analysis = master.get("dimension_analysis", {})
    all_dim_keys = dim_keys + [("life_stage_coherence", "Life Stage Coherence")]
    if dim_analysis:
        lines.append("### Dimension Analysis")
        for key, lbl in all_dim_keys:
            note = dim_analysis.get(key)
            if note:
                lines.append(f"- **{lbl}**: {note}")
        lines.append("")

    return "\n".join(lines)

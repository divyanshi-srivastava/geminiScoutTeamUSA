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
    # Remove trailing commas before } or ] — the most common LLM JSON mistake
    raw = re.sub(r",\s*([}\]])", r"\1", raw)
    return raw

_SYSTEM = """You are a quality assurance engineer for an AI sports scouting pipeline.

You receive per-persona eval results from a batch test run. Each result includes biometrics, eval scores, and compliance status.

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
    "distinctness": "One sentence"
  }
}

Rules:
- pipeline_score is your holistic 1-10 judgment of the pipeline's overall quality, not a simple average
- Cite specific persona IDs (e.g., "03_adaptive_visual_impairment") when calling out issues
- suggested_improvements: max 4, must be actionable (what to change, not just what's wrong)
- critical_issues: empty array [] if everything passed — do not omit the key"""


async def generate_master_report(persona_results: list) -> dict:
    """Calls the master evaluator LLM and returns the structured analysis dict."""
    summaries = []
    for r in persona_results:
        ev = r.get("eval_result") or {}
        summaries.append({
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
        })

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

    # ── Dimension averages ──
    dim_keys = [
        ("authenticity",     "Authenticity"),
        ("personalization",  "Personalization"),
        ("interview_quality","Interview Quality"),
        ("distinctness",     "Pathway Distinctness"),
    ]

    lines.append("### Dimension Averages")
    lines.append("```")
    for key, label in dim_keys:
        avg = _dim_avg(persona_results, key)
        lines.append(f"  {label:<24} {_bar(avg)}")
    lines.append("```")
    lines.append("")

    # ── Per-persona scorecard ──
    lines += [
        "### Per-Persona Scorecard",
        "",
        "| Persona | Overall | Auth | Pers | IQ | Distinct | Compliance |",
        "|---------|:-------:|:----:|:----:|:--:|:--------:|:----------:|",
    ]
    for r in persona_results:
        ev = r.get("eval_result") or {}
        label = r.get("persona_label", r.get("persona_id", "?"))[:38]
        overall  = ev.get("overall", "—")
        auth     = (ev.get("authenticity") or {}).get("score", "—")
        pers     = (ev.get("personalization") or {}).get("score", "—")
        iq       = (ev.get("interview_quality") or {}).get("score", "—")
        dist     = (ev.get("distinctness") or {}).get("score", "—")
        comp_ok  = (ev.get("compliance") or {}).get("passed")
        comp_str = "✓" if comp_ok else ("✗" if comp_ok is False else "—")
        if r.get("error"):
            lines.append(f"| {label:<38} | ERROR | — | — | — | — | — |")
        else:
            lines.append(
                f"| {label:<38} | **{overall}** | {auth} | {pers} | {iq} | {dist} | {comp_str} |"
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
    if dim_analysis:
        lines.append("### Dimension Analysis")
        for key, label in dim_keys:
            note = dim_analysis.get(key)
            if note:
                lines.append(f"- **{label}**: {note}")
        lines.append("")

    return "\n".join(lines)

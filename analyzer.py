"""
analyzer.py - LLM analysis stages and pure-Python score aggregation.

Each lab analysis function wraps exactly one LLM call. compute_overall_score()
does not call the LLM; it only combines sub-scores with fixed weights.
"""

import json
from typing import Any

from llm import ask_json, ask_text
from prompts import (
    RESUME_PROFILE_PROMPT,
    JD_PROFILE_PROMPT,
    KEYWORD_MATCH_PROMPT,
    BULLET_QUALITY_PROMPT,
    JARGON_AUDIT_PROMPT,
    STRUCTURE_AUDIT_PROMPT,
    DEGREE_ALIGNMENT_PROMPT,
    OVERALL_SUMMARY_PROMPT,
    COVER_LETTER_PROMPT,
    COVER_LETTER_REVISION_PROMPT,
)


def _dump(data: Any) -> str:
    """Serialise pipeline data for LLM user messages."""
    return json.dumps(data, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Extraction functions
# ---------------------------------------------------------------------------

def extract_resume_profile(resume_text: str) -> dict:
    """Convert plain resume text to a structured candidate profile."""
    user = f"RESUME TEXT:\n\n{resume_text}"
    return ask_json(RESUME_PROFILE_PROMPT, user, temperature=0.0, max_tokens=2500)


def extract_jd_profile(jd_text: str) -> dict:
    """Convert plain job-description text to a structured JD profile."""
    user = f"JOB DESCRIPTION TEXT:\n\n{jd_text}"
    return ask_json(JD_PROFILE_PROMPT, user, temperature=0.0, max_tokens=2000)


# ---------------------------------------------------------------------------
# Evaluation functions
# ---------------------------------------------------------------------------

def analyse_keyword_match(resume_profile: dict, jd_profile: dict) -> dict:
    """Compare resume keywords against JD requirements."""
    user = (
        f"RESUME PROFILE:\n{_dump(resume_profile)}\n\n"
        f"JD PROFILE:\n{_dump(jd_profile)}"
    )
    return ask_json(KEYWORD_MATCH_PROMPT, user, temperature=0.2, max_tokens=3000)


def analyse_bullets(resume_profile: dict) -> dict:
    """Score resume bullets against the Action, Technology, Impact rubric."""
    user = f"RESUME PROFILE:\n{_dump(resume_profile)}"
    result = ask_json(BULLET_QUALITY_PROMPT, user, temperature=0.2, max_tokens=3000)
    _normalise_bullet_score(result)
    return result


def analyse_jargon(
    resume_profile: dict,
    degree_program: str,
    jd_profile: dict,
) -> dict:
    """Detect game-dev jargon and suggest diagnostic translations."""
    user = (
        f"DEGREE PROGRAM: {degree_program}\n\n"
        f"RESUME PROFILE:\n{_dump(resume_profile)}\n\n"
        f"JD PROFILE:\n{_dump(jd_profile)}"
    )
    result = ask_json(JARGON_AUDIT_PROMPT, user, temperature=0.2, max_tokens=1800)
    _normalise_jargon_score(result)
    return result


def analyse_structure(resume_text: str) -> dict:
    """Audit resume structure and ATS-friendly formatting."""
    user = f"RESUME TEXT:\n\n{resume_text}"
    return ask_json(STRUCTURE_AUDIT_PROMPT, user, temperature=0.0, max_tokens=1800)


def analyse_degree_alignment(jd_profile: dict, degree_program: str) -> dict:
    """Assess whether the JD title aligns with the student's degree programme."""
    user = f"DEGREE PROGRAM: {degree_program}\n\nJD PROFILE:\n{_dump(jd_profile)}"
    return ask_json(DEGREE_ALIGNMENT_PROMPT, user, temperature=0.2, max_tokens=900)


def summarise_overall(report: dict) -> str:
    """Generate a three-bullet executive summary for the analysis report."""
    summary_input = {
        "overall_score": report.get("overall_score", 0),
        "passes_ats_threshold": report.get("passes_ats_threshold", False),
        "keyword_match": report.get("keyword_match", {}),
        "bullets": report.get("bullets", {}),
        "jargon": report.get("jargon", {}),
        "structure": report.get("structure", {}),
        "degree_alignment": report.get("degree_alignment", {}),
    }
    user = f"ANALYSIS REPORT:\n{_dump(summary_input)}"
    return ask_text(OVERALL_SUMMARY_PROMPT, user, temperature=0.3, max_tokens=400).strip()


def generate_cover_letter(report: dict) -> str:
    """Generate a tailored cover letter draft from verified analysis data."""
    cover_input = {
        "resume_profile": report.get("resume_profile", {}),
        "jd_profile": report.get("jd_profile", {}),
        "overall_score": report.get("overall_score", 0),
        "passes_ats_threshold": report.get("passes_ats_threshold", False),
        "keyword_match": report.get("keyword_match", {}),
        "degree_alignment": report.get("degree_alignment", {}),
    }
    user = f"APPLICATION CONTEXT:\n{_dump(cover_input)}"
    return ask_text(COVER_LETTER_PROMPT, user, temperature=0.4, max_tokens=1200).strip()


def revise_cover_letter(report: dict, current_draft: str, revision_request: str) -> str:
    """Revise a cover letter draft using a factual follow-up request."""
    revision_input = {
        "resume_profile": report.get("resume_profile", {}),
        "jd_profile": report.get("jd_profile", {}),
        "analysis": {
            "keyword_match": report.get("keyword_match", {}),
            "degree_alignment": report.get("degree_alignment", {}),
        },
        "current_draft": current_draft,
        "revision_request": revision_request,
    }
    user = f"REVISION CONTEXT:\n{_dump(revision_input)}"
    return ask_text(COVER_LETTER_REVISION_PROMPT, user, temperature=0.4, max_tokens=1200).strip()


# ---------------------------------------------------------------------------
# Score aggregation - no LLM call
# ---------------------------------------------------------------------------

def _score(value: object) -> float:
    """Coerce a sub-score to a bounded float."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(100.0, number))


def _normalise_bullet_score(result: dict) -> None:
    """Recompute bullet_quality_avg from returned bullet levels."""
    levels = {"L1_OK": 1, "L2_BETTER": 2, "L3_BEST": 3}
    bullets = result.get("bullets", [])
    if not isinstance(bullets, list) or not bullets:
        result["bullet_quality_avg"] = 0
        return

    total = 0
    for bullet in bullets:
        if isinstance(bullet, dict):
            total += levels.get(str(bullet.get("level", "")), 0)
    result["bullet_quality_avg"] = int(round(100 * total / (3 * len(bullets))))


def _normalise_jargon_score(result: dict) -> None:
    """Recompute jargon_score from returned flag severities."""
    flags = result.get("flags", [])
    if not isinstance(flags, list):
        result["flags"] = []
        result["jargon_score"] = 100
        return

    counts = {"high": 0, "medium": 0, "low": 0}
    for flag in flags:
        if isinstance(flag, dict):
            severity = str(flag.get("severity", "")).lower()
            if severity in counts:
                counts[severity] += 1
    result["jargon_score"] = max(
        0,
        100 - 10 * counts["high"] - 5 * counts["medium"] - 2 * counts["low"],
    )


def compute_overall_score(report: dict) -> int:
    """Compute the fixed weighted composite score from report sub-scores."""
    total = (
        _score(report.get("keyword_match", {}).get("keyword_match_score")) * 0.40
        + _score(report.get("bullets", {}).get("bullet_quality_avg")) * 0.25
        + _score(report.get("structure", {}).get("structure_score")) * 0.15
        + _score(report.get("jargon", {}).get("jargon_score")) * 0.10
        + _score(report.get("degree_alignment", {}).get("degree_alignment_score")) * 0.10
    )
    return int(round(total))

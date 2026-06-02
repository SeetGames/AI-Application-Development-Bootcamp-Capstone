"""
report.py - Markdown renderer for analysis reports.
"""

from pathlib import Path


def render_markdown(report: dict, *, out_path: str) -> None:
    """Render the full analysis report dict to a Markdown file."""
    lines = _build_lines(report)
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


def _mark(value: object) -> str:
    """Return a readable status marker."""
    return "Yes" if value else "No"


def _safe_cell(value: object) -> str:
    """Make Markdown table cells safer."""
    return str(value or "").replace("\n", " ").replace("|", "/").strip()


def _build_lines(report: dict) -> list[str]:
    """Build Markdown lines from a report dictionary."""
    meta = report.get("meta", {})
    rp = report.get("resume_profile", {})
    jd = report.get("jd_profile", {})
    km = report.get("keyword_match", {})
    bullets = report.get("bullets", {})
    jargon = report.get("jargon", {})
    struct = report.get("structure", {})
    degree = report.get("degree_alignment", {})
    score = report.get("overall_score", 0)
    passes = report.get("passes_ats_threshold", False)
    summary = report.get("summary", "")

    candidate = rp.get("name", "Unknown Candidate")
    jd_title = jd.get("job_title", "Unknown Role")
    company = jd.get("company", "Unknown Company")
    verdict = "PASS" if passes else "FAIL"

    lines: list[str] = [
        "# Resume Analysis Report",
        "",
        f"**Candidate:** {_safe_cell(candidate)}  ",
        f"**Target role:** {_safe_cell(jd_title)} @ {_safe_cell(company)}  ",
        f"**Degree:** {_safe_cell(meta.get('degree', ''))}  ",
        f"**Generated:** {_safe_cell(meta.get('generated_at', ''))}  ",
        "",
        f"## Overall Score: {score}/100 ({verdict} - 60% ATS threshold)",
        "",
        "## Executive Summary",
        "",
        summary.strip(),
        "",
    ]

    present = km.get("present", [])
    missing = km.get("missing", [])
    km_score = km.get("keyword_match_score", 0)
    lines += [
        "## Keyword Match",
        "",
        f"**Score:** {km_score}/100",
        "",
        "| Present keywords (up to 20) | Missing keywords (up to 20) |",
        "|---|---|",
    ]
    max_rows = max(len(present), len(missing), 1)
    for i in range(min(max_rows, 20)):
        p_item = present[i] if i < len(present) else {}
        m_item = missing[i] if i < len(missing) else {}
        p_cell = _safe_cell(p_item.get("keyword", ""))
        m_cell = ""
        if m_item:
            keyword = _safe_cell(m_item.get("keyword", ""))
            importance = _safe_cell(m_item.get("importance", ""))
            m_cell = f"**{keyword}** ({importance})"
        lines.append(f"| {p_cell} | {m_cell} |")
    lines.append("")

    bullet_list = bullets.get("bullets", [])
    bq_avg = bullets.get("bullet_quality_avg", 0)
    lines += [
        "## Bullet Quality Audit",
        "",
        f"**Average score:** {bq_avg}/100 (L1=OK, L2=Better, L3=Best)",
        "",
        "| Project / Role | Bullet (truncated to 80 chars) | Action | Tech | Impact | Level | What's Missing |",
        "|---|---|---|---|---|---|---|",
    ]
    for bullet in bullet_list:
        text = _safe_cell(bullet.get("bullet_text", ""))[:80]
        parent = _safe_cell(bullet.get("parent_title", ""))
        action = _mark(bullet.get("has_action_verb"))
        tech = _mark(bullet.get("has_specific_technology"))
        impact = _mark(bullet.get("has_measurable_impact"))
        level = _safe_cell(bullet.get("level", ""))
        missing_text = _safe_cell(bullet.get("what_is_missing", ""))
        lines.append(
            f"| {parent} | {text} | {action} | {tech} | {impact} | {level} | {missing_text} |"
        )
    lines.append("")

    flags = jargon.get("flags", [])
    jargon_score = jargon.get("jargon_score", 0)
    lines += [
        "## Game-Dev Jargon Flags",
        "",
        f"**Score:** {jargon_score}/100",
        "",
    ]
    if flags:
        lines += [
            "| Term Used | Suggested Translation | Severity |",
            "|---|---|---|",
        ]
        for flag in flags:
            lines.append(
                f"| {_safe_cell(flag.get('term_used', ''))} "
                f"| {_safe_cell(flag.get('suggested_translation', ''))} "
                f"| {_safe_cell(flag.get('severity', ''))} |"
            )
    else:
        lines.append("No game-dev jargon flags raised.")
    lines.append("")

    tt = struct.get("three_thirds", {})
    ats_flags = struct.get("ats_red_flags", [])
    struct_score = struct.get("structure_score", 0)
    headings_present = ", ".join(struct.get("section_headings_present", [])) or "none detected"
    headings_missing = ", ".join(struct.get("section_headings_missing", [])) or "none missing"
    lines += [
        "## Structure Audit",
        "",
        f"**Score:** {struct_score}/100  "
        f"| Pages (est.): {_safe_cell(struct.get('page_count_estimate', '?'))}  "
        f"| Single-column: {_mark(struct.get('single_column_likely'))}",
        "",
        f"**Headings present:** {_safe_cell(headings_present)}  ",
        f"**Headings missing:** {_safe_cell(headings_missing)}",
        "",
        "**Three-Thirds compliance:**",
        "",
        "| Zone | Check | Status |",
        "|---|---|---|",
        f"| Top third | Name present | {_mark(tt.get('top_third_has_name'))} |",
        f"| Top third | Contact present | {_mark(tt.get('top_third_has_contact'))} |",
        f"| Top third | Summary / featured | {_mark(tt.get('top_third_has_summary_or_featured'))} |",
        f"| Middle third | Projects / experience | {_mark(tt.get('middle_third_has_projects_or_experience'))} |",
        f"| Bottom third | Skills / keywords | {_mark(tt.get('bottom_third_has_skills_keywords'))} |",
        "",
    ]
    if ats_flags:
        lines += [
            "**ATS red flags:**",
            "",
            "| Issue | Evidence |",
            "|---|---|",
        ]
        for flag in ats_flags:
            lines.append(
                f"| {_safe_cell(flag.get('issue', ''))} | {_safe_cell(flag.get('evidence', ''))} |"
            )
    else:
        lines.append("No ATS red flags detected.")
    lines.append("")

    lines += [
        "## Degree Alignment",
        "",
        f"**Score:** {degree.get('degree_alignment_score', 0)}/100",
        f"**Degree:** {_safe_cell(degree.get('student_degree', ''))}  ",
        f"**JD Title:** {_safe_cell(degree.get('jd_title', ''))}  ",
        f"**On suggested list:** {_mark(degree.get('title_on_suggested_list'))} "
        f"{_safe_cell(degree.get('matched_against', ''))}  ",
        f"**Commentary:** {_safe_cell(degree.get('fit_commentary', ''))}",
        "",
    ]

    km_contrib = round(km.get("keyword_match_score", 0) * 0.40, 1)
    bq_contrib = round(bullets.get("bullet_quality_avg", 0) * 0.25, 1)
    st_contrib = round(struct.get("structure_score", 0) * 0.15, 1)
    ja_contrib = round(jargon.get("jargon_score", 0) * 0.10, 1)
    da_contrib = round(degree.get("degree_alignment_score", 0) * 0.10, 1)
    lines += [
        "## Score Breakdown",
        "",
        "| Component | Raw | Weight | Contribution |",
        "|---|---|---|---|",
        f"| Keyword match | {km.get('keyword_match_score', 0)} | 40% | {km_contrib} |",
        f"| Bullet quality | {bullets.get('bullet_quality_avg', 0)} | 25% | {bq_contrib} |",
        f"| Structure | {struct.get('structure_score', 0)} | 15% | {st_contrib} |",
        f"| Jargon | {jargon.get('jargon_score', 0)} | 10% | {ja_contrib} |",
        f"| Degree alignment | {degree.get('degree_alignment_score', 0)} | 10% | {da_contrib} |",
        f"| **Total** | | | **{score}** |",
        "",
    ]

    cover_letter_path = report.get("cover_letter_path")
    if cover_letter_path:
        lines += [
            "## Cover Letter Draft",
            "",
            f"Saved separately: `{cover_letter_path}`",
            "",
        ]

    return lines

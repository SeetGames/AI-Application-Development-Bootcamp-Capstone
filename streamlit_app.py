"""
streamlit_app.py - web UI for the Resume and Cover Letter Assistant.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

from analyzer import (
    analyse_bullets,
    analyse_degree_alignment,
    analyse_jargon,
    analyse_keyword_match,
    analyse_structure,
    compute_overall_score,
    extract_jd_profile,
    extract_resume_profile,
    generate_cover_letter,
    revise_cover_letter,
    summarise_overall,
)
from main import ATS_PASS_THRESHOLD, DEFAULT_MODEL, VALID_DEGREES
from parse import read_jd_text, read_resume_pdf
from report import render_markdown


OUTPUT_DIR = Path("outputs")
SAMPLE_RESUME = Path("inputs/strong_resume.pdf")
SAMPLE_JD = Path("inputs/job_rtis_systems_engineer.txt")


st.set_page_config(
    page_title="Resume and Cover Letter Assistant",
    page_icon=None,
    layout="wide",
)


def _inject_css() -> None:
    """Apply compact dashboard styling."""
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        div[data-testid="stStatusWidget"] {
            display: none !important;
        }
        div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stAlert"]) {
            margin-top: 0.5rem;
        }
        .small-muted {
            color: #a8adb7;
            font-size: 0.88rem;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(120px, 1fr));
            gap: 16px;
            margin: 16px 0 20px;
        }
        .metric-card {
            min-height: 96px;
            border: 1px solid #2f3440;
            border-radius: 8px;
            background: #161a22;
            padding: 14px 16px;
            box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset;
        }
        .metric-label {
            color: #a8adb7;
            font-size: 0.82rem;
            font-weight: 650;
            letter-spacing: 0;
            margin-bottom: 8px;
        }
        .metric-value {
            color: #f7f8fa;
            font-size: 1.8rem;
            font-weight: 750;
            line-height: 1.1;
        }
        .metric-status {
            display: inline-flex;
            align-items: center;
            margin-top: 10px;
            border-radius: 999px;
            padding: 3px 9px;
            font-size: 0.78rem;
            font-weight: 750;
        }
        .metric-status.pass {
            color: #a7f3d0;
            background: #064e3b;
            border: 1px solid #047857;
        }
        .metric-status.fail {
            color: #fecaca;
            background: #7f1d1d;
            border: 1px solid #b91c1c;
        }
        @media (max-width: 900px) {
            .metric-grid {
                grid-template-columns: repeat(2, minmax(120px, 1fr));
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _read_uploaded_text(uploaded_file) -> str:
    """Read a Streamlit text upload as UTF-8."""
    return uploaded_file.getvalue().decode("utf-8").strip()


def _read_uploaded_resume(uploaded_file) -> str:
    """Persist an uploaded PDF briefly so the existing parser can read it."""
    suffix = Path(uploaded_file.name).suffix or ".pdf"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp.write(uploaded_file.getvalue())
            temp_path = temp.name
        return read_resume_pdf(temp_path)
    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except OSError:
                pass


def _load_sample_inputs() -> tuple[bytes, str]:
    """Load bundled sample inputs for a quick demo."""
    return SAMPLE_RESUME.read_bytes(), read_jd_text(str(SAMPLE_JD))


def _write_report_files(report: dict, timestamp: str) -> tuple[Path, Path]:
    """Write JSON and Markdown reports and return their paths."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    json_path = OUTPUT_DIR / f"match_report_{timestamp}.json"
    md_path = OUTPUT_DIR / f"match_report_{timestamp}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    render_markdown(report, out_path=str(md_path))
    return json_path, md_path


def _run_pipeline(
    resume_text: str,
    jd_text: str,
    degree: str,
    include_cover_letter: bool,
) -> dict:
    """Run the full LLM pipeline and return the generated report."""
    progress = st.progress(0)
    status = st.empty()

    status.write("Extracting resume profile...")
    resume_profile = extract_resume_profile(resume_text)
    progress.progress(1 / 8)

    status.write("Extracting JD profile...")
    jd_profile = extract_jd_profile(jd_text)
    progress.progress(2 / 8)

    status.write("Checking keyword match...")
    keyword_match = analyse_keyword_match(resume_profile, jd_profile)
    progress.progress(3 / 8)

    status.write("Auditing bullet quality...")
    bullets = analyse_bullets(resume_profile)
    progress.progress(4 / 8)

    status.write("Checking jargon...")
    jargon = analyse_jargon(resume_profile, degree, jd_profile)
    progress.progress(5 / 8)

    status.write("Checking structure...")
    structure = analyse_structure(resume_text)
    progress.progress(6 / 8)

    status.write("Checking degree alignment...")
    degree_alignment = analyse_degree_alignment(jd_profile, degree)
    progress.progress(7 / 8)

    now = datetime.now()
    report = {
        "meta": {
            "generated_at": now.isoformat(timespec="seconds"),
            "model": os.getenv("MODEL", DEFAULT_MODEL),
            "source": "streamlit",
            "degree": degree,
            "ats_pass_threshold": ATS_PASS_THRESHOLD,
        },
        "resume_profile": resume_profile,
        "jd_profile": jd_profile,
        "keyword_match": keyword_match,
        "bullets": bullets,
        "jargon": jargon,
        "structure": structure,
        "degree_alignment": degree_alignment,
    }
    report["overall_score"] = compute_overall_score(report)
    report["passes_ats_threshold"] = report["overall_score"] >= ATS_PASS_THRESHOLD

    status.write("Generating summary...")
    report["summary"] = summarise_overall(report)

    if include_cover_letter:
        status.write("Generating cover letter...")
        report["cover_letter"] = generate_cover_letter(report)

    timestamp = now.strftime("%Y%m%d_%H%M%S")
    json_path, md_path = _write_report_files(report, timestamp)
    report["json_path"] = str(json_path)
    report["md_path"] = str(md_path)

    if include_cover_letter:
        cover_path = OUTPUT_DIR / f"cover_letter_{timestamp}.txt"
        cover_path.write_text(report["cover_letter"], encoding="utf-8")
        report["cover_letter_path"] = str(cover_path)

    progress.progress(1.0)
    status.write("Done.")
    return report


def _keyword_rows(items: list[dict]) -> list[dict]:
    """Prepare keyword rows for table display."""
    rows = []
    for item in items:
        rows.append(
            {
                "keyword": item.get("keyword", ""),
                "category": item.get("category", ""),
                "importance": item.get("importance", ""),
                "found_in": item.get("found_in", ""),
            }
        )
    return rows


def _metric_card(label: str, value: str, status: str | None = None) -> str:
    """Render a dark metric card without Streamlit delta arrows."""
    badge = ""
    if status:
        status_class = "pass" if status == "PASS" else "fail"
        badge = f'<div class="metric-status {status_class}">{status}</div>'
    return (
        '<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f"{badge}"
        "</div>"
    )


def _show_report(report: dict) -> None:
    """Render the report dashboard."""
    score = report.get("overall_score", 0)
    verdict = "PASS" if report.get("passes_ats_threshold") else "FAIL"
    keyword = report.get("keyword_match", {})
    bullets = report.get("bullets", {})
    structure = report.get("structure", {})
    jargon = report.get("jargon", {})
    degree = report.get("degree_alignment", {})

    st.markdown(
        '<div class="metric-grid">'
        + _metric_card("Score", f"{score}/100", verdict)
        + _metric_card("Keyword", f"{keyword.get('keyword_match_score', 0)}/100")
        + _metric_card("Bullets", f"{bullets.get('bullet_quality_avg', 0)}/100")
        + _metric_card("Structure", f"{structure.get('structure_score', 0)}/100")
        + _metric_card("Jargon", f"{jargon.get('jargon_score', 0)}/100")
        + "</div>",
        unsafe_allow_html=True,
    )

    tabs = st.tabs(
        [
            "Summary",
            "Keywords",
            "Bullets",
            "Structure",
            "Jargon",
            "Degree",
            "Cover Letter",
            "Downloads",
        ]
    )

    with tabs[0]:
        st.markdown(report.get("summary", "").strip())
        st.divider()
        st.write("Target role:", report.get("jd_profile", {}).get("job_title", ""))
        st.write("Candidate:", report.get("resume_profile", {}).get("name", ""))

    with tabs[1]:
        left, right = st.columns(2)
        with left:
            st.subheader("Present")
            st.dataframe(_keyword_rows(keyword.get("present", [])), use_container_width=True)
        with right:
            st.subheader("Missing")
            st.dataframe(_keyword_rows(keyword.get("missing", [])), use_container_width=True)

    with tabs[2]:
        st.dataframe(bullets.get("bullets", []), use_container_width=True)

    with tabs[3]:
        tt = structure.get("three_thirds", {})
        st.write("Headings present:", ", ".join(structure.get("section_headings_present", [])) or "none")
        st.write("Headings missing:", ", ".join(structure.get("section_headings_missing", [])) or "none")
        st.dataframe(
            [
                {"check": "Name in top third", "status": tt.get("top_third_has_name", False)},
                {"check": "Contact in top third", "status": tt.get("top_third_has_contact", False)},
                {
                    "check": "Summary or featured focus",
                    "status": tt.get("top_third_has_summary_or_featured", False),
                },
                {
                    "check": "Projects or experience in middle",
                    "status": tt.get("middle_third_has_projects_or_experience", False),
                },
                {
                    "check": "Skills or keywords in bottom",
                    "status": tt.get("bottom_third_has_skills_keywords", False),
                },
            ],
            use_container_width=True,
        )
        st.dataframe(structure.get("ats_red_flags", []), use_container_width=True)

    with tabs[4]:
        st.dataframe(jargon.get("flags", []), use_container_width=True)

    with tabs[5]:
        st.write("Score:", degree.get("degree_alignment_score", 0))
        st.write("Matched against:", degree.get("matched_against", ""))
        st.write(degree.get("fit_commentary", ""))

    with tabs[6]:
        cover_letter = report.get("cover_letter", "")
        if cover_letter:
            st.text_area("Draft", cover_letter, height=420)
            revision = st.text_area("Revision request", placeholder="Example: make it shorter and more formal")
            if st.button("Revise cover letter", type="secondary"):
                if not revision.strip():
                    st.warning("Enter a revision request first.")
                else:
                    try:
                        updated = revise_cover_letter(report, cover_letter, revision.strip())
                        report["cover_letter"] = updated
                        path = report.get("cover_letter_path")
                        if path:
                            Path(path).write_text(updated, encoding="utf-8")
                        st.session_state["report"] = report
                        st.rerun()
                    except RuntimeError as exc:
                        st.error(f"LLM error: {exc}")
        else:
            st.info("Enable cover-letter generation before running the analysis.")

    with tabs[7]:
        json_text = json.dumps(report, indent=2, ensure_ascii=False)
        st.download_button(
            "Download JSON",
            json_text,
            file_name=Path(report.get("json_path", "match_report.json")).name,
            mime="application/json",
        )
        md_path = report.get("md_path")
        if md_path and Path(md_path).exists():
            st.download_button(
                "Download Markdown",
                Path(md_path).read_text(encoding="utf-8"),
                file_name=Path(md_path).name,
                mime="text/markdown",
            )
        if report.get("cover_letter"):
            st.download_button(
                "Download Cover Letter",
                report["cover_letter"],
                file_name=Path(report.get("cover_letter_path", "cover_letter.txt")).name,
                mime="text/plain",
            )


def main() -> None:
    """Render the Streamlit app."""
    _inject_css()

    st.title("Resume and Cover Letter Assistant")

    with st.sidebar:
        st.caption(f"Model: {os.getenv('MODEL', DEFAULT_MODEL)}")
        degree = st.selectbox("Degree", sorted(VALID_DEGREES), index=sorted(VALID_DEGREES).index("RTIS"))
        include_cover_letter = st.checkbox("Generate cover letter", value=True)
        use_sample = st.button("Load sample inputs")

    if use_sample:
        resume_bytes, sample_jd = _load_sample_inputs()
        st.session_state["sample_resume_bytes"] = resume_bytes
        st.session_state["jd_text"] = sample_jd

    left, right = st.columns([1, 1])
    with left:
        resume_upload = st.file_uploader("Resume PDF", type=["pdf"])
        if "sample_resume_bytes" in st.session_state and resume_upload is None:
            st.markdown('<div class="small-muted">Sample resume loaded.</div>', unsafe_allow_html=True)

    with right:
        jd_upload = st.file_uploader("Job description text file", type=["txt"])
        jd_default = st.session_state.get("jd_text", "")
        jd_text = st.text_area("Job description", value=jd_default, height=260)

    if jd_upload is not None:
        try:
            jd_text = _read_uploaded_text(jd_upload)
            st.session_state["jd_text"] = jd_text
        except UnicodeDecodeError:
            st.error("Could not decode the uploaded JD file as UTF-8.")

    run = st.button("Run analysis", type="primary")
    if run:
        try:
            if resume_upload is not None:
                resume_text = _read_uploaded_resume(resume_upload)
            elif "sample_resume_bytes" in st.session_state:
                class _SampleUpload:
                    name = SAMPLE_RESUME.name

                    def getvalue(self):
                        return st.session_state["sample_resume_bytes"]

                resume_text = _read_uploaded_resume(_SampleUpload())
            else:
                st.error("Upload a resume PDF or load the sample inputs.")
                return

            if not jd_text.strip():
                st.error("Paste a job description or upload a text file.")
                return

            report = _run_pipeline(resume_text, jd_text.strip(), degree, include_cover_letter)
            st.session_state["report"] = report
            st.success("Analysis complete.")
        except ValueError as exc:
            st.error(str(exc))
        except RuntimeError as exc:
            st.error(f"LLM error: {exc}")
        except OSError as exc:
            st.error(f"File error: {exc}")

    if "report" in st.session_state:
        _show_report(st.session_state["report"])


if __name__ == "__main__":
    main()

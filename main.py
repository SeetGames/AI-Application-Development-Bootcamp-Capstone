"""
main.py - CLI entry point for the Resume and Cover Letter Assistant.

The default run executes the Day 4 Resume x JD analysis pipeline. Passing
--cover-letter adds the capstone cover-letter draft flow.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from analyzer import (
    extract_resume_profile,
    extract_jd_profile,
    analyse_keyword_match,
    analyse_bullets,
    analyse_jargon,
    analyse_structure,
    analyse_degree_alignment,
    summarise_overall,
    compute_overall_score,
    generate_cover_letter,
    revise_cover_letter,
)
from parse import read_resume_pdf, read_jd_text
from report import render_markdown


VALID_DEGREES = {"RTIS", "IMGD", "UXGD", "BFA"}
ATS_PASS_THRESHOLD = 60
DEFAULT_MODEL = "groq/llama-3.3-70b-versatile"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments, accepting either positional or named inputs."""
    parser = argparse.ArgumentParser(
        description="Resume x JD analyzer with optional cover-letter generation."
    )
    parser.add_argument("positional", nargs="*", help="Optional: resume.pdf jd.txt degree")
    parser.add_argument("--resume", help="Path to the PDF resume.")
    parser.add_argument("--jd", help="Path to the plain-text job description.")
    parser.add_argument("--degree", metavar="DEGREE", help="RTIS, IMGD, UXGD, or BFA.")
    parser.add_argument(
        "--cover-letter",
        action="store_true",
        help="Generate a tailored cover letter draft after the analysis report.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="After generating a cover letter, accept follow-up revision requests.",
    )
    args = parser.parse_args()

    if args.positional:
        if len(args.positional) != 3:
            parser.error("positional usage requires exactly: resume.pdf jd.txt degree")
        if args.resume or args.jd or args.degree:
            parser.error("use either positional arguments or --resume/--jd/--degree, not both")
        args.resume, args.jd, args.degree = args.positional

    if not args.resume or not args.jd or not args.degree:
        parser.error("resume, jd, and degree are required")

    args.degree = args.degree.upper()
    if args.degree not in VALID_DEGREES:
        parser.error(f"degree must be one of: {', '.join(sorted(VALID_DEGREES))}")

    if args.interactive:
        args.cover_letter = True

    return args


def _write_json(path: Path, data: dict) -> None:
    """Write a JSON file using UTF-8."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _print_summary(summary: str) -> None:
    """Print summary bullets with a blank line above."""
    if summary.strip():
        print()
        print(summary.strip())


def _interactive_revisions(report: dict, draft: str, path: Path) -> str:
    """Run optional follow-up cover-letter revisions from stdin."""
    current = draft
    print()
    print("Enter cover-letter revision requests. Press Enter on a blank line to finish.")
    while True:
        request = input("Revision request: ").strip()
        if not request:
            break
        current = revise_cover_letter(report, current, request)
        path.write_text(current, encoding="utf-8")
        print(f"Updated cover letter: {path}")
    return current


def main() -> int:
    """Run the full analysis pipeline and write output artifacts."""
    args = parse_args()
    model = os.getenv("MODEL", DEFAULT_MODEL)
    print(f"Using model: {model}")

    try:
        print(f"[1/8] Parsing resume: {args.resume}")
        resume_text = read_resume_pdf(args.resume)
        print(f"[2/8] Reading JD: {args.jd} (degree={args.degree})")
        jd_text = read_jd_text(args.jd)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    try:
        print("[3/8] Extracting resume profile (LLM)...")
        resume_profile = extract_resume_profile(resume_text)

        print("[4/8] Extracting JD profile (LLM)...")
        jd_profile = extract_jd_profile(jd_text)

        print("[5/8] Keyword match (LLM)...")
        keyword_match = analyse_keyword_match(resume_profile, jd_profile)

        print("[6/8] Bullet audit (LLM)...")
        bullets = analyse_bullets(resume_profile)

        print("[7/8] Jargon, structure, degree alignment (LLM x3)...")
        jargon = analyse_jargon(resume_profile, args.degree, jd_profile)
        structure = analyse_structure(resume_text)
        degree_alignment = analyse_degree_alignment(jd_profile, args.degree)
    except RuntimeError as exc:
        print(f"LLM error: {exc}", file=sys.stderr)
        return 1

    now = datetime.now()
    report = {
        "meta": {
            "generated_at": now.isoformat(timespec="seconds"),
            "model": model,
            "resume_path": args.resume,
            "jd_path": args.jd,
            "degree": args.degree,
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

    try:
        print("[8/8] Final summary (LLM)...")
        report["summary"] = summarise_overall(report)

        ts = now.strftime("%Y%m%d_%H%M%S")
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)

        cover_letter_path = None
        if args.cover_letter:
            print("[extra] Cover letter draft (LLM)...")
            cover_letter = generate_cover_letter(report)
            cover_letter_path = output_dir / f"cover_letter_{ts}.txt"
            cover_letter_path.write_text(cover_letter, encoding="utf-8")
            report["cover_letter"] = cover_letter
            report["cover_letter_path"] = str(cover_letter_path)

            if args.interactive:
                report["cover_letter"] = _interactive_revisions(
                    report,
                    cover_letter,
                    cover_letter_path,
                )

        json_path = output_dir / f"match_report_{ts}.json"
        md_path = output_dir / f"match_report_{ts}.md"
        _write_json(json_path, report)
        render_markdown(report, out_path=str(md_path))
    except RuntimeError as exc:
        print(f"LLM error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Output error: {exc}", file=sys.stderr)
        return 1

    verdict = "PASS" if report["passes_ats_threshold"] else "FAIL"
    print()
    print(f"Score: {report['overall_score']}/100  ({verdict} 60% ATS threshold)")
    print(f"JSON:  {json_path}")
    print(f"MD:    {md_path}")
    if cover_letter_path:
        print(f"Cover letter: {cover_letter_path}")
    _print_summary(report.get("summary", ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

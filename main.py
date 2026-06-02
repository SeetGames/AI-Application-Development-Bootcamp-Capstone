"""
main.py — CLI entry point for the Day 4 Resume Analyzer.

Task 5 of the Day 4 lab (Track A).
Study material reference: §4 The Multi-Stage Pipeline

Your job is to write the main() function. The argument parser is already
provided — do not modify parse_args().
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from parse import read_resume_pdf, read_jd_text
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
)
from report import render_markdown


VALID_DEGREES = {"RTIS", "IMGD", "UXGD", "BFA"}
ATS_PASS_THRESHOLD = 60


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments. Pre-provided — do not modify.

    Usage:
        python main.py --resume path/to/resume.pdf \\
                       --jd     path/to/job_description.txt \\
                       --degree RTIS
    """
    parser = argparse.ArgumentParser(
        description="Day 4 Resume × JD Analyzer — diagnostic feedback only."
    )
    parser.add_argument(
        "--resume", required=True,
        help="Path to the PDF résumé."
    )
    parser.add_argument(
        "--jd", required=True,
        help="Path to the plain-text job description."
    )
    parser.add_argument(
        "--degree", required=True, choices=sorted(VALID_DEGREES),
        help="Your DigiPen degree code (RTIS | IMGD | UXGD | BFA)."
    )
    return parser.parse_args()


def main() -> int:
    """
    Orchestrate the full analysis pipeline. Return 0 on success, 1 on error.

    Steps to implement:
      [1/8] Parse CLI arguments (call parse_args()).
      [2/8] Load documents — call read_resume_pdf() and read_jd_text();
            catch ValueError and print to stderr, then return 1.
      [3/8] Extract structured profiles — call extract_resume_profile() and
            extract_jd_profile(); print progress as "[3/8] Extracting profiles…".
      [4/8] Run the 5 evaluations in order:
              analyse_keyword_match(resume_profile, jd_profile)
              analyse_bullets(resume_profile)
              analyse_jargon(resume_profile, args.degree, jd_profile)
              analyse_structure(resume_text)
              analyse_degree_alignment(jd_profile, args.degree)
            Print a [4/8]…[8/8] progress line for each.
      [9/9] Assemble the report dict:
              {
                "resume_profile":  resume_profile,
                "jd_profile":      jd_profile,
                "keyword_match":   keyword_match,
                "bullets":         bullets,
                "jargon":          jargon,
                "structure":       structure,
                "degree_alignment": degree_alignment,
              }
            Compute overall_score with compute_overall_score(report).
            Add to report:
              report["overall_score"]       = overall_score
              report["passes_ats_threshold"] = overall_score >= ATS_PASS_THRESHOLD
              report["summary"]             = summarise_overall(report)

            Build a timestamped filename:
              ts = datetime.now().strftime("%Y%m%d_%H%M%S")
              json_path = Path("outputs") / f"match_report_{ts}.json"
              md_path   = Path("outputs") / f"match_report_{ts}.md"

            Save JSON: json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            Save Markdown: render_markdown(report, out_path=md_path)

            Print the final verdict and the 3-bullet summary.
            Return 0.
    """
    # TODO: implement this function
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())

"""
parse.py — PDF and plain-text reading; no LLM calls.

Task 1 of the Day 4 lab (Track A).
Study material reference: §5 Document Parsing
"""

import re
import sys

from pypdf import PdfReader


# Résumé text below this character count likely means an image-only PDF.
_MIN_RESUME_CHARS = 200

# JD text below this character count likely means the student forgot to paste content.
_MIN_JD_CHARS = 100

# Rough token estimate: 1 token ≈ 4 chars. Truncate above ~6 000 tokens.
_MAX_RESUME_CHARS = 6000 * 4


def read_resume_pdf(path: str) -> str:
    """
    Extract plain text from a PDF résumé using pypdf.

    Requirements:
    1. Open the file with ``pypdf.PdfReader(path)``.
       Raise ``ValueError`` with a clear message if the file is not found or
       cannot be opened (catch ``FileNotFoundError`` separately from ``Exception``).
    2. If the résumé has more than 2 pages, print a warning to ``sys.stderr``.
       ATS systems typically expect a one-page résumé.
    3. Extract text from each page with ``page.extract_text() or ""``.
       Join page texts with ``"\\n\\n"``.
    4. Collapse runs of 3 or more consecutive blank lines to 2 using ``re.sub``.
    5. Strip leading/trailing whitespace from the full text.
    6. Raise ``ValueError`` if the result is shorter than ``_MIN_RESUME_CHARS``
       characters (likely an image-based / scanned PDF — no text layer).
    7. Truncate to ``_MAX_RESUME_CHARS`` characters if very long, and print a
       warning to ``sys.stderr``.

    Args:
        path: Path to the PDF file.

    Returns:
        Extracted plain text.

    Raises:
        ValueError: If the file is not found, cannot be opened, or is too short.
    """
    try:
        reader = PdfReader(path)
    except FileNotFoundError as exc:
        raise ValueError(f"Resume file not found: {path}") from exc
    except Exception as exc:
        raise ValueError(f"Could not open resume PDF '{path}': {exc}") from exc

    if len(reader.pages) > 2:
        print(
            f"WARNING: resume has {len(reader.pages)} pages; ATS resumes are usually 1 page.",
            file=sys.stderr,
        )

    page_texts = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(page_texts)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if len(text) < _MIN_RESUME_CHARS:
        raise ValueError(
            f"Resume text is too short ({len(text)} chars). "
            "The PDF may be image-only or scanned."
        )

    if len(text) > _MAX_RESUME_CHARS:
        print(
            f"WARNING: resume text is {len(text)} chars; truncating to {_MAX_RESUME_CHARS}.",
            file=sys.stderr,
        )
        text = text[:_MAX_RESUME_CHARS]

    return text


def read_jd_text(path: str) -> str:
    """
    Read a plain-text job description file (UTF-8).

    Requirements:
    1. Open the file with ``open(path, encoding="utf-8")``.
       Raise ``ValueError`` with a clear message if the file is not found.
       Catch other ``Exception`` types and raise ``ValueError`` with the cause.
    2. Strip the content.
    3. Raise ``ValueError`` if the stripped content has fewer than
       ``_MIN_JD_CHARS`` characters.

    Args:
        path: Path to the plain-text job description file.

    Returns:
        Content of the file as a string.

    Raises:
        ValueError: If the file is not found or the content is too short.
    """
    try:
        with open(path, encoding="utf-8") as file:
            text = file.read().strip()
    except FileNotFoundError as exc:
        raise ValueError(f"Job description file not found: {path}") from exc
    except Exception as exc:
        raise ValueError(f"Could not read job description '{path}': {exc}") from exc

    if len(text) < _MIN_JD_CHARS:
        raise ValueError(
            f"Job description text is too short ({len(text)} chars). "
            "Provide a complete plain-text job description."
        )

    return text

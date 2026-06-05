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


def _clean_extracted_text(page_texts: list[str]) -> str:
    """Join PDF page text and normalize excessive blank lines."""
    text = "\n\n".join(page_texts)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _extract_resume_with_pypdf(path: str) -> tuple[str, int]:
    """Extract PDF text with pypdf."""
    reader = PdfReader(path, strict=False)
    page_texts = [page.extract_text() or "" for page in reader.pages]
    return _clean_extracted_text(page_texts), len(reader.pages)


def _extract_resume_with_pymupdf(path: str) -> tuple[str, int]:
    """Extract PDF text with PyMuPDF, which handles some PDFs pypdf rejects."""
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is not installed. Run `python -m pip install -r requirements.txt` "
            "and try again."
        ) from exc

    with fitz.open(path) as document:
        page_texts = [page.get_text("text") for page in document]
        return _clean_extracted_text(page_texts), document.page_count


def _validate_resume_text(text: str) -> str:
    """Validate and truncate extracted resume text."""
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


def read_resume_pdf(path: str) -> str:
    """
    Extract plain text from a PDF résumé.

    pypdf is tried first because it is lightweight and already used by the
    project. Some valid PDFs have object streams or trailers that pypdf cannot
    parse, so PyMuPDF is used as a fallback before reporting an open error.

    Args:
        path: Path to the PDF file.

    Returns:
        Extracted plain text.

    Raises:
        ValueError: If the file is not found, cannot be opened, or is too short.
    """
    errors = []
    try:
        text, page_count = _extract_resume_with_pypdf(path)
    except FileNotFoundError as exc:
        raise ValueError(f"Resume file not found: {path}") from exc
    except Exception as exc:
        errors.append(f"pypdf: {exc}")
        try:
            text, page_count = _extract_resume_with_pymupdf(path)
        except FileNotFoundError as fallback_exc:
            raise ValueError(f"Resume file not found: {path}") from fallback_exc
        except Exception as fallback_exc:
            errors.append(f"PyMuPDF: {fallback_exc}")
            details = "; ".join(errors)
            raise ValueError(f"Could not open resume PDF '{path}': {details}") from fallback_exc

    if page_count > 2:
        print(
            f"WARNING: resume has {page_count} pages; ATS resumes are usually 1 page.",
            file=sys.stderr,
        )

    return _validate_resume_text(text)




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

# Resume and Cover Letter Assistant

## 1. Project Title and Description

Resume and Cover Letter Assistant is a Python CLI app for students and early-career applicants. It compares a PDF resume against a plain-text job description, produces an ATS-style compatibility report, and can generate a tailored cover letter draft from verified resume facts.

## 2. Problem Statement

Applicants often miss job-specific keywords or use project language that does not translate clearly to recruiters. This tool gives structured feedback on resume fit before submission and helps draft a cover letter that stays grounded in the applicant's actual experience.

## 3. Technology Stack

- Python 3.10+
- Groq API through LiteLLM
- `python-dotenv` for `.env` secrets
- `pypdf` for PDF text extraction
- Markdown and JSON output files

Default model: `groq/llama-3.3-70b-versatile`.

## 4. Setup Instructions

1. Clone or download this repository.
2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and add your Groq key:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Run the analyzer:

   ```powershell
   python main.py inputs/strong_resume.pdf inputs/job_rtis_systems_engineer.txt RTIS
   ```

6. Run the analyzer with cover-letter generation:

   ```powershell
   python main.py inputs/strong_resume.pdf inputs/job_rtis_systems_engineer.txt RTIS --cover-letter
   ```

Reports are written to `outputs/` as timestamped `.json`, `.md`, and optional cover-letter `.txt` files.

## 5. Usage Examples

Example 1: strong resume against a relevant systems job.

```powershell
python main.py inputs/strong_resume.pdf inputs/job_rtis_systems_engineer.txt RTIS --cover-letter
```

Expected output includes a score, a PASS/FAIL verdict, paths to the JSON and Markdown reports, and a cover-letter text file.

Example 2: weak resume against an unrelated marketing job.

```powershell
python main.py inputs/weak_resume.pdf inputs/job_unrelated.txt RTIS
```

Expected output is a lower score with missing keyword diagnostics and a Markdown report showing which scoring components pulled the total down.

Optional follow-up cover-letter revision mode:

```powershell
python main.py inputs/strong_resume.pdf inputs/job_rtis_systems_engineer.txt RTIS --interactive
```

After the first draft is generated, type revision requests such as "make it shorter" or "make the tone more formal". Press Enter on a blank line to finish.

## 6. Known Limitations

- The parser only supports text-based PDFs. Scanned or image-only resumes will fail validation.
- The score is a heuristic based on the bootcamp rubric and a 60% ATS threshold; real employers may use different filters.
- Cover letters are grounded in extracted resume facts, so extraction mistakes can affect the draft.

## 7. Future Improvements

- Add a Streamlit interface for uploading a resume and job description without using the terminal.
- Add automated regression tests with mocked LLM responses for the full pipeline.
- Add OCR support for scanned PDFs.

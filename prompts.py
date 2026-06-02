"""
prompts.py — all 8 system prompts used by analyzer.py.

Task 3 of the Day 4 lab (Track A).
Study material references:
  §3.3 Schema-First Prompt Design
  §6.1 Extraction Prompts
  §6.2 Evaluation Prompts
  §6.3 Feedback-Only Principle

Every prompt must follow ICCO structure:
  Instruction  — what the model must do
  Context      — relevant background (rubric tables, schema description)
  Constraints  — rules the model must not break
  Output       — the exact JSON schema expected

Every prompt (except OVERALL_SUMMARY_PROMPT) must end with:
  "Output ONLY a valid JSON object matching the schema above. No prose. No
  markdown fences. No commentary. Never rewrite or generate résumé content."

Temperature guidance (set in the ask_json() call in analyzer.py):
  Extraction prompts (RESUME_PROFILE, JD_PROFILE): 0.0
  Evaluation prompts (KEYWORD_MATCH, BULLET_QUALITY, JARGON, STRUCTURE, DEGREE): 0.2–0.3
  OVERALL_SUMMARY_PROMPT: 0.3
"""


# ---------------------------------------------------------------------------
# Extraction prompts
# ---------------------------------------------------------------------------

# Purpose: extract a structured candidate profile from plain résumé text.
# Input to ask_json(): system=RESUME_PROFILE_PROMPT, user="RÉSUMÉ TEXT:\n\n{text}"
# Expected output schema — all fields required; arrays may be empty:
# {
#   "name": "string",
#   "contact": {
#     "email": "string", "phone": "string", "linkedin": "string",
#     "github": "string", "portfolio": "string"
#   },
#   "summary": "string",
#   "education": [{"school": "string", "degree": "string",
#                  "graduation_date": "string", "courses": ["string"]}],
#   "projects":  [{"title": "string", "date": "string", "bullets": ["string"]}],
#   "experience":[{"title": "string", "company": "string",
#                  "date": "string", "bullets": ["string"]}],
#   "skills": {
#     "languages": ["string"], "frameworks": ["string"], "tools": ["string"],
#     "concepts": ["string"], "platforms": ["string"]
#   }
# }
RESUME_PROFILE_PROMPT = """
TODO: Write the full ICCO-structured system prompt here.
"""


# Purpose: extract a structured JD profile from free-form job posting text.
# Input to ask_json(): system=JD_PROFILE_PROMPT, user="JOB DESCRIPTION TEXT:\n\n{text}"
# Expected output schema — all fields required; arrays may be empty:
# {
#   "job_title": "string",
#   "company": "string",
#   "location": "string",
#   "experience_level": "string",
#   "required_skills": ["string"],
#   "preferred_skills": ["string"],
#   "tools_technologies": ["string"],
#   "responsibilities": ["string"],
#   "soft_skills": ["string"],
#   "buzzwords": ["string"],
#   "deal_breakers": ["string"]
# }
JD_PROFILE_PROMPT = """
TODO: Write the full ICCO-structured system prompt here.
"""


# ---------------------------------------------------------------------------
# Evaluation prompts
# ---------------------------------------------------------------------------

# Purpose: compare résumé keywords against JD requirements; produce a score.
# Input to ask_json():
#   system=KEYWORD_MATCH_PROMPT
#   user="RÉSUMÉ PROFILE:\n{json}\n\nJD PROFILE:\n{json}"
# Expected output schema:
# {
#   "present": [{"keyword": "string", "category": "language|framework|tool|concept|soft_skill|buzzword",
#                "found_in": "summary|projects|experience|education|skills", "exact_match": true}],
#   "missing": [{"keyword": "string", "category": "...", "importance": "required|preferred",
#                "suggested_section": "skills|projects|experience|summary",
#                "why_it_matters": "string (25 words max — diagnostic only)"}],
#   "keyword_match_score": 0
# }
# Scoring formula: 100 × (required_skills found in résumé) / max(1, total required_skills)
KEYWORD_MATCH_PROMPT = """
TODO: Write the full ICCO-structured system prompt here.
"""


# Purpose: score each résumé bullet against the Action → Technology → Impact rubric.
# Input to ask_json(): system=BULLET_QUALITY_PROMPT, user="RÉSUMÉ PROFILE:\n{json}"
# Expected output schema:
# {
#   "bullets": [{"source": "projects|experience", "parent_title": "string",
#                "bullet_text": "string (verbatim)", "has_action_verb": true,
#                "has_specific_technology": true, "has_measurable_impact": false,
#                "level": "L1_OK|L2_BETTER|L3_BEST",
#                "what_is_missing": "string (20 words max — diagnose only)"}],
#   "bullet_quality_avg": 0
# }
# Scoring formula: round(100 × sum(level_score) / (3 × count)) where L1=1, L2=2, L3=3
# IMPORTANT: embed the Action→Technology→Impact rubric verbatim inside this prompt,
# including the L1/L2/L3 reference level examples.
BULLET_QUALITY_PROMPT = """
TODO: Write the full ICCO-structured system prompt here.
      Remember to embed the ATI rubric verbatim.
"""


# Purpose: detect game-dev jargon that should be translated for non-game recruiters.
# Input to ask_json():
#   system=JARGON_AUDIT_PROMPT
#   user="DEGREE PROGRAM: {code}\n\nRÉSUMÉ PROFILE:\n{json}\n\nJD PROFILE:\n{json}"
# Expected output schema:
# {
#   "flags": [{"bullet_text": "string (verbatim)", "term_used": "string",
#              "suggested_translation": "string (from the table only)",
#              "severity": "low|medium|high"}],
#   "jargon_score": 0
# }
# Severity rules: high if JD has no game-dev language; medium if mixed; low if game studio role.
# Scoring formula: max(0, 100 - 10*high_count - 5*medium_count - 2*low_count)
# IMPORTANT: embed the full 15-row Game-Dev → SE translation table verbatim.
JARGON_AUDIT_PROMPT = """
TODO: Write the full ICCO-structured system prompt here.
      Remember to embed the 15-row translation table verbatim.
"""


# Purpose: audit Three-Thirds layout compliance and ATS formatting.
# Input to ask_json(): system=STRUCTURE_AUDIT_PROMPT, user="RÉSUMÉ TEXT:\n\n{text}"
# Expected output schema:
# {
#   "page_count_estimate": 1,
#   "single_column_likely": true,
#   "section_headings_present": ["string"],
#   "section_headings_missing": ["string"],
#   "three_thirds": {
#     "top_third_has_name": true,
#     "top_third_has_contact": true,
#     "top_third_has_summary_or_featured": true,
#     "middle_third_has_projects_or_experience": true,
#     "bottom_third_has_skills_keywords": true
#   },
#   "ats_red_flags": [{"issue": "string", "evidence": "string"}],
#   "structure_score": 0
# }
# IMPORTANT: embed the Three-Thirds zone table and ATS formatting rules verbatim.
STRUCTURE_AUDIT_PROMPT = """
TODO: Write the full ICCO-structured system prompt here.
      Remember to embed the Three-Thirds table and ATS rules verbatim.
"""


# Purpose: assess how well the JD's job title fits the student's degree programme.
# Input to ask_json():
#   system=DEGREE_ALIGNMENT_PROMPT
#   user="DEGREE PROGRAM: {code}\n\nJD PROFILE:\n{json}"
# Expected output schema:
# {
#   "student_degree": "string",
#   "jd_title": "string",
#   "title_on_suggested_list": true,
#   "matched_against": "string (the suggested-titles list used)",
#   "fit_commentary": "string (2–3 sentences — diagnostic only)",
#   "degree_alignment_score": 0
# }
# Include in context: the four degree-code → suggested job title lists from
# reference/Personal_Resume_Handout.md.
DEGREE_ALIGNMENT_PROMPT = """
TODO: Write the full ICCO-structured system prompt here.
      Include the four degree → title lists from the Personal_Resume_Handout.
"""


# ---------------------------------------------------------------------------
# Synthesis prompt
# ---------------------------------------------------------------------------

# Purpose: produce a 3-bullet plain Markdown executive summary from the full report.
# Input to ask_text(): system=OVERALL_SUMMARY_PROMPT, user="ANALYSIS REPORT:\n{json}"
# Returns: plain Markdown string (not JSON).
# NOTE: this prompt does NOT need the JSON output constraint line.
#       It also does NOT need a JSON schema — ask_text() is used, not ask_json().
# The summary must be diagnostic only — no rewrites, no generated résumé content.
OVERALL_SUMMARY_PROMPT = """
TODO: Write the full ICCO-structured system prompt here.
      Output is plain Markdown bullets, not JSON.
"""

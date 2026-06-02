"""
prompts.py - system prompts used by analyzer.py.

The analysis prompts follow ICCO structure:
Instruction, Context, Constraints, Output. JSON-returning prompts embed the
exact schema expected by downstream code and end with the lab's no-prose rule.
"""

JSON_ONLY_RULE = (
    "Output ONLY a valid JSON object matching the schema above. No prose. "
    "No markdown fences. No commentary. Never rewrite or generate "
    "r\u00e9sum\u00e9 content."
)


# ---------------------------------------------------------------------------
# Extraction prompts
# ---------------------------------------------------------------------------

RESUME_PROFILE_PROMPT = """
Instruction:
Extract a structured candidate profile from the resume text supplied by the user.
Copy facts that are literally present in the document. Your job is extraction, not evaluation.

Context:
The document is a Singapore entry-level technical resume for an ATS-style analysis pipeline.
Downstream code depends on the exact JSON keys below. Projects and experience bullets will be audited later, so preserve bullet wording verbatim.

Constraints:
- Use only the supplied resume text.
- Never invent contact details, skills, courses, dates, companies, metrics, or project facts.
- If a field is absent, return an empty string, empty array, or empty object using the schema shape.
- Normalise obvious skill spellings only when the source clearly supports it, for example "py" to "Python" or "Github Actions" to "GitHub Actions".
- Keep project and experience bullets as verbatim strings; do not improve, shorten, rewrite, or generate bullets.
- Separate projects from professional experience based on section headings and surrounding text.

Output:
{
  "name": "string",
  "contact": {
    "email": "string",
    "phone": "string",
    "linkedin": "string",
    "github": "string",
    "portfolio": "string"
  },
  "summary": "string",
  "education": [
    {
      "school": "string",
      "degree": "string",
      "graduation_date": "string",
      "courses": ["string"]
    }
  ],
  "projects": [
    {
      "title": "string",
      "date": "string",
      "bullets": ["string"]
    }
  ],
  "experience": [
    {
      "title": "string",
      "company": "string",
      "date": "string",
      "bullets": ["string"]
    }
  ],
  "skills": {
    "languages": ["string"],
    "frameworks": ["string"],
    "tools": ["string"],
    "concepts": ["string"],
    "platforms": ["string"]
  }
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate r\u00e9sum\u00e9 content.
"""


JD_PROFILE_PROMPT = """
Instruction:
Extract a structured job-description profile from the job posting text supplied by the user.
Copy requirements, skills, tools, responsibilities, and constraints that are literally present.

Context:
The posting is used by an ATS compatibility pipeline for Singapore entry-level or early-career roles.
Downstream evaluation compares the resume profile against required skills, preferred skills, tools, soft skills, and deal breakers.

Constraints:
- Use only the supplied job description text.
- Never invent a company, title, location, salary, qualification, technology, or requirement.
- Put must-have requirements in required_skills and optional or nice-to-have requirements in preferred_skills.
- Put specific tools, platforms, languages, frameworks, and products in tools_technologies even if they also appear in required_skills or preferred_skills.
- Put communication, teamwork, problem-solving, and similar behavioural requirements in soft_skills.
- If a field is absent, return an empty string or empty array using the schema shape.

Output:
{
  "job_title": "string",
  "company": "string",
  "location": "string",
  "experience_level": "string",
  "required_skills": ["string"],
  "preferred_skills": ["string"],
  "tools_technologies": ["string"],
  "responsibilities": ["string"],
  "soft_skills": ["string"],
  "buzzwords": ["string"],
  "deal_breakers": ["string"]
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate r\u00e9sum\u00e9 content.
"""


# ---------------------------------------------------------------------------
# Evaluation prompts
# ---------------------------------------------------------------------------

KEYWORD_MATCH_PROMPT = """
Instruction:
Compare the resume profile JSON against the JD profile JSON and audit ATS keyword coverage.

Context:
ATS screening primarily checks whether required job keywords are visible in the resume.
Use the JD profile as the source of truth for required and preferred keywords.
Use the resume profile as the source of truth for whether the candidate explicitly shows each keyword.

Evaluation criteria:
- Required keywords come from jd_profile.required_skills and must be weighted most heavily.
- Tools and technologies from jd_profile.tools_technologies may count as required if they also appear in required_skills or responsibilities.
- Preferred keywords come from jd_profile.preferred_skills, tools_technologies not already required, soft_skills, and buzzwords.
- Count a keyword as present only if it is explicit in the resume profile or is a clear synonym with the same professional meaning.
- Do not give credit for skills that are merely plausible from the degree or project title.
- keyword_match_score = round(100 * required_keywords_found / max(1, total_required_keywords)).

Constraints:
- Return diagnostic observations only.
- Do not rewrite missing keywords into resume text.
- For each missing item, suggested_section is only a likely place to address the gap; it is not generated resume content.
- Use categories only from: language, framework, tool, concept, soft_skill, buzzword.
- Clamp keyword_match_score to an integer from 0 to 100.

Output:
{
  "present": [
    {
      "keyword": "string",
      "category": "language|framework|tool|concept|soft_skill|buzzword",
      "found_in": "summary|projects|experience|education|skills",
      "exact_match": true
    }
  ],
  "missing": [
    {
      "keyword": "string",
      "category": "language|framework|tool|concept|soft_skill|buzzword",
      "importance": "required|preferred",
      "suggested_section": "skills|projects|experience|summary",
      "why_it_matters": "string (25 words max - diagnostic only)"
    }
  ],
  "keyword_match_score": 0
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate r\u00e9sum\u00e9 content.
"""


BULLET_QUALITY_PROMPT = """
Instruction:
Score every project and experience bullet in the resume profile against the Action, Technology, Impact rubric.

Context:
This rubric evaluates whether a technical resume bullet is specific enough for a recruiter or ATS reviewer.

Action, Technology, Impact rubric:
| Component | Requirement | Evidence to look for |
|---|---|---|
| Action | The bullet starts with or clearly contains a concrete action verb. | Designed, built, implemented, automated, deployed, analysed, optimised, tested, integrated, led. |
| Technology | The bullet names a specific language, framework, tool, platform, protocol, algorithm, or technical method. | Python, C++, FastAPI, Docker, AWS, Terraform, Redis, TCP/IP, SAT, Vulkan. |
| Impact | The bullet states measurable or concrete outcome, scale, reliability, user value, or operational result. | 40% reduction, 500+ tasks, 99.9% uptime, under 5 minutes, 60 fps, 3-month period. |

Reference levels:
| Level | Meaning | Standard |
|---|---|---|
| L1_OK | Basic claim. | Has an action, but technology or impact is vague or missing. |
| L2_BETTER | Specific technical work. | Has action plus specific technology, or action plus concrete impact. |
| L3_BEST | Recruiter-ready evidence. | Has action, specific technology, and measurable or concrete impact. |

Scoring:
- L1_OK = 1 point.
- L2_BETTER = 2 points.
- L3_BEST = 3 points.
- bullet_quality_avg = round(100 * sum(level_score) / (3 * count)).
- If there are no bullets, bullet_quality_avg = 0.

Constraints:
- Evaluate only bullets found in resume_profile.projects and resume_profile.experience.
- bullet_text must be copied verbatim from the profile.
- what_is_missing must diagnose the absent component only; it must never provide a rewritten bullet.
- Clamp bullet_quality_avg to an integer from 0 to 100.

Output:
{
  "bullets": [
    {
      "source": "projects|experience",
      "parent_title": "string",
      "bullet_text": "string (verbatim)",
      "has_action_verb": true,
      "has_specific_technology": true,
      "has_measurable_impact": false,
      "level": "L1_OK|L2_BETTER|L3_BEST",
      "what_is_missing": "string (20 words max - diagnose only)"
    }
  ],
  "bullet_quality_avg": 0
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate r\u00e9sum\u00e9 content.
"""


JARGON_AUDIT_PROMPT = """
Instruction:
Detect game-development jargon in resume bullets that may be unclear to non-game recruiters, and flag diagnostic translations.

Context:
Many DigiPen resumes describe game projects. For non-game roles, some game-specific terms should be translated conceptually so the candidate can understand what recruiters may miss.

Game-Dev to Software Engineering translation table:
| Game-dev term | Suggested translation |
|---|---|
| game loop | application loop or event loop |
| gameplay loop | user workflow or event loop |
| NPC AI | agent decision logic |
| enemy AI | autonomous agent behaviour |
| mob spawner | event-driven entity generation |
| HP bar | status indicator or health metric UI |
| HUD | operational dashboard or status display |
| level editor | content editor or configuration editor |
| tiled map | grid-based layout or data structure |
| sprite rendering | 2D rendering or UI rendering |
| asset pipeline | build pipeline or content pipeline |
| netcode | network synchronisation or protocol logic |
| collision detection | spatial query or geometry processing |
| physics engine | simulation engine |
| shader | GPU rendering program |

Severity rules:
- high: the JD has no game-development language and the role is outside games or interactive media.
- medium: the JD is a mixed technical role where some game terms may transfer but still need clearer framing.
- low: the JD is a game studio, interactive simulation, graphics, or game-adjacent role.

Scoring:
- jargon_score = max(0, 100 - 10*high_count - 5*medium_count - 2*low_count).

Constraints:
- Only flag terms that appear in the resume profile.
- term_used must be the exact game-dev source term from the left column of the table, not a translated or generic term.
- suggested_translation must come from the table above only.
- A suggested translation is diagnostic only; never rewrite the resume bullet.
- If no game-dev terms are found, return an empty flags array and jargon_score 100.
- Clamp jargon_score to an integer from 0 to 100.

Output:
{
  "flags": [
    {
      "bullet_text": "string (verbatim)",
      "term_used": "string",
      "suggested_translation": "string (from the table only)",
      "severity": "low|medium|high"
    }
  ],
  "jargon_score": 0
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate r\u00e9sum\u00e9 content.
"""


STRUCTURE_AUDIT_PROMPT = """
Instruction:
Audit the raw resume text for Three-Thirds layout compliance and ATS-friendly formatting.

Context:
The Three-Thirds model checks whether a one-page resume puts the most scannable information in predictable zones.

Three-Thirds zone table:
| Zone | Expected content |
|---|---|
| Top third | Candidate name, contact details, concise summary or featured technical focus. |
| Middle third | Strongest projects or experience, with technical bullets and impact evidence. |
| Bottom third | Skills, tools, education, and keyword-dense supporting information. |

ATS formatting rules:
| Rule | Standard |
|---|---|
| Page length | One page is ideal for entry-level; two pages may be acceptable; more than two is a concern. |
| Columns | Single-column text is safest for ATS parsing. |
| Headings | Use standard headings such as Summary, Projects, Experience, Education, Skills. |
| Contact | Name, email, phone, and links should be visible near the top. |
| Text layer | Content should be selectable text, not only images. |
| Keyword visibility | Skills should be explicit and grouped where an ATS can find them. |
| Decorative formatting | Avoid tables, text boxes, icons-only contact details, and complex graphics that may parse poorly. |

Scoring guidance:
- Start from 100.
- Subtract 10 for each missing Three-Thirds boolean.
- Subtract 5 for each missing standard heading.
- Subtract 10 for each ATS red flag.
- Clamp structure_score to an integer from 0 to 100.

Constraints:
- Use only evidence visible in the supplied resume text.
- page_count_estimate is an estimate from the text; do not invent exact PDF metadata.
- ats_red_flags must include short evidence only, not rewritten resume content.

Output:
{
  "page_count_estimate": 1,
  "single_column_likely": true,
  "section_headings_present": ["string"],
  "section_headings_missing": ["string"],
  "three_thirds": {
    "top_third_has_name": true,
    "top_third_has_contact": true,
    "top_third_has_summary_or_featured": true,
    "middle_third_has_projects_or_experience": true,
    "bottom_third_has_skills_keywords": true
  },
  "ats_red_flags": [
    {
      "issue": "string",
      "evidence": "string"
    }
  ],
  "structure_score": 0
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate r\u00e9sum\u00e9 content.
"""


DEGREE_ALIGNMENT_PROMPT = """
Instruction:
Assess how well the JD job title and role family align with the student's DigiPen degree programme.

Context:
Use these degree-code to suggested job-title lists as the grounding rubric.

RTIS suggested titles:
Software Engineer, Systems Engineer, Backend Engineer, Platform Engineer, Infrastructure Engineer, DevOps Engineer, Tools Engineer, C++ Developer, Graphics Programmer, Engine Programmer, Simulation Engineer, Gameplay Programmer.

IMGD suggested titles:
Game Designer, Level Designer, Systems Designer, Gameplay Designer, Technical Designer, Producer, QA Game Analyst, Narrative Designer, Content Designer, Interactive Designer.

UXGD suggested titles:
UX Designer, UI Designer, Product Designer, Interaction Designer, UX Researcher, Design Researcher, Front-End Designer, Visual Designer, Prototype Designer.

BFA suggested titles:
Concept Artist, 3D Artist, Environment Artist, Character Artist, Animator, Technical Artist, Illustrator, UI Artist, Motion Designer, Visual Development Artist.

Scoring rubric:
- 100: JD title is on the suggested list or a near-identical title.
- 80: JD title is in the same role family and strongly aligned.
- 60: JD is adjacent and plausible for the degree but not the primary target.
- 30: JD is weakly related; transferable skills exist but title fit is poor.
- 0: JD is unrelated to the degree pathway.

Constraints:
- Use the degree code and JD profile supplied by the user.
- title_on_suggested_list is true only for exact, near-exact, or obvious same-title-family matches.
- fit_commentary must be diagnostic only and must not rewrite resume or cover letter content.
- Clamp degree_alignment_score to an integer from 0 to 100.

Output:
{
  "student_degree": "string",
  "jd_title": "string",
  "title_on_suggested_list": true,
  "matched_against": "string (the suggested-titles list used)",
  "fit_commentary": "string (2-3 sentences - diagnostic only)",
  "degree_alignment_score": 0
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate r\u00e9sum\u00e9 content.
"""


# ---------------------------------------------------------------------------
# Synthesis and cover letter prompts
# ---------------------------------------------------------------------------

OVERALL_SUMMARY_PROMPT = """
Instruction:
Write a concise executive summary of the resume-to-JD analysis.

Context:
The user needs fast diagnostic feedback before deciding how to improve their own application materials.
The input report already contains all scores and findings.

Constraints:
- Return exactly three Markdown bullet points.
- Focus on the strongest signal, the largest gap, and the most actionable next diagnostic.
- Do not rewrite resume bullets, summaries, or cover letter text.
- Do not invent facts beyond the analysis report.
- Keep each bullet under 28 words.

Output:
- Bullet 1
- Bullet 2
- Bullet 3
"""


COVER_LETTER_PROMPT = """
Instruction:
Generate a tailored cover letter draft using only the supplied resume profile, JD profile, and analysis report.

Context:
This is a capstone Resume and Cover Letter Assistant. The draft should help an entry-level Singapore technology candidate apply for the target role while staying faithful to verified resume facts.

Constraints:
- Use only facts found in the supplied resume profile and report.
- Never invent employment history, metrics, education, skills, certifications, or personal details.
- Emphasise overlap between the resume and the JD; avoid claiming missing required skills as if the candidate has them.
- Keep the tone professional, direct, and suitable for a junior or entry-level applicant.
- Do not mention ATS scores, internal rubric names, or model analysis mechanics.
- Length: 250 to 350 words.

Output:
Return the cover letter draft as plain text with a greeting, 3 to 4 short paragraphs, and a closing sign-off.
"""


COVER_LETTER_REVISION_PROMPT = """
Instruction:
Revise an existing cover letter draft according to the user's follow-up request.

Context:
The assistant must preserve factual accuracy against the supplied resume profile, JD profile, and original analysis report.

Constraints:
- Use only verified facts from the supplied context.
- If the user asks to add an unsupported claim, omit the claim and keep the draft factual.
- Preserve the requested tone or length when it does not conflict with accuracy.
- Do not mention these rules in the output.
- Return only the revised cover letter draft.

Output:
Plain text revised cover letter draft.
"""

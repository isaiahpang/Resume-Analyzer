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
## Instruction
Extract the résumé into the JSON schema below.

## Constraints
- Copy text exactly as written.
- Do not infer or improve anything.
- Missing strings = "".
- Missing sections = [].
- Keep bullets verbatim.
- Skills must use only:
  languages, frameworks, tools, concepts, platforms.
- Do not duplicate skills.

## Output
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

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
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
## Instruction
Extract the job description into the JSON schema below.

## Constraints
- Extract only explicit information.
- Do not infer or improve anything.
- required_skills = must-have requirements.
- preferred_skills = bonus or nice-to-have requirements.
- responsibilities = day-to-day tasks.
- soft_skills = behavioural traits.
- buzzwords = marketing/culture language.
- deal_breakers = hard requirements.
- Missing arrays = [].

## Output
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

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
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
## Instruction
Compare the résumé profile against the JD profile.

## Constraints
- Evaluate only required_skills and preferred_skills.
- Match exact keywords and clear variants.
- category:
  language | framework | tool | concept | soft_skill | buzzword
- found_in:
  summary | projects | experience | education | skills
- importance:
  required | preferred
- suggested_section:
  skills | projects | experience | summary
- why_it_matters must be 25 words or fewer.
- keyword_match_score:
  round(100 * required_found / max(1, total_required))

## Output
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
      "why_it_matters": "string"
    }
  ],
  "keyword_match_score": 0
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
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
## Instruction
Score every project and experience bullet using the ATI rubric.

## Context
ATI rubric:

L1_OK
- Has action verb only.
- Missing technology or impact.
- Score = 1

L2_BETTER
- Has action verb and technology.
- Missing measurable impact.
- Score = 2

L3_BEST
- Has action verb, technology, and measurable impact.
- Score = 3

bullet_quality_avg must be a percentage from 0-100.

Calculation steps:
1. Convert levels into scores:
   L1_OK=1
   L2_BETTER=2
   L3_BEST=3

2. Add all scores.

3. Compute:
   total_possible = bullet_count * 3

4. Compute:
   bullet_quality_avg =
   round(100 * total_score / total_possible)

Example:
- 10 bullets
- nine L3_BEST
- one L2_BETTER

total_score = 29
total_possible = 30

bullet_quality_avg = 97

## Constraints
- Use verbatim bullet text.
- measurable impact = metrics, percentages, counts, or outcomes.
- what_is_missing must be 20 words or fewer.
- bullet_quality_avg must be an integer from 0-100.
- No bullets = [] and score 0.

## Output
{
  "bullets": [
    {
      "source": "projects|experience",
      "parent_title": "string",
      "bullet_text": "string",
      "has_action_verb": true,
      "has_specific_technology": true,
      "has_measurable_impact": false,
      "level": "L1_OK|L2_BETTER|L3_BEST",
      "what_is_missing": "string"
    }
  ],
  "bullet_quality_avg": 0
}

Output ONLY valid JSON.
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
## Instruction
Detect game-dev jargon in the résumé using the table below.

## Context
Translation table:

- Game loop → Real-time application loop / event-driven architecture
- Sprite rendering → 2D graphics rendering
- Level editor → Developer tooling / content authoring tool
- Level scripting → Gameplay automation / scripting layer
- Mob spawner / enemy AI → Entity management system / behaviour system
- HP bar / HUD → Real-time UI rendering / overlay system
- Collision detection (SAT, AABB) → Computational geometry / spatial algorithms
- Gameplay programmer → Application developer / systems programmer
- Shipped a game → Delivered a software product to end users
- Game jam (48 hours) → Rapid prototyping under time constraints
- Tiled map loading → Data-driven level/content loading from structured files
- Component-based engine → ECS (Entity-Component-System) architecture
- Asset pipeline → Content/data pipeline / build automation
- Frame rate optimisation → Performance profiling and optimisation
- Multiplayer netcode → Real-time network programming / client-server architecture

Severity:
- high = non-game role
- medium = mixed role
- low = game-dev role

jargon_score:
max(0, 100 - 10*high - 5*medium - 2*low)

## Constraints
- Flag only listed terms.
- Use verbatim bullet text.
- suggested_translation must match the table exactly.

## Output
{
  "flags": [
    {
      "bullet_text": "string",
      "term_used": "string",
      "suggested_translation": "string",
      "severity": "low|medium|high"
    }
  ],
  "jargon_score": 0
}

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
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
## Instruction
Audit the résumé structure and ATS formatting.

## Context
Three-Thirds model:

Top:
- Name
- Contact
- Summary or featured project

Middle:
- Projects or experience with bullets

Bottom:
- Skills section

ATS rules:
- No tables or multi-columns
- No headers/footers with important info
- No images/icons
- Standard headings only
- Standard bullet symbols only
- No decorative separators
- Contact info must be at top

structure_score:
- Start 100
- -10 per failed three_thirds check
- -5 per ats_red_flag
- Clamp 0–100

## Constraints
- page_count_estimate:
  1 if under 4000 chars else 2
- section_headings_missing:
  Summary, Education, Experience, Projects, Skills
- Use evidence for every ATS flag.

## Output
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

Output ONLY a valid JSON object matching the schema above. No prose. No markdown fences. No commentary. Never rewrite or generate résumé content.
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
## Instruction
Check whether the JD title matches the student's degree.

## Context

RTIS — Real-Time Interactive Simulation
Focus:
Low latency systems, engine development, high-performance computing, systems programming

Relevant titles:
Game Engine Developer, Systems Engineer, Site Reliability Engineer,
DevOps Engineer, AI/ML Engineer, Data Analyst, Data Scientist,
Full Stack Developer, Cybersecurity Engineer, Simulation Engineer,
Graphics Programmer, Technical Product Manager,
Technical Project Manager

IMGD — Interactive Media & Game Development
Focus:
Interactive systems, real-time rendering, game systems,
immersive visualisation

Relevant titles:
Game Developer, Systems Engineer, Full Stack Developer,
Data Engineer, Infrastructure Engineer, DevOps Engineer,
Cybersecurity Engineer, AI/ML Engineer, Technical Designer,
Technical Artist, Gameplay Programmer, Tools Engineer,
Technical Product Manager, Technical Project Manager

UXGD — User Experience & Game Design
Focus:
UX design, software engineering, product strategy,
digital product management

Relevant titles:
App Developer, UI/UX Designer, Product Designer,
Product Manager, Product Operations Manager,
Project Manager, Marketing & Design Specialist,
Process Architect, Technical Designer,
Technical Artist, UX Researcher, UX Engineer

BFA — Digital Art and Animation
Focus:
Visual storytelling, CG production, game engine projects

Relevant titles:
Technical Artist, UI/UX Designer, Creative Designer,
Unreal Engine Artist, 3D Graphic Artist,
Production Assistant, Project Manager,
Project Operations

Scores:
- 100 = strong match
- 60 = related field
- 30 = unrelated

## Constraints
- Use only the provided lists.
- fit_commentary = 2–3 sentences.
- degree_alignment_score:
  100, 60, or 30 only.

## Output
{
  "student_degree": "string",
  "jd_title": "string",
  "title_on_suggested_list": true,
  "matched_against": "string",
  "fit_commentary": "string",
  "degree_alignment_score": 0
}

Output ONLY valid JSON.
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
## Instruction
Write a 3-bullet Markdown summary of the analysis report.

## Constraints
- Exactly 3 bullet points.
- Each line starts with "- ".
- 1–2 sentences per bullet.
- Bullet 1: overall impression.
- Bullet 2: biggest strength.
- Bullet 3: biggest weakness or risk.
- Use second person.
- Do not mention raw scores.
- Diagnostic only.
- No headers or extra text.

## Output
Plain Markdown only.
"""
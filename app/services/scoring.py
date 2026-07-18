import re

from app.data.verbs import ACTION_VERBS


def scan_action_verbs(text_lower: str) -> tuple[int, list[str]]:
    """Scans lowercase text for action verbs, returning matching list and score."""
    found = []
    for verb in ACTION_VERBS:
        pattern = r"\b" + re.escape(verb) + r"\b"
        if re.search(pattern, text_lower):
            found.append(verb)
    score = min(len(found) * 10, 20)
    return score, found


def scan_quantifiable_metrics(text: str) -> tuple[int, list[str]]:
    """Finds numbers, percentages, and dollar amounts representing metrics inside text."""
    pattern = r"\b(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?%\b|\$\b(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?[KkMmB]?(?:\b)?|\b(?:\d{1,3}(?:,\d{3})*|\d+)\s*(?:users|clients|servers|dollars|percent|reduction|increase|growth|saved)\b"
    matches = re.findall(pattern, text, re.IGNORECASE)
    score = min(len(matches) * 10, 25)
    return score, matches


def calculate_resume_strength(text_lower: str, text_original: str) -> tuple[int, dict]:
    """Calculates overall structural score based on sections existence, contact channels, etc."""
    score = 0
    breakdown = {}

    # 1. Work Experience Section (25 pts)
    exp_keywords = ["experience", "work", "history", "employment", "professional background"]
    has_exp = any(kw in text_lower for kw in exp_keywords)
    exp_score = 25 if has_exp else 0
    score += exp_score
    breakdown["work_experience"] = {"score": exp_score, "max": 25, "checked": has_exp}

    # 2. Projects Section (25 pts)
    proj_keywords = ["projects", "project", "personal project", "portfolio projects"]
    has_proj = any(kw in text_lower for kw in proj_keywords)
    proj_score = 25 if has_proj else 0
    score += proj_score
    breakdown["projects"] = {"score": proj_score, "max": 25, "checked": has_proj}

    # 3. Education Section (20 pts)
    edu_keywords = ["education", "academic", "university", "college", "degree", "gpa"]
    has_edu = any(kw in text_lower for kw in edu_keywords)
    edu_score = 20 if has_edu else 0
    score += edu_score
    breakdown["education"] = {"score": edu_score, "max": 20, "checked": has_edu}

    # 4. Dedicated Skills Section (20 pts)
    skills_keywords = ["skills", "technologies", "expertise", "technical skills"]
    has_skills = any(kw in text_lower for kw in skills_keywords)
    skills_score = 20 if has_skills else 0
    score += skills_score
    breakdown["skills_section"] = {"score": skills_score, "max": 20, "checked": has_skills}

    # 5. Contact Info & Links (10 pts)
    links_score = 0
    has_github = "github.com" in text_lower or "github.io" in text_lower
    has_linkedin = "linkedin.com" in text_lower
    has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text_lower))
    has_phone = bool(
        re.search(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", text_lower)
    )

    if has_github:
        links_score += 3
    if has_linkedin:
        links_score += 3
    if has_email:
        links_score += 2
    if has_phone:
        links_score += 2

    score += links_score
    breakdown["contact_info"] = {
        "score": links_score,
        "max": 10,
        "github": has_github,
        "linkedin": has_linkedin,
        "email": has_email,
        "phone": has_phone,
    }

    return score, breakdown


def generate_dynamic_verdict(
    matching_skills: list[str],
    missing_skills: list[str],
    category_progress: list[dict],
    potential_improvement: float,
) -> str:
    """Creates a textual feedback verdict based on skills compliance."""
    matched_names = [s for s in matching_skills]
    missing_names = [s for s in missing_skills]

    top_categories = []
    for cat in category_progress:
        if cat["coverage"] >= 60.0:
            top_categories.append(cat["category"].lower())

    weak_categories = []
    for cat in category_progress:
        if cat["coverage"] < 40.0:
            weak_categories.append(cat["category"].lower())

    verdict = "Your resume "

    if top_categories:
        verdict += f"demonstrates strong {', '.join(top_categories[:2])} fundamentals."
    elif matched_names:
        verdict += f"shows solid keywords match with items such as {', '.join(matched_names[:3])}."
    else:
        verdict += "lacks clearly matched target technical keywords."

    if weak_categories:
        verdict += f" However, gaps in {', '.join(weak_categories[:2])}"
        if missing_names:
            verdict += f" (missing skills like {', '.join(missing_names[:3])})"
        verdict += " reduce compliance with the target job profile."
    elif missing_names:
        verdict += f" However, key missing skills like {', '.join(missing_names[:3])} reduce compatibility with the target role."
    else:
        verdict += " Your skills map completely to the target job requirements!"

    if potential_improvement > 0:
        verdict += f" Adding the highlighted skills could significantly improve your ATS score by up to an estimated +{potential_improvement:.2f}%."
    else:
        verdict += " You have excellent compliance with the target job profile."

    return verdict


def generate_suggestions(
    text_lower: str,
    text_original: str,
    match_percentage: float,
    action_verb_count: int,
    metric_count: int,
    strength_breakdown: dict,
) -> list[dict]:
    """Generates detailed bullet items with actionable improvements for structural alignment."""
    suggestions = []

    # Category: Resume Structure
    if not strength_breakdown["work_experience"]["checked"]:
        suggestions.append(
            {
                "category": "Resume Structure",
                "priority": "High",
                "title": "Add Work Experience Section",
                "description": "Your resume lacks a clearly labeled Work Experience section. Add one detailing your professional roles, responsibilities, and achievements.",
            }
        )

    if not strength_breakdown["projects"]["checked"]:
        suggestions.append(
            {
                "category": "Resume Structure",
                "priority": "High",
                "title": "Add Projects Section",
                "description": "Including a Projects section showcases practical implementation of your skills, which is critical for standing out to recruiters.",
            }
        )

    if not strength_breakdown["skills_section"]["checked"]:
        suggestions.append(
            {
                "category": "Resume Structure",
                "priority": "High",
                "title": "Add Dedicated Skills Section",
                "description": "Create a dedicated 'Technical Skills' section. ATS scanners look for structured skills sections to quickly index your qualifications.",
            }
        )

    if not strength_breakdown["education"]["checked"]:
        suggestions.append(
            {
                "category": "Resume Structure",
                "priority": "Medium",
                "title": "Add Education Section",
                "description": "Add details about your degrees, certifications, or academic training to complete the structural requirement.",
            }
        )

    contact = strength_breakdown["contact_info"]
    if not contact["github"] or not contact["linkedin"]:
        missing_links = []
        if not contact["github"]:
            missing_links.append("GitHub profile")
        if not contact["linkedin"]:
            missing_links.append("LinkedIn profile")
        suggestions.append(
            {
                "category": "Resume Structure",
                "priority": "Medium",
                "title": f"Add Contact Links ({', '.join(missing_links)})",
                "description": f"Recruiters expect to find links to professional platforms. Add your {', and '.join(missing_links)} to the header.",
            }
        )

    # Category: Technical Skills
    if match_percentage < 40:
        suggestions.append(
            {
                "category": "Technical Skills",
                "priority": "High",
                "title": "Improve Skill Coverage",
                "description": "Your resume matches less than 40% of the job description's required skills. Review the missing skills list and integrate them naturally into your work history.",
            }
        )
    elif match_percentage < 70:
        suggestions.append(
            {
                "category": "Technical Skills",
                "priority": "Medium",
                "title": "Address Key Missing Skills",
                "description": "Your skill match is moderate. Review the missing skills list and add 2-3 key technical items to improve alignment.",
            }
        )
    else:
        suggestions.append(
            {
                "category": "Technical Skills",
                "priority": "Low",
                "title": "Great Skill Alignment",
                "description": "You have matching skills for over 70% of the job description. Ensure they are listed in your experience with relevant context.",
            }
        )

    # Category: Experience
    if action_verb_count < 5:
        suggestions.append(
            {
                "category": "Experience",
                "priority": "Medium",
                "title": "Use Strong Action Verbs",
                "description": f"We only detected {action_verb_count} action verbs (like 'optimized', 'developed'). Revise your bullet points to start with strong, action-oriented verbs.",
            }
        )
    else:
        suggestions.append(
            {
                "category": "Experience",
                "priority": "Low",
                "title": "Good Action Verbs Usage",
                "description": f"Great! Your resume uses {action_verb_count} action verbs, making your contributions sound active and impact-driven.",
            }
        )

    if metric_count < 3:
        suggestions.append(
            {
                "category": "Experience",
                "priority": "High",
                "title": "Quantify Achievements",
                "description": f"We found only {metric_count} quantifiable metrics (numbers, %, $). Recruiters and ATS prefer resumes that show measurable impact. Quantify your accomplishments (e.g. 'Optimized app load time by 30%').",
            }
        )
    else:
        suggestions.append(
            {
                "category": "Experience",
                "priority": "Low",
                "title": "Quantified Impact Detected",
                "description": f"Excellent! Your resume includes {metric_count} quantifiable metrics showing measurable results.",
            }
        )

    # Category: Projects
    if strength_breakdown["projects"]["checked"] and len(text_lower) < 1500:
        suggestions.append(
            {
                "category": "Projects",
                "priority": "Medium",
                "title": "Elaborate on Projects",
                "description": "Your overall resume content is a bit brief. Expand on your projects by using the STAR method (Situation, Task, Action, Result) to write descriptive bullet points.",
            }
        )

    # Category: Certifications
    suggestions.append(
        {
            "category": "Certifications",
            "priority": "Low",
            "title": "Add Professional Certifications",
            "description": "Incorporate certifications related to the job role (e.g. AWS, Scrum Master, or equivalent) in a dedicated section to validate your expertise.",
        }
    )

    return suggestions

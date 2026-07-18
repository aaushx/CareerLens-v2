import logging
import re

from sklearn.metrics.pairwise import cosine_similarity

from app.data import SKILLS_CATEGORIES
from app.services.nlp import extract_skills, get_tfidf_vectorizer
from app.services.roadmap import get_learning_recommendation
from app.services.scoring import (
    calculate_resume_strength,
    generate_dynamic_verdict,
    generate_suggestions,
    scan_action_verbs,
    scan_quantifiable_metrics,
)

logger = logging.getLogger(__name__)


def _compute_skill_match_and_coverage(
    found_skills: list[str], jd_skills: list[str]
) -> tuple[list[str], list[str], dict, dict, list[dict]]:
    """Compares candidate skills to job description requirements and categorizes them."""
    matching_skills = list(set(found_skills) & set(jd_skills))
    missing_skills = list(set(jd_skills) - set(found_skills))

    categorized_matching = {}
    categorized_missing = {}

    for category, skills in SKILLS_CATEGORIES.items():
        # Find matching in this category
        cat_match = [s for s in matching_skills if s in skills]
        if cat_match:
            categorized_matching[category] = cat_match

        # Find missing in this category
        cat_miss = [s for s in missing_skills if s in skills]
        if cat_miss:
            enriched_miss = []
            for s in cat_miss:
                rec_info = get_learning_recommendation(s)
                enriched_miss.append(
                    {
                        "name": s,
                        "difficulty": rec_info["difficulty"],
                        "est_time": rec_info["est_time"],
                    }
                )
            categorized_missing[category] = enriched_miss

    # Calculate skill category progress/coverage
    category_progress = []
    for category, skills in SKILLS_CATEGORIES.items():
        cat_jd_skills = [s for s in jd_skills if s in skills]
        if len(cat_jd_skills) > 0:
            cat_matched = [s for s in matching_skills if s in skills]
            coverage = round((len(cat_matched) / len(cat_jd_skills)) * 100, 2)
            category_progress.append(
                {
                    "category": category,
                    "total": len(cat_jd_skills),
                    "matched": len(cat_matched),
                    "coverage": coverage,
                }
            )

    return (
        matching_skills,
        missing_skills,
        categorized_matching,
        categorized_missing,
        category_progress,
    )


def _compute_semantic_match(
    extracted_text: str, job_description: str, fallback_score: float
) -> float:
    """Computes cosine similarity between resume and job description using TF-IDF."""
    try:
        vectorizer = get_tfidf_vectorizer()
        tfidf_matrix = vectorizer.fit_transform([extracted_text, job_description])
        similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        similarity_score = max(0.0, min(1.0, float(similarity_score)))
        return round(similarity_score * 100, 2)
    except Exception as e:
        logger.error(f"Semantic similarity match calculation failed: {e}", exc_info=True)
        return fallback_score


def _get_weights_by_jd_skills(jd_skills_count: int) -> tuple[float, float, float]:
    """Retrieves weights for skill, semantic, and strength scores based on job requirements density."""
    if jd_skills_count == 0:
        return 0.0, 0.4, 0.6
    elif jd_skills_count <= 2:
        return 0.4, 0.2, 0.4
    else:
        return 0.6, 0.1, 0.3


def _apply_senior_penalty(
    job_description_lower: str,
    resume_text_lower: str,
    resume_strength_score: float,
    weight_strength: float,
) -> float:
    """Applies score deductions if a senior role is targetted but no senior attributes are found."""
    if "senior" in job_description_lower:
        experience_pattern = r"\b(?:5|6|7|8|9|\d{2,})\+?\s*years?"
        has_senior_keyword = "senior" in resume_text_lower
        has_enough_years = bool(re.search(experience_pattern, resume_text_lower))

        if not has_senior_keyword and not has_enough_years:
            strength_deduction = 10.0 / weight_strength
            return max(0.0, resume_strength_score - strength_deduction)
    return resume_strength_score


def _apply_single_skill_cap(
    jd_skills_count: int,
    final_score: float,
    skill_match: float,
    semantic_match: float,
    strength_score: float,
    w_skill: float,
    w_sem: float,
    w_str: float,
) -> tuple[float, float, float, float]:
    """Caps the final score at 85% if only a single skill is analyzed to avoid false compliance spikes."""
    if jd_skills_count == 1 and final_score > 85.0:
        scale_factor = 85.0 / final_score
        skill_match = round(skill_match * scale_factor, 2)
        semantic_match = round(semantic_match * scale_factor, 2)
        strength_score = round(strength_score * scale_factor, 2)
        # Recompute final_score to guarantee exact match
        final_score = (w_skill * skill_match) + (w_sem * semantic_match) + (w_str * strength_score)

    return round(final_score, 2), skill_match, semantic_match, strength_score


def _compute_potential_improvements(
    missing_skills: list[str], final_score: float
) -> tuple[list[dict], float]:
    """Calculates potential score gains if key missing skills are added to the resume."""
    potential_improvements = []
    current_temp_score = final_score

    CATEGORY_IMPACT = {
        "Programming Languages": 8.0,
        "Frameworks": 8.0,
        "Backend": 6.0,
        "Frontend": 6.0,
        "Database": 5.0,
        "DevOps": 5.0,
        "Cloud": 5.0,
        "AI / Machine Learning": 5.0,
        "Tools": 3.0,
        "Version Control": 3.0,
    }

    def get_skill_importance(skill):
        for cat, s_list in SKILLS_CATEGORIES.items():
            if skill in s_list:
                return CATEGORY_IMPACT.get(cat, 5.0)
        return 5.0

    sorted_missing = sorted(missing_skills, key=get_skill_importance, reverse=True)

    for s in sorted_missing[:4]:
        impact = get_skill_importance(s)
        if current_temp_score + impact > 100.0:
            impact = 100.0 - current_temp_score
        if impact > 0:
            potential_improvements.append({"name": s, "impact": round(impact, 2)})
            current_temp_score = round(current_temp_score + impact, 2)

    return potential_improvements, round(current_temp_score, 2)


def _generate_roadmap_timeline(categorized_missing: dict) -> list[dict]:
    """Constructs a chronologically paced learning timeline for missing technical categories."""
    roadmap_timeline = []
    start_day = 1

    flat_missing_skills = []
    for cat, skills_list in categorized_missing.items():
        for skill in skills_list:
            flat_missing_skills.append(skill)

    skill_stages = {
        "graphql": [
            ("Foundational GraphQL", "Schema design, types, queries, and mutations."),
            ("Apollo Client Integration", "Caching, query hooks, and optimistic UI updates."),
        ],
        "docker": [
            (
                "Docker Basics",
                "Containerizing applications, writing Dockerfiles, and managing volumes.",
            ),
            (
                "Docker Compose",
                "Multi-container setups, networking, and local development orchestration.",
            ),
        ],
        "kubernetes": [
            (
                "Kubernetes Orchestration",
                "Pods, deployments, services, and configuration management.",
            ),
            ("K8s Scaling & Helm", "Horizontal autoscaling, Helm charts, and ingress management."),
        ],
        "typescript": [
            (
                "TypeScript Basics",
                "Type annotations, interfaces, types, and strict compiler configs.",
            ),
            (
                "TS Advanced Patterns",
                "Generics, utility types, declaration files, and tsconfig setups.",
            ),
        ],
        "react": [
            (
                "React Hooks & Context",
                "Functional components, custom hooks, and state context API.",
            ),
            (
                "State Management & Perf",
                "Redux/Zustand, bundle splitting, and rendering optimization.",
            ),
        ],
    }

    for skill in flat_missing_skills[:4]:
        name_lower = skill["name"].lower()
        duration_str = skill["est_time"]
        try:
            match = re.search(r"\d+", duration_str)
            days = int(match.group()) if match else 7
        except Exception:
            days = 7

        stages = skill_stages.get(name_lower)
        if stages:
            mid_day = start_day + (days // 2) - 1
            end_day = start_day + days - 1
            roadmap_timeline.append(
                {
                    "days": f"DAY {start_day}-{mid_day}",
                    "title": stages[0][0],
                    "description": stages[0][1],
                }
            )
            roadmap_timeline.append(
                {
                    "days": f"DAY {mid_day+1}-{end_day}",
                    "title": stages[1][0],
                    "description": stages[1][1],
                }
            )
        else:
            mid_day = start_day + (days // 2) - 1
            end_day = start_day + days - 1
            roadmap_timeline.append(
                {
                    "days": f"DAY {start_day}-{mid_day}",
                    "title": f"Foundational {skill['name']}",
                    "description": f"Master core concepts, syntax, and fundamental tools of {skill['name']}.",
                }
            )
            roadmap_timeline.append(
                {
                    "days": f"DAY {mid_day+1}-{end_day}",
                    "title": f"Advanced {skill['name']} Projects",
                    "description": f"Build practical portfolio projects and integrate {skill['name']} into your workflow.",
                }
            )
        start_day += days

    if not roadmap_timeline:
        roadmap_timeline.append(
            {
                "days": "Day 1-3",
                "title": "Keep Learning",
                "description": "No critical missing skills. Keep optimizing your resume for specific company cultures.",
            }
        )

    return roadmap_timeline


def perform_analysis(
    extracted_text: str, job_description: str, filename: str, extraction_method: str
) -> dict:
    """Coordinates parser metadata, scoring calculators, and NLP engines to build full ATS profile analysis."""
    resume_text_lower = extracted_text.lower()
    job_description_lower = job_description.lower()

    # 1. Skill Extraction
    found_skills = extract_skills(resume_text_lower)
    jd_skills = extract_skills(job_description_lower)

    # 2. Skill Match and Coverage
    (
        matching_skills,
        missing_skills,
        categorized_matching,
        categorized_missing,
        category_progress,
    ) = _compute_skill_match_and_coverage(found_skills, jd_skills)

    # 3. Base percentages calculation
    w_skill, w_sem, w_str = _get_weights_by_jd_skills(len(jd_skills))

    if len(jd_skills) > 0:
        skill_match_percentage = round((len(matching_skills) / len(jd_skills)) * 100, 2)
    else:
        skill_match_percentage = 100.00

    # 4. NLP Semantic Similarity
    similarity_percentage = _compute_semantic_match(
        extracted_text, job_description, skill_match_percentage
    )

    # 5. Strength Score & Penalty application
    base_strength_score, strength_breakdown = calculate_resume_strength(
        resume_text_lower, extracted_text
    )
    resume_strength_score = float(base_strength_score)
    resume_strength_score = _apply_senior_penalty(
        job_description_lower, resume_text_lower, resume_strength_score, w_str
    )

    # 6. Weighted Final Score & Cap application
    final_score = (
        (w_skill * skill_match_percentage)
        + (w_sem * similarity_percentage)
        + (w_str * resume_strength_score)
    )
    final_score, skill_match_percentage, similarity_percentage, resume_strength_score = (
        _apply_single_skill_cap(
            len(jd_skills),
            final_score,
            skill_match_percentage,
            similarity_percentage,
            resume_strength_score,
            w_skill,
            w_sem,
            w_str,
        )
    )

    # 7. Action Verbs & Metrics Scanner
    action_verb_count, found_verbs = scan_action_verbs(resume_text_lower)
    metric_count, found_metrics = scan_quantifiable_metrics(extracted_text)

    # 8. Suggestions & Badge
    suggestions = generate_suggestions(
        resume_text_lower,
        extracted_text,
        skill_match_percentage,
        action_verb_count,
        metric_count,
        strength_breakdown,
    )

    if resume_strength_score >= 81:
        badge = "Job Ready"
    elif resume_strength_score >= 61:
        badge = "Advanced"
    elif resume_strength_score >= 41:
        badge = "Intermediate"
    else:
        badge = "Beginner"

    ats_readiness = round((0.6 * final_score) + (0.4 * resume_strength_score), 2)

    # 9. Potential Improvements
    potential_improvements, estimated_potential_score = _compute_potential_improvements(
        missing_skills, final_score
    )

    # 10. Verdict Generator
    verdict = generate_dynamic_verdict(
        matching_skills, missing_skills, category_progress, estimated_potential_score - final_score
    )

    # 11. Checklist items mapping
    has_contact = (
        strength_breakdown["contact_info"]["email"] or strength_breakdown["contact_info"]["phone"]
    )
    has_skills = strength_breakdown["skills_section"]["checked"]
    has_projects = strength_breakdown["projects"]["checked"]
    has_education = strength_breakdown["education"]["checked"]
    has_experience = strength_breakdown["work_experience"]["checked"]

    cert_keywords = [
        "certification",
        "certifications",
        "certified",
        "credential",
        "credentials",
        "certificate",
        "certificates",
    ]
    has_certs = any(kw in resume_text_lower for kw in cert_keywords)

    has_linkedin = strength_breakdown["contact_info"]["linkedin"]
    has_github = strength_breakdown["contact_info"]["github"]

    checklist = {
        "contact_info": has_contact,
        "skills": has_skills,
        "projects": has_projects,
        "education": has_education,
        "experience": has_experience,
        "certifications": has_certs,
        "linkedin": has_linkedin,
        "github": has_github,
    }

    # 12. Resume Component Percentages
    proj_val = 0
    if has_projects:
        proj_val = 60
        proj_val += 20 if action_verb_count > 3 else 10
        proj_val += 20 if len(extracted_text) > 1000 else 10
        proj_val = min(100, proj_val)

    skills_val = 0
    if has_skills:
        skills_val = 60
        skills_val += int(40 * (skill_match_percentage / 100.0))
        skills_val = min(100, skills_val)

    edu_val = 100 if has_education else 0

    exp_val = 0
    if has_experience:
        exp_val = 60
        exp_val += 20 if action_verb_count > 5 else 10
        exp_val += 20 if metric_count > 2 else 10
        exp_val = min(100, exp_val)

    certs_val = 100 if has_certs else 0

    contact_val = 0
    if strength_breakdown["contact_info"]["email"]:
        contact_val += 40
    if strength_breakdown["contact_info"]["phone"]:
        contact_val += 20
    if has_linkedin:
        contact_val += 20
    if has_github:
        contact_val += 20

    strength_percentages = {
        "projects": proj_val,
        "skills": skills_val,
        "education": edu_val,
        "experience": exp_val,
        "certifications": certs_val,
        "contact_info": contact_val,
    }

    # 13. Compliance & Quick Wins & Timeline
    compliance = {
        "keyword_density": {
            "status": (
                "Optimal"
                if skill_match_percentage >= 70
                else ("Good" if skill_match_percentage >= 40 else "Low")
            ),
            "class": "success" if skill_match_percentage >= 40 else "danger",
        },
        "file_format": {"status": "Passed", "class": "success"},
        "complex_formatting": {
            "status": "Review" if extraction_method == "OCR Extraction" else "Passed",
            "class": "warning" if extraction_method == "OCR Extraction" else "success",
        },
    }

    quick_wins = []
    if metric_count < 3:
        quick_wins.append(
            {
                "title": "Quantify Impact",
                "points": "+5 pts",
                "description": "Add numbers or percentages to your last 3 bullet points to show measurable achievements.",
            }
        )
    if action_verb_count < 5:
        quick_wins.append(
            {
                "title": "Action Verbs",
                "points": "+3 pts",
                "description": "Replace generic phrases like 'responsible for' with active verbs like 'Spearheaded' or 'Architected'.",
            }
        )
    if not checklist.get("linkedin") or not checklist.get("github"):
        missing_prof = []
        if not checklist.get("linkedin"):
            missing_prof.append("LinkedIn")
        if not checklist.get("github"):
            missing_prof.append("GitHub")
        quick_wins.append(
            {
                "title": f"Add {', '.join(missing_prof)} Link",
                "points": "+2 pts",
                "description": f"Include your professional {', and '.join(missing_prof)} URL in the resume header to increase profile depth.",
            }
        )
    if len(quick_wins) == 0:
        quick_wins.append(
            {
                "title": "Optimize Keyword Density",
                "points": "+2 pts",
                "description": "Add 2 more secondary skills from the missing skills list to align closer with the target job profile.",
            }
        )

    roadmap_timeline = _generate_roadmap_timeline(categorized_missing)

    return {
        "success": True,
        "metrics": {
            "skill_match": skill_match_percentage,
            "semantic_match": similarity_percentage,
            "resume_strength": float(resume_strength_score),
            "final_score": final_score,
            "ats_readiness": ats_readiness,
            "badge": badge,
        },
        "skills": {
            "matching": categorized_matching,
            "missing": categorized_missing,
            "matching_flat_count": len(matching_skills),
            "missing_flat_count": len(missing_skills),
            "total_jd_count": len(jd_skills),
            "category_progress": category_progress,
        },
        "suggestions": suggestions,
        "extraction_method": extraction_method,
        "details": {
            "action_verb_count": action_verb_count,
            "metric_count": metric_count,
            "strength_breakdown": strength_breakdown,
        },
        "verdict": verdict,
        "potential_improvements": potential_improvements,
        "estimated_potential_score": estimated_potential_score,
        "checklist": checklist,
        "strength_percentages": strength_percentages,
        "has_certifications": has_certs,
        "compliance": compliance,
        "quick_wins": quick_wins,
        "roadmap_timeline": roadmap_timeline,
        "filename": filename,
    }

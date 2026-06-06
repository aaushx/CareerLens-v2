import os
import re
import fitz
import pytesseract

from PIL import Image
from flask import Flask, render_template, request, jsonify, send_file, session
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from werkzeug.utils import secure_filename

# ReportLab imports for PDF generation
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# -------------------------------
# Tesseract OCR Path (Windows)
# -------------------------------
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# -------------------------------
# Load Transformer Model
# -------------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

app = Flask(__name__)
# Secret key for session management
app.secret_key = "ats-secret-key-optimization-platform-2026"

# -------------------------------
# Upload Folder Setup
# -------------------------------
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# -------------------------------
# Skill Database by Category
# -------------------------------
SKILLS_CATEGORIES = {
    "Programming Languages": [
        "python", "java", "c++", "c", "c#", "typescript", "javascript", "go", "rust", "ruby", "php", "swift", "kotlin", "r", "matlab", "scala", "perl"
    ],
    "Frontend": [
        "html", "css", "tailwind", "bootstrap", "sass", "less", "html5", "css3"
    ],
    "Backend": [
        "node.js", "node", "express", "fastapi", "flask", "django", "spring boot", "laravel", "rails", "asp.net", "graphql"
    ],
    "Database": [
        "sql", "postgresql", "mongodb", "mysql", "redis", "elasticsearch", "sqlite", "oracle", "cassandra", "mariadb", "dynamodb"
    ],
    "DevOps": [
        "docker", "kubernetes", "jenkins", "ci/cd", "terraform", "ansible", "gitlab", "circleci", "aws codebuild", "argocd"
    ],
    "Cloud": [
        "aws", "azure", "gcp", "heroku", "digitalocean", "cloudflare", "openstack"
    ],
    "AI / Machine Learning": [
        "machine learning", "deep learning", "nlp", "computer vision", "pandas", "numpy", "pytorch", "tensorflow", "keras", "scikit-learn", "scipy", "llm", "langchain", "huggingface"
    ],
    "Frameworks": [
        "react", "angular", "vue", "next.js", "svelte", "jquery", "django", "flask", "spring boot", "laravel", "rails", "nuxt.js"
    ],
    "Tools": [
        "tesseract", "pytesseract", "pymupdf", "fitz", "pillow", "reportlab", "gunicorn", "pip", "npm", "webpack", "babel", "vite", "postman"
    ],
    "Version Control": [
        "git", "github", "gitlab", "bitbucket", "svn"
    ]
}

ALL_SKILLS = []
for skills in SKILLS_CATEGORIES.values():
    ALL_SKILLS.extend(skills)

# De-duplicate
ALL_SKILLS = list(set(ALL_SKILLS))

# -------------------------------
# Skills Extraction Helper
# -------------------------------
def extract_skills(text_lower):
    matches = []
    for skill in ALL_SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
        for m in re.finditer(pattern, text_lower):
            matches.append((m.start(), m.end(), skill))
            
    filtered_skills = set()
    for s1, e1, skill1 in matches:
        is_sub = False
        for s2, e2, skill2 in matches:
            if s2 <= s1 and e1 <= e2:
                if (s1, e1) != (s2, e2):
                    is_sub = True
                    break
                elif skill1 != skill2 and len(skill1) < len(skill2):
                    is_sub = True
                    break
        if not is_sub:
            filtered_skills.add(skill1)
            
    return list(filtered_skills)

# -------------------------------
# Action Verbs & Metrics
# -------------------------------
ACTION_VERBS = [
    "designed", "developed", "implemented", "optimized", "managed", "led", "created", 
    "built", "engineered", "achieved", "improved", "increased", "reduced", "spearheaded", 
    "executed", "orchestrated", "architected", "streamlined", "automated"
]

def scan_action_verbs(text_lower):
    count = 0
    found = []
    for verb in ACTION_VERBS:
        pattern = r"\b" + re.escape(verb) + r"\b"
        matches = re.findall(pattern, text_lower)
        if matches:
            count += len(matches)
            found.append(verb)
    return count, found

def scan_quantifiable_metrics(text):
    patterns = [
        r"\b\d+%\b",
        r"\$\d+(?:,\d{3})*(?:\.\d+)?\b",
        r"\b\d+\s*(?:k|m|b|percent|percent|times|x)\b",
        r"\b\d+(?:\.\d+)?x\b"
    ]
    matches_count = 0
    found_metrics = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            matches_count += len(matches)
            found_metrics.extend(matches)
    return matches_count, found_metrics

# -------------------------------
# Learning Recommendations & Roadmap Database
# -------------------------------
ROADMAP_DB = {
    "python": {
        "difficulty": "Beginner",
        "est_time": "14 Days",
        "resources": ["Python for Everybody (Coursera)", "Real Python Tutorials", "Roadmap.sh Python Path"]
    },
    "java": {
        "difficulty": "Intermediate",
        "est_time": "21 Days",
        "resources": ["Java Programming Specialization (Duke)", "Java Brains Spring Boot", "Roadmap.sh Java Path"]
    },
    "c++": {
        "difficulty": "Advanced",
        "est_time": "30 Days",
        "resources": ["LearnCPP.com", "Udacity C++ Nanodegree", "Roadmap.sh C++ Path"]
    },
    "c#": {
        "difficulty": "Intermediate",
        "est_time": "14 Days",
        "resources": ["Microsoft C# Foundations", "Pluralsight C# Path", "Roadmap.sh ASP.NET Path"]
    },
    "typescript": {
        "difficulty": "Intermediate",
        "est_time": "7 Days",
        "resources": ["TypeScript Handbook", "Execute Program TypeScript Course", "Roadmap.sh TypeScript Path"]
    },
    "javascript": {
        "difficulty": "Beginner",
        "est_time": "10 Days",
        "resources": ["JavaScript Info", "FreeCodeCamp JavaScript Course", "Roadmap.sh JavaScript Path"]
    },
    "go": {
        "difficulty": "Intermediate",
        "est_time": "14 Days",
        "resources": ["A Tour of Go", "Let's Go Book by Alex Edwards", "Roadmap.sh Go Path"]
    },
    "rust": {
        "difficulty": "Advanced",
        "est_time": "30 Days",
        "resources": ["The Rust Book", "Rustlings Exercises", "Roadmap.sh Rust Path"]
    },
    "react": {
        "difficulty": "Beginner",
        "est_time": "7 Days",
        "resources": ["React Official Docs", "FreeCodeCamp React Course", "Roadmap.sh React Path"]
    },
    "angular": {
        "difficulty": "Intermediate",
        "est_time": "14 Days",
        "resources": ["Angular Tour of Heroes", "Angular Core Course by Max", "Roadmap.sh Angular Path"]
    },
    "vue": {
        "difficulty": "Beginner",
        "est_time": "7 Days",
        "resources": ["Vue.js Guide", "Vue School Courses", "Roadmap.sh Vue Path"]
    },
    "next.js": {
        "difficulty": "Intermediate",
        "est_time": "7 Days",
        "resources": ["Next.js Learn Course", "Lee Robinson Next.js Courses", "Roadmap.sh React Path"]
    },
    "flask": {
        "difficulty": "Beginner",
        "est_time": "5 Days",
        "resources": ["Flask Documentation Tutorial", "Miguel Grinberg Flask Mega-Tutorial", "Roadmap.sh Python Path"]
    },
    "django": {
        "difficulty": "Intermediate",
        "est_time": "14 Days",
        "resources": ["Django Girls Tutorial", "Django for Beginners Book", "Roadmap.sh Python Path"]
    },
    "node": {
        "difficulty": "Intermediate",
        "est_time": "10 Days",
        "resources": ["NodeJS.dev Learn", "Express Tutorial by MDN", "Roadmap.sh Backend Path"]
    },
    "node.js": {
        "difficulty": "Intermediate",
        "est_time": "10 Days",
        "resources": ["NodeJS.dev Learn", "Express Tutorial by MDN", "Roadmap.sh Backend Path"]
    },
    "express": {
        "difficulty": "Intermediate",
        "est_time": "5 Days",
        "resources": ["Express Docs", "MDN Express Tutorial", "Roadmap.sh Backend Path"]
    },
    "spring boot": {
        "difficulty": "Advanced",
        "est_time": "21 Days",
        "resources": ["Spring Boot Tutorial (JavaBrains)", "Spring Guides", "Roadmap.sh Java Path"]
    },
    "fastapi": {
        "difficulty": "Beginner",
        "est_time": "5 Days",
        "resources": ["FastAPI Tutorial User Guide", "Tiangolo FastAPI Courses", "Roadmap.sh Python Path"]
    },
    "sql": {
        "difficulty": "Beginner",
        "est_time": "7 Days",
        "resources": ["SQLBolt Interactive Tutorial", "SQLZoo Practice", "Roadmap.sh PostgreSQL Path"]
    },
    "postgresql": {
        "difficulty": "Intermediate",
        "est_time": "10 Days",
        "resources": ["PG Exercises", "PostgreSQL Tutorial", "Roadmap.sh PostgreSQL Path"]
    },
    "mongodb": {
        "difficulty": "Intermediate",
        "est_time": "7 Days",
        "resources": ["MongoDB University Basics", "Net Ninja MongoDB Playlist", "Roadmap.sh Backend Path"]
    },
    "mysql": {
        "difficulty": "Beginner",
        "est_time": "7 Days",
        "resources": ["MySQL Tutorial", "Codecademy SQL Course", "Roadmap.sh Backend Path"]
    },
    "redis": {
        "difficulty": "Intermediate",
        "est_time": "5 Days",
        "resources": ["Redis University RU101", "Redis Crash Course", "Roadmap.sh Backend Path"]
    },
    "elasticsearch": {
        "difficulty": "Advanced",
        "est_time": "14 Days",
        "resources": ["Elastic Guide by Udemy", "Elastic official quickstarts", "Roadmap.sh Backend Path"]
    },
    "firebase": {
        "difficulty": "Beginner",
        "est_time": "5 Days",
        "resources": ["Firebase Web Codelab", "Net Ninja Firebase Course", "Roadmap.sh Frontend Path"]
    },
    "aws": {
        "difficulty": "Intermediate",
        "est_time": "14 Days",
        "resources": ["AWS Solutions Architect Course", "Stephane Maarek AWS Course", "Roadmap.sh DevOps Path"]
    },
    "azure": {
        "difficulty": "Intermediate",
        "est_time": "14 Days",
        "resources": ["AZ-900 Microsoft Learn", "Azure Administrator Path", "Roadmap.sh DevOps Path"]
    },
    "gcp": {
        "difficulty": "Intermediate",
        "est_time": "14 Days",
        "resources": ["Google Cloud ACE path", "Qwiklabs GCP Basics", "Roadmap.sh DevOps Path"]
    },
    "docker": {
        "difficulty": "Intermediate",
        "est_time": "7 Days",
        "resources": ["Docker for Beginners (TechWorld with Nana)", "Docker Get Started Docs", "Roadmap.sh DevOps Path"]
    },
    "kubernetes": {
        "difficulty": "Advanced",
        "est_time": "21 Days",
        "resources": ["CKA Mumshad Course", "Kubernetes.io Tutorials", "Roadmap.sh DevOps Path"]
    },
    "git": {
        "difficulty": "Beginner",
        "est_time": "3 Days",
        "resources": ["Pro Git Book", "GitHub Skills Git Guide", "Roadmap.sh DevOps Path"]
    },
    "github": {
        "difficulty": "Beginner",
        "est_time": "2 Days",
        "resources": ["GitHub Skills Intro", "GitLab GitHub Workflows", "Roadmap.sh DevOps Path"]
    },
    "jenkins": {
        "difficulty": "Intermediate",
        "est_time": "10 Days",
        "resources": ["Jenkins Pipeline Tutorial", "CloudBees Tutorials", "Roadmap.sh DevOps Path"]
    },
    "ci/cd": {
        "difficulty": "Intermediate",
        "est_time": "7 Days",
        "resources": ["CI/CD Crash Course", "GitHub Actions Course", "Roadmap.sh DevOps Path"]
    },
    "terraform": {
        "difficulty": "Advanced",
        "est_time": "10 Days",
        "resources": ["HashiCorp Learn Terraform", "Terraform Up & Running Book", "Roadmap.sh DevOps Path"]
    },
    "machine learning": {
        "difficulty": "Intermediate",
        "est_time": "21 Days",
        "resources": ["Andrew Ng Machine Learning Specialization", "Kaggle ML Course", "Roadmap.sh AI/ML Path"]
    },
    "deep learning": {
        "difficulty": "Advanced",
        "est_time": "30 Days",
        "resources": ["Deep Learning Specialization (DeepLearning.AI)", "Fast.ai Practical Deep Learning", "Roadmap.sh AI/ML Path"]
    },
    "nlp": {
        "difficulty": "Advanced",
        "est_time": "21 Days",
        "resources": ["Hugging Face NLP Course", "Stanford CS224N Lectures", "Roadmap.sh AI/ML Path"]
    },
    "computer vision": {
        "difficulty": "Advanced",
        "est_time": "21 Days",
        "resources": ["OpenCV Tutorials", "Stanford CS231N Course", "Roadmap.sh AI/ML Path"]
    },
    "pandas": {
        "difficulty": "Beginner",
        "est_time": "5 Days",
        "resources": ["Kaggle Pandas Course", "Pandas official user guide", "Roadmap.sh AI/ML Path"]
    },
    "numpy": {
        "difficulty": "Beginner",
        "est_time": "3 Days",
        "resources": ["NumPy Quickstart Tutorial", "Real Python NumPy guides", "Roadmap.sh AI/ML Path"]
    },
    "pytorch": {
        "difficulty": "Intermediate",
        "est_time": "14 Days",
        "resources": ["PyTorch Official Tutorials", "PyTorch Deep Learning by Daniel Bourke", "Roadmap.sh AI/ML Path"]
    },
    "tensorflow": {
        "difficulty": "Intermediate",
        "est_time": "14 Days",
        "resources": ["TensorFlow Developer Specialization", "Keras Deep Learning Guides", "Roadmap.sh AI/ML Path"]
    },
    "keras": {
        "difficulty": "Beginner",
        "est_time": "7 Days",
        "resources": ["Keras Getting Started Guide", "Simple Deep Learning with Keras", "Roadmap.sh AI/ML Path"]
    },
    "scikit-learn": {
        "difficulty": "Intermediate",
        "est_time": "10 Days",
        "resources": ["Scikit-Learn documentation guides", "Hands-On Machine Learning Book", "Roadmap.sh AI/ML Path"]
    }
}

def get_learning_recommendation(skill):
    skill_lower = skill.lower()
    if skill_lower in ROADMAP_DB:
        data = ROADMAP_DB[skill_lower]
        return {
            "name": skill,
            "difficulty": data["difficulty"],
            "est_time": data["est_time"],
            "resources": data["resources"]
        }
    return {
        "name": skill,
        "difficulty": "Intermediate",
        "est_time": "7 Days",
        "resources": [f"{skill} Documentation", f"FreeCodeCamp {skill} Tutorial", f"Roadmap.sh {skill} Path"]
    }

# -------------------------------
# OCR Function
# -------------------------------
def extract_text_with_ocr(filepath):
    extracted_text = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            try:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img)
                extracted_text += text + "\n"
            except Exception as e:
                print(f"OCR error on page: {e}")
    return extracted_text

# -------------------------------
# Resume Strength Function
# -------------------------------
def calculate_resume_strength(text_lower, text_original):
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
    has_phone = bool(re.search(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", text_lower))
    
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
        "phone": has_phone
    }
    
    return score, breakdown

# -------------------------------
# Home Route
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -------------------------------
# Upload Route (Renders result.html)
# -------------------------------
# -------------------------------
# Core Analysis Engine Helper
# -------------------------------
def perform_analysis(extracted_text, job_description, filename, extraction_method):
    resume_text_lower = extracted_text.lower()
    job_description_lower = job_description.lower()

    # -------------------------------
    # Skill Extraction Logic
    # -------------------------------
    found_skills = extract_skills(resume_text_lower)
    jd_skills = extract_skills(job_description_lower)

    # -------------------------------
    # Skill Overlap & Categorization
    # -------------------------------
    matching_skills = list(set(found_skills) & set(jd_skills))
    missing_skills = list(set(jd_skills) - set(found_skills))

    # Group skills by categories for the frontend
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
                enriched_miss.append({
                    "name": s,
                    "difficulty": rec_info["difficulty"],
                    "est_time": rec_info["est_time"]
                })
            categorized_missing[category] = enriched_miss

    # Calculate skill category progress/coverage
    category_progress = []
    
    for category, skills in SKILLS_CATEGORIES.items():
        cat_jd_skills = [s for s in jd_skills if s in skills]
        if len(cat_jd_skills) > 0:
            cat_matched = [s for s in matching_skills if s in skills]
            coverage = round((len(cat_matched) / len(cat_jd_skills)) * 100, 2)
            category_progress.append({
                "category": category,
                "total": len(cat_jd_skills),
                "matched": len(cat_matched),
                "coverage": coverage
            })

    # -------------------------------
    # Percentages and Scores
    # -------------------------------
    # Define weights based on target skill count
    if len(jd_skills) == 0:
        weight_skill = 0.0
        weight_semantic = 0.7
        weight_strength = 0.3
    elif len(jd_skills) <= 2:
        weight_skill = 0.3
        weight_semantic = 0.5
        weight_strength = 0.2
    else:
        weight_skill = 0.5
        weight_semantic = 0.3
        weight_strength = 0.2

    # Calculate base scores
    if len(jd_skills) > 0:
        skill_match_percentage = round((len(matching_skills) / len(jd_skills)) * 100, 2)
    else:
        skill_match_percentage = 100.00

    # NLP Semantic Similarity
    resume_embedding = model.encode([extracted_text])
    jd_embedding = model.encode([job_description])
    
    similarity_score = cosine_similarity(resume_embedding, jd_embedding)[0][0]
    # Bound and scale to [0, 100]
    similarity_score = max(0.0, min(1.0, float(similarity_score)))
    similarity_percentage = round(similarity_score * 100, 2)

    # Resume Strength Score
    base_strength_score, strength_breakdown = calculate_resume_strength(resume_text_lower, extracted_text)
    resume_strength_score = float(base_strength_score)

    # 1. Apply Senior Penalty directly to resume_strength_score
    senior_penalty_applied = False
    if "senior" in job_description_lower:
        experience_pattern = r"\b(?:5|6|7|8|9|\d{2,})\+?\s*years?"
        has_senior_keyword = "senior" in resume_text_lower
        has_enough_years = bool(re.search(experience_pattern, resume_text_lower))
        
        if not has_senior_keyword and not has_enough_years:
            senior_penalty_applied = True
            strength_deduction = 10.0 / weight_strength
            resume_strength_score = max(0.0, resume_strength_score - strength_deduction)

    # Calculate base final score
    final_score = (weight_skill * skill_match_percentage) + (weight_semantic * similarity_percentage) + (weight_strength * resume_strength_score)
    final_score = round(final_score, 2)

    # 2. Apply Single Skill Cap (max 85.0 overall)
    if len(jd_skills) == 1 and final_score > 85.0:
        scale_factor = 85.0 / final_score
        skill_match_percentage = round(skill_match_percentage * scale_factor, 2)
        similarity_percentage = round(similarity_percentage * scale_factor, 2)
        resume_strength_score = round(resume_strength_score * scale_factor, 2)
        # Recompute final_score to guarantee exact match
        final_score = (weight_skill * skill_match_percentage) + (weight_semantic * similarity_percentage) + (weight_strength * resume_strength_score)

    skill_match_percentage = round(skill_match_percentage, 2)
    similarity_percentage = round(similarity_percentage, 2)
    resume_strength_score = round(resume_strength_score, 2)
    final_score = round(final_score, 2)

    # -------------------------------
    # Action Verbs & Metrics Scanner
    # -------------------------------
    action_verb_count, found_verbs = scan_action_verbs(resume_text_lower)
    metric_count, found_metrics = scan_quantifiable_metrics(extracted_text)

    # -------------------------------
    # Suggestions Generation
    # -------------------------------
    suggestions = generate_suggestions(
        resume_text_lower, extracted_text, skill_match_percentage, 
        action_verb_count, metric_count, strength_breakdown
    )

    # Determine Strength Badge
    if resume_strength_score >= 81:
        badge = "Job Ready"
    elif resume_strength_score >= 61:
        badge = "Advanced"
    elif resume_strength_score >= 41:
        badge = "Intermediate"
    else:
        badge = "Beginner"

    # ATS Readiness Score
    ats_readiness = round((0.6 * final_score) + (0.4 * resume_strength_score), 2)

    # -------------------------------
    # Dynamic Potential Improvement Estimator
    # -------------------------------
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
        "Version Control": 3.0
    }
    
    # Sort missing skills by category importance
    def get_skill_importance(skill):
        for cat, s_list in SKILLS_CATEGORIES.items():
            if skill in s_list:
                return CATEGORY_IMPACT.get(cat, 5.0)
        return 5.0
        
    sorted_missing = sorted(missing_skills, key=get_skill_importance, reverse=True)
    
    # Get top missing skill score boosts
    for s in sorted_missing[:4]: # top 4 items
        impact = get_skill_importance(s)
        if current_temp_score + impact > 100.0:
            impact = 100.0 - current_temp_score
        if impact > 0:
            potential_improvements.append({
                "name": s,
                "impact": round(impact, 2)
            })
            current_temp_score = round(current_temp_score + impact, 2)
            
    estimated_potential_score = round(current_temp_score, 2)

    # -------------------------------
    # Dynamic Resume Verdict Generator
    # -------------------------------
    verdict = generate_dynamic_verdict(matching_skills, missing_skills, category_progress, estimated_potential_score - final_score)

    # -------------------------------
    # ATS Checklist Scanner
    # -------------------------------
    has_contact = strength_breakdown["contact_info"]["email"] or strength_breakdown["contact_info"]["phone"]
    has_skills = strength_breakdown["skills_section"]["checked"]
    has_projects = strength_breakdown["projects"]["checked"]
    has_education = strength_breakdown["education"]["checked"]
    has_experience = strength_breakdown["work_experience"]["checked"]
    
    cert_keywords = ["certification", "certifications", "certified", "credential", "credentials", "certificate", "certificates"]
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
        "github": has_github
    }

    # -------------------------------
    # Resume Strength Component Percentages
    # -------------------------------
    # Projects
    proj_val = 0
    if has_projects:
        proj_val = 60
        proj_val += 20 if action_verb_count > 3 else 10
        proj_val += 20 if len(extracted_text) > 1000 else 10
        proj_val = min(100, proj_val)
        
    # Skills
    skills_val = 0
    if has_skills:
        skills_val = 60
        skills_val += int(40 * (skill_match_percentage / 100.0))
        skills_val = min(100, skills_val)
        
    # Education
    edu_val = 100 if has_education else 0
    
    # Experience
    exp_val = 0
    if has_experience:
        exp_val = 60
        exp_val += 20 if action_verb_count > 5 else 10
        exp_val += 20 if metric_count > 2 else 10
        exp_val = min(100, exp_val)
        
    # Certifications
    certs_val = 100 if has_certs else 0
    
    # Contact Info
    contact_val = 0
    if strength_breakdown["contact_info"]["email"]: contact_val += 40
    if strength_breakdown["contact_info"]["phone"]: contact_val += 20
    if has_linkedin: contact_val += 20
    if has_github: contact_val += 20

    strength_percentages = {
        "projects": proj_val,
        "skills": skills_val,
        "education": edu_val,
        "experience": exp_val,
        "certifications": certs_val,
        "contact_info": contact_val
    }

    # -------------------------------
    # ATS Compliance & Quick Wins & Timeline Roadmap
    # -------------------------------
    compliance = {
        "keyword_density": {
            "status": "Optimal" if skill_match_percentage >= 70 else ("Good" if skill_match_percentage >= 40 else "Low"),
            "class": "success" if skill_match_percentage >= 40 else "danger"
        },
        "file_format": {
            "status": "Passed",
            "class": "success"
        },
        "complex_formatting": {
            "status": "Review" if extraction_method == "OCR Extraction" else "Passed",
            "class": "warning" if extraction_method == "OCR Extraction" else "success"
        }
    }

    quick_wins = []
    if metric_count < 3:
        quick_wins.append({
            "title": "Quantify Impact",
            "points": "+5 pts",
            "description": "Add numbers or percentages to your last 3 bullet points to show measurable achievements."
        })
    if action_verb_count < 5:
        quick_wins.append({
            "title": "Action Verbs",
            "points": "+3 pts",
            "description": "Replace generic phrases like 'responsible for' with active verbs like 'Spearheaded' or 'Architected'."
        })
    if not checklist.get("linkedin") or not checklist.get("github"):
        missing_prof = []
        if not checklist.get("linkedin"): missing_prof.append("LinkedIn")
        if not checklist.get("github"): missing_prof.append("GitHub")
        quick_wins.append({
            "title": f"Add {', '.join(missing_prof)} Link",
            "points": "+2 pts",
            "description": f"Include your professional {', and '.join(missing_prof)} URL in the resume header to increase profile depth."
        })
    if len(quick_wins) == 0:
        quick_wins.append({
            "title": "Optimize Keyword Density",
            "points": "+2 pts",
            "description": "Add 2 more secondary skills from the missing skills list to align closer with the target job profile."
        })

    # Generate chronologically structured learning roadmap timeline based on missing skills
    roadmap_timeline = []
    start_day = 1
    
    # Flatten the missing skills list
    flat_missing_skills = []
    for cat, skills_list in categorized_missing.items():
        for skill in skills_list:
            flat_missing_skills.append(skill)
            
    # Standard timeline descriptions based on skill name
    skill_stages = {
        "graphql": [
            ("Foundational GraphQL", "Schema design, types, queries, and mutations."),
            ("Apollo Client Integration", "Caching, query hooks, and optimistic UI updates.")
        ],
        "docker": [
            ("Docker Basics", "Containerizing applications, writing Dockerfiles, and managing volumes."),
            ("Docker Compose", "Multi-container setups, networking, and local development orchestration.")
        ],
        "kubernetes": [
            ("Kubernetes Orchestration", "Pods, deployments, services, and configuration management."),
            ("K8s Scaling & Helm", "Horizontal autoscaling, Helm charts, and ingress management.")
        ],
        "typescript": [
            ("TypeScript Basics", "Type annotations, interfaces, types, and strict compiler configs."),
            ("TS Advanced Patterns", "Generics, utility types, declaration files, and tsconfig setups.")
        ],
        "react": [
            ("React Hooks & Context", "Functional components, custom hooks, and state context API."),
            ("State Management & Perf", "Redux/Zustand, bundle splitting, and rendering optimization.")
        ]
    }
    
    for skill in flat_missing_skills[:4]:  # Top 4 missing skills
        name_lower = skill["name"].lower()
        # Parse duration
        duration_str = skill["est_time"]  # e.g., "7 Days", "14 Days"
        try:
            days = int(re.search(r"\d+", duration_str).group())
        except Exception:
            days = 7
            
        stages = skill_stages.get(name_lower)
        if stages:
            mid_day = start_day + (days // 2) - 1
            end_day = start_day + days - 1
            roadmap_timeline.append({
                "days": f"DAY {start_day}-{mid_day}",
                "title": stages[0][0],
                "description": stages[0][1]
            })
            roadmap_timeline.append({
                "days": f"DAY {mid_day+1}-{end_day}",
                "title": stages[1][0],
                "description": stages[1][1]
            })
        else:
            mid_day = start_day + (days // 2) - 1
            end_day = start_day + days - 1
            roadmap_timeline.append({
                "days": f"DAY {start_day}-{mid_day}",
                "title": f"Foundational {skill['name']}",
                "description": f"Master core concepts, syntax, and fundamental tools of {skill['name']}."
            })
            roadmap_timeline.append({
                "days": f"DAY {mid_day+1}-{end_day}",
                "title": f"Advanced {skill['name']} Projects",
                "description": f"Build practical portfolio projects and integrate {skill['name']} into your workflow."
            })
        start_day += days

    if not roadmap_timeline:
        roadmap_timeline.append({
            "days": "Day 1-3",
            "title": "Keep Learning",
            "description": "No critical missing skills. Keep optimizing your resume for specific company cultures."
        })

    # Prepare Template Payload
    # -------------------------------
    results = {
        "success": True,
        "metrics": {
            "skill_match": skill_match_percentage,
            "semantic_match": similarity_percentage,
            "resume_strength": float(resume_strength_score),
            "final_score": final_score,
            "ats_readiness": ats_readiness,
            "badge": badge
        },
        "skills": {
            "matching": categorized_matching,
            "missing": categorized_missing,
            "matching_flat_count": len(matching_skills),
            "missing_flat_count": len(missing_skills),
            "total_jd_count": len(jd_skills),
            "category_progress": category_progress
        },
        "suggestions": suggestions,
        "extraction_method": extraction_method,
        "details": {
            "action_verb_count": action_verb_count,
            "metric_count": metric_count,
            "strength_breakdown": strength_breakdown
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
        "filename": filename
    }
    
    return results

# -------------------------------
# Upload Route (Renders result.html)
# -------------------------------
@app.route("/upload", methods=["POST"])
def upload():
    # -------------------------------
    # Validate Request Files
    # -------------------------------
    if "resume" not in request.files:
        return "No resume file uploaded", 400

    file = request.files["resume"]

    if file.filename == "":
        return "No selected file", 400

    if not file.filename.lower().endswith(".pdf"):
        return "Only PDF files are allowed", 400

    # -------------------------------
    # Validate Job Description
    # -------------------------------
    if "job_description" not in request.form:
        return "Job description is missing", 400

    job_description = request.form["job_description"]

    if len(job_description.strip()) < 20:
        return "Job description must be at least 20 characters long", 400

    job_description_lower = job_description.lower()

    # -------------------------------
    # Save Resume Safely
    # -------------------------------
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    extracted_text = ""
    extraction_method = "PDF Text Extraction"

    # -------------------------------
    # Text Extraction & Cleanup Wrapper
    # -------------------------------
    try:
        # Normal extraction
        with fitz.open(filepath) as doc:
            for page in doc:
                text = page.get_text()
                if text:
                    extracted_text += text + "\n"

        # OCR Fallback
        if len(extracted_text.strip()) < 100:
            print("PDF text extraction weak. Switching to OCR...")
            extracted_text = extract_text_with_ocr(filepath)
            extraction_method = "OCR Extraction"

    except Exception as e:
        print(f"Error during file extraction: {e}")
        return f"Failed to extract text from PDF: {str(e)}", 500
    finally:
        # Secure file deletion
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error removing temp file {filepath}: {e}")

    # -------------------------------
    # Final Verification
    # -------------------------------
    if len(extracted_text.strip()) == 0:
        return "Could not extract any text from the uploaded PDF", 400

    results = perform_analysis(extracted_text, job_description, filename, extraction_method)
    session["results"] = results
    return render_template("result.html", results_json=results, **results)

# -------------------------------
# Demo Route (POST)
# -------------------------------
@app.route("/demo", methods=["POST"])
def demo():
    demo_resume_text = """
    Alexander Davis
    Senior React Developer | Full Stack Engineer
    alexander.davis@email.com | +1 (555) 019-2834 | github.com/alexdavis | linkedin.com/in/alexanderdavis
    
    Summary:
    Dynamic and results-driven Senior React Developer with over 6 years of experience building high-performance web applications. Expert in React, TypeScript, Next.js, and modern state management. Proven track record of optimizing application performance, streamlining CI/CD pipelines, and leading cross-functional teams.
    
    Technical Skills:
    - Languages: JavaScript (ES6+), TypeScript, HTML5, CSS3, SQL, Python
    - Frameworks & Libraries: React.js, Next.js, Node.js, Express, Tailwind CSS, Bootstrap
    - State Management: Redux Toolkit, Context API, Zustand
    - Database & Tools: PostgreSQL, MongoDB, Redis, Git, Webpack, Vite, Postman
    - DevOps & Cloud: Docker, AWS (S3, EC2), CI/CD (GitHub Actions)
    
    Professional Experience:
    Senior Front-End Developer | InnovateTech (2022 - Present)
    - Spearheaded the redesign of the core enterprise dashboard using React and TypeScript, boosting load times by 32% and enhancing user engagement.
    - Designed and implemented clean, reusable component libraries with React and Tailwind CSS, reducing development cycle time by 15%.
    - Integrated complex RESTful APIs and established state management patterns using Zustand, improving data consistency across 12+ app views.
    - Mentored 4 junior developers on clean code standards and React hooks best practices.
    
    Software Engineer | CloudScale Solutions (2020 - 2022)
    - Developed scalable web interfaces in React and Node.js for SaaS clients, serving over 50k active weekly users.
    - Optimized database queries in PostgreSQL, achieving a 20% reduction in API response latency.
    - Built containerized development environments using Docker and automated testing via GitHub Actions.
    
    Projects:
    Interactive Portfolio & Analytics Tool
    - Built a personal analytics dashboard in Next.js and Tailwind CSS, incorporating interactive Chart.js visualizations.
    
    Education:
    Bachelor of Science in Computer Science | University of State (2016 - 2020)
    """
    
    job_description = request.form.get("job_description", "")
    if not job_description or len(job_description.strip()) < 20:
        job_description = """
        Senior React Developer
        Responsibilities:
        - Build responsive, beautiful, and interactive web applications.
        - Translate Figma designs into high-quality code.
        - Master state management, routing, and optimization.
        - Integrate GraphQL APIs and containerize apps.
        Requirements:
        - Expert level React.js, TypeScript, and Tailwind CSS.
        - Hands-on experience with Node.js, GraphQL, and Docker.
        - Familiarity with CI/CD, Git, and cloud services (AWS).
        """
        
    results = perform_analysis(demo_resume_text, job_description, "Alexander_Davis_Lead_Dev.pdf", "Demo Resume Parsing")
    session["results"] = results
    return render_template("result.html", results_json=results, **results)

# -------------------------------
# Set Session Results (POST)
# -------------------------------
@app.route("/set_session_results", methods=["POST"])
def set_session_results():
    data = request.json
    if data:
        session["results"] = data
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "No data provided"}), 400

# -------------------------------
# Download PDF Route (ReportLab)
# -------------------------------
@app.route("/download_pdf")
def download_pdf():
    # Read calculations from current session
    data = session.get("results")
    if not data:
        return "No active report results found to download. Please run a scan first.", 400

    try:
        pdf_buffer = generate_pdf_report(data)
        return send_file(
            pdf_buffer,
            download_name="ATS_Optimization_Report.pdf",
            as_attachment=True,
            mimetype="application/pdf"
        )
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return f"Failed to generate PDF report: {str(e)}", 500

# -------------------------------
# Dynamic Verdict Generator Helper
# -------------------------------
def generate_dynamic_verdict(matching_skills, missing_skills, category_progress, potential_improvement):
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

# -------------------------------
# Suggestions Generator Helper
# -------------------------------
def generate_suggestions(text_lower, text_original, match_percentage, action_verb_count, metric_count, strength_breakdown):
    suggestions = []
    
    # Category: Resume Structure
    if not strength_breakdown["work_experience"]["checked"]:
        suggestions.append({
            "category": "Resume Structure",
            "priority": "High",
            "title": "Add Work Experience Section",
            "description": "Your resume lacks a clearly labeled Work Experience section. Add one detailing your professional roles, responsibilities, and achievements."
        })
        
    if not strength_breakdown["projects"]["checked"]:
        suggestions.append({
            "category": "Resume Structure",
            "priority": "High",
            "title": "Add Projects Section",
            "description": "Including a Projects section showcases practical implementation of your skills, which is critical for standing out to recruiters."
        })
        
    if not strength_breakdown["skills_section"]["checked"]:
        suggestions.append({
            "category": "Resume Structure",
            "priority": "High",
            "title": "Add Dedicated Skills Section",
            "description": "Create a dedicated 'Technical Skills' section. ATS scanners look for structured skills sections to quickly index your qualifications."
        })
        
    if not strength_breakdown["education"]["checked"]:
        suggestions.append({
            "category": "Resume Structure",
            "priority": "Medium",
            "title": "Add Education Section",
            "description": "Add details about your degrees, certifications, or academic training to complete the structural requirement."
        })
        
    contact = strength_breakdown["contact_info"]
    if not contact["github"] or not contact["linkedin"]:
        missing_links = []
        if not contact["github"]:
            missing_links.append("GitHub profile")
        if not contact["linkedin"]:
            missing_links.append("LinkedIn profile")
        suggestions.append({
            "category": "Resume Structure",
            "priority": "Medium",
            "title": f"Add Contact Links ({', '.join(missing_links)})",
            "description": f"Recruiters expect to find links to professional platforms. Add your {', and '.join(missing_links)} to the header."
        })
        
    # Category: Technical Skills
    if match_percentage < 40:
        suggestions.append({
            "category": "Technical Skills",
            "priority": "High",
            "title": "Improve Skill Coverage",
            "description": "Your resume matches less than 40% of the job description's required skills. Review the missing skills list and integrate them naturally into your work history."
        })
    elif match_percentage < 70:
        suggestions.append({
            "category": "Technical Skills",
            "priority": "Medium",
            "title": "Address Key Missing Skills",
            "description": "Your skill match is moderate. Review the missing skills list and add 2-3 key technical items to improve alignment."
        })
    else:
        suggestions.append({
            "category": "Technical Skills",
            "priority": "Low",
            "title": "Great Skill Alignment",
            "description": "You have matching skills for over 70% of the job description. Ensure they are listed in your experience with relevant context."
        })
        
    # Category: Experience
    if action_verb_count < 5:
        suggestions.append({
            "category": "Experience",
            "priority": "Medium",
            "title": "Use Strong Action Verbs",
            "description": f"We only detected {action_verb_count} action verbs (like 'optimized', 'developed'). Revise your bullet points to start with strong, action-oriented verbs."
        })
    else:
        suggestions.append({
            "category": "Experience",
            "priority": "Low",
            "title": "Good Action Verbs Usage",
            "description": f"Great! Your resume uses {action_verb_count} action verbs, making your contributions sound active and impact-driven."
        })
        
    if metric_count < 3:
        suggestions.append({
            "category": "Experience",
            "priority": "High",
            "title": "Quantify Achievements",
            "description": f"We found only {metric_count} quantifiable metrics (numbers, %, $). Recruiters and ATS prefer resumes that show measurable impact. Quantify your accomplishments (e.g. 'Optimized app load time by 30%')."
        })
    else:
        suggestions.append({
            "category": "Experience",
            "priority": "Low",
            "title": "Quantified Impact Detected",
            "description": f"Excellent! Your resume includes {metric_count} quantifiable metrics showing measurable results."
        })
        
    # Category: Projects
    if strength_breakdown["projects"]["checked"] and len(text_lower) < 1500:
        suggestions.append({
            "category": "Projects",
            "priority": "Medium",
            "title": "Elaborate on Projects",
            "description": "Your overall resume content is a bit brief. Expand on your projects by using the STAR method (Situation, Task, Action, Result) to write descriptive bullet points."
        })
        
    # Category: Certifications
    suggestions.append({
        "category": "Certifications",
        "priority": "Low",
        "title": "Add Professional Certifications",
        "description": "Incorporate certifications related to the job role (e.g. AWS, Scrum Master, or equivalent) in a dedicated section to validate your expertise."
    })
    
    return suggestions

# -------------------------------
# ReportLab PDF Helper Function
# -------------------------------
def generate_pdf_report(data):
    buffer = BytesIO()
    # Margins: 36pt = 0.5 inch
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles for premium presentation
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#4f46e5'),
        spaceAfter=12
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    
    bold_body = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # 1. Document Title
    story.append(Paragraph("ATS Optimization Analysis Report", title_style))
    story.append(Paragraph(f"Method of Parsing: {data.get('extraction_method', 'N/A')}", body_style))
    story.append(Spacer(1, 10))
    
    # 2. Main Metrics Table
    metrics = data.get('metrics', {})
    score_data = [
        [
            Paragraph("<b>Overall Score</b>", body_style),
            Paragraph("<b>Skill Match</b>", body_style),
            Paragraph("<b>Semantic Match</b>", body_style),
            Paragraph("<b>Resume Strength</b>", body_style)
        ],
        [
            Paragraph(f"<font color='#4f46e5'><b>{metrics.get('final_score', 0):.2f}%</b></font>", ParagraphStyle('ScoreMain', parent=title_style, fontSize=18)),
            Paragraph(f"<b>{metrics.get('skill_match', 0):.2f}%</b>", ParagraphStyle('ScoreSkl', parent=title_style, fontSize=18, textColor=colors.HexColor('#0f172a'))),
            Paragraph(f"<b>{metrics.get('semantic_match', 0):.2f}%</b>", ParagraphStyle('ScoreSem', parent=title_style, fontSize=18, textColor=colors.HexColor('#0f172a'))),
            Paragraph(f"<b>{metrics.get('resume_strength', 0):.2f}%</b><br/><font size='7'>{metrics.get('badge', '')}</font>", body_style)
        ]
    ]
    t = Table(score_data, colWidths=[135, 135, 135, 135])
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))
    
    # 3. Dynamic Resume Verdict
    story.append(Paragraph("Resume Verdict", section_style))
    story.append(Paragraph(data.get('verdict', ''), body_style))
    story.append(Spacer(1, 10))
    
    # 4. ATS Checklist
    story.append(Paragraph("ATS Structural Checklist", section_style))
    chk = data.get('checklist', {})
    
    items = [
        ("Contact Information", chk.get('contact_info')),
        ("Skills Section", chk.get('skills')),
        ("Projects Section", chk.get('projects')),
        ("Education Section", chk.get('education')),
        ("Work Experience", chk.get('experience')),
        ("Certifications", chk.get('certifications')),
        ("LinkedIn Profile", chk.get('linkedin')),
        ("GitHub Profile", chk.get('github'))
    ]
    
    chk_rows = []
    for i in range(0, len(items), 2):
        item1_name, item1_val = items[i]
        item2_name, item2_val = items[i+1]
        
        status1 = "<font color='green'><b>PASS</b></font>" if item1_val else "<font color='red'><b>FAIL</b></font>"
        status2 = "<font color='green'><b>PASS</b></font>" if item2_val else "<font color='red'><b>FAIL</b></font>"
        
        chk_rows.append([
            Paragraph(item1_name, body_style), Paragraph(status1, body_style),
            Paragraph(item2_name, body_style), Paragraph(status2, body_style)
        ])
        
    t_chk = Table(chk_rows, colWidths=[180, 90, 180, 90])
    t_chk.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_chk)
    story.append(Spacer(1, 12))
    
    # 5. Missing Skills Roadmap
    story.append(Paragraph("Prioritized Missing Skills & Learning Roadmap", section_style))
    missing_skills = data.get('skills', {}).get('missing', {})
    
    flat_missing = []
    for cat, s_list in missing_skills.items():
        for s in s_list:
            flat_missing.append(s)
            
    if not flat_missing:
        story.append(Paragraph("No missing skills! Excellent keyword compliance.", body_style))
    else:
        for idx, s in enumerate(flat_missing[:8]): # Top 8 missing skills in PDF
            story.append(Paragraph(f"<b>Priority {idx+1}: {s['name']}</b> (Difficulty: {s['difficulty']} | Est. Time: {s.get('est_time', '7 Days')})", bold_body))
            story.append(Spacer(1, 3))
            
    story.append(Spacer(1, 10))
    
    # 6. Prioritized Improvement Suggestions
    story.append(Paragraph("Prioritized Improvement Suggestions", section_style))
    suggestions = data.get('suggestions', [])
    for idx, sugg in enumerate(suggestions[:6]): # top 6 suggestions
        story.append(Paragraph(f"<b>[{sugg.get('priority')} Priority] - {sugg.get('title')}</b>: {sugg.get('description')}", body_style))
        story.append(Spacer(1, 3))
        
    doc.build(story)
    buffer.seek(0)
    return buffer

# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
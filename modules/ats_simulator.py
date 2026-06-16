"""
ATS Simulator: Simulates how a corporate Applicant Tracking System would score a resume
against a specific job description using skill-based keyword matching, section detection,
and formatting analysis.
"""

import re
import os

ATS_SECTION_KEYWORDS = {
    "summary": ["summary", "objective", "profile", "about me", "professional summary"],
    "skills": ["skills", "technical skills", "core competencies", "expertise"],
    "experience": ["experience", "work experience", "employment", "work history"],
    "education": ["education", "academic", "qualification", "degree"],
    "projects": ["projects", "portfolio", "personal projects", "academic projects"],
}

FORMATTING_RED_FLAGS = [
    ("table", r'\|.*\|'),
    ("columns", r'\t{3,}'),
    ("headers", r'={5,}|-{5,}'),
]

# Massive English stopword list — these are NOT valid ATS keywords
STOPWORDS = {
    "the", "and", "for", "are", "that", "this", "have", "will", "from", "your",
    "you", "can", "our", "all", "any", "has", "its", "not", "but", "they", "their",
    "been", "more", "than", "work", "with", "about", "also", "into", "when", "what",
    "how", "who", "which", "where", "was", "were", "had", "his", "her", "him",
    "she", "they", "them", "then", "than", "too", "very", "just", "over", "such",
    "other", "some", "each", "both", "few", "most", "would", "could", "should",
    "must", "may", "might", "shall", "being", "become", "between", "through",
    "during", "before", "after", "above", "below", "here", "there", "same",
    "only", "own", "new", "make", "like", "use", "used", "using", "get", "got",
    "good", "well", "help", "high", "look", "need", "way", "day", "time", "year",
    "even", "know", "take", "made", "come", "give", "find", "think", "see",
    "want", "feel", "try", "best", "set", "put", "give", "keep", "let", "right",
    "still", "add", "large", "often", "hand", "place", "case", "show", "why",
    "ask", "men", "end", "long", "big", "down", "does", "across", "along",
    "however", "therefore", "because", "although", "while", "since", "unless",
    "provide", "provided", "ensure", "required", "requirements", "responsible",
    "including", "following", "related", "relevant", "preferred", "plus",
    "degree", "experience", "skills", "team", "role", "position", "company",
    "employment", "hiring", "candidate", "assess", "assessment", "evaluate",
    "communication", "collaboration", "ability", "strong", "excellent", "great",
    "proactive", "dynamic", "fast", "driven", "passion", "passionate", "detail",
    "oriented", "motivated", "analytical", "creative", "innovative", "flexible",
    "hybrid", "remote", "onsite", "fulltime", "part", "contract", "permanent",
    "salary", "package", "benefit", "benefits", "apply", "application", "join",
    "opportunity", "opportunities", "responsibilities", "qualification",
    "qualifications", "description", "decision", "generative", "operate",
    "support", "maintain", "manage", "develop", "design", "build", "create",
    "implement", "deliver", "drive", "lead", "enable", "ensure", "review",
    "analyze", "collaborate", "contribute", "solving", "problem", "solution",
    "mission", "vision", "goal", "objective", "function", "report", "process",
    "agent", "autogen", "automation", "business", "capabilities", "configure",
    "construct", "content", "contexts", "copilots", "enterprise", "feedback",
    "fine", "genai", "generators", "framework", "system", "systems", "platform",
    "platforms", "tools", "tool", "services", "service", "product", "products",
    "solutions", "architecture", "architectures", "infrastructure", "environment",
    "environments", "application", "applications", "software", "development",
    "engineer", "engineering", "developer", "developers", "program", "programs",
    "project", "projects", "management", "manager", "director", "executive",
    "professional", "expert", "expertise", "knowledge", "understanding", "strong",
    "excellent", "outstanding", "exceptional", "proven", "track", "record",
    "demonstrated", "ability", "capable", "proficient", "proficiency", "familiar",
    "familiarity", "experience", "experienced", "working", "work", "works",
    "worked", "using", "used", "uses", "use", "creating", "created", "creates",
    "create", "building", "built", "builds", "build", "developing", "developed",
    "develops", "develop", "designing", "designed", "designs", "design",
    "implementing", "implemented", "implements", "implement", "deploying",
    "deployed", "deploys", "deploy", "managing", "managed", "manages", "manage",
    "leading", "led", "leads", "lead", "supporting", "supported", "supports",
    "support", "maintaining", "maintained", "maintains", "maintain", "testing",
    "tested", "tests", "test", "analyzing", "analyzed", "analyzes", "analyze",
    "evaluating", "evaluated", "evaluates", "evaluate", "optimizing", "optimized",
    "optimizes", "optimize", "improving", "improved", "improves", "improve",
    "driving", "drove", "drives", "drive", "delivering", "delivered", "delivers",
    "deliver", "ensuring", "ensured", "ensures", "ensure", "providing", "provided",
    "provides", "provide", "collaborating", "collaborated", "collaborates",
    "collaborate", "working", "closely", "cross", "functional", "teams", "team",
    "members", "clients", "customers", "users", "stakeholders", "partners",
    "vendors", "internal", "external", "global", "local", "regional", "national",
    "international", "company", "organization", "industry", "sector", "market",
    "domain", "field", "area", "environment", "culture", "values", "mission",
    "vision", "goals", "objectives", "strategy", "strategies", "strategic",
    "tactical", "operational", "execution", "delivery", "performance", "metrics",
    "kpis", "results", "outcomes", "impact", "value", "roi", "quality", "standards",
    "best", "practices", "guidelines", "policies", "procedures", "processes",
    "methodologies", "frameworks", "tools", "technologies", "systems", "platforms",
    "applications", "software", "hardware", "infrastructure", "networks", "security",
    "data", "information", "knowledge", "insights", "analytics", "reporting",
    "dashboards", "visualizations", "models", "algorithms", "machine", "learning",
    "artificial", "intelligence", "ai", "ml", "deep", "neural", "networks", "nlp",
    "computer", "vision", "robotics", "automation", "cloud", "computing", "aws",
    "azure", "gcp", "devops", "ci", "cd", "pipelines", "containers", "docker",
    "kubernetes", "microservices", "apis", "rest", "graphql", "databases", "sql",
    "nosql", "relational", "non", "data", "warehouses", "lakes", "pipelines",
    "etl", "elt", "big", "hadoop", "spark", "kafka", "streaming", "real", "time",
    "batch", "processing", "web", "mobile", "desktop", "frontend", "backend",
    "full", "stack", "ui", "ux", "design", "development", "testing", "deployment",
    "maintenance", "support", "operations", "management", "leadership", "mentoring",
    "coaching", "training", "hiring", "recruiting", "onboarding", "performance",
    "reviews", "feedback", "career", "growth", "development", "opportunities",
}

def _load_skill_taxonomy():
    """Load the tech skills list to use as a reference for meaningful keyword extraction."""
    skills = set()
    base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, "..", "data")
    for fname in ["tech_skills.txt", "non_tech_skills.txt"]:
        fpath = os.path.join(data_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip().lower()
                    if s:
                        skills.add(s)
    return skills

# Load once at module import time
_SKILL_TAXONOMY = _load_skill_taxonomy()

def simulate_ats_score(resume_text: str, job_description: str) -> dict:
    """
    Returns a full ATS simulation report with a score out of 100.
    Keywords are now cross-referenced against the skills taxonomy for accuracy.
    """
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()

    # --- 1. Skill-Based Keyword Matching (40 points) ---
    # Extract clean technical skills from JD using our robust unified skill extractor
    from .skill_extractor import extract_skills_from_text
    from .job_analyzer import clean_extracted_skills
    
    extracted = extract_skills_from_text(job_description)
    cleaned = clean_extracted_skills(extracted)
    jd_keywords = set(s.lower() for s in cleaned)

    matched_kw = []
    missing_kw = []

    for kw in jd_keywords:
        pattern = re.escape(kw)
        if re.search(r'\b' + pattern + r'\b' if ' ' not in kw else pattern, resume_lower):
            matched_kw.append(kw)
        else:
            missing_kw.append(kw)

    kw_score = min(40, (len(matched_kw) / max(len(jd_keywords), 1)) * 40)

    # --- 2. Section Detection (30 points) ---
    section_results = {}
    section_score = 0
    points_per_section = 30 / len(ATS_SECTION_KEYWORDS)

    for section, keywords in ATS_SECTION_KEYWORDS.items():
        found = any(kw in resume_lower for kw in keywords)
        section_results[section] = found
        if found:
            section_score += points_per_section

    # --- 3. Formatting Check (20 points) ---
    format_warnings = []
    format_score = 20
    for name, pattern in FORMATTING_RED_FLAGS:
        match = re.search(pattern, resume_text)
        if match:
            # Extract 20 characters of context around the match to show exactly where it is
            start = max(0, match.start() - 20)
            end = min(len(resume_text), match.end() + 20)
            context = resume_text[start:end].replace('\n', ' ').replace('\r', '').strip()
            # truncate long contexts
            if len(context) > 60:
                context = context[:60] + "..."
                
            format_warnings.append(f"Detected possible {name} formatting near \"...{context}...\" — ATS may misread this section.")
            format_score -= 7

    format_score = max(0, format_score)

    # --- 4. Length Check (10 points) ---
    word_count = len(resume_text.split())
    length_score = 10
    length_note = ""
    if word_count < 200:
        length_score = 3
        length_note = f"Resume is too short ({word_count} words). ATS may flag it as incomplete."
    elif word_count > 1000:
        length_score = 7
        length_note = f"Resume is very long ({word_count} words). Consider trimming to 1-2 pages."
    else:
        length_note = f"Good length ({word_count} words)."

    # --- Final Score ---
    total = round(kw_score + section_score + format_score + length_score)
    total = max(0, min(100, total))

    grade = "Poor"
    if total >= 80:
        grade = "Excellent"
    elif total >= 60:
        grade = "Good"
    elif total >= 40:
        grade = "Fair"

    return {
        "ats_score": total,
        "grade": grade,
        "breakdown": {
            "keyword_score": round(kw_score, 1),
            "keyword_max": 40,
            "section_score": round(section_score, 1),
            "section_max": 30,
            "format_score": round(format_score, 1),
            "format_max": 20,
            "length_score": round(length_score, 1),
            "length_max": 10,
        },
        "matched_keywords": sorted(matched_kw)[:20],
        "missing_keywords": sorted(missing_kw)[:20],
        "section_detection": section_results,
        "format_warnings": format_warnings,
        "length_note": length_note,
        "total_jd_keywords": len(jd_keywords),
    }

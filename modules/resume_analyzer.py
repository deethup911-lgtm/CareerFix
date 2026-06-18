import re
import json
import os
from .skill_extractor import extract_skills_from_text
from .utils import get_env_var
from .ollama_client import generate_content

# Keywords that signal an actively-enrolled student (not just a recent graduate)
_STUDENT_ENROLLED_KEYWORDS = [
    "pursuing", "currently pursuing", "currently studying",
    "1st year", "2nd year", "3rd year", "4th year", "5th year",
    "first year", "second year", "third year", "fourth year", "fifth year",
    "semester", "ongoing", "expected graduation", "expected to graduate",
    "integrated mca", "integrated bca", "integrated b.tech",
]

# Degree abbreviations that, when combined with zero work-experience, imply student/fresher
_DEGREE_KEYWORDS = [
    "b.sc", "b.tech", "bca", "mca", "b.e", "m.sc", "m.tech", "bba", "mba",
    "b.com", "m.com", "bachelor", "master", "undergraduate", "postgraduate"
]

def detect_experience_level_and_years(text):
    text_lower = text.lower()
    years = 0

    # Try to find 'X years experience' (professional, not academic)
    # Covers: "5 years experience", "5 years of experience", "5 years of work experience", "5+ years"
    matches = re.findall(
        r'(\d+)(?:\+| -| to)?\s*years?(?:\s*of)?(?:\s*work)?\s*experience',
        text_lower
    )
    if not matches:
        matches = re.findall(r'experience:?\s*(\d+)', text_lower)

    if matches:
        try:
            years = int(matches[0])
        except Exception:
            pass

    if years == 0:
        # Distinguish actively-enrolled students from recent graduates (Fresher)
        is_enrolled = any(kw in text_lower for kw in _STUDENT_ENROLLED_KEYWORDS)
        is_student_keyword = re.search(r'\bstudent\b', text_lower)
        has_degree = any(kw in text_lower for kw in _DEGREE_KEYWORDS)

        if is_enrolled or is_student_keyword:
            level = "Student"
        elif has_degree:
            # Graduate with 0 work experience → Fresher
            level = "Fresher"
        else:
            level = "Fresher"  # Default for 0-year candidates
    elif 1 <= years <= 2:
        level = "Junior"
    elif 3 <= years <= 5:
        level = "Mid-Level"
    else:
        level = "Senior"

    return level, years

def analyze_resume(resume_text):
    # 1. Local Skill Extraction
    local_skills = extract_skills_from_text(resume_text)
    
    # 2. Local Experience Detection
    level, years = detect_experience_level_and_years(resume_text)
    
    result = {
        "skills": local_skills,
        "experience_level": level,
        "experience_years": years,
        "summary": "Generated locally based on extracted skills.",
        "projects": [],
        "education": "Not extracted locally.",
        "domain_hint": "General/IT",
        "contact_info": {
            "name": "",
            "email": "",
            "phone": "",
            "linkedin": ""
        },
        "error_log": []
    }
    
    # 3. Optional Ollama Enhancement
    try:
        prompt = f"""
        Analyze the following resume text.
        Extract any major projects, a professional summary, the education background, a general domain hint (e.g., AI/ML, Full Stack, HR, Marketing), and contact information.

        IMPORTANT GUIDELINES:
        1. Do not hallucinate skills. Only return skills that are clearly mentioned in the text.
        2. For `experience_years`, ONLY count full-time, professional employment. DO NOT count university degrees, academic projects, hackathons, or student club leadership as years of experience. Short internships (e.g., 3 weeks) do NOT count as full years. If the candidate is a student or recent graduate without long-term employment, experience_years MUST be 0.
        3. For `experience_level`, use EXACTLY one of these values:
           - "Student"  → currently enrolled in a degree (e.g., 3rd year MCA, pursuing B.Tech)
           - "Fresher"  → recently graduated, 0 years of work experience
           - "Junior"   → 1-2 years of professional experience
           - "Mid-Level" → 3-5 years
           - "Senior"  → 6+ years

        Return a JSON object with this structure:
        {{
            "skills": ["List of ONLY skills present in the resume text"],
            "experience_level": "Student/Fresher/Junior/Mid-Level/Senior",
            "experience_years": 0,
            "summary": "A 2-sentence summary of the candidate.",
            "projects": ["Project 1 name/description", "Project 2 name/description"],
            "education": "Highest degree or education info",
            "domain_hint": "Domain name",
            "contact_info": {{
                "name": "Candidate Full Name or ''",
                "email": "Email address or ''",
                "phone": "Phone number or ''",
                "linkedin": "LinkedIn or Portfolio URL or ''"
            }}
        }}
        Resume Text:
        {resume_text}
        """

        ollama_data = generate_content(prompt, json_mode=True)
        if ollama_data:
            # Merge logic: Local skills are source of truth, Ollama can only add if present in text
            ollama_skills = ollama_data.get("skills", [])
            for gs in ollama_skills:
                if gs.lower() in resume_text.lower() and gs not in result["skills"]:
                    result["skills"].append(gs)

            # Update other fields
            result["summary"] = ollama_data.get("summary", result["summary"])
            result["projects"] = ollama_data.get("projects", [])
            result["education"] = ollama_data.get("education", result["education"])
            result["domain_hint"] = ollama_data.get("domain_hint", result["domain_hint"])
            result["contact_info"] = ollama_data.get("contact_info", result["contact_info"])

            # If Ollama found more precise years, trust it if local failed
            # BUT: never let Ollama downgrade a local "Student" classification —
            # local keyword detection is more reliable for enrollment status.
            if result["experience_years"] == 0 and ollama_data.get("experience_years", 0) > 0:
                result["experience_years"] = ollama_data["experience_years"]
                # Only update level if local didn't tag as Student
                if result["experience_level"] != "Student":
                    result["experience_level"] = ollama_data.get("experience_level", result["experience_level"])
            elif result["experience_level"] == "Fresher":
                # If local said Fresher but Ollama says Student, trust Ollama
                ollama_level = ollama_data.get("experience_level", "")
                if ollama_level == "Student":
                    result["experience_level"] = "Student"

    except Exception as e:
        print(f"Ollama enhancement failed: {e}")
        result["error_log"].append(f"Ollama enhancement failed: {e}")
            
    # Clean up skills
    result["skills"] = sorted(list(set(result["skills"])))
    
    return result

def is_student_resume(resume_text, resume_analysis):
    if not resume_analysis:
        return False
    
    if resume_analysis.get("experience_level") in ["Fresher", "Student", "Intern"]:
        return True
        
    if resume_analysis.get("experience_years", 0) == 0:
        return True
        
    text_lower = (resume_text or "").lower()
    student_keywords = [
        r"\bstudent\b", r"\buniversity\b", r"\bcollege\b", 
        r"\bundergrad", r"\bpostgrad", r"\binternship\b", 
        r"\bsummer intern", r"\bfresher\b", r"\bco-op\b", 
        r"\bb\.tech\b", r"\bm\.tech\b", r"\bb\.s\b", r"\bm\.s\b", r"\bbca\b", r"\bmca\b"
    ]
    for pattern in student_keywords:
        if re.search(pattern, text_lower):
            return True
            
    return False


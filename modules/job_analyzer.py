import json
from .skill_extractor import extract_skills_from_text

def clean_extracted_skills(skills):
    # Remove soft skills / generic terms that might slip in
    generic_terms = {
        "project", "team", "business", "solution", "communication", 
        "motivation", "collaboration", "problem solving", "leadership",
        "analytical", "agile", "scrum", "development"
    }
    
    cleaned = []
    for s in skills:
        if s.lower() not in generic_terms:
            cleaned.append(s)
    return cleaned

def extract_job_skills(job_description):
    """
    Extracts skills purely locally using the robust regex engine.
    Gemini extraction has been disabled here to prevent O(N) API rate limit exhaustion
    and long loading times during the matching phase.
    """
    local_skills = extract_skills_from_text(job_description)
    
    final_skills = clean_extracted_skills(local_skills)
    return sorted(list(set(final_skills)))

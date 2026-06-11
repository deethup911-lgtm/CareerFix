import re
import json
import os
from .skill_extractor import extract_skills_from_text
from .utils import get_env_var
from .ollama_client import generate_content

def detect_experience_level_and_years(text):
    text_lower = text.lower()
    years = 0
    
    # Try to find 'X years experience'
    matches = re.findall(r'(\d+)(?:\+| -| to)?\s*years?(?:\s*of)?\s*(?:work)?\s*experience', text_lower)
    if not matches:
        matches = re.findall(r'experience:?\s*(\d+)', text_lower)
    
    if matches:
        try:
            years = int(matches[0])
        except:
            pass
            
    level = "Fresher"
    if years == 0:
        fresher_keywords = ["intern", "fresher", "student", "graduate", "trainee", "b.sc", "b.tech", "entry level", "entry-level"]
        if any(kw in text_lower for kw in fresher_keywords):
            level = "Fresher"
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
        IMPORTANT: Do not hallucinate skills. Only return skills that are clearly mentioned in the text.
        Return a JSON object with this structure:
        {{
            "skills": ["List of ONLY skills present in the resume text"],
            "experience_level": "Fresher/Junior/Mid-Level/Senior",
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
            if result["experience_years"] == 0 and ollama_data.get("experience_years", 0) > 0:
                result["experience_years"] = ollama_data["experience_years"]
                result["experience_level"] = ollama_data.get("experience_level", result["experience_level"])
                
    except Exception as e:
        print(f"Ollama enhancement failed: {e}")
        result["error_log"].append(f"Ollama enhancement failed: {e}")
            
    # Clean up skills
    result["skills"] = sorted(list(set(result["skills"])))
    
    return result

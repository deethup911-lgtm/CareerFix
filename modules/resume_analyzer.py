import re
import json
import os
from .skill_extractor import extract_skills_from_text
from .utils import get_env_var
try:
    from google import genai
except ImportError:
    genai = None

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
        "error_log": []
    }
    
    # 3. Optional Gemini Enhancement
    api_key = get_env_var("GEMINI_API_KEY")
    if api_key and genai:
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"""
            Analyze the following resume text.
            Extract any major projects, a professional summary, the education background, and a general domain hint (e.g., AI/ML, Full Stack, HR, Marketing).
            IMPORTANT: Do not hallucinate skills. Only return skills that are clearly mentioned in the text.
            Return a JSON object with this structure:
            {{
                "skills": ["List of ONLY skills present in the resume text"],
                "experience_level": "Fresher/Junior/Mid-Level/Senior",
                "experience_years": 0,
                "summary": "A 2-sentence summary of the candidate.",
                "projects": ["Project 1 name/description", "Project 2 name/description"],
                "education": "Highest degree or education info",
                "domain_hint": "Domain name"
            }}
            Resume Text:
            {resume_text}
            """
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            
            gemini_data = json.loads(response.text)
            
            # Merge logic: Local skills are source of truth, Gemini can only add if present in text
            gemini_skills = gemini_data.get("skills", [])
            for gs in gemini_skills:
                if gs.lower() in resume_text.lower() and gs not in result["skills"]:
                    result["skills"].append(gs)
            
            # Update other fields
            result["summary"] = gemini_data.get("summary", result["summary"])
            result["projects"] = gemini_data.get("projects", [])
            result["education"] = gemini_data.get("education", result["education"])
            result["domain_hint"] = gemini_data.get("domain_hint", result["domain_hint"])
            
            # If Gemini found more precise years, trust it if local failed
            if result["experience_years"] == 0 and gemini_data.get("experience_years", 0) > 0:
                result["experience_years"] = gemini_data["experience_years"]
                result["experience_level"] = gemini_data.get("experience_level", result["experience_level"])
                
        except Exception as e:
            print(f"Gemini enhancement failed: {e}")
            result["error_log"].append(f"Gemini enhancement failed: {e}")
            
    # Clean up skills
    result["skills"] = sorted(list(set(result["skills"])))
    
    return result

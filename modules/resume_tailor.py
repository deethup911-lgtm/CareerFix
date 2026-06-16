import json
import re
from .ollama_client import generate_content, REASONING_MODEL
from .resume_analyzer import detect_experience_level_and_years
from .experience_extractor import extract_job_experience

def validate_and_sanitize_tailoring(result, resume_text, candidate_level, candidate_years, matched_skills, missing_skills):
    """
    Validates and sanitizes LLM suggestions on the Python side.
    Ensures no senior titles are added for freshers/juniors, no skills are fabricated,
    and no advanced concepts are invented.
    """
    resume_lower = resume_text.lower()
    
    # 1. Forbidden senior words (for fresher/junior candidates)
    is_junior_candidate = candidate_level in ["Fresher", "Junior"]
    forbidden_pattern = re.compile(
        r'\b(senior|sr\.?|lead|architect|principal|director|manager|chief|vp)\b', 
        re.IGNORECASE
    )
    
    # 2. Do-not-add keywords replacements
    do_not_add_map = {
        r'\bfine-tuning\b': 'integration',
        r'\bfine tuning\b': 'integration',
        r'\blora\b': '',
        r'\bpeft\b': '',
        r'\bmlops\b': 'deployment',
        r'\bmodel monitoring\b': 'model testing',
        r'\bgdpr\b': '',
        r'\bbusiness stakeholder\b': '',
        r'\bstakeholder\b': '',
        r'\b5\+\s*years\b': f"{candidate_years} years" if candidate_years > 0 else "entry level",
        r'\b5\s*years\b': f"{candidate_years} years" if candidate_years > 0 else "entry level"
    }
    
    def sanitize_text(text):
        if not isinstance(text, str):
            return text
            
        cleaned = text
        
        # Apply do-not-add keyword rules if not in resume
        for pattern, replacement in do_not_add_map.items():
            raw_word = re.sub(r'\\b', '', pattern).replace('\\s*', ' ').replace('\\+', '+')
            if raw_word.lower() not in resume_lower:
                cleaned = re.compile(pattern, re.IGNORECASE).sub(replacement, cleaned)
                
        # Apply forbidden senior words rule if candidate is junior/fresher
        if is_junior_candidate:
            cleaned = forbidden_pattern.sub('', cleaned)
            
        # Clean up double spaces, punctuation anomalies
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\s+([,\.!])', r'\1', cleaned)
        cleaned = cleaned.strip()
        return cleaned

    # Process summary suggestion
    if "summary_suggestion" in result:
        result["summary_suggestion"] = sanitize_text(result["summary_suggestion"])
        
    # Process project bullet suggestions
    if "project_bullet_suggestions" in result and isinstance(result["project_bullet_suggestions"], list):
        result["project_bullet_suggestions"] = [
            sanitize_text(b) for b in result["project_bullet_suggestions"]
        ]
        
    # Process skills section suggestions
    if "skills_section_suggestion" in result and isinstance(result["skills_section_suggestion"], list):
        result["skills_section_suggestion"] = [
            sanitize_text(s) for s in result["skills_section_suggestion"]
        ]
        
    # 3. Matched/Missing skills validation (keep only valid taxonomy missing skills)
    if "ats_keywords_to_add" in result and isinstance(result["ats_keywords_to_add"], list):
        valid_missing = set(s.lower() for s in missing_skills)
        validated_kws = []
        for kw in result["ats_keywords_to_add"]:
            # Clean parentheses comments like "(learn/add only if true)"
            kw_clean = re.sub(r'\(.*\)', '', kw).strip().lower()
            if kw_clean in valid_missing:
                # Add “add only if true/experienced” warning suffix
                suffix = " (add only if true/experienced)"
                if not kw.endswith(suffix):
                    kw = f"{kw_clean.title()}{suffix}"
                validated_kws.append(kw)
            else:
                # Substring check
                match_found = next((m for m in valid_missing if m in kw_clean or kw_clean in m), None)
                if match_found:
                    suffix = " (add only if true/experienced)"
                    validated_kws.append(f"{match_found.title()}{suffix}")
        result["ats_keywords_to_add"] = validated_kws

    return result

def get_rule_based_fallback(matched_skills, missing_skills, candidate_level, candidate_years):
    return {
        "summary_suggestion": f"AI & Software Developer specializing in {', '.join(matched_skills[:3]) if matched_skills else 'software engineering'}. Proven ability to build applications using {', '.join(matched_skills[3:5]) if len(matched_skills) > 4 else 'modern frameworks'}.",
        "project_bullet_suggestions": [
            f"Optimized software performance by integrating {', '.join(matched_skills[:2]) if matched_skills else 'core features'} to meet requirements.",
            f"Collaborated on development workflows using {matched_skills[2] if len(matched_skills) > 2 else 'industry standard tools'}."
        ],
        "skills_section_suggestion": [
            "Group core technical competencies at the top of your skills section for better ATS visibility."
        ],
        "ats_keywords_to_add": [f"{s.title()} (add only if true/experienced)" for s in missing_skills[:5]],
        "course_recommendations": [
            f"Review official documentation or standard courses for {missing_skills[0]}" if missing_skills else "Brush up on technical skill gaps."
        ],
        "warnings": ["qwen3:8b was unavailable. Returned static rule-based suggestions."]
    }

def tailor_resume(resume_text, job_description, matched_skills, missing_skills):
    # 1. Experience Detection (Python side)
    candidate_level, candidate_years = detect_experience_level_and_years(resume_text)
    
    # 2. JD Seniority Detection (Python side)
    jd_exp_data = extract_job_experience(job_description)
    jd_seniority = jd_exp_data["seniority"]
    
    try:
        prompt = f"""
        You are an elite executive career coach and ATS optimization expert.
        Analyze the candidate's resume and the target job description.
        Candidate Experience Level: {candidate_level} ({candidate_years} years)
        Job Seniority Level: {jd_seniority}
        
        Provide highly specific, actionable advice on exactly what sentences to replace and what keywords to add.
        
        CRITICAL RULES:
        1. DO NOT suggest senior/lead/architect wording for fresher or junior candidates.
        2. DO NOT invent skills or advanced concepts (e.g. fine-tuning, LoRA, PEFT, MLOps, model monitoring, GDPR) unless they are clearly present in the candidate's resume text.
        3. Suggest direct, actionable improvements based strictly on verified resume content.
        
        Return a JSON object with this exact structure:
        {{
          "summary_suggestion": "Replace '...' with '...'",
          "project_bullet_suggestions": [
             "In the [Project Name] section, replace '...' with '...'"
          ],
          "skills_section_suggestion": [
             "Move [Skill] to the top of your skills list"
          ],
          "ats_keywords_to_add": ["{', '.join(missing_skills[:10])} (add only if true/experienced)"],
          "course_recommendations": [
             "Optional: Recommend a specific course to close a critical gap"
          ],
          "warnings": ["Any warnings about overclaiming or formatting issues"]
        }}
        
        Resume (excerpt):
        {resume_text[:2000]}
        
        Job Description (excerpt):
        {job_description[:2000]}
        """
            
        result = generate_content(prompt, json_mode=True, model=REASONING_MODEL)
        if result and isinstance(result, dict) and "summary_suggestion" in result:
            # Apply Python guardrails & sanitization
            return validate_and_sanitize_tailoring(
                result, resume_text, candidate_level, candidate_years, matched_skills, missing_skills
            )
        else:
            return get_rule_based_fallback(matched_skills, missing_skills, candidate_level, candidate_years)
            
    except Exception as e:
        print(f"Error tailoring resume: {e}")
        return get_rule_based_fallback(matched_skills, missing_skills, candidate_level, candidate_years)

def generate_interview_questions(job_title, job_description, candidate_skills):
    try:
        prompt = f"""
        You are a senior hiring manager preparing for an interview.
        Generate exactly 5 realistic, targeted interview questions for this role.
        Mix technical and behavioral questions based on the job and the candidate's skills.
        
        Job Title: {job_title}
        Candidate Skills: {', '.join(candidate_skills[:20])}
        Job Description (excerpt): {job_description[:1500]}
        
        Return a JSON object:
        {{
          "questions": [
            {{"question": "...", "type": "Technical", "tip": "Focus on..."}},
            {{"question": "...", "type": "Behavioral", "tip": "Use the STAR method"}}
          ]
        }}
        """
        result = generate_content(prompt, json_mode=True, model=REASONING_MODEL)
        if result:
            return result
        return {"questions": [{"question": "Error generating questions", "type": "Error", "tip": ""}]}
    except Exception as e:
        print(f"Error generating interview questions: {e}")
        return {"questions": [{"question": f"Error: {e}", "type": "Error", "tip": ""}]}

CERTIFICATION_DATABASE = {
    "aws": {"name": "AWS Certified Solutions Architect", "provider": "Amazon / Coursera", "url": "https://aws.amazon.com/certification/", "duration": "3-6 months"},
    "azure": {"name": "Microsoft Certified: Azure Developer Associate", "provider": "Microsoft", "url": "https://learn.microsoft.com/en-us/credentials/certifications/azure-developer/", "duration": "1-2 months"},
    "gcp": {"name": "Google Cloud Associate Cloud Engineer", "provider": "Google", "url": "https://cloud.google.com/learn/certification/associate-cloud-engineer", "duration": "2-3 months"},
    "python": {"name": "Python Institute: Certified Associate in Python Programming", "provider": "Python Institute", "url": "https://pythoninstitute.org/pcap", "duration": "1 month"},
    "docker": {"name": "Docker Certified Associate (DCA)", "provider": "Docker / Mirantis", "url": "https://training.mirantis.com/certification/dca-certification-exam/", "duration": "1-2 months"},
    "kubernetes": {"name": "Certified Kubernetes Application Developer (CKAD)", "provider": "CNCF / Linux Foundation", "url": "https://training.linuxfoundation.org/certification/certified-kubernetes-application-developer-ckad/", "duration": "2 months"},
    "react": {"name": "React Basics & Advanced Course Certifications", "provider": "Meta / Coursera", "url": "https://www.coursera.org/professional-certificates/meta-front-end-developer", "duration": "1-2 months"},
    "javascript": {"name": "JavaScript Algorithms and Data Structures", "provider": "freeCodeCamp", "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/", "duration": "1 month"},
    "ux": {"name": "Google UX Design Professional Certificate", "provider": "Google / Coursera", "url": "https://www.coursera.org/professional-certificates/google-ux-design", "duration": "3-6 months"},
    "user experience": {"name": "Google UX Design Professional Certificate", "provider": "Google / Coursera", "url": "https://www.coursera.org/professional-certificates/google-ux-design", "duration": "3-6 months"},
    "ui": {"name": "UI/UX Design Specialization", "provider": "CalArts / Coursera", "url": "https://www.coursera.org/specializations/ui-ux-design", "duration": "2-3 months"},
    "machine learning": {"name": "Machine Learning Specialization", "provider": "DeepLearning.AI / Stanford", "url": "https://www.coursera.org/specializations/machine-learning-introduction", "duration": "2-3 months"},
    "deep learning": {"name": "Deep Learning Specialization", "provider": "DeepLearning.AI / Coursera", "url": "https://www.coursera.org/specializations/deep-learning", "duration": "3 months"},
    "tensorflow": {"name": "TensorFlow Developer Professional Certificate", "provider": "DeepLearning.AI / Coursera", "url": "https://www.coursera.org/professional-certificates/tensorflow-in-practice", "duration": "1-2 months"},
    "pytorch": {"name": "PyTorch for Deep Learning Bootcamp", "provider": "Udemy", "url": "https://www.udemy.com/course/pytorch-for-deep-learning/", "duration": "1 month"}
}

def suggest_certifications(missing_skills, job_title):
    import urllib.parse
    try:
        # Build rule-based fallback list in case Ollama fails or doesn't have the model
        fallback_certs = []
        for skill in missing_skills:
            skill_lower = skill.lower().strip()
            if skill_lower in CERTIFICATION_DATABASE:
                cert_info = CERTIFICATION_DATABASE[skill_lower]
                fallback_certs.append({
                    "name": cert_info["name"],
                    "provider": cert_info["provider"],
                    "skill_addressed": skill,
                    "url": cert_info["url"],
                    "duration": cert_info["duration"],
                    "free": "freecodecamp" in cert_info["url"].lower()
                })
                
        if not fallback_certs:
            # Generate generic fallback entries for any other technical gaps
            for skill in missing_skills[:3]:
                quoted_query = urllib.parse.quote(f"{skill} certification")
                fallback_certs.append({
                    "name": f"Mastering {skill.title()} Professional Certificate",
                    "provider": "Coursera / Udemy / edX",
                    "skill_addressed": skill,
                    "url": f"https://www.coursera.org/search?query={quoted_query}",
                    "duration": "1-2 months",
                    "free": False
                })

        prompt = f"""
        You are a career development advisor.
        Based on the missing skills for this job, recommend the top 3-5 specific certifications or courses 
        that would directly close the skill gaps and make the candidate more competitive.
        Provide suggestions for popular sites like Coursera, Udemy, edX, or official providers.
        
        Job Title: {job_title}
        Missing Skills: {', '.join(missing_skills[:15])}
        
        Return a JSON object:
        {{
          "certifications": [
            {{
              "name": "AWS Certified Solutions Architect",
              "provider": "Amazon / Coursera",
              "skill_addressed": "AWS",
              "url": "https://aws.amazon.com/certification/",
              "duration": "3-6 months",
              "free": false
            }}
          ]
        }}
        """
        result = generate_content(prompt, json_mode=True, model=REASONING_MODEL)
        if result and isinstance(result, dict) and "certifications" in result and len(result["certifications"]) > 0:
            return result
        # Return fallback certifications if Ollama fails or returns empty lists
        return {"certifications": fallback_certs[:3]}
    except Exception as e:
        print(f"Error suggesting certifications: {e}")
        return {"certifications": fallback_certs[:3] if 'fallback_certs' in locals() else []}

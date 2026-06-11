import json
from .ollama_client import generate_content

def tailor_resume(resume_text, job_description, matched_skills, missing_skills):
    try:
        prompt = f"""
        You are an elite executive career coach and ATS optimization expert.
        Analyze the candidate's resume and the target job description.
        Provide highly specific, actionable advice on exactly what sentences to replace and what keywords to add to maximize their chances of getting hired.
        
        CRITICAL RULES:
        1. DO NOT fabricate experience. DO NOT add skills the user does not have.
        2. Make your suggestions extremely professional and impactful. Focus on action verbs and quantifiable metrics.
        3. Phrase your suggestions as direct, actionable instructions (e.g., "Replace the sentence '...' with '...'").
        
        Return a JSON object with this exact structure:
        {{
          "summary_suggestion": "Replace '...' with '...'",
          "project_bullet_suggestions": [
             "In the [Project Name] section, replace '...' with '...'",
             "Add a new bullet to [Experience]: '...'"
          ],
          "skills_section_suggestion": [
             "Move [Skill] to the top of your skills list", 
             "Group [Skill1] and [Skill2] under 'Frontend Development'"
          ],
          "ats_keywords_to_add": ["{', '.join(missing_skills[:10])} (learn/add only if true)"],
          "course_recommendations": [
             "Optional: Recommend a specific course to close a critical gap"
          ],
          "warnings": ["Any warnings about overclaiming or formatting issues"]
        }}
        
        Resume:
        {resume_text[:2000]}
        
        Job Description:
        {job_description[:2000]}
        """
            
        result = generate_content(prompt, json_mode=True)
        if result:
            return result
        else:
            return {
                "summary_suggestion": "Error generating suggestions.",
                "project_bullet_suggestions": [],
                "skills_section_suggestion": [],
                "ats_keywords_to_add": [],
                "course_recommendations": [],
                "warnings": ["Failed to communicate with local AI."]
            }
    except Exception as e:
        print(f"Error tailoring resume: {e}")
        return {
            "summary_suggestion": "Error communicating with AI.",
            "project_bullet_suggestions": [],
            "skills_section_suggestion": [],
            "ats_keywords_to_add": [],
            "course_recommendations": [],
            "warnings": [str(e)]
        }

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
        result = generate_content(prompt, json_mode=True)
        if result:
            return result
        return {"questions": [{"question": "Error generating questions", "type": "Error", "tip": ""}]}
    except Exception as e:
        print(f"Error generating interview questions: {e}")
        return {"questions": [{"question": f"Error: {e}", "type": "Error", "tip": ""}]}

def suggest_certifications(missing_skills, job_title):
    try:
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
        result = generate_content(prompt, json_mode=True)
        if result:
            return result
        return {"certifications": []}
    except Exception as e:
        print(f"Error suggesting certifications: {e}")
        return {"certifications": []}

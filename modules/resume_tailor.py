import json
from .ollama_client import generate_content

def tailor_resume(resume_text, job_description, matched_skills, missing_skills, generate_full_resume=False):
    try:
        if generate_full_resume:
            prompt = f"""
            You are an expert resume writer.
            Analyze the candidate's resume and the target job description.
            REWRITE the resume content to perfectly match this specific job, while remaining truthful to their actual skills.
            Do NOT fabricate experience or add skills they do not possess.
            
            Return a JSON object with a fully tailored resume section:
            {{
              "tailored_summary": "A powerful new professional summary rewritten for this role...",
              "tailored_experience": [
                 "Rewritten bullet point 1 highlighting relevant achievements",
                 "Rewritten bullet point 2 emphasizing required skills"
              ],
              "updated_skills": ["Skill 1", "Skill 2"],
              "ats_keywords_added": ["Keyword 1", "Keyword 2"],
              "warnings": ["Any warnings about overclaiming"]
            }}
            
            Resume:
            {resume_text[:2000]}
            
            Job Description:
            {job_description[:2000]}
            """
        else:
            prompt = f"""
            You are an expert career coach.
            Analyze the candidate's resume and the target job description.
            Provide highly specific, actionable advice on how to tweak their resume for this exact job.
            
            DO NOT fabricate experience. DO NOT add skills the user does not have.
            
            Return a JSON object:
            {{
              "summary_suggestion": "Replace this sentence with: '...'",
              "project_bullet_suggestions": [
                 "Replace 'Did XYZ' with 'Achieved XYZ using [Skill] to improve [Metric]'",
                 "Add a bullet about your experience with [Keyword]"
              ],
              "skills_section_suggestion": ["Move [Skill] to the top of your skills list", "Group [Skill1] and [Skill2] under 'Frontend Development'"],
              "ats_keywords_to_add": ["{', '.join(missing_skills)} (learn/add only if true)"],
              "course_recommendations": [
                 "If you did the 'Meta Front-End Developer' course on Coursera and have a certificate you might have a better chance at winning."
              ],
              "warnings": ["Any warnings about overclaiming"]
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

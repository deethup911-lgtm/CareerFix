import json
from .utils import get_env_var
try:
    from google import genai
except ImportError:
    genai = None

MODEL = "gemini-2.0-flash"

def _get_client():
    api_key = get_env_var("GEMINI_API_KEY")
    if not api_key or not genai:
        return None
    return genai.Client(api_key=api_key)

def tailor_resume(resume_text, job_description, matched_skills, missing_skills):
    client = _get_client()
    if not client:
        return {
            "summary_suggestion": "Gemini API key missing. Cannot generate tailored summary.",
            "project_bullet_suggestions": [],
            "skills_section_suggestion": [],
            "ats_keywords_to_add": [],
            "warnings": ["Missing Gemini credentials."]
        }
        
    try:
        prompt = f"""
        You are an expert career coach.
        Analyze the candidate's resume and the target job description.
        Provide highly specific, actionable advice on how to tweak their resume for this exact job.
        
        DO NOT fabricate experience. DO NOT add skills the user does not have.
        
        Return a JSON object:
        {{
          "summary_suggestion": "Rewrite the current summary to: '...'",
          "project_bullet_suggestions": [
             "Replace 'Did XYZ' with 'Achieved XYZ using [Skill] to improve [Metric]'",
             "Add a bullet about your experience with [Keyword]"
          ],
          "skills_section_suggestion": ["Move [Skill] to the top of your skills list", "Group [Skill1] and [Skill2] under 'Frontend Development'"],
          "ats_keywords_to_add": ["{', '.join(missing_skills)} (learn/add only if true)"],
          "warnings": ["Any warnings about overclaiming"]
        }}
        
        Resume:
        {resume_text[:2000]}
        
        Job Description:
        {job_description[:2000]}
        """
        
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error tailoring resume: {e}")
        return {
            "summary_suggestion": "Error communicating with AI.",
            "project_bullet_suggestions": [],
            "skills_section_suggestion": [],
            "ats_keywords_to_add": [],
            "warnings": [str(e)]
        }

def generate_interview_questions(job_title, job_description, candidate_skills):
    client = _get_client()
    if not client:
        return {"questions": ["Gemini unavailable. Please try again later."]}

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
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error generating interview questions: {e}")
        return {"questions": [{"question": f"Error: {e}", "type": "Error", "tip": ""}]}

def suggest_certifications(missing_skills, job_title):
    client = _get_client()
    if not client:
        return {"certifications": []}

    try:
        prompt = f"""
        You are a career development advisor.
        Based on the missing skills for this job, recommend the top 3-5 specific certifications 
        that would directly close the skill gaps and make the candidate more competitive.
        Only recommend real, widely-recognized certifications.
        
        Job Title: {job_title}
        Missing Skills: {', '.join(missing_skills[:15])}
        
        Return a JSON object:
        {{
          "certifications": [
            {{
              "name": "AWS Certified Solutions Architect",
              "provider": "Amazon",
              "skill_addressed": "AWS",
              "url": "https://aws.amazon.com/certification/",
              "duration": "3-6 months",
              "free": false
            }}
          ]
        }}
        """
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error suggesting certifications: {e}")
        return {"certifications": []}

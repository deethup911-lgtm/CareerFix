import json
from .utils import get_env_var
try:
    from google import genai
except ImportError:
    genai = None

def tailor_resume(resume_text, job_description, matched_skills, missing_skills):
    api_key = get_env_var("GEMINI_API_KEY")
    if not api_key or not genai:
        return {
            "summary_suggestion": "Gemini API key missing. Cannot generate tailored summary.",
            "project_bullet_suggestions": [],
            "skills_section_suggestion": [],
            "ats_keywords_to_add": [],
            "warnings": ["Missing Gemini credentials."]
        }
        
    try:
        client = genai.Client(api_key=api_key)
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
            model='gemini-2.5-flash',
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

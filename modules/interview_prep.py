from .utils import get_env_var
try:
    from google import genai
except ImportError:
    genai = None

def generate_interview_questions(job_description, resume_skills):
    api_key = get_env_var("GEMINI_API_KEY")
    if not api_key or not genai:
        return {
            "technical": ["What is your strongest technical skill?", "Describe a challenging project."],
            "hr": ["Why do you want to work here?", "Where do you see yourself in 5 years?"],
            "project": ["Can you explain your role in your most recent project?"],
            "skill_based": [f"How have you used {s}?" for s in resume_skills[:3]]
        }
        
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        Generate interview questions based on the following job description and candidate's skills.
        Candidate skills: {', '.join(resume_skills)}
        
        Return a JSON object with lists of questions:
        {{
          "technical": ["Tech q1", "Tech q2"],
          "hr": ["HR q1", "HR q2"],
          "project": ["Project q1", "Project q2"],
          "skill_based": ["Skill q1", "Skill q2"]
        }}
        
        Job Description:
        {job_description[:1500]}
        """
        import json
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error generating interview prep: {e}")
        return {
            "technical": ["Error generating technical questions."],
            "hr": [],
            "project": [],
            "skill_based": []
        }

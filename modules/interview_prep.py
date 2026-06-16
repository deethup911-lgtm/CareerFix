from .utils import get_env_var
from .ollama_client import generate_content, REASONING_MODEL

def generate_interview_questions(job_description, resume_skills):
    try:
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
        result = generate_content(prompt, json_mode=True, model=REASONING_MODEL)
        if result:
            return result
        else:
            return {
                "technical": ["What is your strongest technical skill?", "Describe a challenging project."],
                "hr": ["Why do you want to work here?", "Where do you see yourself in 5 years?"],
                "project": ["Can you explain your role in your most recent project?"],
                "skill_based": [f"How have you used {s}?" for s in resume_skills[:3]]
            }
    except Exception as e:
        print(f"Error generating interview prep: {e}")
        return {
            "technical": ["Error generating technical questions."],
            "hr": [],
            "project": [],
            "skill_based": []
        }

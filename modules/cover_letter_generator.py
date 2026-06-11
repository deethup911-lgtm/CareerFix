from .utils import get_env_var
from .ollama_client import generate_content

def generate_cover_letter(candidate_summary, resume_skills, job_title, company, job_description, is_fresher=False):
    try:
        fresher_note = "The candidate is a fresher/recent graduate. Focus on their projects, internship, and eagerness to learn." if is_fresher else "Focus on their proven experience."
        
        prompt = f"""
        Write a concise, professional cover letter for the role of {job_title} at {company}.
        {fresher_note}
        Do not fabricate years of experience or skills. Mention only real skills: {', '.join(resume_skills)}.
        
        Candidate Summary: {candidate_summary}
        
        Job Description:
        {job_description[:1500]}
        
        Return ONLY the cover letter text, no markdown blocks.
        """
        
        result = generate_content(prompt, json_mode=False)
        return result.strip() if result else "Failed to generate cover letter."
    except Exception as e:
        print(f"Error generating cover letter: {e}")
        return "Failed to generate cover letter."

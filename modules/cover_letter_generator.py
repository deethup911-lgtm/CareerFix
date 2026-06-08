from .utils import get_env_var
try:
    from google import genai
except ImportError:
    genai = None

def generate_cover_letter(candidate_summary, resume_skills, job_title, company, job_description, is_fresher=False):
    api_key = get_env_var("GEMINI_API_KEY")
    if not api_key or not genai:
        return "Gemini API key missing. Cannot generate cover letter."
        
    try:
        client = genai.Client(api_key=api_key)
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
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error generating cover letter: {e}")
        return "Failed to generate cover letter."

import pytest
from modules.resume_analyzer import analyze_resume

def test_local_fallback_analyzer(monkeypatch):
    # Simulate no Gemini key
    monkeypatch.setenv("GEMINI_API_KEY", "")
    
    resume_text = "I am a fresher. I know Python and Java."
    analysis = analyze_resume(resume_text)
    
    assert analysis["experience_level"] == "Fresher"
    assert "Python" in analysis["skills"]
    assert "Java" in analysis["skills"]
    assert analysis["summary"] == "Generated locally based on extracted skills."

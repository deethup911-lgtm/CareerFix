import pytest
from modules.matcher import calculate_match

def test_calculate_match():
    # Provide dummy profile
    profile = {
        "skills": ["Python", "AWS", "SQL"],
        "summary": "Data Engineer with Python"
    }
    job = {
        "title": "Data Engineer",
        "description": "Requires Python, SQL, and AWS."
    }
    
    match = calculate_match(profile, job)
    
    # Python, SQL, AWS in both
    assert match["skill_match"] == 100.0
    assert "Python" in match["matched_skills"]
    assert len(match["missing_skills"]) == 0

import pytest
from modules.job_filter import extract_required_experience, is_senior_role, filter_jobs_by_experience

def test_extract_required_experience():
    assert extract_required_experience("5 to 8 years") == 5
    assert extract_required_experience("6+ years") == 6
    assert extract_required_experience("Exp - 4 yrs") == 4
    assert extract_required_experience("Min. 1 year") == 1
    assert extract_required_experience("Experience: 3 years") == 3

def test_fresher_filter():
    jobs = [
        {"title": "Dev", "description": "5 to 8 years"},
        {"title": "Dev", "description": "6+ years"},
        {"title": "Dev", "description": "Exp - 4 yrs"},
        {"title": "Dev", "description": "Min. 1 year"},
        {"title": "Intern", "description": "0 years experience"}
    ]
    filtered = filter_jobs_by_experience(jobs, "Fresher", 0)
    assert len(filtered) == 1
    assert filtered[0]["title"] == "Intern"

def test_senior_keywords():
    assert is_senior_role("Senior Developer") == True
    assert is_senior_role("Principal Engineer") == True
    assert is_senior_role("Software Engineer") == False

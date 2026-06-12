import pytest
from modules.experience_extractor import extract_job_experience
from modules.job_filter import filter_jobs_by_experience

def test_extract_job_experience():
    assert extract_job_experience("5 to 8 years")["experience_min"] == 5
    assert extract_job_experience("6+ years")["experience_min"] == 6
    assert extract_job_experience("Exp - 4 yrs")["experience_min"] == 4
    assert extract_job_experience("Min. 1 year")["experience_min"] == 1
    assert extract_job_experience("Experience: 3 years")["experience_min"] == 3

def test_fresher_filter():
    jobs = [
        {"title": "Dev", "description": "5 to 8 years"},
        {"title": "Dev", "description": "6+ years"},
        {"title": "Dev", "description": "Exp - 4 yrs"},
        {"title": "Dev", "description": "Min. 1 year"},
        {"title": "Intern", "description": "0 years experience"}
    ]
    filtered = filter_jobs_by_experience(jobs, "Fresher", 0)
    assert len(filtered) == 2
    assert any(j["description"] == "Min. 1 year" for j in filtered)
    assert any(j["title"] == "Intern" for j in filtered)


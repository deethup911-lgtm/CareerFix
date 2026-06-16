import pytest
from modules.matcher import calculate_match, classify_job_skills

def test_classify_job_skills():
    desc = """
    We are looking for a Software Engineer.
    Must-have qualifications:
    - Python, SQL, and Docker.
    
    Nice-to-have or preferred qualifications:
    - Kubernetes, AWS, and PyTorch would be a plus.
    """
    skills_list = ["Python", "SQL", "Docker", "Kubernetes", "AWS", "PyTorch"]
    required, preferred = classify_job_skills(desc, skills_list)
    
    assert "Python" in required
    assert "SQL" in required
    assert "Docker" in required
    assert "Kubernetes" in preferred
    assert "AWS" in preferred
    assert "PyTorch" in preferred

def test_calculate_match_scoring():
    profile = {
        "skills": ["Python", "SQL"],
        "experience_years": 2,
        "experience_level": "Junior",
        "summary": "Junior developer with Python and SQL"
    }
    
    # 1. Job with missing skills & specific experience
    job_1 = {
        "title": "Backend Developer",
        "description": "Requires Python, SQL, Docker. Preferred qualifications: AWS."
    }
    
    match_1 = calculate_match(profile, job_1)
    
    # Total skills: 4 (Python, SQL, Docker, AWS)
    # Required: Python, SQL, Docker (3)
    # Preferred: AWS (1)
    # Matched Required: Python, SQL (2/3)
    # Matched Preferred: None (0/1)
    # Total Required = 3, Total Preferred = 1
    # Denominator = 3 * 0.8 + 1 * 0.2 = 2.6
    # Numerator = 2 * 0.8 + 0 * 0.2 = 1.6
    # Skill Fit = (1.6 / 2.6) * 100 = 61.5%
    assert abs(match_1["skill_match"] - 61.5) < 0.2
    
    # Experience requirement is not specified, so exp_fit = 80.0
    assert match_1["experience_match"] == 80.0
    
    # Missing required: Docker (1) -> penalty = 1 * 4 = 4
    # Missing preferred: AWS (1) -> penalty = 1 * 1 = 1
    # Total skill penalty = 5
    assert match_1["required_penalty"] == 4.0
    assert match_1["preferred_penalty"] == 1.0

def test_calculate_match_sparse_jd():
    # Sparse JD: skills <= 2 should trigger alternative weights (40% skills, 15% exp, 45% semantic)
    profile = {
        "skills": ["Python"],
        "experience_years": 1,
        "experience_level": "Fresher",
        "summary": "Fresher learning Python"
    }
    job = {
        "title": "Python Developer",
        "description": "Must know Python."
    }
    match = calculate_match(profile, job)
    
    # Total skills in JD = 1 (<=2), so sparse weights are used:
    # skill_weight = 0.40, semantic_weight = 0.45, exp_weight = 0.15
    assert match["skill_match"] == 100.0
    assert match["experience_match"] == 80.0

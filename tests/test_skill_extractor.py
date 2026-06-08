import pytest
from modules.skill_extractor import extract_skills_from_text

def test_extract_many_skills():
    text = "Java Python HTML5 CSS3 JavaScript React MongoDB MySQL Git Linux VS Code Tailwind CSS"
    skills = extract_skills_from_text(text)
    expected = [
        "CSS3", "Git", "HTML5", "Java", "JavaScript", "Linux", 
        "MongoDB", "MySQL", "Python", "React", "Tailwind CSS", "VS Code"
    ]
    # Check if all expected skills are in the extracted skills
    for exp in expected:
        assert exp in skills

def test_r_false_positive():
    text = "React developer with JavaScript. Looking for an R&D role."
    skills = extract_skills_from_text(text)
    assert "React" in skills
    assert "JavaScript" in skills
    assert "R" not in skills
    assert "R Programming" not in skills

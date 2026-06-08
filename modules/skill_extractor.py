import os
import re

def load_skills(file_path):
    skills = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                skill = line.strip()
                if skill:
                    skills.append(skill)
    return skills

def get_aliases():
    return {
        "JS": "JavaScript",
        "ML": "Machine Learning",
        "DL": "Deep Learning",
        "AI": "Artificial Intelligence",
        "NLP": "Natural Language Processing",
        "OOP": "Object Oriented Programming",
        "HTML5": "HTML",
        "CSS3": "CSS",
        "Node": "Node.js",
        "Express": "Express.js",
        "Mongo DB": "MongoDB",
        "Visual Studio Code": "VS Code"
    }

def extract_skills_from_text(text):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tech_path = os.path.join(base_dir, 'data', 'tech_skills.txt')
    non_tech_path = os.path.join(base_dir, 'data', 'non_tech_skills.txt')

    tech_skills = load_skills(tech_path)
    non_tech_skills = load_skills(non_tech_path)
    
    all_skills = tech_skills + non_tech_skills
    aliases = get_aliases()
    
    extracted_skills = set()
    
    # Pre-process text to avoid matching single 'R' incorrectly
    # We will search using word boundaries.
    text_lower = text.lower()
    
    for skill in all_skills:
        # Escape skill for regex
        escaped_skill = re.escape(skill)
        
        # Word boundary search
        # If skill is "C++" or "C#", \b might fail due to non-word chars.
        # We handle special cases manually or use more permissive boundaries.
        # If skill is very short (e.g., "R", "C") it needs stricter boundaries.
        # But we already mapped "R Programming" in our lists instead of "R".
        # Let's ensure any single or double character skill has stricter space boundaries.
        if len(skill) <= 2 or skill in ["C++", "C#", "Node.js", "Express.js", "Vue.js", "Next.js", ".NET"]:
            pattern = r'(?<![A-Za-z0-9_])' + escaped_skill + r'(?![A-Za-z0-9_])'
        else:
            pattern = r'\b' + escaped_skill + r'\b'
            
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Resolve alias if any
            final_skill = skill
            for k, v in aliases.items():
                if skill.lower() == k.lower():
                    final_skill = v
            extracted_skills.add(final_skill)
            
    # Handle aliases present in text directly (e.g. JS -> JavaScript)
    for k, v in aliases.items():
        escaped_k = re.escape(k)
        if re.search(r'\b' + escaped_k + r'\b', text, re.IGNORECASE):
            extracted_skills.add(v)
            
    # Avoid R false positive if it matched "R" (wait, R is not in our list, we used R Programming)
    # Our tech_skills.txt does not have "R", it has "R Programming" and "RStudio".
    
    return sorted(list(extracted_skills))

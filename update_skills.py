import os
import sys

base_dir = r"d:\projects\Fix"
sys.path.append(base_dir)

from modules.role_recommender import TECH_CATEGORIES

tech_path = os.path.join(base_dir, 'data', 'tech_skills.txt')
non_tech_path = os.path.join(base_dir, 'data', 'non_tech_skills.txt')

existing = set()
with open(tech_path, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip(): existing.add(line.strip().lower())
with open(non_tech_path, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip(): existing.add(line.strip().lower())

new_skills = set()
for cat in TECH_CATEGORIES:
    for s in cat['skills']:
        if s.lower() not in existing:
            # Simple casing: capitalize words
            cased_skill = " ".join([word.capitalize() for word in s.split()])
            if s.lower() == "ui" or s.lower() == "ux" or s.lower() == "ci/cd" or s.lower() == "api":
                cased_skill = s.upper()
            new_skills.add(cased_skill)

with open(tech_path, 'a', encoding='utf-8') as f:
    for s in new_skills:
        f.write(s + "\n")

print(f"Added {len(new_skills)} new skills.")

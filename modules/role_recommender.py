import re
from .utils import get_env_var
from .ollama_client import generate_content

def make_internship_role(role_name):
    # Strip Junior, Jr., Associate, Entry Level, Trainee, Intern, Internship
    # to prevent double-suffix like "AI Intern Intern"
    cleaned = re.sub(r'(?i)\b(junior|jr\.?|associate|entry\s+level|trainee|intern(?:ship)?)\b', '', role_name)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return f"{cleaned} Intern"


TECH_CATEGORIES = [
    {
        "name": "AI / ML / Data Science",
        "skills": {"python", "machine learning", "deep learning", "nlp", "natural language processing", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "rag", "langchain", "faiss", "hugging face", "generative ai", "prompt engineering", "artificial intelligence"},
        "roles": ["AI Engineer", "Machine Learning Engineer", "Data Scientist", "NLP Engineer", "Generative AI Developer", "RAG Developer", "AI Application Developer"],
        "junior_roles": ["Junior AI Engineer", "AI Associate", "Junior Machine Learning Engineer", "Entry Level Data Scientist", "ML Associate", "AI Intern", "Junior NLP Engineer", "Data Science Analyst"]
    },
    {
        "name": "Web / Full Stack",
        "skills": {"html", "html5", "css", "css3", "javascript", "typescript", "react", "next.js", "angular", "vue.js", "tailwind css", "bootstrap", "node.js", "express.js", "php", "laravel", "django", "flask", "fastapi", "mongodb", "mysql", "postgresql", "mern"},
        "roles": ["Full Stack Developer", "Web Developer", "Frontend Developer", "Backend Developer", "React Developer", "Node.js Developer", "MERN Stack Developer", "Software Developer"],
        "junior_roles": ["Junior Web Developer", "Junior Frontend Developer", "Junior Software Developer", "Associate Software Engineer", "Trainee Developer", "Junior React Developer", "Entry Level Full Stack Developer"]
    },
    {
        "name": "Java / Enterprise Backend",
        "skills": {"java", "spring", "spring boot", "hibernate", "jpa", "j2ee", "jdbc", "soap", "rest api", "sql", "mysql", "postgresql"},
        "roles": ["Java Developer", "Backend Developer", "Spring Boot Developer", "Enterprise Application Developer", "Software Engineer"],
        "junior_roles": ["Junior Java Developer", "Associate Software Engineer", "Trainee Java Developer", "Entry Level Backend Developer"]
    },
    {
        "name": ".NET",
        "skills": {"c#", ".net", "asp.net", "sql server", "azure"},
        "roles": [".NET Developer", "ASP.NET Developer", "Backend Developer", "Software Engineer"],
        "junior_roles": ["Junior .NET Developer", ".NET Intern", "ASP.NET Intern", "Junior C# Developer", "Associate Software Engineer"]
    },
    {
        "name": "Data Analyst / BI",
        "skills": {"sql", "excel", "advanced excel", "power bi", "tableau", "pandas", "numpy", "data analysis", "data visualization"},
        "roles": ["Data Analyst", "Business Intelligence Analyst", "Power BI Developer", "Reporting Analyst"],
        "junior_roles": ["Junior Data Analyst", "Associate Data Analyst", "Entry Level Data Analyst", "BI Analyst Trainee"]
    },
    {
        "name": "DevOps / Cloud",
        "skills": {"docker", "kubernetes", "aws", "azure", "gcp", "linux", "ci/cd", "github actions", "jenkins", "terraform", "ansible"},
        "roles": ["DevOps Engineer", "Cloud Engineer", "Site Reliability Engineer", "Cloud Support Engineer"],
        "junior_roles": ["Junior DevOps Engineer", "Cloud Associate", "DevOps Trainee", "Junior Cloud Engineer", "Entry Level SRE"]
    },
    {
        "name": "Mobile Development",
        "skills": {"flutter", "dart", "react native", "android", "kotlin", "java", "swift", "ios", "mobile application development"},
        "roles": ["Mobile App Developer", "Flutter Developer", "Android Developer", "React Native Developer", "iOS Developer"],
        "junior_roles": ["Junior Android Developer", "Junior Flutter Developer", "Junior Mobile Developer", "Associate Mobile App Developer"]
    },
    {
        "name": "Cybersecurity",
        "skills": {"cybersecurity", "ethical hacking", "penetration testing", "network security", "information security", "owasp", "cryptography", "firewalls", "vulnerability assessment"},
        "roles": ["Cybersecurity Analyst", "Security Engineer", "Penetration Tester", "Information Security Analyst"],
        "junior_roles": ["Cybersecurity Intern", "Security Analyst Intern", "Junior Security Analyst", "Penetration Testing Intern", "Entry Level Information Security Analyst"]
    },
    {
        "name": "QA / Testing",
        "skills": {"qa", "quality assurance", "manual testing", "automation testing", "selenium", "cypress", "junit", "pytest", "testng", "appium", "postman"},
        "roles": ["QA Engineer", "Automation Tester", "Software Test Engineer", "QA Analyst"],
        "junior_roles": ["QA Intern", "Junior QA Engineer", "Manual Testing Intern", "Software Testing Intern", "Entry Level QA Analyst"]
    },
    {
        "name": "UI / UX",
        "skills": {"ui", "ux", "user interface", "user experience", "figma", "adobe xd", "sketch", "wireframing", "prototyping", "usability testing"},
        "roles": ["UI/UX Designer", "Product Designer", "UX Researcher", "UI Developer"],
        "junior_roles": ["UI/UX Design Intern", "Junior UI Designer", "UX Research Intern", "Product Design Intern", "Entry Level UI Developer"]
    },
    {
        "name": "Database Administration",
        "skills": {"dba", "database administration", "oracle", "sql server", "mysql", "postgresql", "mongodb", "cassandra", "redis", "database design"},
        "roles": ["Database Administrator", "DBA", "Database Engineer", "Data Engineer"],
        "junior_roles": ["Database Intern", "Junior DBA", "Junior Data Engineer", "Database Administration Trainee", "Entry Level Database Developer"]
    },
    {
        "name": "System Administration",
        "skills": {"system administration", "linux", "windows server", "active directory", "bash", "shell scripting", "powershell", "troubleshooting"},
        "roles": ["System Administrator", "IT Support Specialist", "Linux Administrator", "Network Administrator"],
        "junior_roles": ["IT Support Intern", "Junior System Administrator", "Linux Admin Intern", "IT Helpdesk Intern", "Entry Level IT Support"]
    },
    {
        "name": "Networking",
        "skills": {"networking", "cisco", "ccna", "routing", "switching", "tcp/ip", "dns", "dhcp", "vpn", "firewalls"},
        "roles": ["Network Engineer", "Network Administrator", "Network Security Engineer"],
        "junior_roles": ["Network Engineering Intern", "Junior Network Engineer", "Network Support Intern", "Entry Level Network Administrator"]
    },
    {
        "name": "Blockchain",
        "skills": {"blockchain", "solidity", "ethereum", "smart contracts", "web3", "cryptography", "rust", "hyperledger"},
        "roles": ["Blockchain Developer", "Smart Contract Developer", "Web3 Developer"],
        "junior_roles": ["Blockchain Intern", "Web3 Developer Intern", "Smart Contract Intern", "Junior Blockchain Developer"]
    },
    {
        "name": "Game Development",
        "skills": {"unity", "unreal engine", "c#", "c++", "game design", "3d modeling", "game programming"},
        "roles": ["Game Developer", "Unity Developer", "Unreal Engine Developer", "Gameplay Programmer"],
        "junior_roles": ["Game Development Intern", "Unity Intern", "Junior Game Developer", "Game Programming Intern", "Entry Level Unity Developer"]
    },
    {
        "name": "Embedded / IoT",
        "skills": {"c", "c++", "embedded c", "microcontrollers", "iot", "raspberry pi", "arduino", "rtos", "firmware"},
        "roles": ["Embedded Systems Engineer", "Firmware Engineer", "IoT Developer"],
        "junior_roles": ["Embedded Systems Intern", "IoT Intern", "Firmware Engineering Intern", "Junior Embedded Developer", "Hardware Intern"]
    },
    {
        "name": "Technical Support",
        "skills": {"technical support", "help desk", "troubleshooting", "customer support", "ticketing systems", "jira", "servicenow"},
        "roles": ["Technical Support Engineer", "Help Desk Technician", "IT Support Specialist"],
        "junior_roles": ["IT Support Intern", "Help Desk Intern", "Technical Support Trainee", "Junior IT Support Specialist"]
    }
]

def recommend_roles(resume_analysis):
    resume_analysis.setdefault("error_log", [])
    skills = [s.lower() for s in resume_analysis.get("skills", [])]
    if not skills:
        return []
        
    experience_level = resume_analysis.get("experience_level", "Fresher")
    
    # 1. Local category-based scoring
    category_scores = []
    domain_hint = (resume_analysis.get("domain_hint") or "").lower()

    for cat in TECH_CATEGORIES:
        matched = [s for s in skills if s in cat["skills"]]
        if matched:
            score = len(matched)
            # Bonus: if Ollama's domain_hint references this category, boost it
            # so it wins tie-breakers over equally-matched categories.
            if domain_hint and any(word in cat["name"].lower() for word in domain_hint.split("/")):
                score += 2
            category_scores.append({
                "name": cat["name"],
                "roles": cat["roles"],
                "junior_roles": cat.get("junior_roles", []),
                "matched_skills": matched,
                "score": score
            })
            
    # Sort categories by number of matched skills
    category_scores.sort(key=lambda x: x["score"], reverse=True)
    
    local_roles = []
    seen_roles = set()
    is_student_or_fresher = experience_level in ["Student", "Fresher"]
    is_junior = experience_level in ["Student", "Fresher", "Junior"]

    for cat in category_scores:
        # For Students/Freshers/Juniors: prefer junior_roles, then fall back to normal roles
        role_pool = cat.get("junior_roles", []) + cat["roles"] if is_junior else cat["roles"]
        for r in role_pool:
            if len(local_roles) >= 5:
                break

            display_role = r
            # Students and Freshers always get internship-suffixed titles
            if is_student_or_fresher:
                display_role = make_internship_role(r)

            # Do not recommend senior roles for students or freshers
            r_lower = display_role.lower()
            if is_student_or_fresher and any(k in r_lower for k in ["senior", "lead", "manager", "principal"]):
                continue

            if display_role not in seen_roles:
                reason = f"Matches {', '.join([s.title() for s in cat['matched_skills']])}."
                local_roles.append({
                    "role": display_role,
                    "reason": reason,
                    "source": "Local"
                })
                seen_roles.add(display_role)
        if len(local_roles) >= 5:
            break

    # 2. Try Ollama to refine
    try:
        is_student_or_fresher = experience_level in ["Student", "Fresher"]
        is_junior = experience_level in ["Student", "Fresher", "Junior"]

        if is_student_or_fresher:
            level_instruction = (
                'Since the candidate is a currently-enrolled Student or recent Fresher, '
                'ONLY recommend internship roles. Every suggested title MUST contain '
                '"Intern" or "Internship" (e.g., "Web Developer Intern", '
                '"Frontend Developer Internship", "React Intern"). '
                'Do NOT suggest full-time, mid-level, or senior roles.'
            )
        elif is_junior:
            level_instruction = (
                'Since the candidate is a Junior, ONLY recommend entry-level and junior job titles. '
                'Use prefixes like Junior, Jr., Associate, Entry Level, or Trainee. '
                'Do NOT suggest mid-level or senior roles.'
            )
        else:
            level_instruction = 'Recommend standard job roles suitable for their experience level.'

        prompt = f"""
        Based ONLY on the following skills extracted from a resume: {', '.join(skills)}.
        The candidate's experience level is: {experience_level}.

        {level_instruction}
        You MUST recommend exactly 5 job roles.

        Do not mention any skill in the reason that is not present in the extracted skills list.
        Projects: {resume_analysis.get('projects', [])}

        Return a JSON array of objects exactly like this, with no wrapper objects:
        [
          {{
            "role": "Job Title",
            "reason": "Brief reason based on matched skills",
            "source": "Ollama"
          }}
        ]
        """
        ollama_roles = generate_content(prompt, json_mode=True)
        if ollama_roles:
            # Handle if Ollama wrapped it in a dict
            if isinstance(ollama_roles, dict):
                for key in ["roles", "job_roles", "recommendations", "job_titles", "data"]:
                    if key in ollama_roles and isinstance(ollama_roles[key], list):
                        ollama_roles = ollama_roles[key]
                        break

            if isinstance(ollama_roles, list) and len(ollama_roles) > 0:
                valid_roles = [r for r in ollama_roles if isinstance(r, dict) and "role" in r]

                # For Students/Freshers: enforce intern suffix — if Ollama returns a
                # non-intern title, force-convert it rather than silently showing wrong roles.
                if is_student_or_fresher:
                    enforced = []
                    for r in valid_roles:
                        title = r.get("role", "")
                        if not any(k in title.lower() for k in ["intern", "internship", "trainee"]):
                            r = dict(r)  # don't mutate original
                            r["role"] = make_internship_role(title)
                        enforced.append(r)
                    valid_roles = enforced

                if valid_roles:
                    return valid_roles
    except Exception as e:
        print(f"Ollama role recommendation failed: {e}")
        resume_analysis["error_log"].append(f"Ollama role recommendation failed: {e}")
            
    return local_roles

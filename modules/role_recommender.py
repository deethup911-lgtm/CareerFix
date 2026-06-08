import json
from .utils import get_env_var
try:
    from google import genai
except ImportError:
    genai = None

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
        "roles": [".NET Developer", "ASP.NET Developer", "Backend Developer", "Software Engineer"]
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
        "roles": ["Cybersecurity Analyst", "Security Engineer", "Penetration Tester", "Information Security Analyst"]
    },
    {
        "name": "QA / Testing",
        "skills": {"qa", "quality assurance", "manual testing", "automation testing", "selenium", "cypress", "junit", "pytest", "testng", "appium", "postman"},
        "roles": ["QA Engineer", "Automation Tester", "Software Test Engineer", "QA Analyst"]
    },
    {
        "name": "UI / UX",
        "skills": {"ui", "ux", "user interface", "user experience", "figma", "adobe xd", "sketch", "wireframing", "prototyping", "usability testing"},
        "roles": ["UI/UX Designer", "Product Designer", "UX Researcher", "UI Developer"]
    },
    {
        "name": "Database Administration",
        "skills": {"dba", "database administration", "oracle", "sql server", "mysql", "postgresql", "mongodb", "cassandra", "redis", "database design"},
        "roles": ["Database Administrator", "DBA", "Database Engineer", "Data Engineer"]
    },
    {
        "name": "System Administration",
        "skills": {"system administration", "linux", "windows server", "active directory", "bash", "shell scripting", "powershell", "troubleshooting"},
        "roles": ["System Administrator", "IT Support Specialist", "Linux Administrator", "Network Administrator"]
    },
    {
        "name": "Networking",
        "skills": {"networking", "cisco", "ccna", "routing", "switching", "tcp/ip", "dns", "dhcp", "vpn", "firewalls"},
        "roles": ["Network Engineer", "Network Administrator", "Network Security Engineer"]
    },
    {
        "name": "Blockchain",
        "skills": {"blockchain", "solidity", "ethereum", "smart contracts", "web3", "cryptography", "rust", "hyperledger"},
        "roles": ["Blockchain Developer", "Smart Contract Developer", "Web3 Developer"]
    },
    {
        "name": "Game Development",
        "skills": {"unity", "unreal engine", "c#", "c++", "game design", "3d modeling", "game programming"},
        "roles": ["Game Developer", "Unity Developer", "Unreal Engine Developer", "Gameplay Programmer"]
    },
    {
        "name": "Embedded / IoT",
        "skills": {"c", "c++", "embedded c", "microcontrollers", "iot", "raspberry pi", "arduino", "rtos", "firmware"},
        "roles": ["Embedded Systems Engineer", "Firmware Engineer", "IoT Developer"]
    },
    {
        "name": "Technical Support",
        "skills": {"technical support", "help desk", "troubleshooting", "customer support", "ticketing systems", "jira", "servicenow"},
        "roles": ["Technical Support Engineer", "Help Desk Technician", "IT Support Specialist"]
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
    for cat in TECH_CATEGORIES:
        matched = [s for s in skills if s in cat["skills"]]
        if matched:
            category_scores.append({
                "name": cat["name"],
                "roles": cat["roles"],
                "matched_skills": matched,
                "score": len(matched)
            })
            
    # Sort categories by number of matched skills
    category_scores.sort(key=lambda x: x["score"], reverse=True)
    
    local_roles = []
    seen_roles = set()
    is_junior = experience_level in ["Fresher", "Junior"]
    
    for cat in category_scores:
        # For Freshers/Juniors: prefer junior_roles, then fall back to normal roles
        role_pool = cat.get("junior_roles", []) + cat["roles"] if is_junior else cat["roles"]
        for r in role_pool:
            if len(local_roles) >= 5:
                break
            # Do not recommend senior roles for freshers
            r_lower = r.lower()
            if experience_level == "Fresher" and any(k in r_lower for k in ["senior", "lead", "manager", "principal"]):
                continue
                
            if r not in seen_roles:
                reason = f"Matches {', '.join([s.title() for s in cat['matched_skills']])}."
                local_roles.append({
                    "role": r,
                    "reason": reason,
                    "source": "Local"
                })
                seen_roles.add(r)
        if len(local_roles) >= 5:
            break

    # 2. Try Gemini to refine
    api_key = get_env_var("GEMINI_API_KEY")
    if api_key and genai:
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"""
            Based ONLY on the following skills extracted from a resume: {', '.join(skills)}.
            The candidate's experience level is: {experience_level}.
            
            {'Since the candidate is a Fresher or Junior, ONLY recommend entry-level and junior job titles. Use prefixes like Junior, Jr., Associate, Entry Level, or Trainee. Do NOT suggest mid-level or senior roles.' if is_junior else 'Recommend 3-5 standard job roles suitable for their experience level.'}
            
            Do not mention any skill in the reason that is not present in the extracted skills list.
            Projects: {resume_analysis.get('projects', [])}
            
            Return a JSON array of objects:
            [
              {{
                "role": "Job Title",
                "reason": "Brief reason based on matched skills",
                "source": "Gemini"
              }}
            ]
            """
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            gemini_roles = json.loads(response.text)
            if gemini_roles:
                return gemini_roles
        except Exception as e:
            print(f"Gemini role recommendation failed: {e}")
            resume_analysis["error_log"].append(f"Gemini role recommendation failed: {e}")
            
    return local_roles

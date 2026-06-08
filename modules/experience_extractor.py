import re

def extract_job_experience(job_description):
    """
    Extracts experience_min, experience_max, and seniority level from a Job Description.
    """
    text_lower = job_description.lower()
    
    experience_min = 0
    experience_max = 99
    
    # 1. Regex to find "X-Y years", "X to Y years", "X+ years", "min X years" (handling decimals like 4.00)
    # Merged with robust yrs/yr abbreviations and exp: formats
    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+\s*(?:years|year|yrs|yr)",                 # 5+ yrs
        r"(\d+(?:\.\d+)?)\s*(?:to|-|–)\s*(\d+(?:\.\d+)?)\s*(?:years|year|yrs|yr)", # 5-8 yrs
        r"exp\s*[-:]\s*(\d+(?:\.\d+)?)\s*(?:years|year|yrs|yr)",         # exp: 5 yrs
        r"experience\s*[-:]\s*(\d+(?:\.\d+)?)\s*(?:years|year|yrs|yr)",  # experience: 5 yrs
        r"minimum\s*(\d+(?:\.\d+)?)\s*(?:years|year|yrs|yr)",            # minimum 5 yrs
        r"min\.?\s*(\d+(?:\.\d+)?)\s*(?:years|year|yrs|yr)",             # min 5 yrs
        r"at least\s*(\d+(?:\.\d+)?)\s*(?:years|year|yrs|yr)",           # at least 5 yrs
        r"(\d+(?:\.\d+)?)\s*(?:years|year|yrs|yr)\s*of(?:.*?)\s*experience", # 5 years of experience
        r"(\d+(?:\.\d+)?)\s*(?:years|year|yrs|yr)\s*experience"          # 5 years experience
    ]
    
    found_years = []
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if isinstance(match, tuple):
                found_years.append((int(float(match[0])), int(float(match[1]))))
            else:
                val = int(float(match))
                found_years.append((val, val + 2)) # If "5+ years", treat as 5-7 roughly for max
                
    if found_years:
        # Take the most prominent (first) match usually
        experience_min = found_years[0][0]
        experience_max = found_years[0][1]

    # 2. Extract Seniority Level
    seniority = "Mid-Level"
    
    # Check Executive / Senior Roles
    exec_keywords = ["vice president", "vp", "director", "principal", "staff", "architect", "head of", "chief"]
    senior_keywords = ["senior", "sr.", "lead", "manager", "experienced"]
    junior_keywords = ["junior", "jr.", "associate", "entry level", "entry-level", "fresher", "graduate", "trainee", "intern"]
    
    # Assign Seniority based on explicit keywords
    is_exec = any(re.search(r'\b' + re.escape(kw) + r'\b', text_lower) for kw in exec_keywords)
    is_senior = any(re.search(r'\b' + re.escape(kw) + r'\b', text_lower) for kw in senior_keywords)
    is_junior = any(re.search(r'\b' + re.escape(kw) + r'\b', text_lower) for kw in junior_keywords)
    
    if is_exec:
        seniority = "Executive"
    elif is_senior:
        seniority = "Senior"
    elif is_junior:
        seniority = "Junior"
    else:
        # Fallback to years if no explicit title keywords
        if experience_min == 0:
            seniority = "Entry-Level"
        elif experience_min <= 2:
            seniority = "Junior"
        elif experience_min <= 5:
            seniority = "Mid-Level"
        elif experience_min <= 8:
            seniority = "Senior"
        else:
            seniority = "Executive"
            
    return {
        "experience_min": experience_min,
        "experience_max": experience_max,
        "seniority": seniority
    }

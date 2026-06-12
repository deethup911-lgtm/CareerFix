from .experience_extractor import extract_job_experience

def filter_jobs_by_experience(jobs, candidate_level, candidate_years):
    filtered_jobs = []
    
    # We now filter purely aggressively on the worst mismatches
    # Milder mismatches are penalized in matcher.py instead of filtered out completely
    
    for job in jobs:
        combined_text = f"{job['title']} {job['description']}"
        exp_data = extract_job_experience(combined_text)
        req_years = exp_data["experience_min"]
        req_seniority = exp_data["seniority"]
        
        # Absolute hard filters
        if candidate_level in ["Fresher", "Student", "Intern"]:
            # Reject > 3 years hard
            if req_years > 3:
                continue
            # Reject Executive / Senior hard
            if req_seniority in ["Executive", "Senior", "Principal"]:
                continue
                
        elif candidate_level == "Junior":
            # Reject > 5 years hard
            if req_years > 5:
                continue
            if req_seniority in ["Executive", "Principal"]:
                continue
                
        filtered_jobs.append(job)
        
    return filtered_jobs

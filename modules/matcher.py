import chromadb
from sentence_transformers import SentenceTransformer, util
from .job_analyzer import extract_job_skills
from .experience_extractor import extract_job_experience

# Load model lazily
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def calculate_match(candidate_profile, job, chroma_collection=None, job_emb=None, cand_emb=None):
    # candidate_profile: dict from resume_analyzer
    candidate_skills = set([s.lower() for s in candidate_profile.get("skills", [])])
    candidate_text = " ".join(candidate_profile.get("skills", [])) + " " + candidate_profile.get("summary", "")
    candidate_years = candidate_profile.get("experience_years", 0)
    candidate_level = candidate_profile.get("experience_level", "Fresher")
    
    # Extract job skills
    job_skills_list = extract_job_skills(job['description'])
    job_skills = set([s.lower() for s in job_skills_list])
    
    # Extract Job Experience
    job_exp_data = extract_job_experience(job['description'])
    req_min_years = job_exp_data["experience_min"]
    req_seniority = job_exp_data["seniority"]
    
    # 1. Skill Match
    if not job_skills:
        skill_match = 0
        matched_skills_list = []
    else:
        matched_skills_list = []
        if chroma_collection and candidate_skills:
            # --- SEMANTIC MATCHING via ChromaDB ---
            for js in job_skills:
                results = chroma_collection.query(
                    query_texts=[js],
                    n_results=1
                )
                if results['distances'] and len(results['distances'][0]) > 0:
                    distance = results['distances'][0][0]
                    # A distance < 1.0 means the skills are semantically related!
                    if distance < 1.0:
                        matched_skills_list.append(js)
        else:
            # Fallback exact matching
            matched = candidate_skills.intersection(job_skills)
            matched_skills_list = list(matched)

        if len(job_skills) <= 2:
            # If a job only lists 1 or 2 generic skills, don't give it 100% match.
            skill_match = 20.0 if matched_skills_list else 0
        else:
            skill_match = (len(matched_skills_list) / len(job_skills)) * 100.0
            
    # 2. Semantic Profile Match
    if job_emb is None or cand_emb is None:
        model = get_model()
        cand_emb = model.encode(candidate_text, convert_to_tensor=True)
        job_emb = model.encode(job['title'] + " " + job['description'], convert_to_tensor=True)
        
    semantic_sim = util.pytorch_cos_sim(cand_emb, job_emb).item() * 100.0
    semantic_sim = max(0, min(100, semantic_sim))
    
    # 3. Experience Match (30%) & Penalty Logic
    exp_fit = 100.0
    penalty = 0
    reasons = []
    
    years_delta = req_min_years - candidate_years
    
    if years_delta > 0:
        # Candidate has fewer years than required
        if years_delta <= 1:
            exp_fit = 80.0
        elif years_delta <= 2:
            exp_fit = 50.0
            penalty += 10
            reasons.append(f"Slightly under-experienced (needs {req_min_years} yrs).")
        elif years_delta <= 4:
            exp_fit = 20.0
            penalty += 40
            reasons.append(f"Under-experienced (needs {req_min_years} yrs).")
        else:
            exp_fit = 0.0
            penalty += 70
            reasons.append(f"Severely under-experienced (needs {req_min_years} yrs, has {candidate_years}).")
            
    # Seniority Mismatch Penalties
    exec_seniorities = ["Executive", "Senior", "Principal", "Director"]
    if candidate_level in ["Fresher", "Junior"] and req_seniority in exec_seniorities:
        penalty += 50
        exp_fit = 0.0
        reasons.append("Rejected due to seniority mismatch (Executive/Senior role).")
        
    final_score = (skill_match * 0.40) + (exp_fit * 0.30) + (semantic_sim * 0.30) - penalty
    final_score = max(0, min(100, final_score))
    
    confidence = "Low"
    if final_score > 70:
        confidence = "High"
    elif final_score > 40:
        confidence = "Medium"
        
    return {
        "final_score": round(final_score, 1),
        "skill_match": round(skill_match, 1),
        "experience_match": round(exp_fit, 1),
        "profile_match": round(semantic_sim, 1),
        "job_experience_requirement": f"{job_exp_data['experience_min']}-{job_exp_data['experience_max']} Years ({req_seniority})" if (job_exp_data['experience_min'] != 0 or job_exp_data['experience_max'] != 99) else f"Not Specified ({req_seniority})",
        "matched_skills": [s for s in job_skills_list if s.lower() in [m.lower() for m in matched_skills_list]],
        "missing_skills": [s for s in job_skills_list if s.lower() not in [m.lower() for m in matched_skills_list]],
        "rejection_reasons": reasons,
        "confidence": confidence
    }

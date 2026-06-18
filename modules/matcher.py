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

def classify_job_skills(job_description, job_skills_list):
    """
    Classifies a list of job skills into required and preferred based on sentence context.
    """
    import re
    from .skill_extractor import extract_skills_from_text
    
    skills_set = set(s.lower() for s in job_skills_list)
    preferred_skills = set()
    
    # Split text into paragraphs/sentences
    sentences = re.split(r'[.\n]', job_description)
    
    preferred_indicators = [
        r'\bpreferred\b', r'\bplus\b', r'\bnice\s+to\s+have\b', r'\bdesired\b', 
        r'\bbeneficial\b', r'\badvantage\b', r'\boptional\b', r'\bbonus\b', 
        r'\bgood\s+to\s+have\b', r'\bwould\s+be\s+great\b', r'\bnot\s+required\b',
        r'\bideal\s+candidate\s+should\s+have\b'
    ]
    preferred_regex = re.compile('|'.join(preferred_indicators), re.IGNORECASE)
    
    in_preferred_section = False
    
    for sentence in sentences:
        sentence_clean = sentence.strip()
        if not sentence_clean:
            continue
            
        lower_sent = sentence_clean.lower()
        # Detect section headers
        if any(h in lower_sent for h in ["preferred qualifications", "preferred skills", "nice to have", "desired skills", "bonus", "plusses"]):
            in_preferred_section = True
        elif any(h in lower_sent for h in ["basic qualifications", "requirements", "must have", "minimum qualifications", "key responsibilities", "skills required"]):
            in_preferred_section = False
            
        # Parse skills from this sentence
        sentence_skills = extract_skills_from_text(sentence_clean)
        for s in sentence_skills:
            s_low = s.lower()
            if s_low in skills_set:
                if in_preferred_section or preferred_regex.search(sentence_clean):
                    preferred_skills.add(s_low)
                    
    required_skills = skills_set - preferred_skills
    
    # Map back to original casing
    skills_casing = {s.lower(): s for s in job_skills_list}
    req_list = sorted([skills_casing[s] for s in required_skills])
    pref_list = sorted([skills_casing[s] for s in preferred_skills])
    
    return req_list, pref_list

def calculate_match(candidate_profile, job, chroma_collection=None, job_emb=None, cand_emb=None):
    # candidate_profile: dict from resume_analyzer
    candidate_skills = set([s.lower() for s in candidate_profile.get("skills", [])])
    candidate_text = " ".join(candidate_profile.get("skills", [])) + " " + candidate_profile.get("summary", "")
    candidate_years = candidate_profile.get("experience_years", 0)
    candidate_level = candidate_profile.get("experience_level", "Fresher")
    
    # Extract job skills
    job_skills_list = extract_job_skills(job['description'])
    
    # Heuristically classify required vs preferred skills
    required_skills, preferred_skills = classify_job_skills(job['description'], job_skills_list)
    
    # Match skills (semantic or exact fallback)
    matched_skills_set = set()
    if job_skills_list:
        if chroma_collection and candidate_skills:
            # --- BATCHED SEMANTIC MATCHING via ChromaDB ---
            # Previously: one query() call per skill (N calls per job → N*jobs total).
            # Now: one query() call with all skills as query_texts → 1 call per job.
            batch_results = chroma_collection.query(
                query_texts=job_skills_list,
                n_results=1
            )
            # batch_results['distances'] is a list of lists, one inner list per query_text.
            # Each inner list contains the distance to the nearest candidate skill in the DB.
            for idx, js in enumerate(job_skills_list):
                distances = batch_results['distances'][idx] if idx < len(batch_results['distances']) else []
                if distances and distances[0] < 1.0:
                    # A distance < 1.0 means the skill is semantically related to a candidate skill.
                    matched_skills_set.add(js.lower())
        else:
            # Fallback exact matching
            matched_skills_set = set(s.lower() for s in candidate_skills if s.lower() in [js.lower() for js in job_skills_list])
            
    # Separate matched required vs preferred
    matched_required = [s for s in required_skills if s.lower() in matched_skills_set]
    matched_preferred = [s for s in preferred_skills if s.lower() in matched_skills_set]
    
    # Separate missing required vs preferred
    missing_required = [s for s in required_skills if s.lower() not in matched_skills_set]
    missing_preferred = [s for s in preferred_skills if s.lower() not in matched_skills_set]
    
    # Calculate weighted skill fit score
    total_required = len(required_skills)
    total_preferred = len(preferred_skills)
    
    denominator = (total_required * 0.8) + (total_preferred * 0.2)
    if denominator == 0:
        # No skills detected in JD — low-signal job; use a neutral score, not 100
        skill_match = 50.0
    else:
        skill_match = ((len(matched_required) * 0.8 + len(matched_preferred) * 0.2) / denominator) * 100.0

    # Extract Job Experience
    job_exp_data = extract_job_experience(job['description'])
    req_min_years = job_exp_data["experience_min"]
    req_seniority = job_exp_data["seniority"]
    
    # Calculate Experience Score Fit
    penalty = 0
    reasons = []
    
    exp_not_specified = (req_min_years == 0 and (req_seniority.lower() in ["entry-level", "not specified", "unknown"] or not req_seniority))
    
    if exp_not_specified:
        exp_fit = 80.0
    elif candidate_years >= req_min_years:
        exp_fit = 100.0
    else:
        if req_min_years > 0:
            exp_fit = max(40.0, (candidate_years / req_min_years) * 100.0)
            reasons.append(f"Under-experienced (needs {req_min_years} yrs, has {candidate_years} yrs).")
        else:
            exp_fit = 100.0
            
    # Seniority Mismatch Penalties
    exec_seniorities = ["Executive", "Senior", "Principal", "Director"]
    if candidate_level in ["Fresher", "Junior"] and req_seniority in exec_seniorities:
        penalty += 50
        exp_fit = 0.0
        reasons.append("Rejected due to seniority mismatch (Executive/Senior role).")
        
    # 2. Semantic Profile Match
    if job_emb is None or cand_emb is None:
        model = get_model()
        if cand_emb is None:
            cand_emb = model.encode(candidate_text, convert_to_tensor=True)
        if job_emb is None:
            import torch
            from .embedding_cache import get_or_create_embedding
            job_text = job['title'] + " " + job['description']
            emb_np = get_or_create_embedding(job_text, model)
            job_emb = torch.tensor(emb_np, dtype=torch.float32)
        
    raw_cosine = util.pytorch_cos_sim(cand_emb, job_emb).item()
    
    # Scale raw cosine similarity from range [0.1, 0.6] to [0, 100]
    semantic_sim = ((raw_cosine - 0.1) / (0.6 - 0.1)) * 100.0
    semantic_sim = max(0.0, min(100.0, semantic_sim))
    
    # Calculate required & preferred skill penalties
    required_penalty = min(20.0, len(missing_required) * 4.0)
    preferred_penalty = min(5.0, len(missing_preferred) * 1.0)
    
    penalty += required_penalty + preferred_penalty
    
    total_jd_skills = len(job_skills_list)
    if total_jd_skills <= 2:
        skill_weight = 0.40
        semantic_weight = 0.45
        exp_weight = 0.15
    else:
        skill_weight = 0.60
        semantic_weight = 0.25
        exp_weight = 0.15
        
    final_score = (skill_match * skill_weight) + (exp_fit * exp_weight) + (semantic_sim * semantic_weight) - penalty
    final_score = max(0.0, min(100.0, final_score))
    
    confidence = "Low"
    if final_score > 70:
        confidence = "High"
    elif final_score > 40:
        confidence = "Medium"
        
    return {
        "final_score": round(final_score, 1),
        "skill_match": round(skill_match, 1),
        "experience_match": round(exp_fit, 1),
        "resume_relevance": round(semantic_sim, 1),
        "profile_match": round(semantic_sim, 1), # Backward compatibility alias
        "job_experience_requirement": f"{job_exp_data['experience_min']}-{job_exp_data['experience_max']} Years ({req_seniority})" if (job_exp_data['experience_min'] != 0 or job_exp_data['experience_max'] != 99) else f"Not Specified ({req_seniority})",
        "matched_skills": [s for s in job_skills_list if s.lower() in matched_skills_set], # Backward compatibility alias
        "missing_skills": [s for s in job_skills_list if s.lower() not in matched_skills_set], # Backward compatibility alias
        "matched_required": matched_required,
        "matched_preferred": matched_preferred,
        "missing_required": missing_required,
        "missing_preferred": missing_preferred,
        "required_penalty": round(required_penalty, 1),
        "preferred_penalty": round(preferred_penalty, 1),
        "rejection_reasons": reasons,
        "confidence": confidence
    }

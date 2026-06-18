import os
import chromadb
import uuid
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import traceback

# Import local modules
from modules.resume_parser import extract_text
from modules.resume_analyzer import analyze_resume
from modules.role_recommender import recommend_roles
from modules.job_search import search_jobs
from modules.job_filter import filter_jobs_by_experience
from modules.matcher import calculate_match
from modules.skill_gap import analyze_skill_gaps


app = FastAPI(title="CareerFix API")

# Configure CORS for React frontend (Vite default port 5173)
# ⚠️  PRODUCTION WARNING: Change allow_origins=["*"] to the exact frontend URL
#     before deploying publicly, e.g.:
#         allow_origins=["https://yourapp.com", "http://localhost:5173"]
#     Leaving it as "*" allows any website to make cross-origin requests to
#     this API, which is a security risk in production environments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobSearchRequest(BaseModel):
    roles: List[str]
    locations: List[str]
    job_type: Optional[str] = None
    candidate_level: Optional[str] = None  # e.g. "Student", "Fresher", "Junior"

class MatchJobsRequest(BaseModel):
    resume_analysis: dict
    jobs: List[dict]

class GenerateResumeRequest(BaseModel):
    resume_analysis: dict
    job_description: str
    job_title: str
    company: str
    matched_skills: List[str]
    missing_skills: List[str]

@app.post("/api/analyze-resume")
def api_analyze_resume(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None)
):
    try:
        if file:
            raw_text = extract_text(file.file, file.filename)
            if not raw_text:
                raise HTTPException(status_code=400, detail="Could not extract text from the provided file.")
        elif text and text.strip():
            raw_text = text.strip()
        else:
            raise HTTPException(status_code=400, detail="Please upload a file or paste your resume text.")
            
        analysis = analyze_resume(raw_text)
        analysis['raw_text'] = raw_text  # Add raw text for UI inspection
        recommended_roles = recommend_roles(analysis)
        
        return {
            "analysis": analysis,
            "recommended_roles": recommended_roles
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search-jobs")
def api_search_jobs(req: JobSearchRequest):
    try:
        is_student = req.candidate_level == "Student"
        # Students always get internship search mode regardless of job_type
        search_internships = is_student or (req.job_type == "Internship")
        effective_job_type = req.job_type or ("Internship" if is_student else None)
        raw_jobs = search_jobs(
            req.roles,
            req.locations,
            job_type_filter=effective_job_type,
            search_internships=search_internships,
            is_student=is_student
        )
        return {"jobs": raw_jobs}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/match-jobs")
def api_match_jobs(req: MatchJobsRequest):
    try:
        analysis = req.resume_analysis
        jobs = req.jobs
        
        # Filter by experience
        filtered_jobs = filter_jobs_by_experience(
            jobs, 
            analysis.get('experience_level', 'Fresher'),
            analysis.get('experience_years', 0)
        )
        
        # --- CHROMA DB SETUP ---
        # Create an ultra-fast in-memory vector database for the candidate's skills
        chroma_client = chromadb.Client()
        collection_name = f"candidate_{uuid.uuid4().hex}"
        collection = chroma_client.create_collection(name=collection_name)
        
        candidate_skills = list(set([s.lower() for s in analysis.get("skills", [])]))
        if candidate_skills:
            collection.add(
                documents=candidate_skills, 
                ids=[f"skill_{i}" for i in range(len(candidate_skills))]
            )
        
        matched_jobs = []
        if filtered_jobs:
            from modules.matcher import get_model
            model = get_model()
            
            # Batch Cache Lookup
            import torch
            from modules.embedding_cache import _ensure_db, get_text_hash, get_cached_embedding, save_embedding
            _ensure_db()  # Thread-safe one-time DB init (replaces direct create_cache_db())
            
            job_texts = [j['title'] + " " + j['description'] for j in filtered_jobs]
            job_embs = [None] * len(filtered_jobs)
            miss_indices = []
            miss_texts = []
            
            for idx, text in enumerate(job_texts):
                h = get_text_hash(text)
                cached = get_cached_embedding(h)
                if cached is not None:
                    print(f"[CACHE HIT] Job {idx}: hash {h[:8]}")
                    job_embs[idx] = torch.tensor(cached, dtype=torch.float32)
                else:
                    print(f"[CACHE MISS] Job {idx}: hash {h[:8]}")
                    miss_indices.append(idx)
                    miss_texts.append(text)
            
            if miss_texts:
                new_embs = model.encode(miss_texts, convert_to_tensor=True, batch_size=32)
                new_embs_np = new_embs.cpu().numpy() if hasattr(new_embs, 'cpu') else new_embs
                for i, idx in enumerate(miss_indices):
                    h = get_text_hash(job_texts[idx])
                    save_embedding(h, job_texts[idx], new_embs_np[i])
                    job_embs[idx] = new_embs[i]
            
            # Encode candidate once
            candidate_text = " ".join(analysis.get("skills", [])) + " " + analysis.get("summary", "")
            cand_emb = model.encode(candidate_text, convert_to_tensor=True)
            
            for i, j in enumerate(filtered_jobs):
                match_data = calculate_match(analysis, j, chroma_collection=collection, job_emb=job_embs[i], cand_emb=cand_emb)
                if match_data['skill_match'] > 0:
                    matched_jobs.append({
                        "job": j,
                        "match_data": match_data
                    })
                
        # Sort by final score
        matched_jobs.sort(key=lambda x: x['match_data']['final_score'], reverse=True)
        
        # UI Rule: Don't show jobs < 30% match unless we have fewer than 2 good jobs
        high_match_jobs = [j for j in matched_jobs if j['match_data']['final_score'] >= 30.0]
        if len(high_match_jobs) >= 2:
            matched_jobs = high_match_jobs
        else:
            # If we don't even have 2 good jobs, at least show the top 2 (even if they suck)
            matched_jobs = matched_jobs[:2]
            
        # Limit to top 20
        matched_jobs = matched_jobs[:20]
        
        gaps = analyze_skill_gaps(matched_jobs)
        
        return {
            "matched_jobs": matched_jobs, # Return top 20
            "skill_gaps": gaps
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/get-resume-suggestions")
def api_get_resume_suggestions(req: GenerateResumeRequest):
    try:
        from modules.resume_tailor import tailor_resume
        
        import json
        resume_text_representation = json.dumps(req.resume_analysis)
        tailored_data = tailor_resume(
            resume_text_representation, 
            req.job_description,
            req.matched_skills,
            req.missing_skills
        )
        
        return tailored_data
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class ATSRequest(BaseModel):
    resume_text: str
    job_description: str

class InterviewRequest(BaseModel):
    job_title: str
    job_description: str
    candidate_skills: List[str]

class CertificationRequest(BaseModel):
    missing_skills: List[str]
    job_title: str

@app.post("/api/ats-score")
def api_ats_score(req: ATSRequest):
    try:
        from modules.ats_simulator import simulate_ats_score
        result = simulate_ats_score(req.resume_text, req.job_description)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview-questions")
def api_interview_questions(req: InterviewRequest):
    try:
        from modules.resume_tailor import generate_interview_questions
        result = generate_interview_questions(req.job_title, req.job_description, req.candidate_skills)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/certifications")
def api_certifications(req: CertificationRequest):
    try:
        from modules.resume_tailor import suggest_certifications
        result = suggest_certifications(req.missing_skills, req.job_title)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

POPULAR_LOCATIONS = [
    "Remote",
    "India",
    "United States",
    "United Kingdom",
    "Canada",
    "Australia",
    "Germany",
    "France",
    "Singapore",
    "Japan",
    "Netherlands",
    "Switzerland",
    "Sweden",
    "Ireland",
    "United Arab Emirates",
    "Brazil",
    "South Africa",
    "Spain",
    "Italy"
]

@app.get("/api/locations/autocomplete")
async def location_autocomplete(q: str):
    if not q or len(q) < 2:
        return {"data": []}
        
    q_lower = q.lower().strip()
    local_matches = []
    for loc in POPULAR_LOCATIONS:
        if loc.lower().startswith(q_lower):
            local_matches.append(loc)
            
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return {"data": local_matches}
        
    url = "https://wft-geo-db.p.rapidapi.com/v1/geo/cities"
    querystring = {"namePrefix": q, "limit": "5", "sort": "-population"}
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "wft-geo-db.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=5)
        response.raise_for_status()
        data = response.json()
        cities = []
        for item in data.get("data", []):
            city = item.get("city")
            country = item.get("countryCode")
            cities.append(f"{city}, {country}")
            
        # Merge local matches (countries/Remote) and API matches (cities)
        # Avoid duplicate entries and limit total results to 6 items
        seen = set(item.lower() for item in local_matches)
        for c in cities:
            if c.lower() not in seen:
                local_matches.append(c)
                seen.add(c.lower())
                
        return {"data": local_matches[:6]}
    except Exception as e:
        print(f"GeoDB Error: {e}")
        return {"data": local_matches}

@app.get("/api/cache/stats")
def api_cache_stats():
    try:
        from modules.embedding_cache import get_cache_stats
        return get_cache_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cache/clear")
def api_cache_clear():
    try:
        from modules.embedding_cache import clear_cache
        clear_cache()
        return {"status": "success", "message": "Embedding cache cleared successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

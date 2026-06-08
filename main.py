import os
import chromadb
import uuid
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
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
from modules.pdf_generator import generate_resume_pdf

app = FastAPI(title="CareerFix API")

# Configure CORS for React frontend (running on Vite's default port 5173 or others)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobSearchRequest(BaseModel):
    roles: List[str]
    locations: List[str]

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
async def api_analyze_resume(
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
async def api_search_jobs(req: JobSearchRequest):
    try:
        raw_jobs = search_jobs(req.roles, req.locations)
        return {"jobs": raw_jobs}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/match-jobs")
async def api_match_jobs(req: MatchJobsRequest):
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
            
            # BATCH INFERENCE: Process 32 jobs at once on the CPU!
            job_texts = [j['title'] + " " + j['description'] for j in filtered_jobs]
            job_embs = model.encode(job_texts, convert_to_tensor=True, batch_size=32)
            
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
async def api_get_resume_suggestions(req: GenerateResumeRequest):
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

@app.get("/api/locations/autocomplete")
async def location_autocomplete(q: str):
    if not q or len(q) < 2:
        return {"data": []}
        
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return {"data": []}
        
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
        return {"data": cities}
    except Exception as e:
        print(f"GeoDB Error: {e}")
        return {"data": []}

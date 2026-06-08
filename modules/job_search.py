import requests
import re
import concurrent.futures
import time
import random
from .utils import get_env_var

def search_adzuna_jobs(role, location="India", limit=10):
    app_id = get_env_var("ADZUNA_APP_ID")
    app_key = get_env_var("ADZUNA_API_KEY")
    
    if not app_id or not app_key:
        print("Skipping Adzuna: Missing ADZUNA_APP_ID or ADZUNA_API_KEY in .env")
        return []
        
    url = f"https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": limit,
        "what": role,
        "where": location
    }
    
    # Stagger requests slightly to prevent 15 threads from hitting Adzuna at the exact same millisecond
    time.sleep(random.uniform(0.1, 1.0))
    
    for attempt in range(3): # Try up to 3 times
        try:
            response = requests.get(url, params=params, timeout=10)
            
            # If rate limited, wait 2 seconds and try again
            if response.status_code == 429:
                print(f"Adzuna Rate Limited (429). Retrying in 2 seconds... (Attempt {attempt+1}/3)")
                time.sleep(2.0)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for item in data.get("results", []):
                jobs.append({
                    "id": str(item.get("id")),
                    "title": item.get("title"),
                    "company": item.get("company", {}).get("display_name", "Unknown"),
                    "location": item.get("location", {}).get("display_name", location),
                    "description": item.get("description", ""),
                    "url": item.get("redirect_url"),
                    "source": "Adzuna"
                })
            return jobs
        except Exception as e:
            if attempt == 2:
                raise Exception(f"Adzuna API Error after 3 attempts: {e}")
            time.sleep(1.0)
            
    return []

def search_remotive_jobs(role, limit=10):
    url = "https://remotive.com/api/remote-jobs"
    params = {"search": role, "limit": limit}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        jobs = []
        for result in data.get("jobs", [])[:limit]:
            # Remotive returns HTML in the description. We strip it out for pure text.
            raw_html = result.get("description", "")
            clean_text = re.sub('<[^<]+?>', ' ', raw_html)
            clean_text = " ".join(clean_text.split()) # normalize whitespace
            
            jobs.append({
                "title": result.get("title", ""),
                "company": result.get("company_name", "Unknown"),
                "location": result.get("candidate_required_location", "Remote"),
                "description": clean_text,
                "url": result.get("url", ""),
                "source": "Remotive"
            })
        return jobs
    except Exception as e:
        print(f"Remotive API Error: {e}")
        return []

def search_jsearch_jobs(role, location="Remote", limit=10):
    rapid_key = get_env_var("RAPIDAPI_KEY")
    if not rapid_key:
        print("Skipping JSearch: RAPIDAPI_KEY missing from .env")
        return []
        
    url = "https://jsearch.p.rapidapi.com/search"
    query = f"{role} in {location}" if location != "Remote" else f"{role} remote"
    
    # JSearch returns ~10 jobs per page. We set num_pages to pull more volume.
    num_pages = max(1, limit // 10)
    querystring = {"query": query, "page": "1", "num_pages": str(num_pages)}

    headers = {
        "x-rapidapi-key": rapid_key,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }

    # Stagger requests to avoid hammering the API with 10+ simultaneous calls
    time.sleep(random.uniform(0.2, 1.5))

    for attempt in range(3):  # Retry up to 3 times on 429
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=15)
            
            if response.status_code == 429:
                wait = 2.0 * (attempt + 1)  # Exponential back-off: 2s, 4s, 6s
                print(f"JSearch Rate Limited (429). Retrying in {wait}s... (Attempt {attempt+1}/3)")
                time.sleep(wait)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for result in data.get("data", []):
                desc = result.get("job_description", "")
                loc = f"{result.get('job_city', '')} {result.get('job_country', '')}".strip()
                if not loc:
                    loc = "Remote"
                    
                jobs.append({
                    "title": result.get("job_title", ""),
                    "company": result.get("employer_name", "Unknown"),
                    "location": loc,
                    "description": desc,
                    "url": result.get("job_apply_link", "") or result.get("job_google_link", ""),
                    "source": "JSearch"
                })
            return jobs
        except Exception as e:
            if attempt == 2:
                print(f"JSearch API Error: {e}")
                return []
            time.sleep(1.5)
    return []

def search_jobs(roles, locations):
    all_jobs = []
    seen_urls = set()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = []
        for role in roles:
            # 1. Fetch from Remotive (Remote only)
            futures.append(executor.submit(search_remotive_jobs, role))
            
            for loc in locations:
                # 2. Fetch from JSearch (Google Jobs)
                futures.append(executor.submit(search_jsearch_jobs, role, loc))
                
                # 3. Fetch from Adzuna
                futures.append(executor.submit(search_adzuna_jobs, role, loc))
                
        for future in concurrent.futures.as_completed(futures):
            try:
                jobs = future.result()
                for j in jobs:
                    if j["url"] and j["url"] not in seen_urls:
                        seen_urls.add(j["url"])
                        all_jobs.append(j)
            except Exception as e:
                print(f"Concurrent API Fetch Error: {e}")
                
    return all_jobs

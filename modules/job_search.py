import requests
import re
import concurrent.futures
import time
import random
from datetime import datetime, timezone
from .utils import get_env_var

def _is_fresh(date_str):
    """Returns True if the job was posted within the last 30 days."""
    if not date_str:
        return True  # No date = keep it (e.g. JSearch sometimes omits)
    try:
        formats = ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"]
        dt = None
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str[:len(fmt)], fmt)
                break
            except:
                continue
        if dt:
            days_old = (datetime.utcnow() - dt).days
            return days_old <= 30
    except:
        pass
    return True  # On parse error, keep the job

def _dedupe_key(job):
    """Smarter deduplication: same title at same company = same job."""
    title = (job.get("title") or "").lower().strip()
    company = (job.get("company") or "").lower().strip()
    return f"{title}|{company}"

def _normalize_job_type(raw):
    if not raw:
        return None
    raw_lower = raw.lower()
    if any(k in raw_lower for k in ["intern", "trainee"]):
        return "Internship"
    if any(k in raw_lower for k in ["contract", "freelance", "temporary"]):
        return "Contract"
    if any(k in raw_lower for k in ["part"]):
        return "Part Time"
    if any(k in raw_lower for k in ["full", "permanent"]):
        return "Full Time"
    return raw.title()

def search_adzuna_jobs(role, location="India", limit=10):
    app_id = get_env_var("ADZUNA_APP_ID")
    app_key = get_env_var("ADZUNA_API_KEY")
    
    if not app_id or not app_key:
        print("Skipping Adzuna: Missing ADZUNA_APP_ID or ADZUNA_API_KEY in .env")
        return []
        
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": limit,
        "what": role,
        "where": location
    }
    
    time.sleep(random.uniform(0.1, 1.0))
    
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                print(f"Adzuna Rate Limited (429). Retrying in 2 seconds... (Attempt {attempt+1}/3)")
                time.sleep(2.0)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for item in data.get("results", []):
                date_str = item.get("created", "")
                if not _is_fresh(date_str):
                    continue  # Skip stale jobs

                salary_min = item.get("salary_min")
                salary_max = item.get("salary_max")
                salary = None
                if salary_min and salary_max:
                    salary = f"₹{int(salary_min):,} – ₹{int(salary_max):,}"
                elif salary_min:
                    salary = f"₹{int(salary_min):,}+"

                jobs.append({
                    "id": str(item.get("id")),
                    "title": item.get("title"),
                    "company": item.get("company", {}).get("display_name", "Unknown"),
                    "location": item.get("location", {}).get("display_name", location),
                    "description": item.get("description", ""),
                    "url": item.get("redirect_url"),
                    "source": "Adzuna",
                    "date_posted": date_str[:10] if date_str else None,
                    "salary": salary,
                    "job_type": _normalize_job_type(item.get("contract_type")),
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
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        jobs = []
        for result in data.get("jobs", [])[:limit]:
            date_str = result.get("publication_date", "")
            if not _is_fresh(date_str):
                continue  # Skip old remote jobs

            raw_html = result.get("description", "")
            clean_text = re.sub('<[^<]+?>', ' ', raw_html)
            clean_text = " ".join(clean_text.split())
            
            job_type = _normalize_job_type(result.get("job_type"))
            
            jobs.append({
                "title": result.get("title", ""),
                "company": result.get("company_name", "Unknown"),
                "location": result.get("candidate_required_location", "Remote"),
                "description": clean_text,
                "url": result.get("url", ""),
                "source": "Remotive",
                "date_posted": date_str[:10] if date_str else None,
                "salary": result.get("salary"),
                "job_type": job_type,
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
    query = f"{role} in {location}" if location.lower() != "remote" else f"{role} remote"
    num_pages = max(1, limit // 10)
    querystring = {"query": query, "page": "1", "num_pages": str(num_pages)}

    headers = {
        "x-rapidapi-key": rapid_key,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }

    time.sleep(random.uniform(0.2, 1.5))

    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=15)
            
            if response.status_code == 429:
                wait = 2.0 * (attempt + 1)
                print(f"JSearch Rate Limited (429). Retrying in {wait}s... (Attempt {attempt+1}/3)")
                time.sleep(wait)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for result in data.get("data", []):
                date_str = result.get("job_posted_at_datetime_utc", "")
                if not _is_fresh(date_str):
                    continue

                desc = result.get("job_description", "")
                loc = f"{result.get('job_city', '')} {result.get('job_country', '')}".strip()
                if not loc:
                    loc = "Remote"

                employment_type = result.get("job_employment_type", "")
                    
                jobs.append({
                    "title": result.get("job_title", ""),
                    "company": result.get("employer_name", "Unknown"),
                    "location": loc,
                    "description": desc,
                    "url": result.get("job_apply_link", "") or result.get("job_google_link", ""),
                    "source": "JSearch",
                    "date_posted": date_str[:10] if date_str else None,
                    "salary": result.get("job_salary_period") and f"{result.get('job_min_salary', '')} – {result.get('job_max_salary', '')} {result.get('job_salary_currency', '')}".strip("– "),
                    "job_type": _normalize_job_type(employment_type),
                })
            return jobs
        except Exception as e:
            if attempt == 2:
                print(f"JSearch API Error: {e}")
                return []
            time.sleep(1.5)
    return []

def search_jobs(roles, locations, job_type_filter=None):
    all_jobs = []
    seen_keys = set()   # Smarter dedup: title+company
    seen_urls = set()   # Also keep URL dedup as backup
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = []
        for role in roles:
            futures.append(executor.submit(search_remotive_jobs, role))
            for loc in locations:
                futures.append(executor.submit(search_jsearch_jobs, role, loc))
                futures.append(executor.submit(search_adzuna_jobs, role, loc))
                
        for future in concurrent.futures.as_completed(futures):
            try:
                jobs = future.result()
                for j in jobs:
                    # Filter by job type if user has specified one
                    if job_type_filter and j.get("job_type") and job_type_filter.lower() not in j.get("job_type", "").lower():
                        continue

                    url = j.get("url") or ""
                    dkey = _dedupe_key(j)
                    
                    if url and url in seen_urls:
                        continue
                    if dkey and dkey in seen_keys:
                        continue
                    
                    if url:
                        seen_urls.add(url)
                    if dkey:
                        seen_keys.add(dkey)
                    all_jobs.append(j)
            except Exception as e:
                print(f"Concurrent API Fetch Error: {e}")
                
    return all_jobs

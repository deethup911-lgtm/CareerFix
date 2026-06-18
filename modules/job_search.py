import requests
import re
import concurrent.futures
import time
import random
import threading
from datetime import datetime, timezone, timedelta
from .utils import get_env_var

LAST_JSEARCH_STATUS = {
    "active": False,
    "skipped": False,
    "error": None,
    "success_count": 0
}

# Lock to protect concurrent writes to LAST_JSEARCH_STATUS from ThreadPoolExecutor workers
_status_lock = threading.Lock()


def parse_date_string(date_str):
    if not date_str:
        return None
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})', date_str)
    if match:
        try:
            return datetime.strptime(match.group(0), "%Y-%m-%d").date()
        except ValueError:
            pass
    return None

def _is_fresh(date_str):
    """Returns True if the job was posted within the last 30 days."""
    if not date_str:
        return True  # No date = keep it (e.g. JSearch sometimes omits)
    try:
        dt = parse_date_string(date_str)
        if not dt:
            return True
        days_old = (datetime.utcnow().date() - dt).days
        if days_old > 365:
            # System clock is far ahead of API data (e.g. 2026 vs 2024).
            # We don't filter out here, but we will shift dates in search_jobs.
            return True
        return days_old <= 30
    except Exception:
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
    global LAST_JSEARCH_STATUS
    rapid_key = get_env_var("RAPIDAPI_KEY")
    if not rapid_key:
        with _status_lock:
            LAST_JSEARCH_STATUS["skipped"] = True
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
                with _status_lock:
                    LAST_JSEARCH_STATUS["error"] = str(e)
                print(f"JSearch API Error: {e}")
                return []
            time.sleep(1.5)
    return []


def is_past_event_job(title, today_date):
    """
    Parses dates from the title (e.g., '13-Jun-26', '13-May-26', '13 Jun 2026') 
    and returns True if the date is strictly in the past compared to today_date.
    """
    import re
    from datetime import datetime
    
    title_lower = title.lower()
    
    months_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }
    
    # Pattern 1: DD-MMM-YY, DD-MMM-YYYY, DD MMM YY, DD MMM YYYY (with dash, space, or slash)
    # e.g., '13-Jun-26', '13 Jun 2026', '13/Jun/26'
    match = re.search(r'(?<![a-zA-Z0-9])(\d{1,2})[-\s\/](jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(?:[a-z]*)[-\s\/](\d{2,4})(?![a-zA-Z0-9])', title_lower)
    if match:
        day = int(match.group(1))
        month = months_map[match.group(2)]
        year_str = match.group(3)
        if len(year_str) == 2:
            year = 2000 + int(year_str)
        else:
            year = int(year_str)
            
        try:
            event_date = datetime(year, month, day).date()
            if event_date < today_date:
                return True
        except ValueError:
            pass
            
    # Pattern 2: DD/MM/YYYY, DD/MM/YY, DD-MM-YYYY, DD-MM-YY
    # e.g., '13/06/2026', '13-05-26'
    match = re.search(r'(?<![a-zA-Z0-9])(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2,4})(?![a-zA-Z0-9])', title_lower)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year_str = match.group(3)
        if len(year_str) == 2:
            year = 2000 + int(year_str)
        else:
            year = int(year_str)
            
        try:
            event_date = datetime(year, month, day).date()
            if event_date < today_date:
                return True
        except ValueError:
            pass
            
    return False

def search_jobs(roles, locations, job_type_filter=None, search_internships=False, is_student=False):
    global LAST_JSEARCH_STATUS
    LAST_JSEARCH_STATUS.clear()
    LAST_JSEARCH_STATUS.update({
        "active": True,
        "skipped": False,
        "error": None,
        "success_count": 0
    })

    # Expand roles to include base titles (e.g. "AI Engineer" instead of only "Junior AI Engineer")
    # to search more broadly and let experience filters handle the seniority.
    expanded_roles = []
    seen_roles = set()
    
    if search_internships:
        for r in roles:
            r_clean = r.strip()
            if not r_clean:
                continue
            
            # Clean the role: strip junior, intern, etc.
            base_r = re.sub(r'(?i)\b(junior|jr\.?|associate|entry\s+level|trainee|intern|internship)\b', '', r_clean)
            base_r = re.sub(r'\s+', ' ', base_r).strip()
            if not base_r:
                base_r = r_clean
                
            # Formulate internship queries
            queries = [
                f"{base_r} Intern",
                f"{base_r} Internship",
                f"{base_r} Summer Internship",
                f"Summer Internship {base_r}",
                base_r
            ]

            # If the candidate is a current student, add student-specific queries
            # that companies use when posting campus/college-targeted internships
            if is_student:
                student_queries = [
                    f"{base_r} Student Intern",
                    f"{base_r} Student Internship",
                    f"Student {base_r} Intern",
                    f"{base_r} Campus Intern",
                    f"{base_r} College Intern",
                    f"{base_r} Graduate Trainee",
                    f"{base_r} Fresher Intern",
                    f"Campus Internship {base_r}",
                ]
                queries.extend(student_queries)

            for q in queries:
                if q.lower() not in seen_roles:
                    expanded_roles.append(q)
                    seen_roles.add(q.lower())
        
        job_type_filter = "Internship"
    else:
        for r in roles:
            r_clean = r.strip()
            if not r_clean:
                continue
            if r_clean.lower() not in seen_roles:
                expanded_roles.append(r_clean)
                seen_roles.add(r_clean.lower())
                
            # Strip common junior/entry level prefixes and suffixes indicating entry level positions
            base_r = re.sub(r'(?i)\b(junior|jr\.?|associate|entry\s+level|trainee|intern)\b', '', r_clean)
            base_r = re.sub(r'\s+', ' ', base_r).strip()
            
            if base_r and base_r.lower() not in seen_roles and len(base_r) > 2:
                expanded_roles.append(base_r)
                seen_roles.add(base_r.lower())
            
    roles = expanded_roles
    all_jobs = []
    seen_keys = set()   # Smarter dedup: title+company
    seen_urls = set()   # Also keep URL dedup as backup
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures_map = {}
        for role in roles:
            f_rem = executor.submit(search_remotive_jobs, role)
            futures_map[f_rem] = ("remotive", role, None)
            for loc in locations:
                f_js = executor.submit(search_jsearch_jobs, role, loc)
                futures_map[f_js] = ("jsearch", role, loc)
                f_adz = executor.submit(search_adzuna_jobs, role, loc)
                futures_map[f_adz] = ("adzuna", role, loc)
                
        for future in concurrent.futures.as_completed(futures_map):
            api_name, role, loc = futures_map[future]
            try:
                jobs = future.result()
                if api_name == "jsearch" and jobs:
                    with _status_lock:
                        LAST_JSEARCH_STATUS["success_count"] += len(jobs)
                    
                for j in jobs:
                    # Filter by job type if user has specified one
                    if job_type_filter:
                        j_type = (j.get("job_type") or "").lower()
                        j_title = (j.get("title") or "").lower()
                        
                        if job_type_filter.lower() == "internship":
                            is_intern_type = "intern" in j_type or "trainee" in j_type
                            is_intern_title = any(k in j_title for k in ["intern", "trainee", "co-op", "apprentice"])
                            if not (is_intern_type or is_intern_title):
                                continue
                        else:
                            if job_type_filter.lower() not in j_type:
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
                if api_name == "jsearch":
                    LAST_JSEARCH_STATUS["error"] = str(e)
                print(f"Concurrent API Fetch Error ({api_name}): {e}")

                
    # --- DYNAMIC DATE SHIFTING ---
    # If the system clock is far ahead of the retrieved jobs (e.g., system is in 2026, APIs are in 2024),
    # we shift all job dates so that the most recent job appears as "Today".
    if all_jobs:
        parsed_dates = []
        for j in all_jobs:
            dp = j.get("date_posted")
            if dp:
                dt = parse_date_string(dp)
                if dt:
                    parsed_dates.append((j, dt))
                    
        if parsed_dates:
            max_dt = max(dt for _, dt in parsed_dates)
            today = datetime.utcnow().date()
            delta_days = (today - max_dt).days
            
            # Filter out stale jobs (>30 days older than max_dt) and shift remaining jobs to today if needed
            filtered_shifted_jobs = []
            for j in all_jobs:
                dp = j.get("date_posted")
                if dp:
                    dt = parse_date_string(dp)
                    if dt:
                        # Filter out jobs that are genuinely older than 30 days relative to the latest retrieved job
                        if (max_dt - dt).days > 30:
                            continue
                        if delta_days > 0:
                            shifted_dt = dt + timedelta(days=delta_days)
                            j["date_posted"] = shifted_dt.strftime("%Y-%m-%d")
                filtered_shifted_jobs.append(j)
            all_jobs = filtered_shifted_jobs
                
    # Filter out past walk-in drives or events
    today = datetime.utcnow().date()
    all_jobs = [j for j in all_jobs if not is_past_event_job(j.get("title", ""), today)]
    
    return all_jobs

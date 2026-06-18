from .experience_extractor import extract_job_experience
from .job_classifier import classify_job_posting
import re

# Job title fragments that are clearly non-entry-level or non-tech for students
_ACADEMIC_ROLE_PATTERN = re.compile(
    r'\b(?:professor|lecturer|faculty|teacher|instructor|adjunct|dean|provost|'
    r'principal investigator|researcher(?:\s+ii|\s+iii)?)\b',
    re.IGNORECASE
)

# Fast pre-filter: any internship-related word anywhere in title/type.
# Used as a cheap gate before running the full classifier.
_INTERNSHIP_PREFILTER = re.compile(
    r'\b(?:intern|internship|trainee|co-?op|apprentice|placement|'
    r'student\s+(?:developer|engineer|analyst|programmer)|'
    r'campus\s+(?:intern|hire)|graduate\s+(?:trainee|scheme|programme)|'
    r'industrial\s+training|work\s+placement|vacation\s+scheme|stipend)\b',
    re.IGNORECASE
)

# Categories the classifier must return for a Student candidate to see the job
_STUDENT_ALLOWED_CATEGORIES = {"Student Internship", "Graduate Internship"}
_MIN_STUDENT_CONFIDENCE = 0.50   # classifier must be at least 50% confident


def _passes_student_filter(job: dict) -> bool:
    """
    Returns True if the job is appropriate for a currently-enrolled Student.
    Uses a two-stage check:
      1. Fast regex pre-filter on title/job_type (cheap)
      2. Full classify_job_posting() on title + description (accurate)
    """
    title    = job.get("title", "")
    job_type = job.get("job_type", "") or ""

    # Stage 1: Quick reject if no internship-related word anywhere
    if not (_INTERNSHIP_PREFILTER.search(title) or
            _INTERNSHIP_PREFILTER.search(job_type)):
        return False

    # Stage 2: Full classification
    result = classify_job_posting(title, job.get("description", ""))
    return (
        result["category"] in _STUDENT_ALLOWED_CATEGORIES and
        result["confidence"] >= _MIN_STUDENT_CONFIDENCE
    )


def filter_jobs_by_experience(jobs, candidate_level, candidate_years):
    filtered_jobs = []

    for job in jobs:
        combined_text = f"{job['title']} {job['description']}"
        exp_data = extract_job_experience(combined_text)
        req_years = exp_data["experience_min"]
        req_seniority = exp_data["seniority"]

        if candidate_level == "Student":
            # Students only see Student Internship / Graduate Internship postings
            if not _passes_student_filter(job):
                continue
            # Also hard-reject if JD explicitly requires senior experience
            if req_years > 2:
                continue

        elif candidate_level in ["Fresher", "Intern"]:
            # Hard-reject academic / teaching roles
            if _ACADEMIC_ROLE_PATTERN.search(job.get("title", "")):
                continue
            # Reject > 3 years hard
            if req_years > 3:
                continue
            # Reject Executive / Senior / Principal hard
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

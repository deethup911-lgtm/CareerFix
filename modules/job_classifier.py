"""
job_classifier.py
-----------------
Classifies a job posting into one of four categories:

  1. Student Internship   — for currently-enrolled students (campus recruit,
                            "currently pursuing", stipend-based, short duration)
  2. Graduate Internship  — for recent graduates / freshers (0-1 yr exp,
                            "fresh graduate", "0 experience welcome")
  3. Entry-Level Job      — full-time role, 0-2 yrs exp, no enrollment signal
  4. Experienced Role     — requires meaningful prior experience (3+ yrs)

Returns:
  {
    "category":   str,    # one of the four above
    "confidence": float,  # 0.0 – 1.0
    "signals":    dict,   # score breakdown (useful for debugging)
  }
"""

import re

# ---------------------------------------------------------------------------
# Signal patterns
# ---------------------------------------------------------------------------

# --- Student Internship signals -------------------------------------------
_STUDENT_ENROLLMENT_PATTERN = re.compile(
    r'\b(?:'
    r'currently\s+(?:enrolled|pursuing|studying)|'
    r'pursuing\s+(?:a\s+)?(?:degree|b\.?tech|b\.?e|mca|bca|m\.?sc|b\.?sc|bachelor|master)|'
    r'enrolled\s+in|'
    r'(?:1st|2nd|3rd|4th|5th|penultimate|final)\s+year|'
    r'first|second|third|fourth|fifth\s+year\s+student|'
    r'undergraduate\s+student|'
    r'college\s+student|university\s+student|'
    r'campus\s+(?:recruit|hire|drive|placement|intern)|'
    r'college\s+(?:recruit|hire)|'
    r'on-campus|off-campus\s+drive|'
    r'stipend|'
    r'industrial\s+training|'
    r'summer\s+(?:intern|internship|project)|'
    r'winter\s+(?:intern|internship)|'
    r'vacation\s+(?:intern|internship|training)|'
    r'student\s+(?:intern|internship|developer|engineer|analyst|trainee)|'
    r'(?:6|8|10|12|16|24)\s*(?:-|to)?\s*weeks?\s+internship|'
    r'(?:1|2|3|4|5|6)\s*(?:-|to)?\s*months?\s+internship'
    r')\b',
    re.IGNORECASE
)

_STUDENT_TITLE_PATTERN = re.compile(
    r'\b(?:'
    r'student\s+intern|campus\s+intern|college\s+intern|'
    r'summer\s+intern|winter\s+intern|vacation\s+intern|'
    r'industrial\s+training|work\s+placement|placement\s+student|'
    r'vacation\s+scheme|co-op\s+student'
    r')\b',
    re.IGNORECASE
)

# --- Graduate Internship signals ------------------------------------------
_GRADUATE_INTERN_PATTERN = re.compile(
    r'\b(?:'
    r'fresh\s+graduate|recent\s+graduate|newly\s+graduated|'
    r'graduate\s+(?:intern|internship|trainee|programme|program|scheme)|'
    r'fresher\s+(?:intern|internship|trainee)|'
    r'0\s*(?:to|-)\s*1\s*years?\s+(?:of\s+)?experience|'
    r'no\s+(?:prior\s+)?experience\s+(?:required|needed)|'
    r'experience\s+not\s+(?:required|mandatory)|'
    r'open\s+to\s+freshers|'
    r'freshers?\s+(?:can|may|are)\s+apply|'
    r'post\s*-?\s*graduate\s+trainee'
    r')\b',
    re.IGNORECASE
)

# --- General internship wording (shared by Student + Graduate) ------------
_INTERNSHIP_GENERIC_PATTERN = re.compile(
    r'\b(?:intern|internship|trainee|apprentice|co-?op|work\s+placement)\b',
    re.IGNORECASE
)

# --- Entry-level (full-time) signals --------------------------------------
_ENTRY_LEVEL_PATTERN = re.compile(
    r'\b(?:'
    r'entry[\s-]level|junior|jr\.?|associate(?!\s+degree)|'
    r'entry\s+(?:position|role|opportunity)|'
    r'(?:0|zero|no)\s+(?:to\s+(?:1|2|one|two))?\s*years?\s+(?:of\s+)?experience|'
    r'(?:fresh|recent)\s+graduates?\s+welcome|'
    r'new\s+grad(?:uate)?|'
    r'early\s+career|'
    r'career\s+(?:starter|starter\s+role)|'
    r'graduate\s+(?:engineer|developer|analyst|hire)(?!\s+(?:scheme|programme|program|trainee))'
    r')\b',
    re.IGNORECASE
)

# --- Experienced role signals ---------------------------------------------
_EXPERIENCED_PATTERN = re.compile(
    r'\b(?:'
    r'(?:3|4|5|6|7|8|9|10|\d{2})\s*\+?\s*years?\s+(?:of\s+)?(?:relevant\s+)?experience|'
    r'minimum\s+(?:3|4|5|6|7|8|9|10|\d{2})\s*years?|'
    r'at\s+least\s+(?:3|4|5|6|7|8|9|10|\d{2})\s*years?|'
    r'senior|sr\.|lead|principal|staff|manager|head\s+of|director|architect'
    r')\b',
    re.IGNORECASE
)

# --- Education requirement signals ----------------------------------------
_BACHELOR_REQUIRED = re.compile(
    r'\b(?:'
    r'bachelor(?:\'s)?\s+degree\s+(?:required|preferred|in)|'
    r'b\.?(?:tech|e|sc|com)\s+(?:required|preferred|in)|'
    r'degree\s+in\s+(?:computer|information|engineering|science)'
    r')\b',
    re.IGNORECASE
)

_CURRENTLY_PURSUING = re.compile(
    r'\b(?:'
    r'currently\s+pursuing|'
    r'pursuing\s+(?:b\.?tech|b\.?e|mca|bca|b\.?sc)|'
    r'(?:3rd|4th|final|penultimate)\s+year\s+(?:students?|candidates?)'
    r')\b',
    re.IGNORECASE
)

_STIPEND_PATTERN = re.compile(
    r'\b(?:stipend|fellowship|scholarship\s+(?:for\s+)?(?:intern|student))\b',
    re.IGNORECASE
)

# Explicit "full.time" / "permanent" wording — pushes away from internship
_FULLTIME_PATTERN = re.compile(
    r'\b(?:full[\s-]time|permanent\s+(?:role|position)|full\s+time\s+employment)\b',
    re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

def classify_job_posting(title: str, description: str) -> dict:
    """
    Classify a job posting and return category + confidence.

    Parameters
    ----------
    title       : Job title string
    description : Job description / JD text

    Returns
    -------
    dict with keys: category (str), confidence (float 0-1), signals (dict)
    """
    text = f"{title} {description}"

    # --- Count signals per category ---
    scores = {
        "Student Internship":  0.0,
        "Graduate Internship": 0.0,
        "Entry-Level Job":     0.0,
        "Experienced Role":    0.0,
    }

    signal_hits = {
        "student_enrollment":  0,
        "student_title":       0,
        "graduate_intern":     0,
        "generic_internship":  0,
        "currently_pursuing":  0,
        "stipend":             0,
        "entry_level":         0,
        "experienced":         0,
        "full_time":           0,
        "bachelor_required":   0,
    }

    # Enrollment / campus signals → strong Student Internship
    student_enrollment_hits = len(_STUDENT_ENROLLMENT_PATTERN.findall(text))
    signal_hits["student_enrollment"] = student_enrollment_hits
    scores["Student Internship"] += student_enrollment_hits * 2.5

    # Title is explicitly a student role
    if _STUDENT_TITLE_PATTERN.search(title):
        signal_hits["student_title"] = 1
        scores["Student Internship"] += 3.0

    # Currently-pursuing language
    pursuing_hits = len(_CURRENTLY_PURSUING.findall(text))
    signal_hits["currently_pursuing"] = pursuing_hits
    scores["Student Internship"] += pursuing_hits * 2.0

    # Stipend → internship (lean student)
    if _STIPEND_PATTERN.search(text):
        signal_hits["stipend"] = 1
        scores["Student Internship"] += 1.5
        scores["Graduate Internship"] += 0.5

    # Graduate internship signals
    grad_hits = len(_GRADUATE_INTERN_PATTERN.findall(text))
    signal_hits["graduate_intern"] = grad_hits
    scores["Graduate Internship"] += grad_hits * 2.5

    # Generic "intern" / "internship" in title
    if _INTERNSHIP_GENERIC_PATTERN.search(title):
        signal_hits["generic_internship"] += 2
        # Lean student if no explicit graduate signal, else graduate
        if scores["Student Internship"] >= scores["Graduate Internship"]:
            scores["Student Internship"] += 1.5
        else:
            scores["Graduate Internship"] += 1.5

    # Generic "intern" in description only
    generic_desc_hits = len(_INTERNSHIP_GENERIC_PATTERN.findall(description))
    signal_hits["generic_internship"] += generic_desc_hits
    intern_score = min(generic_desc_hits * 0.5, 2.0)  # cap at 2.0
    if scores["Student Internship"] >= scores["Graduate Internship"]:
        scores["Student Internship"] += intern_score
    else:
        scores["Graduate Internship"] += intern_score

    # Entry-level signals
    entry_hits = len(_ENTRY_LEVEL_PATTERN.findall(text))
    signal_hits["entry_level"] = entry_hits
    scores["Entry-Level Job"] += entry_hits * 1.5

    # Experienced role signals
    exp_hits = len(_EXPERIENCED_PATTERN.findall(text))
    signal_hits["experienced"] = exp_hits
    scores["Experienced Role"] += exp_hits * 2.0

    # Full-time signal — penalises internship categories
    if _FULLTIME_PATTERN.search(text):
        signal_hits["full_time"] = 1
        scores["Student Internship"] -= 1.0
        scores["Graduate Internship"] -= 0.5
        scores["Entry-Level Job"] += 0.5

    # Bachelor-required signal — slight experienced push unless it's with internship wording
    if _BACHELOR_REQUIRED.search(text):
        signal_hits["bachelor_required"] = 1
        if signal_hits["generic_internship"] == 0:
            scores["Entry-Level Job"] += 0.5
            scores["Experienced Role"] += 0.3

    # Floor all scores at 0
    scores = {k: max(0.0, v) for k, v in scores.items()}

    # --- Default fallback: if no signals at all, classify by experience ---
    total_signal = sum(scores.values())
    if total_signal == 0:
        # Use experience extractor as tiebreaker
        from .experience_extractor import extract_job_experience
        exp_data = extract_job_experience(text)
        req_min = exp_data["experience_min"]
        if req_min == 0:
            scores["Entry-Level Job"] = 1.0
        elif req_min <= 2:
            scores["Entry-Level Job"] = 1.0
        else:
            scores["Experienced Role"] = 1.0
        total_signal = sum(scores.values())

    # --- Pick winner ---
    best_category = max(scores, key=scores.__getitem__)
    best_score = scores[best_category]

    # Confidence = winner's share of total signal, scaled to [0.4, 1.0]
    raw_confidence = best_score / total_signal if total_signal > 0 else 0.5
    # Map [0, 1] → [0.4, 1.0] so even weak wins report at least 0.4
    confidence = 0.4 + raw_confidence * 0.6
    confidence = round(min(1.0, max(0.4, confidence)), 2)

    return {
        "category":   best_category,
        "confidence": confidence,
        "signals":    signal_hits,
        "scores":     {k: round(v, 2) for k, v in scores.items()},
    }

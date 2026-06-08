# CareerFix — AI-Powered ATS Resume & Job Matching Engine

CareerFix is a full-stack AI-powered Applicant Tracking System (ATS) simulator and job recommendation engine. It analyzes your resume, matches it against live job postings from multiple boards, gives semantic skill matching scores, and uses Google Gemini to coach you on how to beat the ATS for each specific role.

---

## Features

- **AI Resume Analysis** — Upload a PDF or paste text. Gemini extracts skills, experience level, projects, and education.
- **Offline Fallback Mode** — If Gemini API quota is exhausted, a local 488-skill taxonomy dictionary provides instant offline parsing.
- **Multi-Board Job Search** — Simultaneously fetches from Adzuna, Remotive, and JSearch (Google Jobs) using parallel threads.
- **Semantic Skill Matching** — Uses ChromaDB + `all-MiniLM-L6-v2` to detect synonym matches (e.g. "Neural Networks" ↔ "Deep Learning").
- **ATS Score Simulator** — Simulates how a corporate ATS software would score your resume against a job: keyword density, section detection, formatting checks, length analysis.
- **AI Resume Tips** — Gemini 2.0 Flash generates custom summary rewrites and bullet point fixes for each specific job.
- **Interview Question Generator** — 5 targeted interview questions per job (mix of technical + behavioral).
- **Job Freshness Filter** — Only shows jobs posted within the last 30 days.
- **Smart Deduplication** — Removes duplicate jobs by title+company hash across all sources.
- **Dynamic Autocomplete UI** — GeoDB Cities API for location autocomplete. Local suggestions for job titles.
- **Junior Role Mapping** — Freshers automatically get entry-level job title suggestions like "Junior AI Engineer" instead of mid-level titles.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React.js (Vite), Vanilla CSS |
| Backend | FastAPI (Python), Uvicorn |
| AI Models | Google Gemini 2.0 Flash, Sentence Transformers (`all-MiniLM-L6-v2`) |
| Vector DB | ChromaDB (in-memory) |
| Resume Parsing | PyPDF2, PyMuPDF |
| Job APIs | Adzuna, Remotive, JSearch (RapidAPI) |
| Location API | GeoDB Cities (RapidAPI) |

---

## Project Structure

```
CareerFix/
├── main.py                        # FastAPI server + all API endpoints
├── requirements.txt               # Python dependencies
├── .env                           # API keys (DO NOT COMMIT)
│
├── modules/
│   ├── resume_parser.py           # PDF/DOCX text extraction
│   ├── resume_analyzer.py         # Gemini skill + experience extraction
│   ├── role_recommender.py        # Local + Gemini role recommendations
│   ├── job_search.py              # Multi-API parallel job fetcher
│   ├── job_filter.py              # Seniority + experience level filter
│   ├── matcher.py                 # ChromaDB + semantic scoring engine
│   ├── ats_simulator.py           # ATS score simulation (offline)
│   ├── resume_tailor.py           # Gemini resume tips + interview Q + certs
│   ├── skill_extractor.py         # Local skill parsing from tech_skills.txt
│   ├── experience_extractor.py    # Regex-based experience year extractor
│   ├── skill_gap.py               # Cross-job skill gap aggregation
│   ├── pdf_generator.py           # Resume PDF export
│   └── utils.py                   # Shared helpers
│
├── data/
│   ├── tech_skills.txt            # 488-skill offline taxonomy
│   └── non_tech_skills.txt        # Non-technical skills dictionary
│
└── frontend/
    └── src/
        ├── pages/
        │   ├── UploadPage.jsx     # Resume upload / paste UI
        │   └── OutputPage.jsx     # Job results, ATS Score, Interview Prep
        └── components/
            └── AutocompleteInput.jsx  # Smart autocomplete with GeoDB
```

---

## Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/CareerFix.git
cd CareerFix
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_google_gemini_api_key
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_API_KEY=your_adzuna_api_key
RAPIDAPI_KEY=your_rapidapi_key
```

#### Getting API Keys:
| API | Link | Cost |
|---|---|---|
| **Gemini API** | [aistudio.google.com](https://aistudio.google.com/app/apikey) | Free (1500 req/day) |
| **Adzuna** | [developer.adzuna.com](https://developer.adzuna.com/) | Free |
| **RapidAPI** (JSearch + GeoDB) | [rapidapi.com](https://rapidapi.com/) | Free tier available |

> **Note:** JSearch and GeoDB Cities both use the same `RAPIDAPI_KEY`. Subscribe to both on RapidAPI with one account.

### 4. Start the Backend
```bash
uvicorn main:app --reload
```
Backend runs on `http://localhost:8000`

### 5. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs on `http://localhost:5173`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze-resume` | Upload PDF or paste resume text |
| `POST` | `/api/search-jobs` | Fetch live jobs from all boards |
| `POST` | `/api/match-jobs` | Run semantic ATS matching |
| `POST` | `/api/get-resume-suggestions` | AI-tailored resume tips |
| `POST` | `/api/ats-score` | ATS simulation score |
| `POST` | `/api/interview-questions` | Generate 5 interview questions |
| `GET` | `/api/locations/autocomplete?q=` | City autocomplete via GeoDB |

---

## How It Works

```
1. Upload Resume (PDF or text)
          ↓
2. Gemini 2.0 Flash extracts skills, experience, domain
   [Fallback: local 488-skill dictionary]
          ↓
3. Role Recommender suggests appropriate job titles based on your experience level
          ↓
4. User clicks Search → 3 Job APIs queried in parallel threads
   (Adzuna + Remotive + JSearch/Google Jobs)
          ↓
5. Jobs filtered: freshness (30 days), deduplication, job type
          ↓
6. ChromaDB embeds candidate skills into vector space
   Sentence Transformers batch-encode all job descriptions
          ↓
7. Semantic Match Score = Skill Match (40%) + Exp Fit (30%) + Semantic Sim (30%)
          ↓
8. Top matches displayed with job type and date badges
          ↓
9. Per job: ATS Score | AI Resume Tips | Interview Questions
```

---

## Environment Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Gemini 429 RESOURCE_EXHAUSTED` | Daily quota hit | Wait until midnight or use a different Google account key |
| `JSearch 429 Too Many Requests` | Rate limit from parallel threads | Reduce job titles / locations in search |
| `Adzuna 429` | Free tier limit | System auto-retries with 3 attempts + jitter |
| `chromadb not installed` | Wrong Python env | Run `python -m pip install chromadb` in the same terminal as uvicorn |
| `Loading... stuck on location` | GeoDB rate limited | Built-in 400ms debounce protects quota; wait a moment |

---


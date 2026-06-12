# CareerFix — AI-Powered ATS Resume & Job Matching Engine

CareerFix is a full-stack AI-powered Applicant Tracking System (ATS) simulator and job recommendation engine. It analyzes your resume, matches it against live job postings from multiple boards, gives semantic skill matching scores, and uses local AI (Ollama) to coach you on how to beat the ATS for each specific role.

---

## Features

- **AI Resume Analysis** — Upload a PDF or paste text. Local AI extracts skills, experience level, contact info, projects, and education.
- **Offline Fallback Mode** — If the AI is unavailable, a local 488-skill taxonomy dictionary provides instant offline parsing.
- **Multi-Board Job Search** — Simultaneously fetches from Adzuna, Remotive, and JSearch (Google Jobs) using parallel threads.
- **Semantic Skill Matching** — Uses ChromaDB + `all-MiniLM-L6-v2` to detect synonym matches (e.g. "Neural Networks" ↔ "Deep Learning").
- **ATS Score Simulator** — Simulates how a corporate ATS software would score your resume against a job: keyword density, section detection, formatting checks, length analysis.
- **AI Resume Tips & Tailoring** — Ollama generates custom summary rewrites and bullet point fixes for each specific job (no direct file export to keep suggestions focused and non-invasive).
- **Persistent Embedding Cache** — Cache job description embeddings locally using SQLite to reduce SentenceTransformer execution and speed up matching performance.
- **Interview Question Generator** — Generates targeted interview questions per job (mix of technical + behavioral).
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
| AI Models | Ollama (`qwen2.5:3b` default), Sentence Transformers (`all-MiniLM-L6-v2`) |
| Vector DB | ChromaDB (in-memory) |
| Resume Parsing | PyMuPDF (fitz), python-docx |
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
│   ├── ollama_client.py           # Interface with local Ollama instance
│   ├── resume_parser.py           # PDF/DOCX text extraction
│   ├── resume_analyzer.py         # AI skill, experience, and contact extraction
│   ├── role_recommender.py        # Local + AI role recommendations
│   ├── job_search.py              # Multi-API parallel job fetcher
│   ├── job_filter.py              # Seniority + experience level filter
│   ├── matcher.py                 # ChromaDB + semantic scoring engine
│   ├── ats_simulator.py           # ATS score simulation (offline)
│   ├── resume_tailor.py           # AI resume tips + interview Q + certs
│   ├── skill_extractor.py         # Local skill parsing from tech_skills.txt
│   ├── experience_extractor.py    # Regex-based experience year extractor
│   ├── skill_gap.py               # Cross-job skill gap aggregation
│   ├── embedding_cache.py         # SQLite persistent embedding cache module
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

### 2. Install Dependencies
**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 3. Setup Local AI (Ollama)
Download and install [Ollama](https://ollama.com/). Then, pull the default testing model (or configure your own):
```bash
ollama run qwen2.5:3b
```

### 4. Configure API Keys

Create a `.env` file in the root directory:
```env
# Optional: Set your preferred Ollama model (default is qwen2.5:3b)
OLLAMA_MODEL=qwen2.5:3b

# Job Board APIs
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_API_KEY=your_adzuna_api_key
RAPIDAPI_KEY=your_rapidapi_key
```

#### Getting API Keys:
| API | Link | Cost |
|---|---|---|
| **Adzuna** | [developer.adzuna.com](https://developer.adzuna.com/) | Free |
| **RapidAPI** (JSearch + GeoDB) | [rapidapi.com](https://rapidapi.com/) | Free tier available |

> **Note:** JSearch and GeoDB Cities both use the same `RAPIDAPI_KEY`. Subscribe to both on RapidAPI with one account.

### 5. Start the Services

**Start the Backend:**
```bash
uvicorn main:app --reload
```
Backend runs on `http://localhost:8000`

**Start the Frontend:**
```bash
cd frontend
npm run dev
```
Frontend runs on `http://localhost:5173`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze-resume` | Upload PDF or paste resume text to extract skills & contact info |
| `POST` | `/api/search-jobs` | Fetch live jobs from all boards |
| `POST` | `/api/match-jobs` | Run semantic ATS matching via ChromaDB |
| `POST` | `/api/get-resume-suggestions` | AI-tailored resume tips and rewriting |
| `POST` | `/api/ats-score` | ATS simulation score based on keyword/format analysis |
| `POST` | `/api/interview-questions` | Generate 5 targeted interview questions |
| `POST` | `/api/certifications` | Recommend certifications to close skill gaps |
| `GET` | `/api/locations/autocomplete?q=` | City autocomplete via GeoDB |
| `GET` | `/api/cache/stats` | View SQLite embedding cache stats (size, count, path) |
| `POST` | `/api/cache/clear` | Clear all saved embeddings from SQLite cache |

---

## Environment Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Ollama connection refused` | Ollama isn't running | Ensure the Ollama app is running in the background |
| `JSearch 429 Too Many Requests` | Rate limit from parallel threads | Reduce job titles / locations in search |
| `Adzuna 429` | Free tier limit | System auto-retries with 3 attempts + jitter |
| `chromadb not installed` | Wrong Python env | Run `python -m pip install chromadb` in the same terminal as uvicorn |
| `Loading... stuck on location` | GeoDB rate limited | Built-in 400ms debounce protects quota; wait a moment |

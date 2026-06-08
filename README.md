# CareerFix

**CareerFix** is an AI-powered job matching, resume analysis, and career guidance assistant.

## Features
- **Resume Parsing**: Extracts clean plain text from PDF and DOCX files.
- **Skill Extraction**: Rule-based skill extraction from resumes combined with optional AI refinement.
- **ESCO Integration**: Standardized occupation mappings for job roles.
- **Job Search**: Live job search via Adzuna API, filtering by location, role, and required experience.
- **Job Matching**: AI-powered matching of user profile to jobs using Sentence Transformers.
- **Skill Gap Analysis**: Actionable feedback on missing skills.
- **Resume Tailoring & Cover Letter Generation**: Generates targeted text for resumes and cover letters using Gemini.
- **Interview Preparation**: Generates tailored interview questions based on the job description.
- **Application Tracker**: Local tracking system to manage job application statuses.

## Tech Stack
- Python 3.11
- Streamlit (Frontend UI)
- PyMuPDF / python-docx (Resume Parsing)
- Google GenAI (Gemini for AI features)
- Sentence Transformers (Semantic Job Matching)
- Adzuna API (Live Job Search)
- ESCO CSV dataset (Career and Role Mapping)
- Pandas & Scikit-learn (Data Processing)

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone <repo_url>
   cd CareerFix
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **API Key Setup**:
   Create a `.env` file in the root directory (already done if cloned directly) and provide your credentials.
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ADZUNA_APP_ID=your_adzuna_app_id_here
   ADZUNA_API_KEY=your_adzuna_api_key_here
   RAPIDAPI_KEY=your_rapidapi_key_here
   ```
   *Note: GEMINI_API_KEY is used for AI resume analysis, tailoring, cover letters, and interview prep. ADZUNA is used for live job search. RAPIDAPI_KEY is optional for location autocomplete.*

5. **ESCO Setup**:
   Download the ESCO CSV classification dataset (English) and place the following files in the `data/esco/` folder:
   - `occupations_en.csv`
   - `skills_en.csv`
   - `occupationSkillRelations_en.csv`
   (Note: These files can be large, so they might not be included in the repo by default).

## How to Run

1. Ensure your virtual environment is activated and `.env` is properly configured.
2. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```
3. Open your browser to the URL displayed in the terminal (usually `http://localhost:8501`).

## How to Test

Tests are written using `pytest`.
```bash
pytest tests/
```

## Limitations
- The ESCO dataset does not contain every modern tool (e.g., React, MongoDB). Therefore, we combine local skill databases with Gemini extraction.
- Free-tier API keys may encounter rate limits.
- The application stores data locally (`data/applications.csv` and `uploaded_resumes/`).

## Future Enhancements
- Migration to a FastAPI backend and React frontend.
- User authentication and login functionality.
- Database integration (MongoDB/PostgreSQL).
- LinkedIn/Naukri/Indeed job scraping integration.
- Automated email reminders and ATS scoring capabilities.
- Advanced learning roadmaps and course recommendations.

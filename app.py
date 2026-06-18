# pyrefly: ignore [missing-import]
import streamlit as st
import os
import pandas as pd

from modules.resume_parser import extract_text
from modules.resume_analyzer import analyze_resume, is_student_resume
from modules.role_recommender import recommend_roles
from modules.job_search import search_jobs
from modules.job_filter import filter_jobs_by_experience
from modules.matcher import calculate_match
from modules.skill_gap import analyze_skill_gaps
from modules.application_tracker import get_applications, add_application
from modules.location_suggestions import get_location_suggestions
from modules.resume_tailor import tailor_resume
from modules.cover_letter_generator import generate_cover_letter
from modules.interview_prep import generate_interview_questions

st.set_page_config(page_title="CareerFix", page_icon="🎯", layout="wide")

# Custom CSS for dark modern UI with green accents
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #C9D1D9;
    }
    .stButton>button {
        background-color: #238636;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #2EA043;
        color: white;
    }
    .card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .tag {
        display: inline-block;
        background-color: #1F6FEB;
        color: white;
        padding: 4px 10px;
        border-radius: 15px;
        margin: 2px;
        font-size: 0.85rem;
    }
    .tag-green {
        background-color: #238636;
    }
    .tag-red {
        background-color: #DA3633;
    }
    h1, h2, h3 {
        color: #58A6FF;
    }
    </style>
""", unsafe_allow_html=True)


def render_internship_guide(reason):
    st.markdown(f"""
    <div style="background-color: #161b22; border: 1px solid #ff7b72; border-radius: 8px; padding: 20px; margin-top: 20px; margin-bottom: 20px;">
        <h3 style="color: #ff7b72; margin-top: 0; display: flex; align-items: center; gap: 8px;">🎓 Student Internship Recommendation Guide</h3>
        <p style="color: #c9d1d9; font-size: 0.95rem; line-height: 1.5; margin-bottom: 15px;">
            <strong>Status Update:</strong> {reason}<br>
            No worries! Getting an internship is all about using the right channels and strategies. Here are the most effective steps you can take to land a student internship:
        </p>
        <hr style="border-color: #30363d; margin: 15px 0;" />
        <div style="display: flex; flex-direction: column; gap: 15px;">
            <div>
                <h4 style="color: #58a6ff; margin: 0 0 5px 0;">🌐 1. Platforms to Check Manually</h4>
                <ul style="margin: 0; padding-left: 20px; color: #c9d1d9; font-size: 0.9rem; line-height: 1.6;">
                    <li><a href="https://internshala.com/" target="_blank" style="color: #58a6ff; font-weight: bold; text-decoration: none;">Internshala</a>: India's largest internship platform, ideal for student freshers.</li>
                    <li><a href="https://www.linkedin.com/" target="_blank" style="color: #58a6ff; font-weight: bold; text-decoration: none;">LinkedIn Jobs</a>: Search for "Software Engineer Intern" and filter by "Internship". Also search posts with hashtags like <code>#internship</code> or <code>#hiring</code>.</li>
                    <li><a href="https://wellfound.com/" target="_blank" style="color: #58a6ff; font-weight: bold; text-decoration: none;">Wellfound (AngelList)</a>: Great for high-growth tech startup internships.</li>
                    <li><a href="https://www.indeed.com/" target="_blank" style="color: #58a6ff; font-weight: bold; text-decoration: none;">Indeed</a>: Search local and remote internships.</li>
                </ul>
            </div>
            <div>
                <h4 style="color: #58a6ff; margin: 0 0 5px 0;">🛠️ 2. Build Projects & Open Source</h4>
                <ul style="margin: 0; padding-left: 20px; color: #c9d1d9; font-size: 0.9rem; line-height: 1.6;">
                    <li><strong>GitHub Portfolio:</strong> Make sure your projects have a detailed <code>README.md</code> with demo links, screenshots, and setup instructions.</li>
                    <li><strong>Open Source Programs:</strong> Apply to programs like <em>Google Summer of Code (GSoC)</em>, <em>Outreachy</em>, or the <em>MLH Fellowship</em>.</li>
                </ul>
            </div>
            <div>
                <h4 style="color: #58a6ff; margin: 0 0 5px 0;">✉️ 3. Direct Outreach & Networking</h4>
                <ul style="margin: 0; padding-left: 20px; color: #c9d1d9; font-size: 0.9rem; line-height: 1.6;">
                    <li>Find engineering managers or tech recruiters at target companies on LinkedIn.</li>
                    <li>Send a short, customized message expressing interest and attach your resume tailored using the <strong>Resume Tailor</strong> feature.</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.title("CareerFix")
st.markdown("### AI-powered job matching, resume analysis, and career guidance assistant.")

# Initialize session state
if 'resume_analysis' not in st.session_state:
    st.session_state.resume_analysis = None
if 'recommended_roles' not in st.session_state:
    st.session_state.recommended_roles = []
if 'jobs' not in st.session_state:
    st.session_state.jobs = []
if 'matched_jobs' not in st.session_state:
    st.session_state.matched_jobs = []
if 'is_student' not in st.session_state:
    st.session_state.is_student = False
if 'jsearch_failed_or_empty' not in st.session_state:
    st.session_state.jsearch_failed_or_empty = False
if 'jsearch_reason' not in st.session_state:
    st.session_state.jsearch_reason = ""
if 'search_internships_run' not in st.session_state:
    st.session_state.search_internships_run = False
if 'last_uploaded_filename' not in st.session_state:
    st.session_state.last_uploaded_filename = None

# ================= 1. Resume Upload =================
st.header("1. Upload Resume")
uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=['pdf', 'docx'])

# Reset student guide state immediately when a DIFFERENT file is selected,
# so the guide from a previous student resume doesn't linger for a new upload.
if uploaded_file is not None:
    if uploaded_file.name != st.session_state.last_uploaded_filename:
        st.session_state.last_uploaded_filename = uploaded_file.name
        st.session_state.is_student = False
        st.session_state.jsearch_failed_or_empty = False
        st.session_state.jsearch_reason = ""
        st.session_state.search_internships_run = False
    if st.button("Analyze Resume"):
        with st.spinner("Parsing and analyzing resume..."):
            # Save uploaded resume
            os.makedirs("uploaded_resumes", exist_ok=True)
            file_path = os.path.join("uploaded_resumes", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            resume_text = extract_text(uploaded_file, uploaded_file.name)
            st.session_state.resume_text = resume_text
            
            if not resume_text:
                st.error("Could not extract text from the file. Please try another resume.")
            else:
                analysis = analyze_resume(resume_text)
                st.session_state.resume_analysis = analysis
                st.session_state.recommended_roles = recommend_roles(analysis)
                st.session_state.is_student = is_student_resume(resume_text, analysis)
                st.session_state.jsearch_failed_or_empty = False
                st.session_state.jsearch_reason = ""
                st.session_state.search_internships_run = False
                st.success("Resume analyzed successfully!")
                st.info(f"🔍 Extracted Skills: {', '.join(analysis.get('skills', [])) if analysis.get('skills') else 'None found'}")
                if analysis.get("error_log"):
                    for err in analysis["error_log"]:
                        st.warning(f"⚠️ {err}")

# ================= 2. Candidate Overview =================
if st.session_state.resume_analysis:
    st.header("2. Candidate Overview")
    analysis = st.session_state.resume_analysis
    
    if st.session_state.get('is_student', False):
        st.info("🎓 **Student / Fresher Resume Detected**: We highly recommend looking for internships (such as summer internships or traineeships) to build your professional portfolio and gain hands-on industry experience!")

    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='card'><h4>Experience Level</h4><p>{analysis.get('experience_level')} ({analysis.get('experience_years')} yrs)</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card'><h4>Detected Domain</h4><p>{analysis.get('domain_hint', 'General')}</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card'><h4>Total Skills</h4><p>{len(analysis.get('skills', []))}</p></div>", unsafe_allow_html=True)
    with col4:
        education = analysis.get('education', 'Not extracted') or 'Not extracted'
        st.markdown(f"<div class='card'><h4>Education</h4><p>{education}</p></div>", unsafe_allow_html=True)
        
    st.markdown("#### Summary")
    st.write(analysis.get('summary', ''))
    
    st.markdown("#### Detected Skills")
    skills_html = "".join([f"<span class='tag'>{s}</span>" for s in analysis.get('skills', [])])
    if skills_html:
        st.markdown(skills_html, unsafe_allow_html=True)
        
    if st.session_state.recommended_roles:
        st.markdown("#### Recommended Career Roles")
        roles_html = "".join([f"<span class='tag tag-green'>{r['role']}</span>" for r in st.session_state.recommended_roles])
        st.markdown(roles_html, unsafe_allow_html=True)
        
    with st.expander("View Extracted Resume Text"):
        st.text(st.session_state.resume_text)

# ================= 3. Job Search =================
st.header("3. Live Job Search")
col_s1, col_s2, col_s3 = st.columns([2, 2, 1])

# Determine default role from recommendations
default_roles = [r['role'] for r in st.session_state.recommended_roles] if st.session_state.recommended_roles else []
default_role_str = ", ".join(default_roles[:2])

with col_s1:
    job_query = st.text_input("Job title, keywords, or company", value=default_role_str)
with col_s2:
    location_query = st.text_input("City, country, or remote", value="India")
    if st.button("Suggest Locations", help="Get standardized location names via RapidAPI"):
        with st.spinner("Fetching..."):
            suggs = get_location_suggestions(location_query)
            if suggs:
                st.info("Try: " + " | ".join(suggs))
            else:
                st.warning("No suggestions (Check RapidAPI key).")
search_internships = st.checkbox(
    "Search specifically for internships (e.g. Summer Internships, Trainee roles)", 
    value=st.session_state.get('is_student', False),
    help="When checked, the search engine expands query keywords to target internships (using JSearch) and filters results for internship positions."
)

with col_s3:
    st.markdown("<br>", unsafe_allow_html=True)
    search_btn = st.button("Find Jobs", use_container_width=True)

if search_btn:
    roles_to_search = []
    if job_query.strip():
        roles_to_search = [job_query.strip()]
    else:
        if default_roles:
            roles_to_search = default_roles
        else:
            st.warning("Could not determine suitable roles from the resume. Please enter a job title manually.")
            st.stop()

    locs_to_search = [l.strip() for l in location_query.split(',')] if location_query else ["India"]

    # ── Phase 1: Fetch jobs from APIs ──────────────────────────────────────
    with st.spinner("🔍 Step 1/2 — Fetching jobs from APIs (JSearch, Adzuna, Remotive)..."):
        try:
            raw_jobs = search_jobs(roles_to_search, locs_to_search, search_internships=search_internships)

            from modules.job_search import LAST_JSEARCH_STATUS
            jsearch_failed_or_empty = False
            reason_msg = ""

            if LAST_JSEARCH_STATUS["skipped"]:
                jsearch_failed_or_empty = True
                reason_msg = "JSearch was skipped because `RAPIDAPI_KEY` is missing in the `.env` file."
            elif LAST_JSEARCH_STATUS["error"]:
                jsearch_failed_or_empty = True
                reason_msg = f"JSearch API encountered an error: {LAST_JSEARCH_STATUS['error']}"
            elif LAST_JSEARCH_STATUS["success_count"] == 0 and search_internships:
                jsearch_failed_or_empty = True
                reason_msg = "JSearch returned no internship listings for the selected roles/locations."

            st.session_state.jsearch_failed_or_empty = jsearch_failed_or_empty
            st.session_state.jsearch_reason = reason_msg
            st.session_state.search_internships_run = search_internships

            if raw_jobs:
                st.session_state.jobs = raw_jobs
                st.success(f"✅ Step 1 complete — Found {len(raw_jobs)} jobs.")
            else:
                st.session_state.jobs = []
                # ── Feature 4: Contextual no-results explanation ──────────────
                apis_tried = []
                if not LAST_JSEARCH_STATUS.get("skipped"):
                    apis_tried.append("JSearch")
                apis_tried += ["Adzuna", "Remotive"]
                tried_str = ", ".join(apis_tried)
                st.warning(
                    f"⚠️ No jobs found after searching **{tried_str}**.\n\n"
                    f"**Suggestions:**\n"
                    f"- Try a broader role name (e.g. 'Software Engineer' instead of 'Junior Python Developer')\n"
                    f"- Try a different location or use 'remote'\n"
                    f"- Uncheck 'Search for internships only' to get all job types\n"
                    f"- Check that your `.env` has a valid `RAPIDAPI_KEY`"
                )
        except Exception as e:
            st.error(str(e))

if st.session_state.get('jsearch_failed_or_empty', False):
    render_internship_guide(st.session_state.get('jsearch_reason', ''))

# ── Phase 2: Match jobs ────────────────────────────────────────────────────
if st.session_state.jobs and st.session_state.resume_analysis:
    with st.spinner("🧠 Step 2/2 — Analyzing job matches with your resume (skill + semantic matching)..."):
        # Filter by experience
        level = st.session_state.resume_analysis.get('experience_level')
        years = st.session_state.resume_analysis.get('experience_years')
        filtered_jobs = filter_jobs_by_experience(st.session_state.jobs, level, years)

        # Match jobs
        matched_jobs = []
        for j in filtered_jobs:
            match_data = calculate_match(st.session_state.resume_analysis, j)
            if match_data['skill_match'] > 0:  # Do not show jobs with zero matched skills
                matched_jobs.append({
                    "job": j,
                    "match_data": match_data
                })

        # Sort by final score
        matched_jobs.sort(key=lambda x: x['match_data']['final_score'], reverse=True)
        st.session_state.matched_jobs = matched_jobs
    
    st.markdown(f"#### Top Matching Jobs ({len(matched_jobs)})")
    
    if st.button("📊 Analyze Skill Gaps Across These Jobs"):
        gaps = analyze_skill_gaps(matched_jobs)
        if gaps:
            st.write("### Skill Gap Analysis Report")
            gaps_df = pd.DataFrame(gaps)
            st.dataframe(gaps_df, use_container_width=True)
        else:
            st.success("No missing skills found across these top jobs! You are a perfect match.")
            
    for idx, item in enumerate(matched_jobs[:10]):
        job = item['job']
        m = item['match_data']
        
        with st.container():
            st.markdown(f"""
            <div class='card'>
                <h3>{job['title']} @ {job['company']}</h3>
                <p><strong>Location:</strong> {job['location']}</p>
                <p>{job['description'][:300]}...</p>
                <p>
                    <strong>Final Match:</strong> {m['final_score']}% | 
                    <strong>Skill Match:</strong> {m['skill_match']}% | 
                    <strong>Resume Relevance:</strong> {m['resume_relevance']}% |
                    <strong>Confidence:</strong> {m['confidence']}
                </p>
                <p>
                    <strong>Matched Skills:</strong> {", ".join(m['matched_skills']) if m['matched_skills'] else 'None'}
                </p>
                <p>
                    <strong>Missing Skills:</strong> {", ".join(m['missing_skills']) if m['missing_skills'] else 'None'}
                </p>
                <a href='{job['url']}' target='_blank' style='color:#58A6FF; text-decoration:none; font-weight:bold;'>🔗 Apply Link</a>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("Save Job", key=f"save_{idx}"):
                    saved = add_application(job['title'], job['company'], job['location'], job['url'], m['final_score'])
                    if saved:
                        st.success("Job Saved to Tracker!")
                    else:
                        st.info("Job already saved.")
            with c2:
                if st.button("Tailor Resume", key=f"tailor_{idx}"):
                    st.session_state[f"tailor_res_{idx}"] = True
            with c3:
                if st.button("Cover Letter", key=f"cover_{idx}"):
                    st.session_state[f"cover_res_{idx}"] = True
            with c4:
                if st.button("Interview Prep", key=f"prep_{idx}"):
                    st.session_state[f"prep_res_{idx}"] = True
                    
            if st.session_state.get(f"tailor_res_{idx}"):
                with st.spinner("Generating resume suggestions..."):
                    res = tailor_resume(st.session_state.resume_text, job['description'], m['matched_skills'], m['missing_skills'])
                    st.json(res)
            
            if st.session_state.get(f"cover_res_{idx}"):
                with st.spinner("Generating cover letter..."):
                    cl = generate_cover_letter(
                        st.session_state.resume_analysis.get('summary', ''),
                        st.session_state.resume_analysis.get('skills', []),
                        job['title'], job['company'], job['description'],
                        is_fresher=(level == "Fresher")
                    )
                    st.text_area("Cover Letter", cl, height=300)
                    
            if st.session_state.get(f"prep_res_{idx}"):
                with st.spinner("Generating interview questions..."):
                    qs = generate_interview_questions(job['description'], st.session_state.resume_analysis.get('skills', []))
                    st.json(qs)

# ================= 4. Application Tracker =================
st.header("4. Application Tracker")
try:
    tracker_df = get_applications()
    if not tracker_df.empty:
        st.dataframe(tracker_df, use_container_width=True)
    else:
        st.info("No applications saved yet.")
except Exception:
    st.info("Application tracker not initialized.")

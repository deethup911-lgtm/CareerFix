# pyrefly: ignore [missing-import]
import streamlit as st
import os
import pandas as pd

from modules.resume_parser import extract_text
from modules.resume_analyzer import analyze_resume
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

# ================= 1. Resume Upload =================
st.header("1. Upload Resume")
uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=['pdf', 'docx'])

if uploaded_file is not None:
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
                st.success("Resume analyzed successfully!")
                st.info(f"🔍 Extracted Skills: {', '.join(analysis.get('skills', [])) if analysis.get('skills') else 'None found'}")
                if analysis.get("error_log"):
                    for err in analysis["error_log"]:
                        st.warning(f"⚠️ {err}")

# ================= 2. Candidate Overview =================
if st.session_state.resume_analysis:
    st.header("2. Candidate Overview")
    analysis = st.session_state.resume_analysis
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='card'><h4>Experience Level</h4><p>{analysis.get('experience_level')} ({analysis.get('experience_years')} yrs)</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card'><h4>Detected Domain</h4><p>{analysis.get('domain_hint', 'General')}</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card'><h4>Total Skills</h4><p>{len(analysis.get('skills', []))}</p></div>", unsafe_allow_html=True)
        
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
with col_s3:
    st.markdown("<br>", unsafe_allow_html=True)
    search_btn = st.button("Find Jobs", use_container_width=True)

if search_btn:
    with st.spinner("Searching for jobs..."):
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
        
        try:
            raw_jobs = search_jobs(roles_to_search, locs_to_search)
            if raw_jobs:
                st.session_state.jobs = raw_jobs
                st.success(f"Found {len(raw_jobs)} jobs. Analyzing and matching...")
            else:
                st.warning("No jobs found for these roles.")
        except Exception as e:
            st.error(str(e))

if st.session_state.jobs and st.session_state.resume_analysis:
    # Filter by experience
    level = st.session_state.resume_analysis.get('experience_level')
    years = st.session_state.resume_analysis.get('experience_years')
    filtered_jobs = filter_jobs_by_experience(st.session_state.jobs, level, years)
    
    # Match jobs
    matched_jobs = []
    for j in filtered_jobs:
        match_data = calculate_match(st.session_state.resume_analysis, j)
        if match_data['skill_match'] > 0: # Do not show jobs with zero matched skills
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

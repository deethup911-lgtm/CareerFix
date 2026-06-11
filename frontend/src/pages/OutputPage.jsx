import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { Search, Briefcase, FileSignature, ArrowRight, Loader, Plus, X, Filter } from 'lucide-react';
import AutocompleteInput from '../components/AutocompleteInput';

export default function OutputPage({ 
  resumeAnalysis, 
  recommendedRoles, 
  jobs, 
  setJobs, 
  matchedJobs, 
  setMatchedJobs 
}) {
  
  const safeRoles = Array.isArray(recommendedRoles) ? recommendedRoles : (recommendedRoles?.roles || []);
  const topRoles = safeRoles.slice(0, 5);
  const initialRole = topRoles.length > 0 ? (topRoles[0].role || topRoles[0]) : "";
  const [jobTitles, setJobTitles] = useState([initialRole]);
  const [locations, setLocations] = useState(["Remote", "India"]);
  const [jobTypeFilter, setJobTypeFilter] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState(null);

  React.useEffect(() => {
    if (jobTitles.length === 1 && jobTitles[0] === "" && topRoles.length > 0) {
      setJobTitles([topRoles[0].role || topRoles[0]]);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(topRoles)]);
  
  const [suggestionLoading, setSuggestionLoading] = useState({});
  const [suggestions, setSuggestions] = useState({});
  const [atsLoading, setAtsLoading] = useState({});
  const [atsResults, setAtsResults] = useState({});
  const [interviewLoading, setInterviewLoading] = useState({});
  const [interviewResults, setInterviewResults] = useState({});
  const [certLoading, setCertLoading] = useState({});
  const [certResults, setCertResults] = useState({});
  
  if (!resumeAnalysis) {
    return <Navigate to="/" />;
  }

  const handleUpdateArray = (setter, array, index, value) => {
    const newArr = [...array];
    newArr[index] = value;
    setter(newArr);
  };

  const handleRemoveItem = (setter, array, index) => {
    setter(array.filter((_, i) => i !== index));
  };

  const handleAddItem = (setter, array) => {
    setter([...array, ""]);
  };

  const handleSearch = async () => {
    const activeRoles = jobTitles.map(s => (s?.title || s || "").toString().trim()).filter(Boolean);
    const activeLocations = locations.map(s => (s || "").toString().trim()).filter(Boolean);
    
    if (activeRoles.length === 0) {
      setError("Please enter at least one Job Title to search.");
      return;
    }
    if (activeLocations.length === 0) {
      setError("Please enter at least one Location to search.");
      return;
    }

    setIsSearching(true);
    setError(null);
    setJobs([]);
    setMatchedJobs([]);
    setSuggestions({});
    setAtsResults({});
    setInterviewResults({});
    setCertResults({});
    
    try {
      const searchRes = await fetch("http://localhost:8000/api/search-jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          roles: activeRoles,
          locations: activeLocations,
          job_type: jobTypeFilter || null
        })
      });
      
      const searchData = await searchRes.json();
      if (!searchRes.ok) throw new Error(searchData.detail || "Search failed");
      
      setJobs(searchData.jobs);
      
      if (searchData.jobs.length > 0) {
        const matchRes = await fetch("http://localhost:8000/api/match-jobs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            resume_analysis: resumeAnalysis,
            jobs: searchData.jobs
          })
        });
        
        const matchData = await matchRes.json();
        if (!matchRes.ok) throw new Error(matchData.detail || "Matching failed");
        
        setMatchedJobs(matchData.matched_jobs);
      }
      
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSearching(false);
    }
  };

  const handleGetSuggestions = async (job, matchData, idx) => {
    setSuggestionLoading(prev => ({ ...prev, [idx]: true }));
    try {
      const res = await fetch("http://localhost:8000/api/get-resume-suggestions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_analysis: resumeAnalysis,
          job_description: job.description,
          job_title: job.title,
          company: job.company,
          matched_skills: matchData.matched_skills || [],
          missing_skills: matchData.missing_skills || [],
          is_top_3: idx < 3
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to get suggestions");
      setSuggestions(prev => ({ ...prev, [idx]: data }));
    } catch (err) {
      alert("Failed to get suggestions: " + err.message);
    } finally {
      setSuggestionLoading(prev => ({ ...prev, [idx]: false }));
    }
  };

  const handleGetATSScore = async (job, idx) => {
    setAtsLoading(prev => ({ ...prev, [idx]: true }));
    try {
      const res = await fetch("http://localhost:8000/api/ats-score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeAnalysis.raw_text || JSON.stringify(resumeAnalysis),
          job_description: job.description
        })
      });
      const data = await res.json();
      setAtsResults(prev => ({ ...prev, [idx]: data }));
    } catch (err) {
      alert("ATS Score failed: " + err.message);
    } finally {
      setAtsLoading(prev => ({ ...prev, [idx]: false }));
    }
  };

  const handleGetInterviewQuestions = async (job, idx) => {
    setInterviewLoading(prev => ({ ...prev, [idx]: true }));
    try {
      const res = await fetch("http://localhost:8000/api/interview-questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_title: job.title,
          job_description: job.description,
          candidate_skills: resumeAnalysis.skills || []
        })
      });
      const data = await res.json();
      setInterviewResults(prev => ({ ...prev, [idx]: data }));
    } catch (err) {
      alert("Interview questions failed: " + err.message);
    } finally {
      setInterviewLoading(prev => ({ ...prev, [idx]: false }));
    }
  };

  const handleGetCertifications = async (matchData, job, idx) => {
    setCertLoading(prev => ({ ...prev, [idx]: true }));
    try {
      const res = await fetch("http://localhost:8000/api/certifications", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          missing_skills: matchData.missing_skills || [],
          job_title: job.title
        })
      });
      const data = await res.json();
      setCertResults(prev => ({ ...prev, [idx]: data }));
    } catch (err) {
      alert("Certifications failed: " + err.message);
    } finally {
      setCertLoading(prev => ({ ...prev, [idx]: false }));
    }
  };

  const handleDownloadPDF = async (job, matchData, idx) => {
    try {
      const tailored_data = suggestions[idx];
      if (!tailored_data) return;
      
      const res = await fetch("http://localhost:8000/api/download-resume-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_analysis: resumeAnalysis,
          tailored_data: tailored_data,
          job_title: job.title,
          company: job.company
        })
      });
      
      if (!res.ok) throw new Error("Failed to generate PDF");
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Tailored_Resume_${job.company.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert("Failed to download PDF: " + err.message);
    }
  };

  const getDaysAgo = (dateStr) => {
    if (!dateStr) return null;
    try {
      const days = Math.floor((Date.now() - new Date(dateStr).getTime()) / (1000 * 60 * 60 * 24));
      if (days === 0) return "Today";
      if (days === 1) return "1 day ago";
      return `${days} days ago`;
    } catch { return null; }
  };

  const getJobTypeColor = (type) => {
    if (!type) return "#555";
    if (type === "Internship") return "#7c3aed";
    if (type === "Contract") return "#d97706";
    if (type === "Part Time") return "#0891b2";
    return "#16a34a";
  };

  const getATSGradeColor = (grade) => {
    if (grade === "Excellent") return "#16a34a";
    if (grade === "Good") return "#2563eb";
    if (grade === "Fair") return "#d97706";
    return "#dc2626";
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="card">
        <h2>Resume Overview</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p><strong>Experience Level:</strong> {resumeAnalysis.experience_level} ({resumeAnalysis.experience_years} years)</p>
            <p><strong>Domain Hint:</strong> {resumeAnalysis.domain_hint}</p>
          </div>
          <div>
            <strong>Extracted Skills:</strong>
            <div style={{ marginTop: '0.5rem' }}>
              {resumeAnalysis.skills?.map(s => (
                <span key={s} className="badge">{s}</span>
              ))}
            </div>
          </div>
        </div>
        
        {resumeAnalysis.raw_text && (
          <details style={{ marginTop: '1.5rem', padding: '1rem', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 'bold', color: 'var(--text-muted)' }}>
              📄 View Extracted Resume Text (Debug)
            </summary>
            <pre style={{ marginTop: '1rem', whiteSpace: 'pre-wrap', fontSize: '0.8rem', background: '#0d1117', padding: '1rem', borderRadius: '4px', maxHeight: '300px', overflowY: 'auto' }}>
              {resumeAnalysis.raw_text}
            </pre>
          </details>
        )}
      </div>

      <div className="card">
        <h2>Find Recommended Jobs</h2>
        <div className="grid grid-cols-2 gap-4 items-start">
          <div className="input-group">
            <label style={{ display: 'flex', justifyContent: 'space-between' }}>
              Job Titles
              <button className="btn btn-outline" onClick={() => handleAddItem(setJobTitles, jobTitles)} style={{ padding: '0.25rem 0.5rem', display: 'flex', alignItems: 'center', fontSize: '0.8rem', gap: '0.25rem' }}>
                <Plus size={14}/> Add
              </button>
            </label>
            {jobTitles.map((title, idx) => (
              <div key={idx} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <AutocompleteInput 
                  className="input-control" 
                  value={title} 
                  placeholder="e.g. AI Engineer"
                  mode="local"
                  localSuggestions={safeRoles.map(r => r.role || r) || []}
                  onChange={val => handleUpdateArray(setJobTitles, jobTitles, idx, val)} 
                />
                <button 
                  onClick={() => handleRemoveItem(setJobTitles, jobTitles, idx)} 
                  style={{ background: 'rgba(218,54,51,0.1)', color: '#DA3633', border: 'none', padding: '0 0.5rem', borderRadius: '4px', cursor: 'pointer' }}
                >
                  <X size={16}/>
                </button>
              </div>
            ))}
            {topRoles.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>AI Suggestions:</span>
                {topRoles.map((r, i) => {
                  const roleName = r.role || r;
                  return (
                    <button
                      key={i}
                      onClick={() => {
                        if (jobTitles.length === 1 && jobTitles[0] === "") {
                          setJobTitles([roleName]);
                        } else if (!jobTitles.includes(roleName)) {
                          setJobTitles([...jobTitles, roleName]);
                        }
                      }}
                      style={{
                        fontSize: '0.75rem',
                        padding: '0.2rem 0.6rem',
                        borderRadius: '999px',
                        background: 'rgba(37, 99, 235, 0.1)',
                        color: '#2563eb',
                        border: '1px solid rgba(37, 99, 235, 0.2)',
                        cursor: 'pointer',
                        transition: 'background 0.2s'
                      }}
                      onMouseOver={e => e.target.style.background = 'rgba(37, 99, 235, 0.2)'}
                      onMouseOut={e => e.target.style.background = 'rgba(37, 99, 235, 0.1)'}
                    >
                      + {roleName}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
          
          <div className="input-group">
            <label style={{ display: 'flex', justifyContent: 'space-between' }}>
              Locations
              <button className="btn btn-outline" onClick={() => handleAddItem(setLocations, locations)} style={{ padding: '0.25rem 0.5rem', display: 'flex', alignItems: 'center', fontSize: '0.8rem', gap: '0.25rem' }}>
                <Plus size={14}/> Add
              </button>
            </label>
            {locations.map((loc, idx) => (
              <div key={idx} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <AutocompleteInput 
                  className="input-control" 
                  value={loc} 
                  placeholder="e.g. India or Remote"
                  mode="api"
                  onChange={val => handleUpdateArray(setLocations, locations, idx, val)} 
                />
                <button 
                  onClick={() => handleRemoveItem(setLocations, locations, idx)} 
                  style={{ background: 'rgba(218,54,51,0.1)', color: '#DA3633', border: 'none', padding: '0 0.5rem', borderRadius: '4px', cursor: 'pointer' }}
                >
                  <X size={16}/>
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Job Type Filter */}
        <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <Filter size={16} style={{ color: 'var(--text-muted)' }}/>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Job Type:</span>
          {["", "Full Time", "Part Time", "Contract", "Internship"].map(type => (
            <button
              key={type}
              onClick={() => setJobTypeFilter(type)}
              style={{
                padding: '0.25rem 0.75rem',
                borderRadius: '999px',
                border: '1px solid var(--border-color)',
                background: jobTypeFilter === type ? 'var(--primary-green)' : 'transparent',
                color: jobTypeFilter === type ? 'white' : 'var(--text-muted)',
                cursor: 'pointer',
                fontSize: '0.8rem',
                transition: 'all 0.2s'
              }}
            >
              {type || "All"}
            </button>
          ))}
        </div>
        
        {error && <div style={{ color: '#d32f2f', marginBottom: '1rem', marginTop: '1rem' }}>{error}</div>}
        
        <button 
          className="btn btn-primary" 
          onClick={handleSearch} 
          disabled={isSearching}
          style={{ marginTop: '1rem' }}
        >
          {isSearching ? 'Searching...' : <><Search size={18} /> Search Jobs</>}
        </button>
      </div>

      {matchedJobs.length > 0 && (
        <>
          <div className="flex justify-between items-center mb-4">
            <h2>Top Matches ({matchedJobs.length} jobs)</h2>
          </div>
          
          <div className="grid" style={{ gap: '1rem' }}>
            {matchedJobs.map((m, idx) => (
              <div key={idx} className="card" style={{ marginBottom: 0 }}>
                <div className="flex justify-between items-center">
                  <h3 style={{ margin: 0 }}>{m.job.title} @ {m.job.company}</h3>
                  <span className="badge" style={{ fontSize: '1rem', background: 'var(--primary-green)', color: 'white' }}>
                    {m.match_data.final_score}% Match
                  </span>
                </div>
                
                {/* Meta row: location, exp, source */}
                <p style={{ margin: '0.5rem 0', color: 'var(--text-muted)', display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
                  📍 {m.job.location} &nbsp;|&nbsp; 🎓 <strong>Req Exp:</strong> {m.match_data.job_experience_requirement} &nbsp;|&nbsp; 🏢 <strong>Source:</strong> {m.job.source || "Unknown"}
                </p>

                {/* Badges Row */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.25rem' }}>
                  {m.job.job_type && (
                    <span style={{ padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', border: `1px solid ${getJobTypeColor(m.job.job_type)}`, color: getJobTypeColor(m.job.job_type) }}>
                      {m.job.job_type}
                    </span>
                  )}
                  {m.job.salary && (
                    <span style={{ padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', border: '1px solid #16a34a', color: '#16a34a' }}>
                      💰 {m.job.salary}
                    </span>
                  )}
                  {m.job.date_posted && getDaysAgo(m.job.date_posted) && (
                    <span style={{ padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                      🕐 {getDaysAgo(m.job.date_posted)}
                    </span>
                  )}
                </div>
                
                <div className="flex" style={{ flexWrap: 'wrap', gap: '1rem', marginTop: '0.75rem', fontSize: '0.9rem' }}>
                  <span className="badge badge-outline" style={{ borderColor: 'var(--primary-green)', color: 'var(--primary-green)' }}>
                    Skill Match: {m.match_data.skill_match}%
                  </span>
                  <span className="badge badge-outline" style={{ borderColor: '#60a5fa', color: '#60a5fa' }}>
                    Exp Match: {m.match_data.experience_match}%
                  </span>
                </div>
                
                {m.match_data.rejection_reasons && m.match_data.rejection_reasons.length > 0 && (
                  <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: 'rgba(218, 54, 51, 0.1)', borderLeft: '4px solid #DA3633', borderRadius: '4px' }}>
                    <strong style={{ color: '#DA3633', fontSize: '0.9rem' }}>Match Penalties:</strong>
                    <ul style={{ margin: '0.25rem 0 0 0', paddingLeft: '1.25rem', fontSize: '0.85rem', color: '#ff7b72' }}>
                      {m.match_data.rejection_reasons.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                <div className="flex" style={{ flexWrap: 'wrap', gap: '0.5rem', marginTop: '1rem' }}>
                  {m.match_data.missing_skills?.slice(0, 5).map(s => (
                    <span key={s} className="badge badge-outline" style={{ borderColor: '#fca5a5', color: '#dc2626' }}>Missing: {s}</span>
                  ))}
                </div>
                
                {/* Action Buttons */}
                <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <a href={m.job.url} target="_blank" rel="noreferrer" className="btn btn-primary" style={{ padding: '0.5rem 1rem' }}>
                    Apply Now
                  </a>
                  
                  <button 
                    className="btn btn-outline" 
                    onClick={() => handleGetSuggestions(m.job, m.match_data, idx)}
                    disabled={suggestionLoading[idx]}
                    style={{ padding: '0.5rem 1rem' }}
                  >
                    {suggestionLoading[idx] ? 'Analyzing...' : '✨ AI Resume Tips'}
                  </button>

                  <button 
                    className="btn btn-outline" 
                    onClick={() => handleGetATSScore(m.job, idx)}
                    disabled={atsLoading[idx]}
                    style={{ padding: '0.5rem 1rem' }}
                  >
                    {atsLoading[idx] ? 'Scoring...' : '🤖 ATS Score'}
                  </button>

                  <button 
                    className="btn btn-outline" 
                    onClick={() => handleGetInterviewQuestions(m.job, idx)}
                    disabled={interviewLoading[idx]}
                    style={{ padding: '0.5rem 1rem' }}
                  >
                    {interviewLoading[idx] ? 'Loading...' : '🎯 Interview Prep'}
                  </button>

                  {m.match_data.missing_skills?.length > 0 && (
                    <button 
                      className="btn btn-outline" 
                      onClick={() => handleGetCertifications(m.match_data, m.job, idx)}
                      disabled={certLoading[idx]}
                      style={{ padding: '0.5rem 1rem' }}
                    >
                      {certLoading[idx] ? 'Loading...' : '🎓 Certifications'}
                    </button>
                  )}
                </div>
                
                {/* ATS Score Panel */}
                {atsResults[idx] && (
                  <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(37,99,235,0.08)', borderRadius: '8px', border: '1px solid rgba(37,99,235,0.3)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                      <h4 style={{ margin: 0, color: '#60a5fa', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        ATS Score Simulation
                      </h4>
                      <span style={{ fontSize: '1.25rem', fontWeight: 'bold', color: getATSGradeColor(atsResults[idx].grade) }}>
                        {atsResults[idx].ats_score}/100 — {atsResults[idx].grade}
                      </span>
                    </div>
                    
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', fontSize: '0.85rem', marginBottom: '1rem' }}>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Keywords ({atsResults[idx].total_jd_keywords || 0} found)</span>
                        <strong>{atsResults[idx].breakdown.keyword_score}/{atsResults[idx].breakdown.keyword_max} pts</strong>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Sections</span>
                        <strong>{atsResults[idx].breakdown.section_score}/{atsResults[idx].breakdown.section_max} pts</strong>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Formatting</span>
                        <strong>{atsResults[idx].breakdown.format_score}/{atsResults[idx].breakdown.format_max} pts</strong>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Length</span>
                        <strong>{atsResults[idx].breakdown.length_score}/{atsResults[idx].breakdown.length_max} pts</strong>
                      </div>
                    </div>
                    
                    {atsResults[idx].format_warnings?.length > 0 && (
                      <div style={{ color: '#fbbf24', fontSize: '0.85rem', marginBottom: '0.75rem', padding: '0.5rem', background: 'rgba(251, 191, 36, 0.1)', borderRadius: '4px' }}>
                        <strong>Format Warnings:</strong> {atsResults[idx].format_warnings.join(" | ")}
                      </div>
                    )}
                    
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '0 0 1rem 0' }}>
                      <em>{atsResults[idx].length_note}</em>
                    </p>
                    
                    {atsResults[idx].missing_keywords?.length > 0 && (
                      <div style={{ marginTop: '0.75rem' }}>
                        <strong style={{ fontSize: '0.85rem', color: '#fca5a5' }}>Top Missing Skills/Keywords:</strong>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.5rem' }}>
                          {atsResults[idx].missing_keywords.slice(0, 15).map(kw => (
                            <span key={kw} style={{ padding: '0.15rem 0.5rem', background: 'rgba(220, 38, 38, 0.1)', color: '#fca5a5', borderRadius: '4px', fontSize: '0.75rem', border: '1px solid rgba(220, 38, 38, 0.2)' }}>
                              {kw}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Interview Questions Panel */}
                {interviewResults[idx] && (
                  <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(124,58,237,0.08)', borderRadius: '8px', border: '1px solid rgba(124,58,237,0.3)' }}>
                    <h4 style={{ margin: '0 0 1rem 0', color: '#a78bfa' }}>🎯 Interview Prep Questions</h4>
                    {interviewResults[idx].questions?.map((q, i) => (
                      <div key={i} style={{ marginBottom: '1rem', paddingBottom: '0.75rem', borderBottom: i < interviewResults[idx].questions.length - 1 ? '1px solid rgba(124,58,237,0.2)' : 'none' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                          <span style={{ fontSize: '0.7rem', padding: '0.15rem 0.5rem', borderRadius: '999px', background: q.type === 'Technical' ? 'rgba(37,99,235,0.2)' : 'rgba(220,38,38,0.2)', color: q.type === 'Technical' ? '#60a5fa' : '#fca5a5', flexShrink: 0, marginTop: '2px' }}>
                            {q.type || "General"}
                          </span>
                          <strong style={{ fontSize: '0.9rem' }}>{q.question}</strong>
                        </div>
                        {q.tip && <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem', color: '#a78bfa' }}>💡 Tip: {q.tip}</p>}
                      </div>
                    ))}
                  </div>
                )}

                {/* Certifications Panel */}
                {certResults[idx] && (
                  <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(217,119,6,0.08)', borderRadius: '8px', border: '1px solid rgba(217,119,6,0.3)' }}>
                    <h4 style={{ margin: '0 0 1rem 0', color: '#fbbf24' }}>🎓 Recommended Certifications to Close Skill Gaps</h4>
                    {certResults[idx].certifications?.map((cert, i) => (
                      <div key={i} style={{ marginBottom: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                        <div>
                          <strong style={{ fontSize: '0.9rem' }}>{cert.name}</strong>
                          <span style={{ marginLeft: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>by {cert.provider}</span>
                          <p style={{ margin: '0.1rem 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>Closes gap: <em>{cert.skill_addressed}</em> | ⏱ {cert.duration}</p>
                        </div>
                        {cert.url && (
                          <a href={cert.url} target="_blank" rel="noreferrer" style={{ fontSize: '0.8rem', color: '#fbbf24', textDecoration: 'none', border: '1px solid #fbbf24', padding: '0.2rem 0.6rem', borderRadius: '4px' }}>
                            Learn →
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* AI Resume Suggestions Panel */}
                {suggestions[idx] && (
                  <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: 'var(--light-green)', borderRadius: 'var(--radius-sm)' }}>
                    <h4 style={{ color: 'var(--primary-green)', marginBottom: '1rem' }}>
                      {idx < 3 ? "✨ Fully Tailored Resume" : "Tailoring Suggestions for this Role"}
                    </h4>
                    
                    {suggestions[idx].tailored_summary ? (
                      <>
                        <div style={{ marginBottom: '1rem' }}>
                          <strong>Tailored Summary:</strong>
                          <p style={{ margin: '0.25rem 0 0 0', fontStyle: 'italic' }}>{suggestions[idx].tailored_summary}</p>
                        </div>
                        <div style={{ marginBottom: '1rem' }}>
                          <strong>Tailored Experience:</strong>
                          <ul style={{ margin: '0.25rem 0 0 0', paddingLeft: '1.5rem' }}>
                            {suggestions[idx].tailored_experience?.map((b, i) => (
                              <li key={i}>{b}</li>
                            ))}
                          </ul>
                        </div>
                        <div style={{ marginBottom: '1rem' }}>
                          <strong>Updated Skills:</strong>
                          <p style={{ margin: '0.25rem 0 0 0' }}>{suggestions[idx].updated_skills?.join(", ")}</p>
                        </div>
                      </>
                    ) : (
                      <>
                        <div style={{ marginBottom: '1rem' }}>
                          <strong>Summary Rewrite:</strong>
                          <p style={{ margin: '0.25rem 0 0 0', fontStyle: 'italic' }}>{suggestions[idx].summary_suggestion}</p>
                        </div>
                        
                        <div style={{ marginBottom: '1rem' }}>
                          <strong>Project Bullet Fixes:</strong>
                          <ul style={{ margin: '0.25rem 0 0 0', paddingLeft: '1.5rem' }}>
                            {suggestions[idx].project_bullet_suggestions?.map((b, i) => (
                              <li key={i}>{b}</li>
                            ))}
                          </ul>
                        </div>
                        
                        <div style={{ marginBottom: '1rem' }}>
                          <strong>Skills Formatting:</strong>
                          <ul style={{ margin: '0.25rem 0 0 0', paddingLeft: '1.5rem' }}>
                            {suggestions[idx].skills_section_suggestion?.map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>
                        
                        {suggestions[idx].course_recommendations?.length > 0 && (
                          <div style={{ marginBottom: '1rem' }}>
                            <strong>Course Recommendations:</strong>
                            <ul style={{ margin: '0.25rem 0 0 0', paddingLeft: '1.5rem', color: '#0891b2' }}>
                              {suggestions[idx].course_recommendations.map((c, i) => (
                                <li key={i}>{c}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </>
                    )}
                    
                    <div>
                      <strong>Missing ATS Keywords (Add if true):</strong>
                      <p style={{ margin: '0.25rem 0 0 0', color: '#dc2626' }}>
                        {suggestions[idx].ats_keywords_to_add?.join(", ")}
                      </p>
                    </div>

                    {/* Download PDF Button */}
                    <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(22, 163, 74, 0.2)' }}>
                      <button 
                        onClick={() => handleDownloadPDF(m.job, m.match_data, idx)}
                        style={{ 
                          padding: '0.5rem 1rem', 
                          background: 'var(--primary-green)', 
                          color: 'white', 
                          border: 'none', 
                          borderRadius: '4px', 
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          fontWeight: 'bold'
                        }}
                      >
                        📄 Download Tailored Resume (PDF)
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

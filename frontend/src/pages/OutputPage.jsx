import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { Search, Briefcase, FileSignature, ArrowRight, Loader, Plus, X } from 'lucide-react';
import AutocompleteInput from '../components/AutocompleteInput';

export default function OutputPage({ 
  resumeAnalysis, 
  recommendedRoles, 
  jobs, 
  setJobs, 
  matchedJobs, 
  setMatchedJobs 
}) {
  
  const initialRoles = recommendedRoles?.length > 0 ? recommendedRoles.map(r => r.role) : [""];
  const [jobTitles, setJobTitles] = useState(initialRoles);
  const [locations, setLocations] = useState(["Remote", "India"]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState(null);
  
  // Track loading state and fetched suggestions per job index
  const [suggestionLoading, setSuggestionLoading] = useState({});
  const [suggestions, setSuggestions] = useState({});
  
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
    setIsSearching(true);
    setError(null);
    setJobs([]);
    setMatchedJobs([]);
    setSuggestions({});
    
    try {
      const searchRes = await fetch("http://localhost:8000/api/search-jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          roles: jobTitles.map(s => s.trim()).filter(Boolean),
          locations: locations.map(s => s.trim()).filter(Boolean)
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
          missing_skills: matchData.missing_skills || []
        })
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to get suggestions");
      
      setSuggestions(prev => ({ ...prev, [idx]: data }));
    } catch (err) {
      console.error(err);
      alert("Failed to get suggestions: " + err.message);
    } finally {
      setSuggestionLoading(prev => ({ ...prev, [idx]: false }));
    }
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
                  localSuggestions={recommendedRoles?.map(r => r.role) || []}
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
        
        {error && <div style={{ color: '#d32f2f', marginBottom: '1rem' }}>{error}</div>}
        
        <button 
          className="btn btn-primary" 
          onClick={handleSearch} 
          disabled={isSearching}
        >
          {isSearching ? 'Searching...' : <><Search size={18} /> Search Jobs</>}
        </button>
      </div>

      {matchedJobs.length > 0 && (
        <>
          <div className="flex justify-between items-center mb-4">
            <h2>Top Matches</h2>
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
                <p style={{ margin: '0.5rem 0', color: 'var(--text-muted)' }}>
                  📍 {m.job.location} &nbsp;|&nbsp; 🎓 <strong>Req Exp:</strong> {m.match_data.job_experience_requirement} &nbsp;|&nbsp; 🏢 <strong>Source:</strong> {m.job.source || "Unknown"}
                </p>
                
                <div className="flex" style={{ flexWrap: 'wrap', gap: '1rem', marginTop: '0.5rem', fontSize: '0.9rem' }}>
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
                
                <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '1rem' }}>
                  <a href={m.job.url} target="_blank" rel="noreferrer" className="btn btn-primary" style={{ padding: '0.5rem 1rem' }}>
                    Apply Now
                  </a>
                  
                  <button 
                    className="btn btn-outline" 
                    onClick={() => handleGetSuggestions(m.job, m.match_data, idx)}
                    disabled={suggestionLoading[idx]}
                    style={{ padding: '0.5rem 1rem' }}
                  >
                    {suggestionLoading[idx] ? 'Analyzing...' : '✨ Get AI Resume Suggestions'}
                  </button>
                </div>
                
                {/* Suggestions Section */}
                {suggestions[idx] && (
                  <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: 'var(--light-green)', borderRadius: 'var(--radius-sm)' }}>
                    <h4 style={{ color: 'var(--primary-green)', marginBottom: '1rem' }}>Tailoring Suggestions for this Role</h4>
                    
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
                    
                    <div>
                      <strong>Missing ATS Keywords (Add if true):</strong>
                      <p style={{ margin: '0.25rem 0 0 0', color: '#dc2626' }}>
                        {suggestions[idx].ats_keywords_to_add?.join(", ")}
                      </p>
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

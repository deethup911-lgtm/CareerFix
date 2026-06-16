import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, Type } from 'lucide-react';

export default function UploadPage({ setResumeAnalysis, setRecommendedRoles, setJobs, setMatchedJobs }) {
  const [inputType, setInputType] = useState('upload'); // 'upload' or 'paste'
  const [file, setFile] = useState(null);
  const [pastedText, setPastedText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected && (selected.type === 'application/pdf' || selected.name.endsWith('.docx'))) {
      setFile(selected);
      setError(null);
    } else {
      setFile(null);
      setError("Please select a valid PDF or DOCX file.");
    }
  };

  const handleUploadClick = () => {
    if (inputType === 'upload') {
      fileInputRef.current.click();
    }
  };

  const handleAnalyze = async () => {
    if (inputType === 'upload' && !file) return;
    if (inputType === 'paste' && !pastedText.trim()) return;
    
    setIsUploading(true);
    setError(null);
    
    const formData = new FormData();
    if (inputType === 'upload') {
      formData.append("file", file);
    } else {
      formData.append("text", pastedText);
    }
    
    try {
      const response = await fetch("http://localhost:8000/api/analyze-resume", {
        method: "POST",
        body: formData,
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || "Analysis failed");
      }
      
      setResumeAnalysis(data.analysis);
      setRecommendedRoles(data.recommended_roles);
      if (setJobs) setJobs([]);
      if (setMatchedJobs) setMatchedJobs([]);
      
      // Navigate to output page
      navigate('/output');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="card text-center" style={{ maxWidth: '600px', margin: '4rem auto' }}>
      <h2>Welcome to CareerFix</h2>
      <p className="mb-4" style={{ color: 'var(--text-muted)' }}>
        Provide your resume to automatically extract your skills, discover matching job roles, and generate a tailored resume.
      </p>

      {/* Toggle Buttons */}
      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginBottom: '2rem' }}>
        <button 
          className={`btn ${inputType === 'upload' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => { setInputType('upload'); setError(null); }}
          style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <UploadCloud size={18} /> Upload PDF
        </button>
        <button 
          className={`btn ${inputType === 'paste' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => { setInputType('paste'); setError(null); }}
          style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <Type size={18} /> Paste Text
        </button>
      </div>
      
      {/* Dynamic Input Area */}
      {inputType === 'upload' ? (
        <div 
          className="upload-zone" 
          onClick={handleUploadClick}
        >
          <UploadCloud size={48} className="upload-icon" />
          {file ? (
            <div>
              <h4 style={{ margin: 0, color: 'var(--text-main)' }}>{file.name}</h4>
              <p style={{ margin: '0.5rem 0 0', fontSize: '0.875rem' }}>Click to change file</p>
            </div>
          ) : (
            <div>
              <h4 style={{ margin: 0 }}>Click to browse</h4>
              <p style={{ margin: '0.5rem 0 0', fontSize: '0.875rem' }}>PDF or DOCX only</p>
            </div>
          )}
          <input 
            type="file" 
            ref={fileInputRef} 
            style={{ display: 'none' }} 
            accept=".pdf,.docx"
            onChange={handleFileChange}
          />
        </div>
      ) : (
        <div style={{ textAlign: 'left' }}>
          <textarea
            value={pastedText}
            onChange={(e) => setPastedText(e.target.value)}
            placeholder="Paste your resume text here..."
            style={{
              width: '100%',
              minHeight: '200px',
              padding: '1rem',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-secondary)',
              color: 'var(--text-main)',
              fontSize: '1rem',
              resize: 'vertical',
              fontFamily: 'inherit'
            }}
          />
        </div>
      )}
      
      {error && (
        <div style={{ color: '#d32f2f', marginTop: '1rem', fontWeight: 500 }}>
          {error}
        </div>
      )}
      
      <div style={{ marginTop: '2rem' }}>
        <button 
          className="btn btn-primary" 
          disabled={ (inputType === 'upload' && !file) || (inputType === 'paste' && !pastedText.trim()) || isUploading }
          onClick={handleAnalyze}
          style={{ width: '100%', padding: '1rem', fontSize: '1.1rem' }}
        >
          {isUploading ? (
            <>Analyzing...</>
          ) : (
            <>
              <FileText size={20} />
              Analyze Resume
            </>
          )}
        </button>
      </div>
    </div>
  );
}

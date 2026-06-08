import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import OutputPage from './pages/OutputPage';
import { Briefcase } from 'lucide-react';
import './index.css';

function App() {
  // Global State (Since we are using React State instead of MongoDB)
  const [resumeAnalysis, setResumeAnalysis] = useState(null);
  const [recommendedRoles, setRecommendedRoles] = useState([]);
  
  // Jobs and Matches
  const [jobs, setJobs] = useState([]);
  const [matchedJobs, setMatchedJobs] = useState([]);

  return (
    <Router>
      <header className="header">
        <Link to="/" className="header-logo">
          <Briefcase size={28} />
          CareerFix
        </Link>
      </header>
      
      <main className="container">
        <Routes>
          <Route path="/" element={
            <UploadPage 
              setResumeAnalysis={setResumeAnalysis} 
              setRecommendedRoles={setRecommendedRoles} 
            />
          } />
          <Route path="/output" element={
            <OutputPage 
              resumeAnalysis={resumeAnalysis} 
              recommendedRoles={recommendedRoles}
              jobs={jobs}
              setJobs={setJobs}
              matchedJobs={matchedJobs}
              setMatchedJobs={setMatchedJobs}
            />
          } />
        </Routes>
      </main>
    </Router>
  );
}

export default App;

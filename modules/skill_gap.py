def analyze_skill_gaps(matched_jobs):
    # Collect all missing skills across jobs
    missing_freq = {}
    for job in matched_jobs:
        for skill in job['match_data']['missing_skills']:
            missing_freq[skill] = missing_freq.get(skill, 0) + 1
            
    total_jobs = len(matched_jobs)
    
    gap_report = []
    for skill, freq in missing_freq.items():
        priority = "Low"
        if freq >= total_jobs * 0.5 and freq > 1:
            priority = "High"
        elif freq >= total_jobs * 0.25:
            priority = "Medium"
            
        gap_report.append({
            "skill": skill,
            "frequency": freq,
            "priority": priority
        })
        
    # Sort by priority and frequency
    priority_order = {"High": 3, "Medium": 2, "Low": 1}
    gap_report.sort(key=lambda x: (priority_order[x['priority']], x['frequency']), reverse=True)
    
    return gap_report

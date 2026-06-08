import pandas as pd
import os
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_FILE = os.path.join(base_dir, 'data', 'applications.csv')

def init_tracker():
    if not os.path.exists(os.path.dirname(TRACKER_FILE)):
        os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
    if not os.path.exists(TRACKER_FILE):
        df = pd.DataFrame(columns=[
            "Job Title", "Company", "Location", "Apply Link", 
            "Match Score", "Status", "Date Added", "Notes"
        ])
        df.to_csv(TRACKER_FILE, index=False)

def add_application(job_title, company, location, link, score, status="Saved", notes=""):
    init_tracker()
    df = pd.read_csv(TRACKER_FILE)
    
    # Check if already exists
    if link in df["Apply Link"].values:
        return False # already saved
        
    new_row = {
        "Job Title": job_title,
        "Company": company,
        "Location": location,
        "Apply Link": link,
        "Match Score": score,
        "Status": status,
        "Date Added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Notes": notes
    }
    df.loc[len(df)] = new_row
    df.to_csv(TRACKER_FILE, index=False)
    return True

def get_applications():
    init_tracker()
    return pd.read_csv(TRACKER_FILE)

def update_status(link, new_status):
    init_tracker()
    df = pd.read_csv(TRACKER_FILE)
    if link in df["Apply Link"].values:
        df.loc[df["Apply Link"] == link, "Status"] = new_status
        df.to_csv(TRACKER_FILE, index=False)
        return True
    return False

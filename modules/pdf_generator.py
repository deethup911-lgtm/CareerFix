from fpdf import FPDF
import io

class ResumePDF(FPDF):
    def header(self):
        # We will keep it simple and clean
        pass
        
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def generate_resume_pdf(analysis: dict, tailored_data: dict, job_title: str, company: str) -> bytes:
    pdf = ResumePDF()
    pdf.add_page()
    
    # Colors (Dark grey for text, Green for accents)
    pdf.set_text_color(50, 50, 50)
    
    # Contact Info
    contact = analysis.get("contact_info", {})
    name = contact.get("name") or analysis.get("name") or "Candidate Name"
    email = contact.get("email", "")
    phone = contact.get("phone", "")
    linkedin = contact.get("linkedin", "")
    
    contact_str = " | ".join(filter(None, [email, phone, linkedin]))
    
    # Title / Name
    pdf.set_font("helvetica", "B", 24)
    pdf.cell(0, 10, name, ln=True, align="C")
    
    if contact_str:
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 6, contact_str, ln=True, align="C")
    
    # Subtitle
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(46, 139, 87) # Sea Green
    pdf.cell(0, 10, f"Tailored for: {job_title} @ {company}", ln=True, align="C")
    pdf.ln(5)
    
    # Summary
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 8, "Professional Summary", ln=True)
    pdf.set_font("helvetica", "", 11)
    
    summary_text = tailored_data.get("tailored_summary") or tailored_data.get("summary") or tailored_data.get("summary_suggestion") or analysis.get("summary", "")
    # Remove markdown bold if any
    summary_text = summary_text.replace("**", "")
    pdf.multi_cell(0, 6, summary_text)
    pdf.ln(5)
    
    # Skills
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 8, "Core Skills", ln=True)
    pdf.set_font("helvetica", "", 11)
    
    # Combine original and new ATS keywords/updated skills
    skills = tailored_data.get("updated_skills") or analysis.get("skills", [])
    new_skills = tailored_data.get("ats_keywords_to_add") or tailored_data.get("ats_keywords_added") or []
    all_skills = list(set(skills + new_skills))
    
    skills_str = ", ".join(all_skills)
    pdf.multi_cell(0, 6, skills_str)
    pdf.ln(5)
    
    # Projects / Experience
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 8, "Experience & Projects", ln=True)
    pdf.set_font("helvetica", "", 11)
    
    projects = analysis.get("projects", [])
    project_suggestions = tailored_data.get("tailored_experience") or tailored_data.get("projects") or tailored_data.get("project_bullet_suggestions") or []
    
    # Just print the tailored suggestions if available, else original
    if project_suggestions:
        for proj in project_suggestions:
            pdf.multi_cell(0, 6, "- " + proj.replace("**", ""))
            pdf.ln(2)
    else:
        for proj in projects:
            pdf.multi_cell(0, 6, "- " + proj.replace("**", ""))
            pdf.ln(2)
            
    # Education
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 8, "Education", ln=True)
    pdf.set_font("helvetica", "", 11)
    edu = analysis.get("education", "Degree Information")
    pdf.multi_cell(0, 6, edu)
    
    # Output to bytes
    return pdf.output(dest="S")

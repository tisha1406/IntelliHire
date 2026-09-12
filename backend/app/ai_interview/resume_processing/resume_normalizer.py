from app.ai_interview.resume_processing.schemas import NormalizedResumeText
import re

class ResumeNormalizer:
    # A simple deterministic set of keywords to identify sections.
    SECTION_KEYWORDS = {
        "summary": [r"\bprofessional\s+summary\b", r"\bsummary\b", r"\bprofile\b", r"\bobjective\b"],
        "education": [r"\beducation\b", r"\bacademic\s+background\b"],
        "experience": [r"\bexperience\b", r"\bemployment\s+history\b", r"\bwork\s+experience\b", r"\bprofessional\s+experience\b", r"\bemployment\b"],
        "skills": [r"\bskills\b", r"\btechnical\s+skills\b", r"\bcore\s+competencies\b"],
        "projects": [r"\bprojects\b", r"\bpersonal\s+projects\b", r"\bacademic\s+projects\b"],
        "certifications": [r"\bcertifications\b", r"\blicenses\b", r"\bcertificates\b"],
        "achievements": [r"\bachievements\b", r"\bawards\b", r"\bhonors\b"]
    }

    @staticmethod
    def normalize(cleaned_text: str) -> NormalizedResumeText:
        lines = cleaned_text.split('\n')
        
        current_section = "unclassified_text"
        sections_data = {
            "unclassified_text": []
        }
        
        for line in lines:
            line_stripped = line.strip()
            # Very short lines are often headers.
            if len(line_stripped) < 50:
                identified_section = None
                for sec, patterns in ResumeNormalizer.SECTION_KEYWORDS.items():
                    for pattern in patterns:
                        # Match exactly or with trailing colons
                        if re.match(rf"^{pattern}:?$", line_stripped, re.IGNORECASE):
                            identified_section = sec
                            break
                    if identified_section:
                        break
                
                if identified_section:
                    current_section = identified_section
                    if current_section not in sections_data:
                        sections_data[current_section] = []
                    continue # Skip adding the header line itself
                    
            if current_section not in sections_data:
                sections_data[current_section] = []
            sections_data[current_section].append(line)
            
        result_sections = {}
        for k, v in sections_data.items():
            if k != "unclassified_text" and v:
                result_sections[k] = "\n".join(v).strip()
                
        unclass_text = "\n".join(sections_data["unclassified_text"]).strip()
        
        return NormalizedResumeText(
            sections=result_sections,
            unclassified_text=unclass_text
        )

from abc import ABC, abstractmethod
from app.ai_interview.schemas.resume import StructuredResume, Education, Experience, Skill, Project, Certification
from app.ai_interview.resume_processing.schemas import NormalizedResumeText
import re

class ResumeStructuredExtractor(ABC):
    @abstractmethod
    def extract(self, normalized_text: NormalizedResumeText) -> StructuredResume:
        pass

class DeterministicResumeStructuredExtractor(ResumeStructuredExtractor):
    """
    Deterministic development/testing implementation.
    Provides predictable baseline parsing. Not equivalent to semantic LLM extraction.
    """
    def extract(self, normalized_text: NormalizedResumeText) -> StructuredResume:
        resume = StructuredResume()
        
        # Summary
        if "summary" in normalized_text.sections:
            resume.professional_summary = normalized_text.sections["summary"]
            
        # Education
        if "education" in normalized_text.sections:
            # Very basic extraction: each non-empty line could be considered a degree for baseline testing.
            lines = normalized_text.sections["education"].split('\n')
            for line in lines:
                if line.strip():
                    resume.education.append(Education(degree=line.strip(), institution=""))
                    
        # Experience
        if "experience" in normalized_text.sections:
            lines = normalized_text.sections["experience"].split('\n')
            for line in lines:
                if line.strip():
                    resume.experience.append(Experience(title=line.strip(), org=""))

        # Skills
        if "skills" in normalized_text.sections:
            # Split by commas or newlines
            skills_text = normalized_text.sections["skills"]
            items = re.split(r'[,\n]', skills_text)
            for item in items:
                if item.strip():
                    resume.skills.append(Skill(name=item.strip()))
                    
        # Projects
        if "projects" in normalized_text.sections:
            lines = normalized_text.sections["projects"].split('\n')
            for line in lines:
                if line.strip():
                    resume.projects.append(Project(name=line.strip(), description=""))

        # Certifications
        if "certifications" in normalized_text.sections:
            lines = normalized_text.sections["certifications"].split('\n')
            for line in lines:
                if line.strip():
                    resume.certifications.append(Certification(name=line.strip(), issuer=""))
                    
        return resume

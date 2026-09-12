"""
Phase 9 — Resume Context Bridge
===============================
Adapts persisted MongoDB resume analysis data into the strict
CandidateInterviewContext schema required by the Interview Engine.
"""
from typing import Dict, Any

from app.ai_interview.resume_processing.schemas import (
    CandidateInterviewContext,
    ExtractionMetadata,
    ExtractionQualityStatus,
)
from app.ai_interview.schemas.resume import (
    StructuredResume,
    Education,
    Experience,
    Skill,
    Project,
    Certification
)

class ResumeContextBridge:
    @staticmethod
    def build(resume_doc: Dict[str, Any], candidate_id: str) -> CandidateInterviewContext:
        """
        Converts the unstructured dict stored in MongoDB `resume_analyses`
        into the engine's strongly-typed CandidateInterviewContext.
        """
        # Data might be nested under 'extracted_data' depending on pipeline phase
        data = resume_doc.get("extracted_data", resume_doc)

        # Map Education
        education_list = []
        for ed in data.get("education", []):
            education_list.append(Education(
                degree=ed.get("degree", ""),
                institution=ed.get("institution", ""),
                year=ed.get("year"),
                cgpa=ed.get("cgpa")
            ))

        # Map Experience
        experience_list = []
        for ex in data.get("experience", []):
            experience_list.append(Experience(
                title=ex.get("title", ""),
                org=ex.get("org", ""),
                description=ex.get("description"),
                duration=ex.get("duration")
            ))

        # Map Skills (sometimes a list of strings, sometimes a list of dicts)
        skills_list = []
        for sk in data.get("skills", []):
            if isinstance(sk, dict):
                skills_list.append(Skill(
                    name=sk.get("name", ""),
                    category=sk.get("category"),
                    proficiency=sk.get("proficiency")
                ))
            else:
                skills_list.append(Skill(name=str(sk)))

        # Map Projects
        project_list = []
        for pr in data.get("projects", []):
            project_list.append(Project(
                name=pr.get("name", ""),
                description=pr.get("description", ""),
                technologies=pr.get("technologies", []),
                link=pr.get("link")
            ))

        # Map Certifications
        cert_list = []
        for cert in data.get("certifications", []):
            if isinstance(cert, dict):
                cert_list.append(Certification(
                    name=cert.get("name", ""),
                    issuer=cert.get("issuer", ""),
                    year=cert.get("year")
                ))
            else:
                cert_list.append(Certification(name=str(cert), issuer=""))

        structured = StructuredResume(
            professional_summary=data.get("professional_summary") or data.get("summary"),
            education=education_list,
            experience=experience_list,
            skills=skills_list,
            projects=project_list,
            certifications=cert_list,
            metadata=data.get("metadata", {})
        )

        metadata = ExtractionMetadata(
            source_type=resume_doc.get("source_type", "unknown"),
            extractor_name="bridged_from_db",
            extractor_version="1.0",
            character_count=resume_doc.get("character_count", 0),
            detected_sections=[],
            warning_count=0,
            processing_duration_ms=0.0
        )

        return CandidateInterviewContext(
            candidate_id=candidate_id,
            structured_resume=structured,
            extraction_metadata=metadata,
            quality_status=ExtractionQualityStatus.HIGH,  # Assume high if it made it to DB
            warnings=[]
        )

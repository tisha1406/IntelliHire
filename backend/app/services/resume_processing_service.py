import json
from datetime import UTC, datetime
from bson import ObjectId

from groq import AsyncGroq
from app.config.settings import settings
from app.resume_processing.parser import ResumeParser
from app.resume_processing.cleaner import ResumeCleaner
from app.repositories.resume_repository import ResumeRepository
from app.repositories.candidate_workflow_repository import CandidateWorkflowRepository
from app.repositories.notification_repository import NotificationRepository
from pydantic import BaseModel, Field
from typing import List

class ExperienceItem(BaseModel):
    title: str
    company: str
    duration: str
    description: str

class EducationItem(BaseModel):
    degree: str
    institution: str
    year: str

class ProjectItem(BaseModel):
    name: str
    description: str

class RadarDataItem(BaseModel):
    subject: str
    A: int
    fullMark: int

class ResumeStructuredOutput(BaseModel):
    overall_score: int
    ats_score: int
    role_match: int
    completeness: int
    technical_skills: List[str]
    soft_skills: List[str]
    experience: List[ExperienceItem]
    education: List[EducationItem]
    projects: List[ProjectItem]
    missing_skills: List[str]
    certifications: List[str]
    languages_known: List[str]
    radar_data: List[RadarDataItem]
    strengths: List[str]
    weaknesses: List[str]
    improve_ats: str
    missing_keywords: List[str]
    grammar_score: int
    formatting_score: int

class ResumeProcessingService:

    def __init__(self):
        self.resume_repo = ResumeRepository()
        self.workflow_repo = CandidateWorkflowRepository()
        self.notification_repo = NotificationRepository()
        # Initialize Groq for fast JSON structuring
        self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    async def process_resume(
        self,
        candidate_id: str,
        company_id: str,
        campaign_id: str,
        file_bytes: bytes,
        filename: str,
    ):
        """
        End-to-end processing: Extract -> Clean -> Structure -> Save -> Update Workflow.
        The original file_bytes are discarded when this function returns.
        """
        # 1. Update Workflow Status to Processing
        await self.workflow_repo.set_step_status(
            candidate_id, "stage", "RESUME_PROCESSING",
            {
                "resume_processing": True, 
                "resume_uploaded": True,
                "resume_uploaded_at": datetime.now(UTC)
            }
        )

        try:
            # 2. Extract Text
            raw_text = ResumeParser.extract_text(file_bytes, filename)
            
            # 3. Clean Text
            cleaned_text = ResumeCleaner.clean_text(raw_text)

            # 4. Structure with LLM
            structured_data = await self._structure_resume_with_llm(cleaned_text)

            # 5. Save Structured Profile
            structured_data["candidate_id"] = ObjectId(candidate_id)
            structured_data["company_id"] = ObjectId(company_id)
            structured_data["campaign_id"] = ObjectId(campaign_id)
            
            # Add processing timeline
            structured_data["timeline"] = [
                {"title": "Resume Uploaded", "status": "done"},
                {"title": "Resume Parsed", "status": "done"},
                {"title": "Skills Extracted", "status": "done"},
                {"title": "Experience Parsed", "status": "done"},
                {"title": "Ready for Interview", "status": "done"}
            ]

            await self.resume_repo.upsert(candidate_id, structured_data)

            # 6. Update Workflow to Analysis Complete
            await self.workflow_repo.set_step_status(
                candidate_id, "stage", "RESUME_ANALYSIS_COMPLETE",
                {
                    "resume_processing": False,
                    "resume_analysed": True,
                    "resume_analysed_at": datetime.now(UTC),
                    "next_action": "PRACTICE" # Or "SYSTEM_CHECK" depending on flow
                }
            )

            # 7. Notify Candidate
            await self.notification_repo.create({
                "candidate_id": ObjectId(candidate_id),
                "type": "resume",
                "title": "Resume Analysis Complete",
                "message": "Your resume has been successfully parsed and analysed. You can now proceed to the practice interview.",
                "read": False,
                "created_at": datetime.now(UTC)
            })

            return True

        except Exception as e:
            # Handle failure
            await self.workflow_repo.set_step_status(
                candidate_id, "stage", "RESUME_UPLOAD_REQUIRED",
                {"resume_processing": False, "resume_uploaded": False}
            )
            # Log error internally or notify candidate
            print(f"Resume processing failed for candidate {candidate_id}: {e}")
            raise e

    async def _structure_resume_with_llm(self, text: str) -> dict:
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("YOUR_") or settings.GROQ_API_KEY.strip() == "":
            print("Warning: GROQ_API_KEY is missing. Using mock resume data.")
            return {
                "overall_score": 85,
                "ats_score": 90,
                "role_match": 80,
                "completeness": 95,
                "technical_skills": ["Python", "React", "Node.js", "MongoDB"],
                "soft_skills": ["Communication", "Leadership", "Problem Solving"],
                "experience": [
                    {"title": "Software Engineer", "company": "Tech Corp", "duration": "2021-Present", "description": "Developed scalable backend microservices using Python and MongoDB."},
                    {"title": "Junior Developer", "company": "StartUp Inc", "duration": "2019-2021", "description": "Built reactive frontend applications and REST APIs using React and Node.js."}
                ],
                "education": [
                    {"degree": "B.S. Computer Science", "institution": "State University", "year": "2019"}
                ],
                "projects": [
                    {"name": "E-Commerce Platform", "description": "Designed and deployed a full-stack e-commerce platform handling 10k daily users."}
                ],
                "missing_skills": ["Docker", "Kubernetes", "AWS"],
                "certifications": ["AWS Certified Developer"],
                "languages_known": ["English", "Hindi"],
                "radar_data": [
                    {"subject": "Frontend", "A": 85, "fullMark": 100},
                    {"subject": "Backend", "A": 90, "fullMark": 100},
                    {"subject": "Architecture", "A": 75, "fullMark": 100},
                    {"subject": "Cloud/DevOps", "A": 60, "fullMark": 100},
                    {"subject": "Databases", "A": 80, "fullMark": 100}
                ],
                "strengths": ["Strong backend programming", "Experience with NoSQL databases"],
                "weaknesses": ["Limited cloud deployment experience"],
                "improve_ats": "Consider adding more cloud and DevOps keywords to improve ATS matching for senior roles.",
                "missing_keywords": ["Docker", "Kubernetes", "CI/CD", "AWS"],
                "grammar_score": 95,
                "formatting_score": 90
            }

        prompt = """
        You are an expert ATS (Applicant Tracking System). Analyze the following resume text and extract the information into the required structured format.
        
        Resume text:
        ---
        {text}
        ---
        """
        
        # Enforce Groq's strict schema requirement (additionalProperties: False)
        def _enforce_strict_schema(schema: dict) -> dict:
            if isinstance(schema, dict):
                if schema.get("type") == "object":
                    schema["additionalProperties"] = False
                    if "properties" not in schema:
                        schema["properties"] = {}
                for k, v in schema.items():
                    _enforce_strict_schema(v)
            elif isinstance(schema, list):
                for item in schema:
                    _enforce_strict_schema(item)
            return schema

        raw_schema = ResumeStructuredOutput.model_json_schema()
        if "$defs" in raw_schema:
            for def_name, def_schema in raw_schema["$defs"].items():
                _enforce_strict_schema(def_schema)
        _enforce_strict_schema(raw_schema)
        
        # Using configured model for fast, cheap structuring
        completion = await self.groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You extract information based on the provided JSON schema."},
                {"role": "user", "content": prompt.replace("{text}", text[:6000])} # limit text size just in case
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "resume_analysis",
                    "strict": True,
                    "schema": raw_schema
                }
            }
        )
        
        try:
            result = json.loads(completion.choices[0].message.content)
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to parse LLM JSON output: {e}")

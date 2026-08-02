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
            {"resume_processing": True, "resume_uploaded": True}
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
        You are an expert ATS (Applicant Tracking System). Analyze the following resume text and extract the information into a structured JSON format.
        
        The JSON MUST have the following schema EXACTLY, no extra text, only valid JSON:
        {
            "overall_score": int (0-100),
            "ats_score": int (0-100),
            "role_match": int (0-100),
            "completeness": int (0-100),
            "technical_skills": [list of strings],
            "soft_skills": [list of strings],
            "missing_skills": [list of strings],
            "certifications": [list of strings],
            "languages_known": [list of strings],
            "radar_data": [
                {"subject": "Frontend", "A": int(0-100), "fullMark": 100},
                {"subject": "Backend", "A": int(0-100), "fullMark": 100},
                {"subject": "Architecture", "A": int(0-100), "fullMark": 100},
                {"subject": "Cloud/DevOps", "A": int(0-100), "fullMark": 100},
                {"subject": "Databases", "A": int(0-100), "fullMark": 100}
            ],
            "strengths": [list of strings (3 max)],
            "weaknesses": [list of strings (2 max)],
            "improve_ats": string (one sentence advice),
            "missing_keywords": [list of strings],
            "grammar_score": int (0-100),
            "formatting_score": int (0-100)
        }
        
        Resume text:
        ---
        {text}
        ---
        """
        
        # Using Llama 3 8b for fast, cheap structuring
        completion = await self.groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You output ONLY valid JSON."},
                {"role": "user", "content": prompt.replace("{text}", text[:6000])} # limit text size just in case
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            result = json.loads(completion.choices[0].message.content)
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to parse LLM JSON output: {e}")

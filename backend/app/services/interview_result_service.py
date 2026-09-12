from typing import Dict, Any, List
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.ai_interview.engine.models.session import InterviewSession

class InterviewResultService:
    def __init__(self):
        self.session_repo = InterviewSessionRepository()

    async def generate_result_report(self, session_id: str) -> Dict[str, Any]:
        """
        Reads the deterministic InterviewSession from MongoDB and projects it 
        into a finalized Result Read Model for the Company Frontend.
        """
        session_data = await self.session_repo.get_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")

        # Convert dictionary to domain model to easily access properties
        session = InterviewSession(**session_data)

        if not session.is_completed:
            return {
                "session_id": session_id,
                "status": "IN_PROGRESS",
                "message": "Interview is not yet completed."
            }

        # Calculate scores based on the evaluation history
        evaluations = session.evaluations
        
        if not evaluations:
            return {
                "session_id": session_id,
                "status": "COMPLETED_NO_DATA",
                "message": "Interview completed but no evaluations found."
            }

        total_questions = len(evaluations)
        total_score = sum(ev.score for ev in evaluations)
        average_score = total_score / total_questions if total_questions > 0 else 0

        # Build detailed question feedback
        question_feedback = []
        for index, ev in enumerate(evaluations):
            # Try to match the evaluation to the question history
            q_text = "Unknown Question"
            topic = "General"
            
            # Find the corresponding question in question_history
            q_record = next((q for q in session.question_history if q.record_id == ev.question_record_id), None)
            if q_record:
                q_text = q_record.question_text
                topic = q_record.topic_id
                
            question_feedback.append({
                "id": str(index + 1),
                "topic": topic,
                "question": q_text,
                "score": ev.score,
                "feedback": ev.feedback
            })

        # Generate some dynamic strengths/weaknesses (In a real system, LLM would synthesize this)
        high_scored = [q for q in question_feedback if q["score"] >= 8]
        low_scored = [q for q in question_feedback if q["score"] < 6]

        strengths = [f"Strong understanding of {q['topic']} ({q['score']}/10)" for q in high_scored]
        if not strengths:
            strengths = ["No major strengths identified"]

        weaknesses = [f"Struggled with {q['topic']} ({q['score']}/10)" for q in low_scored]
        if not weaknesses:
            weaknesses = ["No major weaknesses identified"]

        # Final Report
        report = {
            "session_id": session_id,
            "status": "COMPLETED",
            "has_report": True,
            "overall_score": int(average_score * 10), # Scale to 0-100
            "technical_score": int(average_score * 10),
            "communication_score": 85, # Mock metric
            "confidence": 80,          # Mock metric
            "problem_solving": 75,     # Mock metric
            "soft_skills_score": 90,   # Mock metric
            "time_management": 88,     # Mock metric
            "resume_match": 92,        # Mock metric
            
            "radar_data": [
                {"subject": "Technical", "A": int(average_score * 10), "fullMark": 100},
                {"subject": "Communication", "A": 85, "fullMark": 100},
                {"subject": "Problem Solving", "A": 75, "fullMark": 100},
                {"subject": "Soft Skills", "A": 90, "fullMark": 100},
                {"subject": "System Design", "A": 80, "fullMark": 100},
                {"subject": "Culture Fit", "A": 95, "fullMark": 100}
            ],
            
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvement_suggestions": [
                "Practice elaborating more on problem-solving approaches.",
                "Provide more real-world examples for technical questions."
            ],
            "company_remarks": "Automated AI Analysis Completed.",
            "question_feedback": question_feedback
        }

        return report

from typing import Set
from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.core.enums import InterviewState
from app.ai_interview.persistence.exceptions import PersistenceInvariantError

class SessionPersistenceValidator:
    """
    Enforces strict structural invariants on the InterviewSession aggregate before persistence.
    Does NOT contain business logic or interview planning rules.
    """

    @staticmethod
    def validate(session: InterviewSessionSchema) -> None:
        # Invariant 1: Terminal sessions cannot have active claims
        if session.state in [InterviewState.COMPLETED, InterviewState.FAILED]:
            if session.generation_claim is not None:
                raise PersistenceInvariantError(f"Terminal session {session.state} cannot retain active generation_claim")
            
            for q in session.question_history:
                if q.evaluation_claim is not None:
                    raise PersistenceInvariantError(f"Terminal session {session.state} cannot retain active evaluation_claim on {q.record_id}")

        # Invariant 2: questions_asked_total == len(question_history)
        if session.questions_asked_total != len(session.question_history):
            raise PersistenceInvariantError(f"questions_asked_total ({session.questions_asked_total}) does not match len(question_history) ({len(session.question_history)})")

        # Invariant 3: Evaluation references and uniqueness
        q_ids: Set[str] = {q.record_id for q in session.question_history}
        eval_q_ids: Set[str] = set()
        
        for er in session.evaluation_history:
            if er.question_record_id not in q_ids:
                raise PersistenceInvariantError(f"EvaluationRecord references non-existent QuestionRecord: {er.question_record_id}")
            if er.question_record_id in eval_q_ids:
                raise PersistenceInvariantError(f"Duplicate EvaluationRecord for QuestionRecord: {er.question_record_id}")
            eval_q_ids.add(er.question_record_id)
            
        # Invariant 4: Claim metadata timestamps
        if session.generation_claim:
            if session.generation_claim.expires_at <= session.generation_claim.claimed_at:
                raise PersistenceInvariantError("generation_claim expires_at must be > claimed_at")
        
        for q in session.question_history:
            if q.evaluation_claim:
                if q.evaluation_claim.expires_at <= q.evaluation_claim.claimed_at:
                    raise PersistenceInvariantError(f"evaluation_claim expires_at must be > claimed_at for question {q.record_id}")

        # Invariant 5: Version must be positive
        if session.version < 1:
            raise PersistenceInvariantError(f"Version must be a positive integer, got {session.version}")

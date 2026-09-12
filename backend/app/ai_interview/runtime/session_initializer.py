import uuid
from datetime import datetime
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.core.enums import InterviewState, TopicState
from app.ai_interview.runtime.exceptions import SessionInitializationError

class SessionInitializer:
    @staticmethod
    def initialize(
        blueprint: InterviewBlueprint,
        candidate_id: str,
        company_id: str,
        campaign_id: str,
        mode_id: str,
        mode_version: int,
        session_id: str = None
    ) -> InterviewSessionSchema:
        """
        Creates a runtime InterviewSession schema securely binding an immutable blueprint.
        Ensures exact TopicProgress creation. Counters start at zero.
        """
        if not blueprint.topics:
            raise SessionInitializationError("Cannot initialize session with empty blueprint.")

        # Prevent duplicate topic progress entries
        unique_topic_ids = set()
        progress_list = []
        for topic in blueprint.topics:
            if topic.topic_id in unique_topic_ids:
                raise SessionInitializationError(f"Duplicate blueprint topic ID found: {topic.topic_id}")
            unique_topic_ids.add(topic.topic_id)
            
            progress_list.append(
                TopicProgress(
                    topic_id=topic.topic_id,
                    state=TopicState.NOT_STARTED,
                    structurally_attempted=False,
                    qualitatively_covered=False,
                    coverage_score=0.0,
                    readiness_score=0.0,
                    follow_up_count=0
                )
            )

        return InterviewSessionSchema(
            session_id=session_id or str(uuid.uuid4()),
            candidate_id=candidate_id,
            company_id=company_id,
            campaign_id=campaign_id,
            mode_id=mode_id,
            mode_version=mode_version,
            state=InterviewState.CREATED,
            blueprint=blueprint,
            questions_asked_total=0,
            current_topic_id=None,
            current_difficulty=None,
            topic_progress=progress_list,
            created_at=datetime.utcnow(),
            started_at=None,
            completed_at=None,
            failure_reason=None
        )

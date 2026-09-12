import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.db.mongo import get_database, connect_db, close_db
from app.config.settings import settings
from jose import jwt
from app.rbac.models import UserRole

# Override MongoDB URI for testing if needed
# We'll assume the environment is set up for testing

@pytest.fixture(autouse=True)
def clear_db(client): # Depend on client to ensure DB is connected via lifespan
    from pymongo import MongoClient
    sync_client = MongoClient(settings.MONGO_URI)
    db = sync_client[settings.DATABASE_NAME]
    db.interview_sessions.delete_many({})
    db.interview_mode_definitions.delete_many({})
    db.resume_analyses.delete_many({})
    sync_client.close()

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def candidate_token():
    from datetime import datetime, timedelta, timezone
    payload = {
        "sub": "cand_1", 
        "role": UserRole.CANDIDATE.value, 
        "candidate_id": "cand_1", 
        "company_id": "comp_1",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

@pytest.fixture
def other_candidate_token():
    from datetime import datetime, timedelta, timezone
    payload = {
        "sub": "cand_2", 
        "role": UserRole.CANDIDATE.value, 
        "candidate_id": "cand_2", 
        "company_id": "comp_1",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

@pytest.fixture
def mock_coordinator():
    with patch("app.api.ws.InterviewTurnCoordinator") as mock_coord_class, \
         patch("app.api.ws.QuestionEngine"), \
         patch("app.api.ws.AnswerEngine"):
        mock_instance = MagicMock()
        mock_coord_class.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_session(candidate_token):
    from app.ai_interview.schemas.session import InterviewSessionSchema, InterviewBlueprint
    from app.ai_interview.core.enums import InterviewState
    from datetime import datetime, timezone
    
    db = get_database()
    
    session = InterviewSessionSchema(
        session_id="session_1",
        candidate_id="cand_1",
        company_id="comp_1",
        campaign_id="camp_1",
        mode_id="mode_1",
        mode_version=1,
        state=InterviewState.IN_PROGRESS,
        blueprint=InterviewBlueprint(
            blueprint_version="1.0",
            topics=[], 
            total_question_budget=5, 
            min_questions=3,
            max_questions=7,
            emergency_max_questions=10
        ),
        created_at=datetime.now(timezone.utc)
    )
    
    from pymongo import MongoClient
    sync_client = MongoClient(settings.MONGO_URI)
    db = sync_client[settings.DATABASE_NAME]
    db.interview_sessions.insert_one(session.model_dump(by_alias=True))
    sync_client.close()
    
    return session

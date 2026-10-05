import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.auth.jwt_handler import create_access_token

client = TestClient(app)

@pytest.mark.asyncio
async def test_tts_voice_resolution():
    # Construct a valid candidate token
    token = create_access_token("cand_1", "candidate", "comp_1", "camp_1", "cand_1")

    with patch("app.api.interview.get_database") as mock_get_db, \
         patch("app.api.interview.TTSResiliencePolicy") as mock_policy, \
         patch("app.api.interview.CampaignRepository") as mock_camp_repo_cls:
         
        # Mock transport snapshot
        mock_snapshot = MagicMock()
        mock_snapshot.current_question.record_id = "q_1"
        mock_snapshot.current_question.question_text = "What is Python?"
        mock_transport = AsyncMock()
        mock_transport.get_session_snapshot.return_value = mock_snapshot
        
        from app.api.interview import get_transport_service
        app.dependency_overrides[get_transport_service] = lambda: mock_transport
        
        # Mock Session
        mock_session_repo = AsyncMock()
        mock_session_repo.get_by_id.return_value = MagicMock(campaign_id="camp_1", voice_id="simran")
        
        mock_db = MagicMock()
        mock_db.interview_sessions = "mock_col"
        mock_get_db.return_value = mock_db
        
        with patch("app.api.interview.InterviewSessionRepository") as mock_sess_repo_cls:
            mock_sess_repo_cls.return_value = mock_session_repo
            
            # Mock Campaign
            mock_camp_repo = AsyncMock()
            mock_camp_repo.get_by_id.return_value = MagicMock(voice_id="ritu", language="hi-IN")
            mock_camp_repo_cls.return_value = mock_camp_repo
            
            # Mock TTS Policy
            mock_policy_inst = AsyncMock()
            mock_policy_inst.execute.return_value = MagicMock(audio_bytes=b"audio", mime_type="audio/wav")
            mock_policy.return_value = mock_policy_inst
            
            # Since dependencies override can be tricky for imported get_transport_service, let's also patch it directly
            # by overriding the dependency on `app`
            from app.api.interview import get_transport_service
            app.dependency_overrides[get_transport_service] = lambda: mock_transport

            headers = {"Authorization": f"Bearer {token}"}
            response = client.post(
                "/api/interview/sessions/sess_1/questions/q_1/speech",
                headers=headers
            )
            
            assert response.status_code == 200
            call_args = mock_policy_inst.execute.call_args[0]
            assert call_args[3] == "simran"

@pytest.mark.asyncio
async def test_tts_voice_resolution_invalid_session_fallback():
    token = create_access_token("cand_1", "candidate", "comp_1", "camp_1", "cand_1")

    with patch("app.api.interview.get_database") as mock_get_db, \
         patch("app.api.interview.TTSResiliencePolicy") as mock_policy, \
         patch("app.api.interview.CampaignRepository") as mock_camp_repo_cls:
         
        mock_snapshot = MagicMock()
        mock_snapshot.current_question.record_id = "q_1"
        mock_snapshot.current_question.question_text = "What is Python?"
        mock_transport = AsyncMock()
        mock_transport.get_session_snapshot.return_value = mock_snapshot
        
        from app.api.interview import get_transport_service
        app.dependency_overrides[get_transport_service] = lambda: mock_transport
        
        mock_session_repo = AsyncMock()
        mock_session_repo.get_by_id.return_value = MagicMock(campaign_id="camp_1", voice_id="manan")
        
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        with patch("app.api.interview.InterviewSessionRepository") as mock_sess_repo_cls:
            mock_sess_repo_cls.return_value = mock_session_repo
            mock_camp_repo = AsyncMock()
            mock_camp_repo.get_by_id.return_value = MagicMock(voice_id="sunny", language="hi-IN")
            mock_camp_repo_cls.return_value = mock_camp_repo
            
            mock_policy_inst = AsyncMock()
            mock_policy_inst.execute.return_value = MagicMock(audio_bytes=b"audio", mime_type="audio/wav")
            mock_policy.return_value = mock_policy_inst
            
            response = client.post(
                "/api/interview/sessions/sess_1/questions/q_1/speech",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            call_args = mock_policy_inst.execute.call_args[0]
            assert call_args[3] == "shubh"

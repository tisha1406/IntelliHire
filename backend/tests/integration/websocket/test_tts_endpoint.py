import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

def test_tts_endpoint_success(client, candidate_token):
    # Setup mock session with active question
    with patch("app.api.interview.InterviewTransportService.get_session_snapshot") as mock_get_snapshot:
        
        mock_snapshot = MagicMock()
        mock_snapshot.current_question.record_id = "q_1"
        mock_snapshot.current_question.question_text = "How do you handle async in Python?"
        mock_get_snapshot.return_value = mock_snapshot
        
        with patch("app.ai_interview.speech_infrastructure.tts.sarvam_bulbul_adapter.SarvamBulbulAdapter.synthesize") as mock_synthesize:
            mock_result = MagicMock()
            mock_result.audio_bytes = b"fake audio"
            mock_result.mime_type = "audio/wav"
            mock_synthesize.return_value = mock_result
            
            response = client.post(
                "/api/interview/sessions/s_1/questions/q_1/speech",
                headers={"Authorization": f"Bearer {candidate_token}"}
            )
            
            assert response.status_code == 200
            assert response.content == b"fake audio"
            assert response.headers["content-type"] == "audio/wav"
            
            # Verify that synthesize was called with authoritative text
            mock_synthesize.assert_called_once_with("How do you handle async in Python?", None)

def test_tts_endpoint_unauthorized_access(client):
    response = client.post(
        "/api/interview/sessions/s_1/questions/q_1/speech"
        # No token
    )
    assert response.status_code == 403

def test_tts_endpoint_wrong_question_id(client, candidate_token):
    with patch("app.api.interview.InterviewTransportService.get_session_snapshot") as mock_get_snapshot:
        mock_snapshot = MagicMock()
        mock_snapshot.current_question.record_id = "q_1" # Active is q_1
        mock_get_snapshot.return_value = mock_snapshot
        
        # Try to synthesize an old or different question
        response = client.post(
            "/api/interview/sessions/s_1/questions/old_q/speech",
            headers={"Authorization": f"Bearer {candidate_token}"}
        )
        assert response.status_code == 400
        assert "Question is not currently active" in response.text

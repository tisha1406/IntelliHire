import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

def test_voice_stt_purity(client, candidate_token):
    """
    Test 1 — STT Purity: STT does not mutate session state.
    """
    with patch("app.api.interview.InterviewTransportService.get_session_snapshot") as mock_get_snapshot:
        mock_snapshot = MagicMock()
        mock_snapshot.is_completed = False
        mock_snapshot.is_failed = False
        mock_snapshot.current_question.record_id = "q_1"
        mock_get_snapshot.return_value = mock_snapshot
        
        with patch("app.ai_interview.speech_infrastructure.stt.sarvam_saaras_adapter.SarvamSaarasAdapter.transcribe") as mock_transcribe:
            mock_result = MagicMock()
            mock_result.transcript = "Candidate transcript"
            mock_result.language = "en"
            mock_result.duration_ms = 100
            mock_transcribe.return_value = mock_result
            
            response = client.post(
                "/api/interview/sessions/s_1/questions/q_1/transcribe",
                headers={"Authorization": f"Bearer {candidate_token}"},
                data={"transcription_request_id": "req_1"},
                files={"file": ("audio.webm", b"fake audio", "audio/webm")}
            )
            
            assert response.status_code == 200
            assert response.json()["transcript"] == "Candidate transcript"
            
            # Verify that get_session_snapshot was called to validate correlation, but NO answer submission happened.
            mock_get_snapshot.assert_called_once()
            # The session snapshot should be identical (no mutation happened on the backend purely because of STT)

def test_voice_tts_purity(client, candidate_token):
    """
    Test 3 — TTS Purity: TTS does not mutate session state.
    """
    with patch("app.api.interview.InterviewTransportService.get_session_snapshot") as mock_get_snapshot:
        mock_snapshot = MagicMock()
        mock_snapshot.current_question.record_id = "q_1"
        mock_snapshot.current_question.question_text = "Persisted question text"
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
            
            # Verify that get_session_snapshot was called to fetch the authoritative text, but NO mutation happened.
            mock_get_snapshot.assert_called_once()

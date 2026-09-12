import { useState, useRef, useCallback } from 'react';

/**
 * Hook for managing communication with the backend STT transcription endpoint.
 * Includes abort controller logic to cancel pending transcription requests if the user navigates away or retries.
 */
export const useSpeechRecognition = (apiBaseUrl, getToken) => {
    const [isTranscribing, setIsTranscribing] = useState(false);
    const [transcriptionError, setTranscriptionError] = useState(null);
    const abortControllerRef = useRef(null);

    const transcribeAudio = useCallback(async (session_id, question_record_id, audioBlob, mimeType) => {
        setIsTranscribing(true);
        setTranscriptionError(null);
        
        // Cancel any pending transcription
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        
        const controller = new AbortController();
        abortControllerRef.current = controller;

        const token = getToken();
        if (!token) {
            setTranscriptionError("Authentication token is missing.");
            setIsTranscribing(false);
            return null;
        }

        try {
            const formData = new FormData();
            const ext = mimeType.split('/')[1] || 'webm';
            formData.append('file', audioBlob, `audio.${ext}`);
            formData.append('transcription_request_id', crypto.randomUUID());

            const response = await fetch(`${apiBaseUrl}/api/interview/sessions/${session_id}/questions/${question_record_id}/transcribe`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                    // Do NOT set Content-Type, fetch sets it automatically for FormData with the correct boundary
                },
                body: formData,
                signal: controller.signal
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Transcription failed with status ${response.status}`);
            }

            const data = await response.json();
            setIsTranscribing(false);
            return data.transcript;

        } catch (err) {
            if (err.name === 'AbortError') {
                console.log("Transcription aborted by user.");
            } else {
                console.error("Transcription error:", err);
                setTranscriptionError(err.message || "An error occurred during transcription.");
            }
            setIsTranscribing(false);
            return null;
        }
    }, [apiBaseUrl, getToken]);

    const cancelTranscription = useCallback(() => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        setIsTranscribing(false);
        setTranscriptionError(null);
    }, []);

    return {
        isTranscribing,
        transcriptionError,
        transcribeAudio,
        cancelTranscription
    };
};

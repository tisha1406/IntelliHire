import { useState, useRef, useCallback } from 'react';
import { convertBlobToWav } from '../../utils/audioConversion.js';

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
            let finalBlob = audioBlob;
            let finalMime = mimeType;
            
            // Convert to WAV for better STT compatibility (especially for WebM/Opus)
            if (!mimeType.includes('wav')) {
                console.log(`[INTERVIEW] STT_REQUEST_INIT session=${session_id} question=${question_record_id} input_type=${mimeType} input_size=${audioBlob.size}`);
                try {
                    const inputSize = audioBlob.size;
                    const convResult = await convertBlobToWav(audioBlob);
                    
                    // convertBlobToWav returns either a Blob directly or {blob, rmsLevel}
                    // Support both return types
                    const wavBlob = (convResult && convResult.blob) ? convResult.blob : convResult;
                    const wavRms  = (convResult && convResult.rmsLevel != null) ? convResult.rmsLevel : null;
                    
                    console.log(`[INTERVIEW] AUDIO_CONVERSION_SUCCESS input_type=${mimeType} input_size=${inputSize} output_type=audio/wav output_size=${wavBlob.size} rms=${wavRms}`);

                    if (wavRms !== null && wavRms < 1.0) {
                        // WAV is silent — the browser-side conversion produced zeros.
                        // Fall back to the original WebM, which Sarvam natively supports.
                        console.warn(`[INTERVIEW] SILENT_WAV_DETECTED rms=${wavRms} — falling back to original WebM blob. Sarvam supports webm natively.`);
                        // finalBlob stays as audioBlob (original WebM), finalMime stays as mimeType
                    } else {
                        finalBlob = wavBlob;
                        finalMime = 'audio/wav';
                    }
                } catch(e) {
                    console.error(`[INTERVIEW] AUDIO_CONVERSION_FAILED error="${e.message}" — falling back to original blob type=${mimeType} size=${audioBlob.size}`, e);
                    // finalBlob remains audioBlob, finalMime remains mimeType
                }
            } else {
                console.log(`[INTERVIEW] STT_REQUEST_INIT session=${session_id} question=${question_record_id} input_type=${mimeType} input_size=${audioBlob.size} (already WAV)`);
            }


            // Log EXACTLY which blob is being uploaded
            const ext = finalMime.includes('wav') ? 'wav' : (finalMime.split('/')[1] || 'webm');
            const filename = `audio.${ext}`;
            console.log(`[INTERVIEW] STT_UPLOAD_BLOB filename=${filename} type=${finalBlob.type} size=${finalBlob.size}`);

            const formData = new FormData();
            formData.append('file', finalBlob, filename);
            formData.append('transcription_request_id', crypto.randomUUID());

            const uploadUrl = `${apiBaseUrl}/api/interview/sessions/${session_id}/questions/${question_record_id}/transcribe`;
            console.log(`[INTERVIEW] STT_HTTP_POST url=${uploadUrl}`);

            const response = await fetch(uploadUrl, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                    // Do NOT set Content-Type, fetch sets it automatically for FormData with the correct boundary
                },
                body: formData,
                signal: controller.signal
            });

            console.log(`[INTERVIEW] STT_HTTP_RESPONSE status=${response.status}`);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMsg = errorData.message || errorData.detail || `Transcription failed with status ${response.status}`;
                console.error(`[INTERVIEW] STT_HTTP_ERROR status=${response.status} detail="${errorMsg}"`);
                throw new Error(errorMsg);
            }

            const data = await response.json();
            const transcriptLength = (data.transcript || '').length;
            console.log(`[INTERVIEW] STT_SUCCESS transcript_length=${transcriptLength}`);
            setIsTranscribing(false);
            return data.transcript;

        } catch (err) {
            if (err.name === 'AbortError') {
                console.log("[INTERVIEW] STT_ABORTED: Transcription aborted by user.");
            } else {
                console.error("[INTERVIEW] STT_ERROR:", err);
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

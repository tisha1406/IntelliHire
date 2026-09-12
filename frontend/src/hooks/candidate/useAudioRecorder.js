import { useState, useRef, useCallback } from 'react';

/**
 * Hook for managing MediaRecorder lifecycle securely.
 * Features:
 * - Proper stream cleanup to prevent microphone light from staying on
 * - State management (idle, recording, stopping, error)
 * - Mime type negotiation
 */
export const useAudioRecorder = () => {
    const [status, setStatus] = useState('idle'); // idle, recording, stopping, error
    const [audioData, setAudioData] = useState(null);
    const [audioMimeType, setAudioMimeType] = useState(null);
    const [error, setError] = useState(null);

    const mediaRecorder = useRef(null);
    const streamRef = useRef(null);
    const audioChunks = useRef([]);

    const cleanup = useCallback(() => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => {
                track.stop();
            });
            streamRef.current = null;
        }
        mediaRecorder.current = null;
    }, []);

    const startRecording = useCallback(async () => {
        setError(null);
        setAudioData(null);
        setAudioMimeType(null);
        audioChunks.current = [];
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;

            // Negotiate MIME type (Safari vs Chrome vs Firefox)
            const mimeTypes = ['audio/webm', 'audio/mp4', 'audio/mp3', 'audio/ogg'];
            let selectedMimeType = null;
            
            for (const mime of mimeTypes) {
                if (MediaRecorder.isTypeSupported(mime)) {
                    selectedMimeType = mime;
                    break;
                }
            }

            if (!selectedMimeType) {
                // Fallback to default
                selectedMimeType = 'audio/webm';
            }

            setAudioMimeType(selectedMimeType);

            const recorder = new MediaRecorder(stream, { mimeType: selectedMimeType });
            
            recorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    audioChunks.current.push(event.data);
                }
            };

            recorder.onstop = () => {
                const blob = new Blob(audioChunks.current, { type: selectedMimeType });
                setAudioData(blob);
                setStatus('idle');
                cleanup();
            };

            recorder.onerror = (e) => {
                console.error("MediaRecorder error:", e);
                setError("An error occurred during recording.");
                setStatus('error');
                cleanup();
            };

            recorder.start();
            mediaRecorder.current = recorder;
            setStatus('recording');
            
        } catch (err) {
            console.error("Failed to start recording:", err);
            setError("Microphone access denied or unavailable.");
            setStatus('error');
            cleanup();
        }
    }, [cleanup]);

    const stopRecording = useCallback(() => {
        if (mediaRecorder.current && status === 'recording') {
            setStatus('stopping');
            mediaRecorder.current.stop();
        }
    }, [status]);

    const cancelRecording = useCallback(() => {
        if (mediaRecorder.current && status === 'recording') {
            mediaRecorder.current.onstop = () => {
                // Override onstop to NOT save the data
                setStatus('idle');
                cleanup();
                setAudioData(null);
            };
            mediaRecorder.current.stop();
        } else {
            cleanup();
            setStatus('idle');
            setAudioData(null);
        }
    }, [status, cleanup]);

    return {
        status,
        audioData,
        audioMimeType,
        error,
        startRecording,
        stopRecording,
        cancelRecording
    };
};

import { useState, useCallback, useEffect, useRef } from 'react';

/**
 * Hook for managing text-to-speech audio playback.
 * Primary path: Backend TTS endpoint (Sarvam AI).
 * Fallback path: window.speechSynthesis.
 */
export const useTextToSpeech = (apiBaseUrl, getToken) => {
    const [isPlaying, setIsPlaying] = useState(false);
    
    // Fallback native synthesizer
    const synthRef = useRef(window.speechSynthesis);
    
    // HTML5 Audio object reference
    const audioRef = useRef(null);
    const objectUrlRef = useRef(null);
    
    // Deduplication tracker
    const lastSpokenQuestionIdRef = useRef(null);

    useEffect(() => {
        // Clean up any ongoing speech or object URLs when component unmounts
        return () => {
            if (synthRef.current) {
                synthRef.current.cancel();
            }
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current = null;
            }
            if (objectUrlRef.current) {
                URL.revokeObjectURL(objectUrlRef.current);
                objectUrlRef.current = null;
            }
        };
    }, []);

    const stopAudio = useCallback(() => {
        if (synthRef.current) {
            synthRef.current.cancel();
        }
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
        }
        setIsPlaying(false);
    }, []);

    const playNativeFallback = useCallback((text) => {
        if (!synthRef.current) return;
        synthRef.current.cancel();
        if (!text) return;

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        
        utterance.onstart = () => setIsPlaying(true);
        utterance.onend = () => setIsPlaying(false);
        utterance.onerror = (e) => {
            console.error("Speech synthesis fallback error:", e);
            setIsPlaying(false);
        };

        synthRef.current.speak(utterance);
    }, []);

    const playQuestion = useCallback(async (session_id, question_record_id, text, autoPlay = false) => {
        // Prevent duplicate auto-play for the same question
        if (autoPlay && lastSpokenQuestionIdRef.current === question_record_id) {
            return;
        }
        
        stopAudio(); // Stop any currently playing audio

        if (!session_id || !question_record_id) {
            // No context, just use fallback
            playNativeFallback(text);
            return;
        }

        const token = getToken();
        if (!token) {
            playNativeFallback(text);
            return;
        }

        try {
            const url = `${apiBaseUrl}/api/interview/sessions/${session_id}/questions/${question_record_id}/speech`;
            
            // TTS is non-blocking to the interview state. We just fire and forget HTTP fetch.
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                console.warn(`Backend TTS failed (${response.status}). Falling back to native synthesis.`);
                playNativeFallback(text);
                return;
            }

            // Read binary audio
            const blob = await response.blob();
            
            // Clean up previous object URL
            if (objectUrlRef.current) {
                URL.revokeObjectURL(objectUrlRef.current);
            }
            
            const objectUrl = URL.createObjectURL(blob);
            objectUrlRef.current = objectUrl;
            
            const audio = new Audio(objectUrl);
            audioRef.current = audio;
            
            audio.onplay = () => {
                setIsPlaying(true);
                lastSpokenQuestionIdRef.current = question_record_id;
            };
            audio.onended = () => setIsPlaying(false);
            audio.onerror = (e) => {
                console.error("Audio playback error:", e);
                setIsPlaying(false);
                // Last ditch fallback if decoding fails
                playNativeFallback(text);
            };

            await audio.play();
            
        } catch (error) {
            console.error("TTS fetch error:", error);
            playNativeFallback(text);
        }
    }, [apiBaseUrl, getToken, playNativeFallback, stopAudio]);

    return {
        isPlaying,
        playQuestion,
        stopAudio
    };
};

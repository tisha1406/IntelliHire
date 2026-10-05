import React, { useEffect } from 'react';
import { Mic, Square, Volume2, XCircle, Loader2 } from 'lucide-react';

import { useAudioRecorder } from '../../hooks/candidate/useAudioRecorder';
import { useSpeechRecognition } from '../../hooks/candidate/useSpeechRecognition';
import { useTextToSpeech } from '../../hooks/candidate/useTextToSpeech';

const VoiceControls = ({ 
    session_id, 
    question_record_id, 
    question_text, 
    apiBaseUrl, 
    getToken,
    onTranscriptReady,
    disabled 
}) => {
    const {
        status: recorderStatus,
        audioData,
        audioMimeType,
        error: recorderError,
        autoStopped,
        startRecording,
        stopRecording,
        cancelRecording
    } = useAudioRecorder();

    const {
        isTranscribing,
        transcriptionError,
        transcribeAudio,
        cancelTranscription
    } = useSpeechRecognition(apiBaseUrl, getToken);

    const {
        isPlaying,
        playQuestion,
        stopAudio
    } = useTextToSpeech(apiBaseUrl, getToken);

    const lastProcessedAudioRef = React.useRef(null);

    // Auto-transcribe when audio is available
    useEffect(() => {
        if (
            audioData && 
            audioMimeType && 
            session_id && 
            question_record_id && 
            lastProcessedAudioRef.current !== audioData
        ) {
            lastProcessedAudioRef.current = audioData;
            const processAudio = async () => {
                const transcript = await transcribeAudio(session_id, question_record_id, audioData, audioMimeType);
                if (transcript) {
                    onTranscriptReady(transcript);
                }
            };
            processAudio();
        }
    }, [audioData, audioMimeType, session_id, question_record_id, transcribeAudio, onTranscriptReady]);

    // Auto-play question TTS when it becomes available
    useEffect(() => {
        if (session_id && question_record_id && question_text && !disabled) {
            playQuestion(session_id, question_record_id, question_text, true);
        }
    }, [session_id, question_record_id, question_text, playQuestion, disabled]);

    // Cleanup resources if disabled (e.g., WS disconnect or evaluation starts)
    useEffect(() => {
        if (disabled) {
            cancelRecording();
            cancelTranscription();
            stopAudio();
        }
    }, [disabled, cancelRecording, cancelTranscription, stopAudio]);

    const handlePlayQuestion = () => {
        if (isPlaying) {
            stopAudio();
        } else {
            // autoPlay is false because this is a manual click
            playQuestion(session_id, question_record_id, question_text, false);
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center', padding: '16px', border: '1px solid var(--border)', borderRadius: '8px', background: 'rgba(255,255,255,0.02)' }}>
            
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                <button 
                    className="c-btn c-btn-ghost"
                    onClick={handlePlayQuestion} 
                    title={isPlaying ? "Stop Audio" : "Listen to Question"}
                    style={{ padding: '8px' }}
                >
                    {isPlaying ? <Square size={20} /> : <Volume2 size={20} />}
                </button>

                {recorderStatus === 'idle' && !isTranscribing && (
                    <button
                        className="c-btn"
                        style={{ backgroundColor: '#EF4444', color: '#fff' }}
                        onClick={startRecording}
                        disabled={disabled}
                    >
                        <Mic size={18} /> Record Answer
                    </button>
                )}

                {recorderStatus === 'recording' && (
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <button
                            className="c-btn"
                            style={{ backgroundColor: '#F59E0B', color: '#fff' }}
                            onClick={stopRecording}
                        >
                            <Square size={18} /> Stop Recording
                        </button>
                        <button className="c-btn c-btn-ghost" onClick={cancelRecording} title="Cancel Recording" style={{ padding: '8px' }}>
                            <XCircle size={20} />
                        </button>
                        <span className="blink-text" style={{ fontSize: '14px', color: '#EF4444' }}>
                            Recording...
                        </span>
                    </div>
                )}

                {isTranscribing && (
                    <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                        <Loader2 size={24} className="c-pulse-icon" />
                        <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
                            Transcribing audio...
                        </span>
                        <button className="c-btn c-btn-ghost" onClick={cancelTranscription} title="Cancel Transcription" style={{ padding: '8px' }}>
                            <XCircle size={20} />
                        </button>
                    </div>
                )}
            </div>

            {(recorderError || transcriptionError) && (
                <div style={{ fontSize: '14px', color: '#EF4444' }}>
                    {recorderError || transcriptionError}
                </div>
            )}

            {autoStopped && recorderStatus === 'idle' && !recorderError && !transcriptionError && (
                <div style={{ fontSize: '14px', color: '#F59E0B' }}>
                    Recording automatically stopped at the 28-second limit. If your answer was cut off, you can finish it in the text box below.
                </div>
            )}

            <style>{`
                .blink-text {
                    animation: blinker 1s linear infinite;
                }
                @keyframes blinker {
                    50% { opacity: 0; }
                }
            `}</style>
        </div>
    );
};

export default VoiceControls;

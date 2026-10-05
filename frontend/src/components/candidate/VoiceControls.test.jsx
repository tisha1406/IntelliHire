/**
 * @vitest-environment jsdom
 */
import React, { useState } from 'react';
import { render, act, cleanup } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import VoiceControls from './VoiceControls';

afterEach(() => {
    cleanup();
});

// Mock dependencies
let mockAudioData = null;
let mockRecorderStatus = 'idle';
let mockAutoStopped = false;
let mockRecorderError = null;

vi.mock('../../hooks/candidate/useAudioRecorder', () => ({
    useAudioRecorder: () => ({
        status: mockRecorderStatus,
        audioData: mockAudioData,
        audioMimeType: mockAudioData ? 'audio/webm' : null,
        error: mockRecorderError,
        autoStopped: mockAutoStopped,
        startRecording: vi.fn(),
        stopRecording: vi.fn(),
        cancelRecording: vi.fn()
    })
}));

const mockTranscribeAudio = vi.fn();
let mockIsTranscribing = false;

vi.mock('../../hooks/candidate/useSpeechRecognition', () => ({
    useSpeechRecognition: (apiBaseUrl, getToken) => {
        // Track getToken calls to simulate effect dependency triggering
        getToken();
        return {
            isTranscribing: mockIsTranscribing,
            transcriptionError: null,
            transcribeAudio: mockTranscribeAudio,
            cancelTranscription: vi.fn()
        };
    }
}));

vi.mock('../../hooks/candidate/useTextToSpeech', () => ({
    useTextToSpeech: () => ({
        isPlaying: false,
        playQuestion: vi.fn(),
        stopAudio: vi.fn()
    })
}));

describe('VoiceControls Transcription Lifecycle', () => {
    beforeEach(() => {
        mockAudioData = null;
        mockRecorderStatus = 'idle';
        mockAutoStopped = false;
        mockRecorderError = null;
        mockIsTranscribing = false;
        mockTranscribeAudio.mockReset();
        mockTranscribeAudio.mockResolvedValue("test transcript");
    });

    it('A. One audio Blob causes exactly one transcription request', async () => {
        const onTranscriptReady = vi.fn();
        const getToken = () => "token";
        
        // Initial render without audio
        const { rerender } = render(
            <VoiceControls
                session_id="123"
                question_record_id="q1"
                question_text="Q1"
                apiBaseUrl="url"
                getToken={getToken}
                onTranscriptReady={onTranscriptReady}
                disabled={false}
            />
        );
        
        expect(mockTranscribeAudio).toHaveBeenCalledTimes(0);
        
        // Simulate recording stopped and audioData populated
        const blob1 = new Blob(["audio1"]);
        mockAudioData = blob1;
        
        rerender(
            <VoiceControls
                session_id="123"
                question_record_id="q1"
                question_text="Q1"
                apiBaseUrl="url"
                getToken={getToken}
                onTranscriptReady={onTranscriptReady}
                disabled={false}
            />
        );
        
        // The effect should immediately trigger transcribeAudio
        expect(mockTranscribeAudio).toHaveBeenCalledTimes(1);
        expect(mockTranscribeAudio).toHaveBeenCalledWith("123", "q1", blob1, "audio/webm");
    });

    it('B. A rerender with the same audioData Blob does NOT cause another request', () => {
        const onTranscriptReady = vi.fn();
        const getToken = () => "token";
        
        const blob1 = new Blob(["audio1"]);
        mockAudioData = blob1;
        
        const { rerender } = render(
            <VoiceControls
                session_id="123"
                question_record_id="q1"
                question_text="Q1"
                apiBaseUrl="url"
                getToken={getToken}
                onTranscriptReady={onTranscriptReady}
                disabled={false}
            />
        );
        
        expect(mockTranscribeAudio).toHaveBeenCalledTimes(1);
        
        // Rerender with exactly the same props
        rerender(
            <VoiceControls
                session_id="123"
                question_record_id="q1"
                question_text="Q1"
                apiBaseUrl="url"
                getToken={getToken}
                onTranscriptReady={onTranscriptReady}
                disabled={false}
            />
        );
        
        // Should NOT trigger again
        expect(mockTranscribeAudio).toHaveBeenCalledTimes(1);
    });

    it('C. A changed getToken function reference does NOT cause the same Blob to be retranscribed', () => {
        const onTranscriptReady = vi.fn();
        const blob1 = new Blob(["audio1"]);
        mockAudioData = blob1;
        
        const { rerender } = render(
            <VoiceControls
                session_id="123"
                question_record_id="q1"
                question_text="Q1"
                apiBaseUrl="url"
                getToken={() => "token1"}
                onTranscriptReady={onTranscriptReady}
                disabled={false}
            />
        );
        
        expect(mockTranscribeAudio).toHaveBeenCalledTimes(1);
        
        // Rerender with a NEW inline getToken function (simulating InterviewRoom inline prop)
        rerender(
            <VoiceControls
                session_id="123"
                question_record_id="q1"
                question_text="Q1"
                apiBaseUrl="url"
                getToken={() => "token2"}
                onTranscriptReady={onTranscriptReady}
                disabled={false}
            />
        );
        
        // Should STILL NOT trigger again due to lastProcessedAudioRef check!
        expect(mockTranscribeAudio).toHaveBeenCalledTimes(1);
    });

    it('G. A NEW recording Blob can be transcribed normally after the previous recording completes', () => {
        const onTranscriptReady = vi.fn();
        const getToken = () => "token";
        
        const blob1 = new Blob(["audio1"]);
        mockAudioData = blob1;
        
        const { rerender } = render(
            <VoiceControls
                session_id="123"
                question_record_id="q1"
                question_text="Q1"
                apiBaseUrl="url"
                getToken={getToken}
                onTranscriptReady={onTranscriptReady}
                disabled={false}
            />
        );
        
        expect(mockTranscribeAudio).toHaveBeenCalledTimes(1);
        expect(mockTranscribeAudio).toHaveBeenCalledWith("123", "q1", blob1, "audio/webm");
        
        // Simulate candidate records a new answer
        const blob2 = new Blob(["audio2"]);
        mockAudioData = blob2;
        
        rerender(
            <VoiceControls
                session_id="123"
                question_record_id="q1"
                question_text="Q1"
                apiBaseUrl="url"
                getToken={getToken}
                onTranscriptReady={onTranscriptReady}
                disabled={false}
            />
        );
        
        // The effect should trigger again because blob2 !== blob1
        expect(mockTranscribeAudio).toHaveBeenCalledTimes(2);
        expect(mockTranscribeAudio).toHaveBeenCalledWith("123", "q1", blob2, "audio/webm");
    });
});

describe('VoiceControls — 30s recording limit notice (Sarvam Saaras hard cap)', () => {
    beforeEach(() => {
        mockAudioData = null;
        mockRecorderStatus = 'idle';
        mockAutoStopped = false;
        mockRecorderError = null;
        mockIsTranscribing = false;
        mockTranscribeAudio.mockReset();
        mockTranscribeAudio.mockResolvedValue("test transcript");
    });

    const renderControls = () => render(
        <VoiceControls
            session_id="123"
            question_record_id="q1"
            question_text="Q1"
            apiBaseUrl="url"
            getToken={() => "token"}
            onTranscriptReady={vi.fn()}
            disabled={false}
        />
    );

    it('shows a notice when the recorder auto-stopped at the time limit', () => {
        mockAutoStopped = true;
        mockRecorderStatus = 'idle';

        const { getByText } = renderControls();

        expect(getByText(/automatically stopped at the 28-second limit/i)).toBeTruthy();
    });

    it('does not show the auto-stop notice on a normal (manually stopped) recording', () => {
        mockAutoStopped = false;
        mockRecorderStatus = 'idle';

        const { queryByText } = renderControls();

        expect(queryByText(/automatically stopped/i)).toBeNull();
    });

    it('prefers a real recorder error over the auto-stop notice', () => {
        mockAutoStopped = true;
        mockRecorderError = "Microphone access denied or unavailable.";
        mockRecorderStatus = 'idle';

        const { getByText, queryByText } = renderControls();

        expect(getByText("Microphone access denied or unavailable.")).toBeTruthy();
        expect(queryByText(/automatically stopped/i)).toBeNull();
    });
});

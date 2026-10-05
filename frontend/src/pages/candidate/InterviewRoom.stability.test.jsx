/**
 * @vitest-environment jsdom
 */
import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import InterviewRoom from './InterviewRoom';
import { vi, describe, it, expect, beforeEach } from 'vitest';

vi.mock('../../hooks/candidate/useCandidate', () => ({
    useCandidateDashboard: () => ({ data: { interview_duration: 45 }, isLoading: false }),
    useStartPractice: () => ({ 
        mutate: vi.fn((_, { onSuccess }) => {
            if (onSuccess) onSuccess({ data: { session_id: "test-session-123" } });
        }), 
        isPending: false 
    }),
    useCompletePractice: () => ({ mutate: vi.fn() }),
    useStartInterview: () => ({ mutate: vi.fn(), isPending: false }),
    useCompleteInterview: () => ({ mutate: vi.fn() })
}));

vi.mock('../../hooks/candidate/useInterviewSession', () => ({
    useInterviewSession: (sessionIdToUse) => ({
        connectionState: "CONNECTED",
        currentQuestion: { record_id: "q1", question_text: "Q1", topic_id: "T1" },
        isEvaluating: false,
        isCompleted: false,
        error: null,
        submitAnswer: vi.fn()
    })
}));

vi.mock('../../hooks/useAuth', () => ({
    __esModule: true,
    default: () => ({ token: "fake-token" })
}));

vi.mock('../../services/api', () => ({
    default: { defaults: { baseURL: "http://localhost:8000" } }
}));

let capturedOnTranscriptReady;
let callbackChangeCount = 0;

vi.mock('../../components/candidate/VoiceControls', () => {
    return {
        default: function MockVoiceControls(props) {
            if (capturedOnTranscriptReady !== props.onTranscriptReady) {
                callbackChangeCount++;
                capturedOnTranscriptReady = props.onTranscriptReady;
            }
            
            return (
                <div data-testid="mock-voice-controls">
                    <button data-testid="trigger-transcript" onClick={() => props.onTranscriptReady("hello")}>
                        Trigger Transcript
                    </button>
                </div>
            );
        }
    }
});

describe('InterviewRoom Callback Stability', () => {
    beforeEach(() => {
        capturedOnTranscriptReady = undefined;
        callbackChangeCount = 0;
    });

    it('maintains referential stability for onTranscriptReady across state updates', () => {
        render(
            <MemoryRouter initialEntries={['/candidate/interview/practice']}>
                <Routes>
                    <Route path="/candidate/interview/:id" element={<InterviewRoom />} />
                </Routes>
            </MemoryRouter>
        );

        // Start the practice session to render VoiceControls
        act(() => {
            const startBtn = screen.getByText(/Start Practice/i);
            if (startBtn) startBtn.click();
        });

        // We assume VoiceControls is now rendered
        expect(callbackChangeCount).toBeGreaterThan(0);
        
        // Reset count to track stability across subsequent state changes
        callbackChangeCount = 0;

        // Trigger the callback, which calls setAnswerText internally
        act(() => {
            screen.getByTestId('trigger-transcript').click();
        });

        // The state update should re-render InterviewRoom
        // Since handleTranscriptReady is wrapped in useCallback, the prop reference shouldn't change
        expect(callbackChangeCount).toBe(0);
        
        // Trigger it again just to be sure
        act(() => {
            screen.getByTestId('trigger-transcript').click();
        });
        
        expect(callbackChangeCount).toBe(0);
    });
});

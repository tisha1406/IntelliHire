/**
 * @vitest-environment jsdom
 */
import React from 'react';
import { render, fireEvent, screen, cleanup } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import InterviewRoom from './InterviewRoom';

import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// Mutable mock state (Checkpoint-3 regression tests need a controllable
// isCompleted per test; the original single test only needed a static false).
let mockIsCompleted = false;
let mockCompletePracticeMutate = vi.fn();
let mockCompleteInterviewMutate = vi.fn();
let mockStartInterviewMutate = vi.fn();
let mockDashboardData = { interview_duration: 45 };

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom');
    return { ...actual, useNavigate: () => mockNavigate };
});

// Mock all the hooks and components to isolate the test
vi.mock('../../hooks/candidate/useCandidate', () => ({
    useCandidateDashboard: () => ({ data: mockDashboardData, isLoading: false }),
    useStartPractice: () => ({ mutate: vi.fn(), isPending: false }),
    useCompletePractice: () => ({ mutate: mockCompletePracticeMutate }),
    useStartInterview: () => ({ mutate: mockStartInterviewMutate, isPending: false }),
    useCompleteInterview: () => ({ mutate: mockCompleteInterviewMutate })
}));

vi.mock('../../hooks/candidate/useInterviewSession', () => ({
    useInterviewSession: (sessionIdToUse) => ({
        connectionState: "CONNECTED",
        currentQuestion: { record_id: "7d1c6529-2e17-429f-91b1-302e6233a09d", question_text: "Test question", topic_id: "Test Topic" },
        isEvaluating: false,
        isCompleted: mockIsCompleted,
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

// We'll mock VoiceControls to capture the props it receives
let capturedVoiceControlProps = {};
vi.mock('../../components/candidate/VoiceControls', () => {
    return {
        default: function MockVoiceControls(props) {
            capturedVoiceControlProps = props;
            return <div data-testid="mock-voice-controls">Voice Controls</div>;
        }
    };
});

describe('InterviewRoom Component', () => {
    beforeEach(() => {
        capturedVoiceControlProps = {};
        mockIsCompleted = false;
        mockCompletePracticeMutate = vi.fn();
        mockCompleteInterviewMutate = vi.fn();
        mockStartInterviewMutate = vi.fn();
        mockDashboardData = { interview_duration: 45 };
        mockNavigate.mockReset();
    });

    afterEach(() => {
        cleanup();
    });

    it('passes the resolved sessionIdToUse to VoiceControls, not the literal "practice" string', () => {
        // Render the component at the /practice route
        render(
            <MemoryRouter initialEntries={['/candidate/interview/practice']}>
                <Routes>
                    <Route path="/candidate/interview/:id" element={<InterviewRoom />} />
                </Routes>
            </MemoryRouter>
        );
        
        // In practice mode before explicitly clicking "Start", practiceSessionId is null.
        // sessionIdToUse will be null.
        // Therefore VoiceControls should receive session_id = null (or whatever practiceSessionId is initialized to),
        // but crucially NOT "practice".
        
        expect(capturedVoiceControlProps).toBeDefined();
        // verify it doesn't pass the URL ID "practice"
        expect(capturedVoiceControlProps.session_id).not.toBe("practice");
        
        // It should be null/undefined initially before practiceSessionId is set
        expect(capturedVoiceControlProps.session_id).toBeFalsy();
    });

    describe('Checkpoint-3 regression: practice completion persistence', () => {
        it('calls completePractice() when a practice session reaches isCompleted', () => {
            mockIsCompleted = true;

            render(
                <MemoryRouter initialEntries={['/candidate/interview/practice']}>
                    <Routes>
                        <Route path="/candidate/interview/:id" element={<InterviewRoom />} />
                        <Route path="/candidate/interview/:id/complete" element={<div>Complete</div>} />
                    </Routes>
                </MemoryRouter>
            );

            expect(mockCompletePracticeMutate).toHaveBeenCalledTimes(1);
        });

        it('does NOT call completePractice() when an official interview session reaches isCompleted', () => {
            mockIsCompleted = true;

            render(
                <MemoryRouter initialEntries={['/candidate/interview/session-abc-123']}>
                    <Routes>
                        <Route path="/candidate/interview/:id" element={<InterviewRoom />} />
                        <Route path="/candidate/interview/:id/complete" element={<div>Complete</div>} />
                    </Routes>
                </MemoryRouter>
            );

            expect(mockCompletePracticeMutate).not.toHaveBeenCalled();
        });

        it('does not call completePractice() when the practice session has not completed yet', () => {
            mockIsCompleted = false;

            render(
                <MemoryRouter initialEntries={['/candidate/interview/practice']}>
                    <Routes>
                        <Route path="/candidate/interview/:id" element={<InterviewRoom />} />
                    </Routes>
                </MemoryRouter>
            );

            expect(mockCompletePracticeMutate).not.toHaveBeenCalled();
        });
    });

    describe('Checkpoint-4 regression: official interview completion persistence', () => {
        it('calls completeInterview() when an official interview session reaches isCompleted', () => {
            mockIsCompleted = true;

            render(
                <MemoryRouter initialEntries={['/candidate/interview/session-abc-123']}>
                    <Routes>
                        <Route path="/candidate/interview/:id" element={<InterviewRoom />} />
                        <Route path="/candidate/interview/:id/complete" element={<div>Complete</div>} />
                    </Routes>
                </MemoryRouter>
            );

            expect(mockCompleteInterviewMutate).toHaveBeenCalledTimes(1);
        });

        it('does NOT call completeInterview() when a practice session reaches isCompleted', () => {
            mockIsCompleted = true;

            render(
                <MemoryRouter initialEntries={['/candidate/interview/practice']}>
                    <Routes>
                        <Route path="/candidate/interview/:id" element={<InterviewRoom />} />
                        <Route path="/candidate/interview/:id/complete" element={<div>Complete</div>} />
                    </Routes>
                </MemoryRouter>
            );

            expect(mockCompleteInterviewMutate).not.toHaveBeenCalled();
        });

        it('does not call completeInterview() when the official session has not completed yet', () => {
            mockIsCompleted = false;

            render(
                <MemoryRouter initialEntries={['/candidate/interview/session-abc-123']}>
                    <Routes>
                        <Route path="/candidate/interview/:id" element={<InterviewRoom />} />
                    </Routes>
                </MemoryRouter>
            );

            expect(mockCompleteInterviewMutate).not.toHaveBeenCalled();
        });
    });

    describe('Official interview start regression: handleStart onSuccess response shape', () => {
        // POST /api/interview/campaigns/{id}/sessions (app/api/interview.py)
        // returns a FLAT CreateSessionResponse body ({session_id, state, ...}),
        // never wrapped in {data: {...}}. handleStart's official branch used to
        // read res.data.session_id unconditionally, which threw
        // "Cannot read properties of undefined (reading 'session_id')" and left
        // the candidate stuck on the pre-interview screen even though the
        // backend had already created the session successfully.
        beforeEach(() => {
            mockDashboardData = { interview_duration: 45, campaign_id: 'camp-1' };
        });

        it('navigates using session_id from a flat response body (the real backend shape)', () => {
            mockStartInterviewMutate.mockImplementation((campaignId, { onSuccess }) => {
                onSuccess({ session_id: 'real-session-1', state: 'created' });
            });

            render(
                <MemoryRouter initialEntries={['/candidate/interview/official']}>
                    <Routes>
                        <Route path="/candidate/interview/:id" element={<InterviewRoom />} />
                    </Routes>
                </MemoryRouter>
            );

            fireEvent.click(screen.getByText('Start Official Interview'));

            expect(mockNavigate).toHaveBeenCalledWith('/candidate/interview/real-session-1');
        });

        it('still navigates correctly if the response ever is wrapped in data (defensive fallback)', () => {
            mockStartInterviewMutate.mockImplementation((campaignId, { onSuccess }) => {
                onSuccess({ data: { session_id: 'real-session-2' } });
            });

            render(
                <MemoryRouter initialEntries={['/candidate/interview/official']}>
                    <Routes>
                        <Route path="/candidate/interview/:id" element={<InterviewRoom />} />
                    </Routes>
                </MemoryRouter>
            );

            fireEvent.click(screen.getByText('Start Official Interview'));

            expect(mockNavigate).toHaveBeenCalledWith('/candidate/interview/real-session-2');
        });

        it('does not crash and logs an error if no session_id is present in either shape', () => {
            const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
            mockStartInterviewMutate.mockImplementation((campaignId, { onSuccess }) => {
                onSuccess({ state: 'created' });
            });

            render(
                <MemoryRouter initialEntries={['/candidate/interview/official']}>
                    <Routes>
                        <Route path="/candidate/interview/:id" element={<InterviewRoom />} />
                    </Routes>
                </MemoryRouter>
            );

            expect(() => fireEvent.click(screen.getByText('Start Official Interview'))).not.toThrow();
            expect(mockNavigate).not.toHaveBeenCalled();
            expect(consoleErrorSpy).toHaveBeenCalled();

            consoleErrorSpy.mockRestore();
        });
    });
});

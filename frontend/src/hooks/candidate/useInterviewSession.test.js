/**
 * @vitest-environment jsdom
 */
import { renderHook, act } from "@testing-library/react";
import { useInterviewSession } from "./useInterviewSession";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";

// Mock AuthContext
vi.mock("../../context/AuthContext", () => ({
    useAuthContext: () => ({ token: "mock_token" })
}));

describe("useInterviewSession - start_interview dispatch", () => {
    let mockWebSocket;
    let mockSend;

    beforeEach(() => {
        mockSend = vi.fn();
        mockWebSocket = {
            readyState: 1, // OPEN
            send: mockSend,
            close: vi.fn()
        };

        global.WebSocket = class { constructor() { Object.assign(this, mockWebSocket); mockWebSocket.instance = this; } };
global.WebSocket.OPEN = 1;
    });

    afterEach(() => {
        vi.restoreAllMocks();
        delete global.WebSocket;
    });

    const triggerEvent = (event_type, data) => {
        act(() => {
            if (mockWebSocket.instance && mockWebSocket.instance.onmessage) {
                mockWebSocket.instance.onmessage({ data: JSON.stringify({ event_type, data }) });
            }
        });
    };

    it("a. created session + current_question null -> sends start_interview once", () => {
        const { result } = renderHook(() => useInterviewSession("session_1"));
        
        act(() => {
            if (mockWebSocket.instance && mockWebSocket.instance.onopen) mockWebSocket.instance.onopen();
        });

        triggerEvent("session_snapshot", {
            interview_state: "created",
            is_completed: false,
            is_failed: false,
            current_question: null
        });

        expect(mockSend).toHaveBeenCalledTimes(1);
        const sentMsg = JSON.parse(mockSend.mock.calls[0][0]);
        expect(sentMsg.command_type).toBe("start_interview");
        expect(sentMsg.session_id).toBe("session_1");
    });

    it("b. active session + current_question exists -> does not send it", () => {
        const { result } = renderHook(() => useInterviewSession("session_2"));
        
        act(() => {
            if (mockWebSocket.instance && mockWebSocket.instance.onopen) mockWebSocket.instance.onopen();
        });

        triggerEvent("session_snapshot", {
            interview_state: "in_progress",
            is_completed: false,
            is_failed: false,
            current_question: { record_id: "q1", question_text: "Hi" }
        });

        expect(mockSend).not.toHaveBeenCalled();
    });

    it("c. completed session -> does not send it", () => {
        const { result } = renderHook(() => useInterviewSession("session_3"));
        
        act(() => {
            if (mockWebSocket.instance && mockWebSocket.instance.onopen) mockWebSocket.instance.onopen();
        });

        triggerEvent("session_snapshot", {
            interview_state: "completed",
            is_completed: true,
            is_failed: false,
            current_question: null
        });

        expect(mockSend).not.toHaveBeenCalled();
    });

    it("d. repeated snapshot/render -> does not send duplicate start commands", () => {
        const { result } = renderHook(() => useInterviewSession("session_4"));
        
        act(() => {
            if (mockWebSocket.instance && mockWebSocket.instance.onopen) mockWebSocket.instance.onopen();
        });

        // First snapshot
        triggerEvent("session_snapshot", {
            interview_state: "created",
            is_completed: false,
            is_failed: false,
            current_question: null
        });

        expect(mockSend).toHaveBeenCalledTimes(1);

        // Re-render
        act(() => {
            result.current;
        });

        // Second snapshot for same session
        // Second snapshot for same session
        triggerEvent("session_snapshot", {
            interview_state: "in_progress",
            is_completed: false,
            is_failed: false,
            current_question: null
        });

        // Should not have sent again
        expect(mockSend).toHaveBeenCalledTimes(1);
    });

    it("e. in_progress snapshot without current_question -> does not send start_interview", () => {
        const { result } = renderHook(() => useInterviewSession("session_5"));
        
        act(() => {
            if (mockWebSocket.instance && mockWebSocket.instance.onopen) mockWebSocket.instance.onopen();
        });

        triggerEvent("session_snapshot", {
            interview_state: "in_progress",
            is_completed: false,
            is_failed: false,
            current_question: null
        });

        expect(mockSend).not.toHaveBeenCalled();
    });

    it("f. is_failed=true snapshot -> does not send start_interview and exposes error", () => {
        const { result } = renderHook(() => useInterviewSession("session_6"));
        
        act(() => {
            if (mockWebSocket.instance && mockWebSocket.instance.onopen) mockWebSocket.instance.onopen();
        });

        triggerEvent("session_snapshot", {
            interview_state: "failed",
            is_completed: false,
            is_failed: true,
            current_question: null
        });

        expect(mockSend).not.toHaveBeenCalled();
        expect(result.current.error).toBe("Interview failed. Please restart the interview.");
    });
});

describe("useInterviewSession - submit_answer dispatch", () => {
    let mockWebSocket;
    let mockSend;

    beforeEach(() => {
        mockSend = vi.fn();
        mockWebSocket = {
            readyState: 1, // OPEN
            send: mockSend,
            close: vi.fn()
        };

        global.WebSocket = class { constructor() { Object.assign(this, mockWebSocket); mockWebSocket.instance = this; } };
        global.WebSocket.OPEN = 1;
    });

    afterEach(() => {
        vi.restoreAllMocks();
        delete global.WebSocket;
    });

    const triggerEvent = (event_type, data) => {
        act(() => {
            if (mockWebSocket.instance && mockWebSocket.instance.onmessage) {
                mockWebSocket.instance.onmessage({ data: JSON.stringify({ event_type, data }) });
            }
        });
    };

    it("A & B. submitAnswer sends `payload` (not `data`) with correct record_id and answer_text", () => {
        const { result } = renderHook(() => useInterviewSession("session_5"));
        
        act(() => {
            if (mockWebSocket.instance && mockWebSocket.instance.onopen) mockWebSocket.instance.onopen();
        });

        // Setup current question
        triggerEvent("session_snapshot", {
            interview_state: "in_progress",
            is_completed: false,
            is_failed: false,
            current_question: { record_id: "q_123", question_text: "What is React?" }
        });

        // Call submitAnswer
        act(() => {
            result.current.submitAnswer("React is a UI library");
        });

        expect(mockSend).toHaveBeenCalledTimes(1);
        const sentMsg = JSON.parse(mockSend.mock.calls[0][0]);
        
        expect(sentMsg.command_type).toBe("submit_answer");
        expect(sentMsg.session_id).toBe("session_5");
        
        // Assert 'payload' exists and 'data' does not
        expect(sentMsg.payload).toBeDefined();
        expect(sentMsg.data).toBeUndefined();
        
        // Assert correct content
        expect(sentMsg.payload.question_record_id).toBe("q_123");
        expect(sentMsg.payload.answer_text).toBe("React is a UI library");
        
        // Assert optimistically locked
        expect(result.current.isEvaluating).toBe(true);
    });

    it("C. a WebSocket `error` event resets isEvaluating to false", () => {
        const { result } = renderHook(() => useInterviewSession("session_6"));
        
        act(() => {
            if (mockWebSocket.instance && mockWebSocket.instance.onopen) mockWebSocket.instance.onopen();
        });

        // Setup current question
        triggerEvent("session_snapshot", {
            interview_state: "in_progress",
            is_completed: false,
            is_failed: false,
            current_question: { record_id: "q_123", question_text: "What is React?" }
        });

        // Call submitAnswer to lock UI
        act(() => {
            result.current.submitAnswer("Test answer");
        });

        expect(result.current.isEvaluating).toBe(true);

        // Simulate backend rejecting the command with an error event
        triggerEvent("error", {
            error_code: "INVALID_COMMAND",
            message: "Missing payload"
        });

        // Assert unlocked UI
        expect(result.current.isEvaluating).toBe(false);
        expect(result.current.error).toBe("Missing payload");
    });
    
    it("D. existing successful submit behavior remains unchanged (evaluation_complete)", () => {
        const { result } = renderHook(() => useInterviewSession("session_7"));
        
        act(() => {
            if (mockWebSocket.instance && mockWebSocket.instance.onopen) mockWebSocket.instance.onopen();
        });

        triggerEvent("session_snapshot", {
            interview_state: "in_progress",
            is_completed: false,
            is_failed: false,
            current_question: { record_id: "q_123", question_text: "What is React?" }
        });

        act(() => {
            result.current.submitAnswer("Test");
        });

        expect(result.current.isEvaluating).toBe(true);

        // Simulate backend success
        triggerEvent("evaluation_complete", {});

        // Assert unlocked UI
        expect(result.current.isEvaluating).toBe(false);
    });
});

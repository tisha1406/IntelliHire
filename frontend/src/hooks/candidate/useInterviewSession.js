import { useState, useEffect, useRef, useCallback } from "react";
import { useAuthContext } from "../../context/AuthContext";

export function useInterviewSession(sessionId) {
    const { token } = useAuthContext();
    
    // Connection State Machine: DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING, FAILED
    const [connectionState, setConnectionState] = useState("DISCONNECTED");
    
    // Logical State Machine
    const [sessionState, setSessionState] = useState(null);
    const [currentQuestion, setCurrentQuestion] = useState(null);
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [isCompleted, setIsCompleted] = useState(false);
    const [error, setError] = useState(null);

    const ws = useRef(null);
    const reconnectTimeout = useRef(null);
    const hasSentStart = useRef(false);

    const connect = useCallback(() => {
        if (!token || !sessionId) return;
        
        if (ws.current?.readyState === WebSocket.OPEN) return;

        setConnectionState(prev => prev === "DISCONNECTED" ? "CONNECTING" : "RECONNECTING");
        
        // Ensure WebSocket URL is correct for your Vite proxy or full URL
        const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsHost = import.meta.env.VITE_WS_URL || `${window.location.hostname}:8000`;
        const wsUrl = `${wsProtocol}//${wsHost}/api/ws/interview/${sessionId}?token=${token}`;

        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            setConnectionState("CONNECTED");
            setError(null);
        };

        socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                handleEvent(message);
            } catch (err) {
                console.error("Failed to parse WS message", err);
            }
        };

        socket.onclose = (event) => {
            // Normal close from the server connection replacement
            if (event.code === 1000) {
                setConnectionState("DISCONNECTED");
                return;
            }
            // Otherwise attempt reconnect
            setConnectionState("DISCONNECTED");
            reconnectTimeout.current = setTimeout(() => {
                connect();
            }, 3000); // 3 second backoff
        };

        socket.onerror = (err) => {
            console.error("WebSocket Error:", err);
            socket.close();
        };

        ws.current = socket;
    }, [token, sessionId]);

    const handleEvent = (message) => {
        const { event_type, data } = message;
        console.log(`[INTERVIEW] WS_EVENT_RECEIVED event=${event_type} session=${sessionId}`);

        switch (event_type) {
            case "session_snapshot":
                setSessionState(data);
                setIsCompleted(data.is_completed);
                if (data.current_question) {
                    setCurrentQuestion(data.current_question);
                    setIsEvaluating(data.evaluation_in_progress || data.pending_evaluation);
                    hasSentStart.current = true;
                } else {
                    setCurrentQuestion(null);
                    setIsEvaluating(false);
                    
                    if (data.is_failed) {
                        setError("Interview failed. Please restart the interview.");
                    } else if (!data.is_completed && !hasSentStart.current && data.interview_state === "created") {
                        if (ws.current?.readyState === WebSocket.OPEN) {
                            console.log(`[INTERVIEW] WS_START_SENT session=${sessionId} command=start_interview`);
                            ws.current.send(JSON.stringify({
                                command_type: "start_interview",
                                command_id: `cmd_start_${Date.now()}`,
                                session_id: sessionId,
                                payload: {}
                            }));
                            hasSentStart.current = true;
                        } else {
                            console.log(`[INTERVIEW] Cannot send WS_START because socket state is ${ws.current?.readyState}`);
                        }
                    } else {
                        console.log(`[INTERVIEW] Did not send WS_START. is_completed=${data.is_completed} hasSentStart=${hasSentStart.current} state=${data.interview_state}`);
                    }
                }
                break;
                
            case "question_ready":
            case "next_question_ready":
                setCurrentQuestion(data);
                setIsEvaluating(false);
                break;

            case "answer_received":
                setIsEvaluating(true);
                break;

            case "evaluation_processing":
                setIsEvaluating(true);
                break;

            case "evaluation_complete":
                setIsEvaluating(false);
                // Next question_ready will arrive shortly or interview_completed
                break;

            case "interview_completed":
                setIsCompleted(true);
                break;
                
            case "connection_replaced":
                setError("Session resumed in another tab or device.");
                if (ws.current) {
                    ws.current.close(1000);
                }
                break;
                
            case "error":
                setError(data.message || data.error_code);
                setIsEvaluating(false);
                break;

            case "decision_ready":
            case "question_generating":
            case "connection_ready":
            case "interview_started":
                // Backend informative events, currently not driving UI state directly
                break;

            default:
                console.warn("Unknown event type:", event_type);
        }
    };

    const submitAnswer = (text) => {
        if (ws.current?.readyState === WebSocket.OPEN && currentQuestion) {
            ws.current.send(JSON.stringify({
                command_type: "submit_answer",
                command_id: `cmd_${Date.now()}`,
                session_id: sessionId,
                payload: {
                    question_record_id: currentQuestion.record_id,
                    answer_text: text
                }
            }));
            // Optimistically lock UI
            setIsEvaluating(true);
        } else {
            console.warn("Cannot submit answer: WebSocket not open or no current question");
        }
    };

    useEffect(() => {
        connect();
        return () => {
            if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
            if (ws.current) {
                ws.current.close(1000);
            }
        };
    }, [connect]);

    return {
        connectionState,
        sessionState,
        currentQuestion,
        isEvaluating,
        isCompleted,
        error,
        submitAnswer
    };
}

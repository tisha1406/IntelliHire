import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
    Mic, Camera, AlertCircle, CheckCircle2, Play, Activity, 
    ArrowRight, ShieldAlert, MonitorSpeaker, Wifi, Target, 
    BrainCircuit, Settings2, Clock, Globe, Loader2, Send
} from "lucide-react";
import { useCandidateDashboard, useStartPractice, useCompletePractice, useStartInterview } from "../../hooks/candidate/useCandidate";
import { useInterviewSession } from "../../hooks/candidate/useInterviewSession";
import "../../styles/candidate/interview.css";

import VoiceControls from "../../components/candidate/VoiceControls";
import useAuth from "../../hooks/useAuth";
import api from "../../services/api";

function useTimer(initialSeconds) {
    const [seconds, setSeconds] = useState(initialSeconds);
    const [isActive, setIsActive] = useState(false);

    useEffect(() => {
        let interval = null;
        if (isActive && seconds > 0) {
            interval = setInterval(() => setSeconds(s => s - 1), 1000);
        } else if (seconds === 0) {
            setIsActive(false);
            clearInterval(interval);
        }
        return () => clearInterval(interval);
    }, [isActive, seconds]);

    const start = () => setIsActive(true);
    const format = () => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
    };

    return { seconds, isActive, start, format };
}

export default function InterviewRoom() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [answerText, setAnswerText] = useState("");
    const { token } = useAuth();
    
    const isPractice = id === "practice";
    const isPreInterview = id === "official";
    const isLiveInterview = !isPractice && !isPreInterview;

    const { data: dashboard, isLoading: dashLoading } = useCandidateDashboard();
    const { mutate: startPractice } = useStartPractice();
    const { mutate: completePractice } = useCompletePractice();
    const { mutate: startInterview, isPending: isStartingSession } = useStartInterview();

    const { 
        connectionState, 
        currentQuestion, 
        isEvaluating, 
        isCompleted, 
        error, 
        submitAnswer 
    } = useInterviewSession(isLiveInterview ? id : null);

    const timer = useTimer(isPractice ? 15 * 60 : parseInt(dashboard?.interview_duration || 45) * 60);

    useEffect(() => {
        if (isCompleted) {
            navigate(`/candidate/interview/${id}/complete`);
        }
    }, [isCompleted, navigate, id]);

    const handleStart = () => {
        if (isPractice) {
            startPractice();
            // Practice is mocked for now
        } else {
            if (!dashboard?.campaign_id) return;
            startInterview(dashboard.campaign_id, {
                onSuccess: (res) => {
                    navigate(`/candidate/interview/${res.data.session_id}`);
                }
            });
        }
    };

    const handleAnswerSubmit = () => {
        if (!answerText.trim()) return;
        submitAnswer(answerText);
        setAnswerText("");
    };

    const handleTranscriptReady = (transcript) => {
        // Append transcript to existing text or set it directly
        setAnswerText(prev => prev ? `${prev} ${transcript}` : transcript);
    };

    if (dashLoading) {
        return <div className="c-interview-room" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Loader2 className="c-pulse-icon" /></div>;
    }

    const practiceCompleted = dashboard?.steps?.find(s => s.key === "practice")?.status === "completed";

    return (
        <div className="c-interview-room">
            {/* Header */}
            <header className="c-interview-header">
                <div className="c-interview-brand">
                    <div className="c-interview-brand-icon">I</div>
                    <div className="c-interview-header-title">
                        IntelliHire <span>Secure Workspace</span>
                    </div>
                </div>
                {isPreInterview ? (
                    <button className="c-btn c-btn-ghost" onClick={() => navigate("/candidate/dashboard")}>
                        Cancel & Return
                    </button>
                ) : (
                    <div style={{ color: "#EF4444", fontWeight: 600, display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#EF4444", animation: "pulse 2s infinite" }} />
                        Session Live
                    </div>
                )}
            </header>

            <main className="c-interview-content">
                {isPreInterview ? (
                    <>
                        <div className="c-interview-top">
                            <h1>Official B2B Interview</h1>
                            <p>Assigned by {dashboard?.company_name}. Please verify your parameters and complete the system check.</p>
                        </div>

                        <div className="c-interview-grid">
                            
                            {/* Strategy & Parameters */}
                            <div className="c-interview-card">
                                <h2 className="c-interview-card-title"><Target size={20} /> Interview Parameters</h2>
                                <div className="c-strat-grid">
                                    <div className="c-strat-item c-strat-full">
                                        <span className="c-strat-label"><BrainCircuit size={12} style={{display:"inline"}}/> Strategy</span>
                                        <span className="c-strat-val">{dashboard?.interview_strategy || "Balanced"}</span>
                                    </div>
                                    <div className="c-strat-item">
                                        <span className="c-strat-label"><Clock size={12} style={{display:"inline"}}/> Duration</span>
                                        <span className="c-strat-val">{dashboard?.interview_duration || "45 Min"}</span>
                                    </div>
                                    <div className="c-strat-item">
                                        <span className="c-strat-label"><Settings2 size={12} style={{display:"inline"}}/> Difficulty</span>
                                        <span className="c-strat-val">Adaptive</span>
                                    </div>
                                    <div className="c-strat-item">
                                        <span className="c-strat-label"><Activity size={12} style={{display:"inline"}}/> Questions</span>
                                        <span className="c-strat-val">Dynamic (5-10)</span>
                                    </div>
                                    <div className="c-strat-item">
                                        <span className="c-strat-label"><Globe size={12} style={{display:"inline"}}/> Language</span>
                                        <span className="c-strat-val">{dashboard?.interview_language || "English"}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Important Instructions */}
                            <div className="c-interview-card">
                                <h2 className="c-interview-card-title"><ShieldAlert size={20} /> Company Instructions</h2>
                                <div className="c-instruction-list">
                                    <div className="c-instruction-item">
                                        <div className="c-instruction-icon"><Mic size={14} /></div>
                                        <div className="c-instruction-text">
                                            <h4>Text & Audio Processing</h4>
                                            <p>This interview phase accepts typed answers and voice recordings via STT.</p>
                                        </div>
                                    </div>
                                    <div className="c-instruction-item">
                                        <div className="c-instruction-icon"><AlertCircle size={14} /></div>
                                        <div className="c-instruction-text">
                                            <h4>No Pausing</h4>
                                            <p>Once started, the timer begins. You cannot pause or exit without failing.</p>
                                        </div>
                                    </div>
                                    <div className="c-instruction-item">
                                        <div className="c-instruction-icon"><Activity size={14} /></div>
                                        <div className="c-instruction-text">
                                            <h4>Dynamic Grading</h4>
                                            <p>The AI dynamically asks follow-ups based on the depth of your answers.</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* System Check */}
                            <div className="c-interview-card">
                                <h2 className="c-interview-card-title"><MonitorSpeaker size={20} /> System Diagnostics</h2>
                                <div className="c-hardware-box">
                                    <div className="c-sys-item">
                                        <div className="c-sys-label"><Globe size={16} /> Browser Check</div>
                                        <div className="c-sys-status ok">Supported</div>
                                    </div>
                                    <div className="c-sys-item">
                                        <div className="c-sys-label"><Wifi size={16} /> Network Quality</div>
                                        <div className="c-sys-status ok">Excellent (45ms)</div>
                                    </div>
                                </div>
                            </div>

                        </div>

                        <div className="c-interview-bottom">
                            <div className="c-interview-meta">
                                <div className="c-meta-item">
                                    <span className="c-meta-label">Est. Completion</span>
                                    <span className="c-meta-value">~ {parseInt(dashboard?.interview_duration || 45)} Minutes</span>
                                </div>
                                <div className="c-meta-item">
                                    <span className="c-meta-label">Practice Recommended</span>
                                    <span className="c-meta-value" style={{color: practiceCompleted ? "#10B981" : "#F59E0B"}}>
                                        {practiceCompleted ? "Done" : "Pending"}
                                    </span>
                                </div>
                                <div className="c-meta-item">
                                    <span className="c-meta-label">Attempts Left</span>
                                    <span className="c-meta-value">1 of 1</span>
                                </div>
                            </div>
                            <button className="c-start-btn" onClick={handleStart} disabled={isStartingSession}>
                                {isStartingSession ? <Loader2 size={20} className="c-pulse-icon" /> : <Play size={20} />} 
                                {isStartingSession ? "Creating Session..." : "Start Official Interview"}
                            </button>
                        </div>
                    </>
                ) : (
                    /* Active Live Interview */
                    <div className="c-active-area">
                        {error && (
                            <div style={{ padding: 16, background: "rgba(239, 68, 68, 0.1)", color: "#EF4444", borderRadius: 8, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 8 }}>
                                <AlertCircle size={20} /> {error}
                            </div>
                        )}
                        
                        <div style={{ fontSize: 14, color: "var(--text-muted)", marginBottom: 16, display: 'flex', gap: 8, alignItems: 'center' }}>
                            <div style={{ width: 8, height: 8, borderRadius: '50%', background: connectionState === "CONNECTED" ? "#10B981" : "#F59E0B" }} />
                            {connectionState}
                        </div>

                        {currentQuestion ? (
                            <>
                                <div style={{ textAlign: "center", maxWidth: 800, width: "100%", marginBottom: 40 }}>
                                    <h3 style={{ fontSize: 18, marginBottom: 12, color: "var(--accent)" }}>
                                        {currentQuestion.topic_id || "Question"}
                                    </h3>
                                    <p style={{ fontSize: 24, fontWeight: 600, lineHeight: 1.5, color: "var(--text)" }}>
                                        {currentQuestion.question_text}
                                    </p>
                                </div>

                                <div style={{ width: "100%", maxWidth: 800, display: "flex", flexDirection: "column", gap: 16 }}>
                                    <VoiceControls
                                        session_id={id}
                                        question_record_id={currentQuestion.record_id}
                                        question_text={currentQuestion.question_text}
                                        apiBaseUrl={api.defaults.baseURL}
                                        getToken={() => token}
                                        onTranscriptReady={handleTranscriptReady}
                                        disabled={isEvaluating || connectionState !== "CONNECTED"}
                                    />
                                    
                                    <div style={{ position: "relative" }}>
                                        <textarea 
                                            className="c-input"
                                            style={{ 
                                                width: "100%", 
                                                minHeight: 160, 
                                                padding: 20, 
                                                fontSize: 16, 
                                                resize: "vertical",
                                                background: "rgba(255,255,255,0.02)",
                                                borderColor: isEvaluating ? "rgba(255,255,255,0.05)" : "var(--border)"
                                            }}
                                            placeholder={isEvaluating ? "Evaluating your response..." : "Type your answer here or record using voice..."}
                                            value={answerText}
                                            onChange={(e) => setAnswerText(e.target.value)}
                                            disabled={isEvaluating}
                                        />
                                        
                                        <button 
                                            className="c-btn c-btn-primary" 
                                            onClick={handleAnswerSubmit} 
                                            disabled={isEvaluating || !answerText.trim() || connectionState !== "CONNECTED"}
                                            style={{ position: "absolute", bottom: 16, right: 16 }}
                                        >
                                            {isEvaluating ? <Loader2 size={18} className="c-pulse-icon" /> : <Send size={18} />}
                                            {isEvaluating ? "Processing" : "Submit Answer"}
                                        </button>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, color: "var(--text-muted)" }}>
                                <Loader2 size={32} className="c-pulse-icon" />
                                <span>{connectionState === "CONNECTED" ? "Preparing next question..." : "Connecting..."}</span>
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}

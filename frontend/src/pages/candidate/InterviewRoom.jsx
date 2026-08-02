import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
    Mic, Camera, AlertCircle, CheckCircle2, Play, Activity, 
    ArrowRight, ShieldAlert, MonitorSpeaker, Wifi, Target, 
    BrainCircuit, Settings2, Clock, Globe, Loader2
} from "lucide-react";
import { useCandidateDashboard, useStartPractice, useCompletePractice, useStartInterview } from "../../hooks/candidate/useCandidate";
import "../../styles/candidate/interview.css";

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
    const [started, setStarted] = useState(false);
    const [currentQIndex, setCurrentQIndex] = useState(0);
    const isPractice = id === "practice";

    const { data: dashboard, isLoading } = useCandidateDashboard();
    const { mutate: startPractice } = useStartPractice();
    const { mutate: completePractice } = useCompletePractice();
    const { mutate: startInterview } = useStartInterview();

    // Mock questions for Phase 1
    const mockQuestions = [
        { topic: "Introduction", text: "Please introduce yourself and explain why you're a good fit for this role." },
        { topic: "Experience", text: "Describe a challenging project you've worked on recently." }
    ];

    const timer = useTimer(isPractice ? 15 * 60 : parseInt(dashboard?.interview_duration || 45) * 60);

    const handleStart = () => {
        if (isPractice) {
            startPractice();
        } else {
            startInterview();
        }
        setStarted(true);
        timer.start();
    };

    const handleNext = () => {
        if (currentQIndex < mockQuestions.length - 1) {
            setCurrentQIndex(currentQIndex + 1);
        } else {
            if (isPractice) {
                completePractice(undefined, {
                    onSuccess: () => navigate("/candidate/dashboard")
                });
            } else {
                navigate("/candidate/dashboard"); // For actual interview, API call would happen here.
            }
        }
    };

    if (isLoading) {
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
                {!started ? (
                    <button className="c-btn c-btn-ghost" onClick={() => navigate("/candidate/dashboard")}>
                        Cancel & Return
                    </button>
                ) : (
                    <div style={{ color: "#EF4444", fontWeight: 600, display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#EF4444", animation: "pulse 2s infinite" }} />
                        Session Recording in Progress
                    </div>
                )}
            </header>

            <main className="c-interview-content">
                {!started ? (
                    <>
                        <div className="c-interview-top">
                            <h1>{isPractice ? "Practice Session" : "Official B2B Interview"}</h1>
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
                                        <span className="c-strat-val">{isPractice ? "15 Min" : dashboard?.interview_duration || "45 Min"}</span>
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
                                            <h4>Audio Only</h4>
                                            <p>This interview uses an AI voice agent. Ensure you are in a quiet environment.</p>
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
                                        <div className="c-sys-label"><Mic size={16} /> Microphone</div>
                                        <div className="c-sys-status ok">Detected</div>
                                    </div>
                                    <div className="c-sys-item">
                                        <div className="c-sys-label"><MonitorSpeaker size={16} /> Speakers</div>
                                        <div className="c-sys-status ok">Detected</div>
                                    </div>
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
                                    <span className="c-meta-value">~ {isPractice ? "15" : parseInt(dashboard?.interview_duration || 45)} Minutes</span>
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
                            <button className="c-start-btn" onClick={handleStart}>
                                <Play size={20} /> Start {isPractice ? "Practice" : "Official Interview"}
                            </button>
                        </div>
                    </>
                ) : (
                    /* Active Interview */
                    <div className="c-active-area">
                        <div style={{ fontSize: 48, fontWeight: 700, fontFamily: "monospace" }}>
                            {timer.format()}
                        </div>
                        
                        <div className="c-pulse-ring">
                            <div className="c-mic-icon">
                                <Mic size={32} />
                            </div>
                        </div>

                        <div style={{ textAlign: "center", maxWidth: 600 }}>
                            <h3 style={{ fontSize: 20, marginBottom: 8, color: "var(--text-secondary)" }}>
                                Topic: {mockQuestions[currentQIndex].topic}
                            </h3>
                            <p style={{ fontSize: 24, fontWeight: 600, lineHeight: 1.4 }}>
                                {mockQuestions[currentQIndex].text}
                            </p>
                        </div>

                        <button className="c-btn c-btn-primary c-btn-lg" onClick={handleNext} style={{ marginTop: 40 }}>
                            Submit Answer <ArrowRight size={18} />
                        </button>
                    </div>
                )}
            </main>
        </div>
    );
}

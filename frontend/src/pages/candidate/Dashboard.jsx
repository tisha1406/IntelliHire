import { motion } from "framer-motion";
import { 
    Play, FileText, Check, Circle, Activity, Video, 
    Calendar, Clock, Languages, BrainCircuit, File, FileDown, Lock, CheckCircle2, ArrowRight,
    Wifi, Monitor, Mic, ShieldCheck, ChevronRight
} from "lucide-react";
import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useCandidateDashboard, useCandidateActivity, useCandidateDocuments } from "../../hooks/candidate/useCandidate";
import "../../styles/candidate/dashboard.css";

const fadeUp = {
    hidden: { opacity: 0, y: 16 },
    show: (i = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.38, delay: i * 0.08 } }),
};

export default function Dashboard() {
    const navigate = useNavigate();

    const { data: dashboard, isLoading } = useCandidateDashboard();
    const { data: activityData } = useCandidateActivity();
    const { data: docsData } = useCandidateDocuments();

    useEffect(() => {
        console.log("Loading candidate dashboard");
    }, []);

    useEffect(() => {
        if (dashboard && !isLoading) {
            console.log("Dashboard API success");
        }
    }, [dashboard, isLoading]);

    if (isLoading) {
        return <div className="c-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading Dashboard...</div>;
    }

    const activities = activityData?.activities || [];
    const documents = docsData?.documents || [];

    const readinessScore = dashboard?.readiness_score || 0;

    // Map backend workflow steps to UI keys
    const getStepState = (stepKey) => {
        const step = dashboard?.steps?.find(s => s.key === stepKey);
        if (stepKey === "analysis") {
            const resumeStep = dashboard?.steps?.find(s => s.key === "resume");
            return resumeStep?.status === "completed" ? "done" : (resumeStep?.status === "in_progress" ? "current" : "locked");
        }
        if (stepKey === "report") {
            const officialStep = dashboard?.steps?.find(s => s.key === "official");
            return dashboard?.stage === "COMPLETED" ? "done" : (officialStep?.status === "completed" ? "current" : "locked");
        }
        return step?.status || "locked";
    };

    const getStepIcon = (state, IconComponent) => {
        if (state === "done") return <Check size={20} />;
        if (state === "locked") return <Lock size={16} style={{opacity: 0.5}} />;
        return <IconComponent size={20} />;
    };

    const getNextAction = () => {
        const action = dashboard?.next_action;
        if (action === "UPLOAD_RESUME") return { title: "Upload Resume", desc: "Upload your latest resume to begin the AI screening.", icon: FileText, cta: "Upload Now", link: "/candidate/resume" };
        if (action === "WAITING_ANALYSIS") return { title: "Analysis Pending", desc: "Our AI is currently reviewing your resume against the job description.", icon: Activity, cta: "View Status", link: "/candidate/resume" };
        if (action === "PRACTICE") return { title: "Practice Interview", desc: "The hiring company recommends completing a practice interview to test your setup.", icon: Play, cta: "Start Practice", link: "/candidate/interview/practice", duration: "10 min" };
        if (action === "OFFICIAL_INTERVIEW") return { title: "Official Interview", desc: `You are ready to begin the official interview for ${dashboard?.company_name}. Ensure you are in a quiet environment.`, icon: Video, cta: "Begin Interview", link: "/candidate/interview/official", duration: dashboard?.interview_duration };
        return { title: "View Final Report", desc: "Your interview has been processed. View your comprehensive performance report.", icon: File, cta: "View Report", link: "/candidate/reports" };
    };

    const nextAction = getNextAction();

    return (
        <div className="c-page">
            <div className="c-dashboard-grid">
                
                {/* 1. ROW 1: Premium Command Center Hero & Next Action */}
                <motion.div className="c-dash-col-8" initial="hidden" animate="show" variants={fadeUp} custom={0}>
                    <div className="c-hero-premium" style={{ padding: '32px', height: '100%', display: 'flex', gap: 24 }}>
                        <div className="c-hero-bg-glow"></div>
                        
                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', zIndex: 1 }}>
                            <h1 style={{ fontSize: 28, marginBottom: 8, fontWeight: 700, letterSpacing: '-0.5px' }}>Good Afternoon, {dashboard?.candidate_name ? dashboard.candidate_name.split(" ")[0] : "Candidate"}</h1>
                            <p style={{ fontSize: 15, color: 'var(--text-secondary)', marginBottom: 24, lineHeight: 1.5 }}>
                                Your AI interview for <strong style={{ color: 'var(--text)' }}>{dashboard?.company_name}</strong> is ready. 
                                You are applying for the <strong style={{ color: 'var(--text)' }}>{dashboard?.job_position}</strong> role.
                            </p>

                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                <span className="c-hero-chip"><Calendar size={14}/> {dashboard?.deadline || "No Deadline"}</span>
                                <span className="c-hero-chip"><Clock size={14}/> {dashboard?.interview_duration || "45 min"}</span>
                                <span className="c-hero-chip"><Languages size={14}/> {dashboard?.interview_language || "English"}</span>
                                <span className="c-hero-chip"><Mic size={14}/> AI Voice</span>
                                <span className="c-hero-chip"><BrainCircuit size={14}/> {dashboard?.interview_strategy || "Balanced"}</span>
                            </div>
                        </div>

                        <div style={{ flex: '0 0 320px', display: 'flex', flexDirection: 'column', gap: 16, zIndex: 1, justifyContent: 'center' }}>
                            {/* Readiness Widget */}
                            <div className="c-hero-readiness-widget">
                                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                                    <div className="c-readiness-circle-lg" style={{ borderTopColor: readinessScore === 100 ? "#10B981" : "#60A5FA" }}>
                                        {readinessScore}%
                                    </div>
                                    <div>
                                        <h4 style={{ fontSize: 16, marginBottom: 4 }}>{readinessScore === 100 ? "Ready to start" : "Almost ready"}</h4>
                                        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{readinessScore === 100 ? "All steps completed" : "Complete steps to unlock"}</p>
                                    </div>
                                </div>
                                <div style={{ width: '100%', height: 4, background: 'rgba(255,255,255,0.1)', borderRadius: 2, marginTop: 16, overflow: 'hidden' }}>
                                    <div style={{ width: `${readinessScore}%`, height: '100%', background: readinessScore === 100 ? '#10B981' : '#3B82F6', transition: 'width 1s ease' }}></div>
                                </div>
                            </div>

                            {/* AI Insight Card */}
                            <div className="c-hero-ai-insight">
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, color: '#06B6D4' }}>
                                    <BrainCircuit size={16} className="c-pulse-icon" />
                                    <span style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5 }}>AI Insight</span>
                                </div>
                                <p style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.5 }}>
                                    Your resume strongly matches this role. Complete a practice session to test your microphone and maximise your readiness score.
                                </p>
                            </div>
                        </div>
                    </div>
                </motion.div>

                <motion.div className="c-dash-col-4" initial="hidden" animate="show" variants={fadeUp} custom={1}>
                    <div className="c-next-action-card" style={{ height: '100%', flexDirection: 'column', alignItems: 'flex-start', justifyContent: 'space-between', padding: '24px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'flex-start' }}>
                            <div className="c-next-icon" style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#60A5FA', border: '1px solid rgba(59, 130, 246, 0.3)', width: 40, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 12 }}>
                                <nextAction.icon size={20} />
                            </div>
                            <span className="c-badge-pill" style={{ '--accent': '#F59E0B', '--accent-rgb': '245,158,11' }}><div className="c-badge-pill-dot"></div> Action Required</span>
                        </div>
                        <div className="c-next-text" style={{ marginTop: 16, marginBottom: 16, width: '100%' }}>
                            <h3 style={{ fontSize: 18 }}>{nextAction.title}</h3>
                            <p style={{ fontSize: 13 }}>{nextAction.desc}</p>
                            {nextAction.duration && <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 8, display: 'flex', alignItems: 'center', gap: 4 }}><Clock size={12}/> {nextAction.duration}</div>}
                        </div>
                        <Link to={nextAction.link} className="c-next-action-btn" style={{ width: '100%', justifyContent: 'center' }}>
                            {nextAction.cta} <ArrowRight size={16} />
                        </Link>
                    </div>
                </motion.div>

                {/* 2. ROW 2: Horizontal Interview Journey & Readiness */}
                <motion.div className="c-dash-col-8" initial="hidden" animate="show" variants={fadeUp} custom={2}>
                    <div className="c-card c-card-info" style={{ padding: "24px", height: "100%", display: "flex", flexDirection: "column" }}>
                        <h3 className="c-card-title" style={{ fontSize: 14, marginBottom: 24 }}>Workflow Status</h3>
                        <div className="c-journey-container" style={{ paddingBottom: 0, flex: 1, display: 'flex', alignItems: 'center' }}>
                            <div className="c-journey-timeline" style={{ padding: "0 10px", width: "100%" }}>
                                
                                <div className={`c-journey-step ${getStepState("resume")}`}>
                                    {getStepState("resume") === "current" && <div className="c-journey-here">You are here</div>}
                                    <div className="c-journey-icon" style={{ borderColor: getStepState("resume") === "done" ? "#10B981" : "var(--border)", color: getStepState("resume") === "done" ? "#10B981" : "inherit" }}>
                                        {getStepIcon(getStepState("resume"), FileText)}
                                    </div>
                                    <div className="c-journey-text">
                                        <h4 style={{ color: getStepState("resume") === "done" ? "#10B981" : "var(--text)" }}>Resume</h4>
                                        <p>{getStepState("resume") === "done" ? "Completed" : "Action Req"}</p>
                                    </div>
                                </div>
                                
                                <div className={`c-journey-step ${getStepState("analysis")}`}>
                                    {getStepState("analysis") === "current" && <div className="c-journey-here">You are here</div>}
                                    <div className="c-journey-icon" style={{ borderColor: getStepState("analysis") === "done" ? "#06B6D4" : "var(--border)", color: getStepState("analysis") === "done" ? "#06B6D4" : "inherit" }}>
                                        {getStepIcon(getStepState("analysis"), Activity)}
                                    </div>
                                    <div className="c-journey-text">
                                        <h4 style={{ color: getStepState("analysis") === "done" ? "#06B6D4" : "var(--text)" }}>Analysis</h4>
                                        <p>{getStepState("analysis") === "done" ? "Passed ATS" : "Pending"}</p>
                                    </div>
                                </div>

                                <div className={`c-journey-step ${getStepState("practice")}`}>
                                    {getStepState("practice") === "current" && <div className="c-journey-here">You are here</div>}
                                    <div className="c-journey-icon" style={{ borderColor: getStepState("practice") === "done" ? "#8B5CF6" : "var(--border)", color: getStepState("practice") === "done" ? "#8B5CF6" : "inherit" }}>
                                        {getStepIcon(getStepState("practice"), Play)}
                                    </div>
                                    <div className="c-journey-text">
                                        <h4 style={{ color: getStepState("practice") === "done" ? "#8B5CF6" : "var(--text)" }}>Practice</h4>
                                        <p>{getStepState("practice") === "done" ? "Completed" : "Recommended"}</p>
                                    </div>
                                </div>

                                <div className={`c-journey-step ${getStepState("official")}`}>
                                    {getStepState("official") === "current" && <div className="c-journey-here">You are here</div>}
                                    <div className="c-journey-icon" style={{ borderColor: getStepState("official") === "done" ? "#3B82F6" : "var(--border)", color: getStepState("official") === "done" ? "#3B82F6" : "inherit" }}>
                                        {getStepIcon(getStepState("official"), Video)}
                                    </div>
                                    <div className="c-journey-text">
                                        <h4 style={{ color: getStepState("official") === "done" ? "#3B82F6" : "var(--text)" }}>Interview</h4>
                                        <p>{getStepState("official") === "done" ? "Recorded" : "Required"}</p>
                                    </div>
                                </div>

                                <div className={`c-journey-step ${getStepState("report")}`}>
                                    {getStepState("report") === "current" && <div className="c-journey-here">You are here</div>}
                                    <div className="c-journey-icon" style={{ borderColor: getStepState("report") === "done" ? "#D946EF" : "var(--border)", color: getStepState("report") === "done" ? "#D946EF" : "inherit" }}>
                                        {getStepIcon(getStepState("report"), File)}
                                    </div>
                                    <div className="c-journey-text">
                                        <h4 style={{ color: getStepState("report") === "done" ? "#D946EF" : "var(--text)" }}>Report</h4>
                                        <p>{getStepState("report") === "done" ? "Available" : "Locked"}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </motion.div>

                <motion.div className="c-dash-col-4" initial="hidden" animate="show" variants={fadeUp} custom={3}>
                    <div className="c-card c-card-primary" style={{ padding: "24px", height: "100%", display: 'flex', flexDirection: 'column' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                            <h3 className="c-card-title" style={{ fontSize: 14 }}>Readiness & Hardware</h3>
                            <div className="c-readiness-circle" style={{ width: 32, height: 32, fontSize: 11, margin: 0, borderWidth: 3 }}>{readinessScore}%</div>
                        </div>
                        <div className="c-checklist" style={{ marginBottom: 16 }}>
                            <div className="c-check-item">
                                <div className={`c-check-icon ${getStepState("resume") === "done" ? "done" : "pending"}`}>{getStepState("resume") === "done" && <Check size={12}/>}</div>
                                Resume Uploaded
                            </div>
                            <div className="c-check-item">
                                <div className={`c-check-icon ${getStepState("practice") === "done" ? "done" : "pending"}`}>{getStepState("practice") === "done" && <Check size={12}/>}</div>
                                Practice Completed
                            </div>
                        </div>
                        <div className="c-widget-grid" style={{ marginTop: 'auto', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
                            <div className="c-widget" style={{ padding: '12px 8px', flexDirection: 'column', alignItems: 'flex-start', gap: 6, background: 'rgba(255,255,255,0.03)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.05)' }}>
                                <Wifi size={14} color="#10B981"/> 
                                <span style={{fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)'}}>Network Stable</span>
                            </div>
                            <div className="c-widget" style={{ padding: '12px 8px', flexDirection: 'column', alignItems: 'flex-start', gap: 6, background: 'rgba(255,255,255,0.03)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.05)' }}>
                                <Monitor size={14} color="#10B981"/> 
                                <span style={{fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)'}}>Browser OK</span>
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* 3. ROW 3: State-Aware Widgets */}
                <motion.div className="c-dash-col-4" initial="hidden" animate="show" variants={fadeUp} custom={4}>
                    <Link to="/candidate/resume" className={`c-action-card-status ${getStepState("analysis")} c-accent-ai c-card`} style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12, textDecoration: 'none', height: '100%' }}>
                        <div className="c-action-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div className="c-action-icon-lg" style={{ background: 'rgba(var(--accent-rgb), 0.1)', color: 'var(--accent)', border: '1px solid rgba(var(--accent-rgb), 0.2)', padding: 12, borderRadius: 12 }}><FileText size={24} /></div>
                            {getStepState("analysis") === "done" && <span className="c-badge-pill" style={{ '--accent': '#10B981', '--accent-rgb': '16, 185, 129' }}><div className="c-badge-pill-dot"></div> Passed</span>}
                        </div>
                        <div>
                            <h3 style={{ color: 'var(--text)', fontSize: 16, marginBottom: 4 }}>Resume Analysis</h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.4 }}>Review ATS score, extracted skills, and role compatibility.</p>
                        </div>
                        <div className="c-action-cta" style={{ color: 'var(--accent)', fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4, marginTop: 'auto' }}>
                            {getStepState("analysis") === "done" ? "View ATS Report" : "Awaiting Upload"} <ArrowRight size={14}/>
                        </div>
                    </Link>
                </motion.div>

                <motion.div className="c-dash-col-4" initial="hidden" animate="show" variants={fadeUp} custom={5}>
                    <Link to={getStepState("practice") === "locked" ? "#" : "/candidate/interview/practice"} className={`c-action-card-status ${getStepState("practice")} c-accent-practice c-card`} style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12, textDecoration: 'none', height: '100%' }}>
                        <div className="c-action-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div className="c-action-icon-lg" style={{ background: 'rgba(var(--accent-rgb), 0.1)', color: 'var(--accent)', border: '1px solid rgba(var(--accent-rgb), 0.2)', padding: 12, borderRadius: 12 }}><Play size={24} /></div>
                            {getStepState("practice") === "current" && <span className="c-badge-pill"><div className="c-badge-pill-dot"></div> Recommended</span>}
                            {getStepState("practice") === "done" && <span className="c-badge-pill" style={{ '--accent': '#10B981', '--accent-rgb': '16, 185, 129' }}><div className="c-badge-pill-dot"></div> Completed</span>}
                        </div>
                        <div>
                            <h3 style={{ color: 'var(--text)', fontSize: 16, marginBottom: 4 }}>Practice Session</h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.4 }}>Test your hardware and warm up with mock AI questions.</p>
                        </div>
                        <div className="c-action-cta" style={{ color: 'var(--accent)', fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4, marginTop: 'auto' }}>
                            {getStepState("practice") === "done" ? "Review Recording" : (getStepState("practice") === "current" ? "Start Practice" : "Locked")} <ArrowRight size={14}/>
                        </div>
                    </Link>
                </motion.div>

                <motion.div className="c-dash-col-4" initial="hidden" animate="show" variants={fadeUp} custom={6}>
                    <Link to={getStepState("official") === "locked" ? "#" : "/candidate/interview/official"} className={`c-action-card-status ${getStepState("official")} c-accent-official c-card`} style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12, textDecoration: 'none', height: '100%' }}>
                        <div className="c-action-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div className="c-action-icon-lg" style={{ background: 'rgba(var(--accent-rgb), 0.1)', color: 'var(--accent)', border: '1px solid rgba(var(--accent-rgb), 0.2)', padding: 12, borderRadius: 12 }}><Video size={24} /></div>
                            {getStepState("official") === "locked" && <span className="c-badge-pill" style={{ '--accent': '#64748B', '--accent-rgb': '100, 116, 139' }}><Lock size={12}/> Locked</span>}
                            {getStepState("official") === "current" && <span className="c-badge-pill" style={{ '--accent': '#F59E0B', '--accent-rgb': '245, 158, 11' }}><div className="c-badge-pill-dot"></div> Required</span>}
                            {getStepState("official") === "done" && <span className="c-badge-pill" style={{ '--accent': '#10B981', '--accent-rgb': '16, 185, 129' }}><div className="c-badge-pill-dot"></div> Completed</span>}
                        </div>
                        <div>
                            <h3 style={{ color: 'var(--text)', fontSize: 16, marginBottom: 4 }}>Official Interview</h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.4 }}>Start your official recorded AI interview for {dashboard?.company_name}.</p>
                        </div>
                        <div className="c-action-cta" style={{ color: 'var(--accent)', fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4, marginTop: 'auto' }}>
                            {getStepState("official") === "done" ? "Interview Finished" : (getStepState("official") === "current" ? "Start Official Interview" : "Complete Practice First")} <ArrowRight size={14}/>
                        </div>
                    </Link>
                </motion.div>

                {/* 4. ROW 4: Audit Log & Documents */}
                <motion.div className="c-dash-col-6" initial="hidden" animate="show" variants={fadeUp} custom={7}>
                    <div className="c-card c-card-info" style={{ height: "100%", padding: 20 }}>
                        <div className="c-card-header" style={{ marginBottom: 16 }}>
                            <h3 className="c-card-title" style={{ fontSize: 14 }}>Recent Activity</h3>
                            <button className="c-icon-btn" style={{ fontSize: 11, padding: '4px 8px', width: 'auto', height: 'auto' }}>View All</button>
                        </div>
                        <div className="c-audit-feed" style={{ gap: 12 }}>
                            {activities.slice(0,4).map((activity, idx) => (
                                <div key={activity.id} className="c-audit-item" style={{ paddingBottom: idx === 3 ? 0 : 12, borderBottom: idx === 3 ? 'none' : undefined }}>
                                    <div className="c-audit-time">{new Date(activity.created_at).toLocaleString()}</div>
                                    <div className="c-audit-content">
                                        <h4 style={{ fontSize: 12 }}>{activity.description}</h4>
                                    </div>
                                    <div className="c-audit-status">
                                        <span className="c-badge-pill" style={{ '--accent': '#10B981', '--accent-rgb': '16, 185, 129', fontSize: 9 }}>
                                            <div className="c-badge-pill-dot"></div> {activity.event}
                                        </span>
                                    </div>
                                </div>
                            ))}
                            {activities.length === 0 && <div style={{fontSize: 12, color: "var(--text-muted)", padding: 12}}>No recent activity.</div>}
                        </div>
                    </div>
                </motion.div>

                <motion.div className="c-dash-col-6" initial="hidden" animate="show" variants={fadeUp} custom={8}>
                    <div className="c-card c-card-secondary" style={{ height: "100%", padding: 20 }}>
                        <div className="c-card-header" style={{ marginBottom: 16 }}>
                            <h3 className="c-card-title" style={{ fontSize: 14 }}>Document Center</h3>
                            <button className="c-icon-btn" style={{ fontSize: 11, padding: '4px 8px', width: 'auto', height: 'auto' }}>Manage</button>
                        </div>
                        <div className="c-doc-list">
                            {documents.slice(0,3).map((doc) => (
                                <div key={doc.id} className="c-doc-row" style={{ padding: '8px 0' }}>
                                    <div className="c-doc-left">
                                        <div style={{ padding: 8, background: 'rgba(255,255,255,0.05)', borderRadius: 8 }}><File size={14} color="var(--text-muted)" /></div>
                                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                                            <span style={{ fontSize: 12, fontWeight: 500, color: "var(--text)" }}>{doc.name}</span>
                                            <span style={{ fontSize: 10, color: "var(--text-muted)" }}>{doc.type}</span>
                                        </div>
                                    </div>
                                    <button className="c-icon-btn" title="Download" style={{ width: 28, height: 28 }}><FileDown size={14} /></button>
                                </div>
                            ))}
                            {documents.length === 0 && <div style={{fontSize: 12, color: "var(--text-muted)", padding: 12}}>No documents available.</div>}
                        </div>
                    </div>
                </motion.div>

            </div>
        </div>
    );
}

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useParams, Link } from "react-router-dom";
import { FaArrowLeft, FaDownload, FaPrint, FaCheckCircle, FaTimesCircle, FaSpinner, FaLightbulb } from "react-icons/fa";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import { Target, Activity, Building } from "lucide-react";

import candidateService from "../../services/company/candidateService";
import interviewService from "../../services/company/interviewService";
import Button from "../../components/common/Button";
import StatusBadge from "../../components/common/StatusBadge";

const SCORE_COLOR = (s) => s >= 80 ? "#10B981" : s >= 60 ? "#F59E0B" : "#EF4444";

const ScoreBar = ({ value, color }) => (
    <div style={{ width: "100%", height: 8, background: "rgba(255,255,255,0.07)", borderRadius: 999, overflow: "hidden" }}>
        <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${value}%` }}
            transition={{ duration: 0.8, delay: 0.4 }}
            style={{ height: "100%", background: color, borderRadius: 999 }}
        />
    </div>
);

export default function CandidateReport() {
    const { id } = useParams();
    const [candidate, setCandidate] = useState(null);
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(true);
    const [sessionStatus, setSessionStatus] = useState(null);
    const [completedSessionId, setCompletedSessionId] = useState(null);
    const [isDownloading, setIsDownloading] = useState(false);

    useEffect(() => {
        const fetchCandidate = async () => {
            try {
                setLoading(true);
                const res = await candidateService.getCandidate(id);
                setCandidate(res.data);

                try {
                    const interviewsRes = await interviewService.getInterviews();
                    // Match pending or completed
                    const candidateSessions = (interviewsRes.data?.interviews || interviewsRes.interviews || []).filter(i => String(i.candidate_id) === String(id));
                    const completedSession = candidateSessions.find(i => i.status === "Completed");
                    
                    if (completedSession) {
                        const reportRes = await interviewService.getInterviewResults(completedSession.id);
                        setReport(reportRes.data || reportRes);
                        setCompletedSessionId(completedSession.id);
                    } else if (candidateSessions.length > 0) {
                        setSessionStatus(candidateSessions[0].status);
                    }
                } catch (e) {
                    console.error("Failed to fetch detailed AI report:", e);
                }
            } catch (err) {
                console.error("Failed to fetch candidate report:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchCandidate();
    }, [id]);

    if (loading) {
        return (
            <div style={{ textAlign: "center", padding: "100px 0", color: "var(--text-secondary)" }}>
                <FaSpinner className="spin-icon" style={{ fontSize: 32, marginBottom: 12 }} />
                <p>Retrieving authentic candidate data...</p>
            </div>
        );
    }

    if (!candidate) return <div style={{ padding: 40, color: "var(--text-secondary)" }}>Candidate report not found.</div>;

    const handleDownloadPdf = async () => {
        if (!completedSessionId || isDownloading) return;
        setIsDownloading(true);
        try {
            const res = await interviewService.downloadInterviewResultsPdf(completedSessionId);
            const blob = new Blob([res.data], { type: "application/pdf" });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.setAttribute("download", `interview_report_${completedSessionId}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error("Failed to download report PDF:", err);
        } finally {
            setIsDownloading(false);
        }
    };

    // We do NOT use aiMatch or resumeScore anymore since they are either redundant or unimplemented
    const scoreData = [];
    
    if (report && report.has_report) {
        scoreData.push({ label: "Overall Interview Score", value: report.overall_score || 0 });
        
        // Add up to 3 topics
        const sortedTopics = [...(report.topic_scores || [])].sort((a,b) => b.score_100 - a.score_100).slice(0, 3);
        sortedTopics.forEach(t => {
            scoreData.push({ label: t.topic_name, value: t.score_100 || 0 });
        });
    }

    // Dynamic radar charting based purely on real topics
    const radarData = report?.topic_scores?.map(ts => ({
        subject: ts.topic_name || ts.topic_id,
        A: ts.score_100 || 0,
        fullMark: 100
    })) || [];

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: 28, animation: "fadeInPage 0.4s ease-out" }}>
            <style>{`
                @keyframes fadeInPage { from { opacity:0; transform:translateY(12px);} to {opacity:1; transform:translateY(0);}}
                @media print { .no-print { display: none !important; }}
            `}</style>

            {/* Top bar */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                    <h1 style={{ fontSize: 22, fontWeight: 800, color: "var(--text)", marginBottom: 4 }}>
                        IntelliHire Candidate Report
                    </h1>
                    <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                        Generated · {new Date().toLocaleDateString("en-US", { day: "numeric", month: "long", year: "numeric" })}
                    </p>
                </div>
                <div className="no-print" style={{ display: "flex", gap: 10 }}>
                    <Link to={`/company/candidates/${candidate.id}`}>
                        <Button variant="outline" icon={<FaArrowLeft />} size="sm">Back</Button>
                    </Link>
                    <Button variant="outline" icon={<FaPrint />} size="sm" onClick={() => window.print()}>Print</Button>
                    <Button
                        variant="primary"
                        icon={<FaDownload />}
                        size="sm"
                        onClick={handleDownloadPdf}
                        disabled={!completedSessionId || isDownloading}
                    >
                        {isDownloading ? "Preparing..." : "Download PDF"}
                    </Button>
                </div>
            </div>

            {/* Candidate identity */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-md)", padding: "28px",
                    boxShadow: "var(--shadow)",
                    background: "linear-gradient(135deg, rgba(29,78,216,0.08) 0%, var(--card) 100%)",
                    display: "flex", gap: 24, alignItems: "center"
                }}
            >
                <div style={{
                    width: 72, height: 72, borderRadius: "50%",
                    background: "linear-gradient(135deg, var(--primary), #6366F1)",
                    color: "#fff", fontSize: 24, fontWeight: 800,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    border: "3px solid rgba(255,255,255,0.1)", flexShrink: 0
                }}>
                    {candidate.name?.split(" ").map(n => n[0]).join("").slice(0, 2)}
                </div>
                <div style={{ flex: 1 }}>
                    <h2 style={{ fontSize: 20, fontWeight: 800, color: "var(--text)", marginBottom: 4 }}>{candidate.name}</h2>
                    <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 8 }}>{candidate.experience || "Experience Not Available"}</p>
                    <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>{candidate.education || "Education Not Available"}</p>
                </div>
                <div style={{ textAlign: "right" }}>
                    <StatusBadge status={candidate.status} />
                    <p style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 8 }}>
                        Applied {candidate.applicationDate ? new Date(candidate.applicationDate).toLocaleDateString("en-US", { day: "numeric", month: "short" }) : "Recently"}
                    </p>
                </div>
            </motion.div>

            {/* In-Progress / No Data fallback */}
            {(!report || report.has_report === false) && (
                <div style={{ textAlign: "center", padding: "60px 20px", background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12 }}>
                    <div style={{ width: 64, height: 64, margin: "0 auto", background: "rgba(59,130,246,0.1)", color: "var(--primary)", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 16 }}>
                        <Activity size={32} />
                    </div>
                    <h3 style={{ fontSize: 20, fontWeight: 700, color: "var(--text)", marginBottom: 8 }}>
                        {sessionStatus === "In Progress" ? "Interview In Progress" : "No Report Available"}
                    </h3>
                    <p style={{ color: "var(--text-secondary)", maxWidth: 400, margin: "0 auto", lineHeight: 1.5 }}>
                        {sessionStatus === "In Progress" 
                            ? "The candidate is currently completing their interview. Check back soon for the full AI evaluation." 
                            : report?.message || "There is no completed interview report for this candidate yet."}
                    </p>
                </div>
            )}

            {/* Score breakdown & Real Evaluation */}
            {report && report.has_report && (
                <>
                    {scoreData.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.15 }}
                            style={{
                                background: "var(--card)", border: "1px solid var(--border)",
                                borderRadius: "var(--radius-md)", padding: "28px",
                                boxShadow: "var(--shadow)"
                            }}
                        >
                            <h4 style={{ fontSize: 15, fontWeight: 700, color: "var(--text)", marginBottom: 22 }}>
                                <Target size={16} style={{ color: "var(--primary)", marginRight: 8, display: "inline" }} />
                                Authentic Score Breakdown
                            </h4>
                            <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                                {scoreData.map(s => (
                                    <div key={s.label}>
                                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                                            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>{s.label}</span>
                                            <span style={{ fontSize: 14, fontWeight: 800, color: SCORE_COLOR(s.value) }}>{s.value}/100</span>
                                        </div>
                                        <ScoreBar value={s.value} color={SCORE_COLOR(s.value)} />
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* Detailed Topic Evaluation */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.35 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", padding: "28px", boxShadow: "var(--shadow)"
                        }}
                    >
                        <h4 style={{ fontSize: 15, fontWeight: 700, color: "var(--text)", marginBottom: 24 }}>Detailed Topic Evaluation</h4>
                        <div style={{ display: "flex", gap: 32, flexWrap: "wrap", alignItems: "flex-start", justifyContent: "center" }}>
                            {radarData.length >= 3 ? (
                                <div style={{ width: 400, height: 350 }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                                            <PolarGrid stroke="var(--border)" />
                                            <PolarAngleAxis dataKey="subject" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} />
                                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                            <Radar name="Candidate" dataKey="A" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.3} strokeWidth={2} />
                                        </RadarChart>
                                    </ResponsiveContainer>
                                </div>
                            ) : (
                                <div style={{ width: 400, height: 200, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)", fontSize: 14, textAlign: "center" }}>
                                    Not enough specific topic dimensions to plot radar chart.
                                </div>
                            )}
                            
                            <div style={{ flex: 1, minWidth: 280, display: "flex", flexDirection: "column", gap: 20 }}>
                                {report.company_remarks && (
                                    <div style={{ padding: 16, background: "rgba(59, 130, 246, 0.05)", border: "1px solid rgba(59, 130, 246, 0.2)", borderRadius: 8 }}>
                                        <div style={{ fontSize: 13, fontWeight: 700, color: "#3B82F6", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                                            <Building size={14} /> Hiring Manager Remarks
                                        </div>
                                        <p style={{ fontSize: 13, color: "var(--text)", lineHeight: 1.5, margin: 0 }}>
                                            "{report.company_remarks}"
                                        </p>
                                    </div>
                                )}
                                <div>
                                    <h5 style={{ fontSize: 14, color: "#10B981", marginBottom: 12, display: "flex", alignItems: "center", gap: 6 }}>
                                        <FaCheckCircle /> Identified Strengths
                                    </h5>
                                    {report.strengths?.length > 0 ? (
                                        <ul style={{ margin: 0, paddingLeft: 18, color: "var(--text)", fontSize: 13, lineHeight: 1.6 }}>
                                            {report.strengths.map((str, i) => <li key={i} style={{marginBottom: 8}}>{str}</li>)}
                                        </ul>
                                    ) : (
                                        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>No specific strengths highlighted.</div>
                                    )}
                                </div>
                                <div>
                                    <h5 style={{ fontSize: 14, color: "#EF4444", marginBottom: 12, display: "flex", alignItems: "center", gap: 6 }}>
                                        <FaTimesCircle /> Areas for Improvement
                                    </h5>
                                    {report.weaknesses?.length > 0 ? (
                                        <ul style={{ margin: 0, paddingLeft: 18, color: "var(--text)", fontSize: 13, lineHeight: 1.6 }}>
                                            {report.weaknesses.map((wk, i) => <li key={i} style={{marginBottom: 8}}>{wk}</li>)}
                                        </ul>
                                    ) : (
                                        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>No specific weaknesses highlighted.</div>
                                    )}
                                </div>
                                <div>
                                    <h5 style={{ fontSize: 14, color: "#F59E0B", marginBottom: 12, display: "flex", alignItems: "center", gap: 6 }}>
                                        <FaLightbulb /> AI Recommendations
                                    </h5>
                                    {report.improvement_suggestions?.length > 0 ? (
                                        <ul style={{ margin: 0, paddingLeft: 18, color: "var(--text)", fontSize: 13, lineHeight: 1.6 }}>
                                            {report.improvement_suggestions.map((wk, i) => <li key={i} style={{marginBottom: 8}}>{wk}</li>)}
                                        </ul>
                                    ) : (
                                        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>No specific recommendations.</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </motion.div>
                    
                    {/* Question Feedback Breakdown */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", padding: "28px", boxShadow: "var(--shadow)",
                            marginBottom: 40
                        }}
                    >
                        <h4 style={{ fontSize: 15, fontWeight: 700, color: "var(--text)", marginBottom: 20 }}>Question-by-Question Breakdown</h4>
                        {report.question_feedback?.length > 0 ? (
                            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                                {report.question_feedback.map((q, idx) => (
                                    <div key={idx} style={{ padding: "16px", border: "1px solid var(--border)", borderRadius: 12, background: "var(--surface)" }}>
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                                            <div>
                                                <span style={{ fontSize: 12, fontWeight: 600, color: "var(--primary)", marginBottom: 4, display: "block" }}>{q.topic || q.topic_id}</span>
                                                <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", lineHeight: 1.5 }}>{q.question}</div>
                                            </div>
                                            <div style={{ fontSize: 18, fontWeight: 800, color: SCORE_COLOR(q.score_100 || 0), flexShrink: 0, marginLeft: 16 }}>
                                                {q.score_100 || 0}/100
                                            </div>
                                        </div>
                                        <div style={{ padding: "12px", background: "rgba(255,255,255,0.03)", borderRadius: 8, fontSize: 13.5, color: "var(--text-secondary)", lineHeight: 1.6, borderLeft: "3px solid var(--border)" }}>
                                            {q.coverage_signal === "qualitatively_covered" ? "Answer was considered comprehensive." 
                                            : q.coverage_signal === "insufficient_detail" ? "Answer lacked sufficient detail."
                                            : q.coverage_signal === "missing" ? "No valid answer provided."
                                            : "Answer partially covered the required areas."} 
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div style={{ padding: 24, textAlign: "center", color: "var(--text-muted)", fontSize: 14 }}>
                                No specific question feedback was recorded.
                            </div>
                        )}
                    </motion.div>
                </>
            )}
        </div>
    );
}

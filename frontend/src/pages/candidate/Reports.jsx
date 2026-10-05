import { motion } from "framer-motion";
import { 
    Target, Activity, FileText, Zap, BrainCircuit, HeartHandshake, 
    Clock, CheckCircle2, AlertTriangle, Download, Building, Info,
    Lock
} from "lucide-react";
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from "recharts";
import { useSearchParams } from "react-router-dom";
import { useState } from "react";
import { useInterviewReport } from "../../hooks/candidate/useCandidate";
import { useAuthContext } from "../../context/AuthContext";
import { downloadInterviewReportPdf } from "../../api/candidate";
import { campaignConfig, candidateJourney } from "../../data/candidate/placeholderData";

const fadeUp = {
    hidden: { opacity: 0, y: 16 },
    show: (i = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.38, delay: i * 0.08 } }),
};

export default function Reports() {
    const [searchParams] = useSearchParams();
    const sessionId = searchParams.get("session_id");

    const { data: report, isLoading, error } = useInterviewReport(sessionId);
    const { token } = useAuthContext();
    const [isDownloading, setIsDownloading] = useState(false);

    const handleDownloadPdf = async () => {
        if (!sessionId || isDownloading) return;
        setIsDownloading(true);
        try {
            const blob = await downloadInterviewReportPdf(token, sessionId);
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = `interview_report_${sessionId}.pdf`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (e) {
            console.error("Failed to download report PDF:", e);
        } finally {
            setIsDownloading(false);
        }
    };

    if (!sessionId) {
        return (
            <div className="c-page">
                <div className="c-page-header">
                    <div>
                        <h1 className="c-page-title">Candidate Report</h1>
                        <p className="c-page-subtitle">No interview session selected.</p>
                    </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "50vh", textAlign: "center", gap: 24 }}>
                    <div style={{ width: 80, height: 80, borderRadius: "50%", background: "rgba(59, 130, 246, 0.1)", display: "flex", alignItems: "center", justifyContent: "center", color: "#3B82F6" }}>
                        <Info size={32} />
                    </div>
                    <div>
                        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8, color: "var(--text)" }}>Please select a session</h2>
                        <p style={{ fontSize: 15, color: "var(--text-secondary)", maxWidth: 500, margin: "0 auto", lineHeight: 1.5 }}>
                            Complete an interview or select a valid session from your dashboard to view its report.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="c-page">
                <div className="c-page-header">
                    <div>
                        <h1 className="c-page-title">Candidate Report</h1>
                        <p className="c-page-subtitle">Loading your interview analysis...</p>
                    </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "50vh" }}>
                    <div style={{ animation: "pulse 2s infinite", color: "var(--primary)" }}>Loading report...</div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="c-page">
                <div className="c-page-header">
                    <div>
                        <h1 className="c-page-title">Candidate Report</h1>
                        <p className="c-page-subtitle">Failed to load report</p>
                    </div>
                </div>
                <div style={{ padding: 24, background: "rgba(239, 68, 68, 0.1)", color: "#EF4444", borderRadius: 8, textAlign: "center" }}>
                    An error occurred while fetching the interview report.
                </div>
            </div>
        );
    }

    // Rich Empty State for Pending Report (IN_PROGRESS or COMPLETED_NO_DATA)
    if (!report || report.has_report === false) {
        return (
            <div className="c-page">
                <div className="c-page-header">
                    <div>
                        <h1 className="c-page-title">Candidate Report</h1>
                        <p className="c-page-subtitle">Your final interview analysis and score breakdown.</p>
                    </div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "50vh", textAlign: "center", gap: 24 }}>
                    <div style={{ width: 80, height: 80, borderRadius: "50%", background: "rgba(59, 130, 246, 0.1)", display: "flex", alignItems: "center", justifyContent: "center", color: "#3B82F6", animation: "pulse 3s infinite" }}>
                        <Lock size={32} />
                    </div>
                    <div>
                        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8, color: "var(--text)" }}>Report Pending Analysis</h2>
                        <p style={{ fontSize: 15, color: "var(--text-secondary)", maxWidth: 500, margin: "0 auto", lineHeight: 1.5 }}>
                            {report?.status === "IN_PROGRESS"
                                ? "You have not completed your official interview yet. The report will be generated automatically once your session is finished."
                                : report?.message || "Your official interview has been recorded. The AI is currently processing the audio and generating a comprehensive score breakdown."
                            }
                        </p>
                    </div>

                    <div className="c-card" style={{ width: "100%", maxWidth: 600, marginTop: 16, textAlign: "left" }}>
                        <div className="c-card-header"><h3 className="c-card-title" style={{ fontSize: 14 }}>Expected Content</h3></div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, padding: "8px 0" }}>
                            <span className="c-tag"><Target size={12} style={{display:"inline"}}/> Overall Score</span>
                            <span className="c-tag"><Activity size={12} style={{display:"inline"}}/> Topic Breakdown</span>
                            <span className="c-tag"><FileText size={12} style={{display:"inline"}}/> Question Feedback</span>
                            <span className="c-tag"><CheckCircle2 size={12} style={{display:"inline"}}/> Strengths & Weaknesses</span>
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    // Map topic scores to Radar chart data
    const radarData = report.topic_scores?.map(ts => ({
        subject: ts.topic_name || ts.topic_id,
        A: ts.score_100 || 0,
        fullMark: 100
    })) || [];

    // Map topic scores to Stat cards
    const statCards = [
        { label: "Overall Score", value: report.overall_score || 0, color: campaignConfig.companyColor, icon: <Target size={14} /> }
    ];
    
    // Add up to 7 topics to the stat cards dynamically
    const colors = ["#8B5CF6", "#10B981", "#F59E0B", "#EC4899", "#14B8A6", "#6366F1", "#06B6D4"];
    (report.topic_scores || []).slice(0, 7).forEach((ts, idx) => {
        statCards.push({
            label: ts.topic_name || ts.topic_id,
            value: ts.score_100 || 0,
            color: colors[idx % colors.length],
            icon: <Activity size={14} />
        });
    });

    return (
        <div className="c-page">
            <motion.div className="c-page-header" variants={fadeUp} initial="hidden" animate="show">
                <div>
                    <h1 className="c-page-title">Candidate Report</h1>
                    <p className="c-page-subtitle">Detailed AI analysis of your official interview for {campaignConfig.companyName}</p>
                </div>
                <div className="c-page-actions">
                    <button
                        className="c-btn c-btn-primary"
                        style={{ background: campaignConfig.companyColor }}
                        onClick={handleDownloadPdf}
                        disabled={isDownloading}
                    >
                        <Download size={15} /> {isDownloading ? "Preparing..." : "Download PDF"}
                    </button>
                </div>
            </motion.div>

            {/* Top Stats */}
            <motion.div custom={1} variants={fadeUp} initial="hidden" animate="show"
                style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 24 }}>
                {statCards.map((s) => (
                    <div key={s.label} className="c-card" style={{ display: "flex", flexDirection: "column", gap: 12, padding: "16px 20px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "var(--text-secondary)", fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {s.icon} {s.label}
                        </div>
                        <div style={{ fontSize: 32, fontWeight: 800, color: s.color, lineHeight: 1 }}>{s.value}<span style={{fontSize: 16, color: "var(--text-muted)"}}>/100</span></div>
                    </div>
                ))}
            </motion.div>

            <div className="c-two-col" style={{ marginBottom: 24 }}>
                {/* Radar Chart */}
                <motion.div custom={2} variants={fadeUp} initial="hidden" animate="show" className="c-card">
                    <div className="c-card-title" style={{ marginBottom: 24 }}>Topic Mastery Radar</div>
                    <div style={{ height: 320, width: "100%" }}>
                        {radarData.length >= 3 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart data={radarData} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                                    <PolarGrid stroke="var(--border-subtle)" />
                                    <PolarAngleAxis dataKey="subject" tick={{ fill: "var(--text-muted)", fontSize: 12 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                    <Radar name="Score" dataKey="A" stroke={campaignConfig.companyColor} fill={campaignConfig.companyColor} fillOpacity={0.2} strokeWidth={2} />
                                </RadarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div style={{ display: "flex", height: "100%", alignItems: "center", justifyContent: "center", color: "var(--text-muted)", fontSize: 14 }}>
                                Not enough topics for radar chart
                            </div>
                        )}
                    </div>
                </motion.div>

                {/* AI Feedback & Company Remarks */}
                <motion.div custom={3} variants={fadeUp} initial="hidden" animate="show" className="c-card" style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                    
                    {report.company_remarks && (
                        <div style={{ padding: 16, background: "rgba(59, 130, 246, 0.05)", border: "1px solid rgba(59, 130, 246, 0.2)", borderRadius: 8 }}>
                            <div style={{ fontSize: 14, fontWeight: 700, color: "#3B82F6", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                                <Building size={16} /> Hiring Manager Remarks
                            </div>
                            <p style={{ fontSize: 14, color: "var(--text)", lineHeight: 1.5, margin: 0 }}>
                                "{report.company_remarks}"
                            </p>
                        </div>
                    )}

                    <div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--success)", marginBottom: 12, display: "flex", alignItems: "center", gap: 6 }}>
                            <CheckCircle2 size={16} /> Key Strengths
                        </div>
                        {(report.strengths || []).length > 0 ? (
                            <ul style={{ margin: 0, paddingLeft: 16, fontSize: 14, color: "var(--text)", display: "flex", flexDirection: "column", gap: 10, lineHeight: 1.5 }}>
                                {report.strengths.map((s,i) => <li key={i}>{s}</li>)}
                            </ul>
                        ) : (
                            <p style={{ margin: 0, fontSize: 14, color: "var(--text-muted)" }}>No specific strengths highlighted.</p>
                        )}
                    </div>
                    <div className="c-divider" />
                    <div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--danger)", marginBottom: 12, display: "flex", alignItems: "center", gap: 6 }}>
                            <AlertTriangle size={16} /> Areas for Improvement
                        </div>
                        {(report.weaknesses || []).length > 0 ? (
                            <ul style={{ margin: 0, paddingLeft: 16, fontSize: 14, color: "var(--text)", display: "flex", flexDirection: "column", gap: 10, lineHeight: 1.5 }}>
                                {report.weaknesses.map((w,i) => <li key={i}>{w}</li>)}
                            </ul>
                        ) : (
                            <p style={{ margin: 0, fontSize: 14, color: "var(--text-muted)" }}>No specific weaknesses highlighted.</p>
                        )}
                    </div>
                    <div className="c-divider" />
                    <div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--warning)", marginBottom: 12, display: "flex", alignItems: "center", gap: 6 }}>
                            <Info size={16} /> AI Recommendations
                        </div>
                        {(report.improvement_suggestions || []).length > 0 ? (
                            <ul style={{ margin: 0, paddingLeft: 16, fontSize: 14, color: "var(--text)", display: "flex", flexDirection: "column", gap: 10, lineHeight: 1.5 }}>
                                {report.improvement_suggestions.map((w,i) => <li key={i}>{w}</li>)}
                            </ul>
                        ) : (
                            <p style={{ margin: 0, fontSize: 14, color: "var(--text-muted)" }}>No specific recommendations at this time.</p>
                        )}
                    </div>
                </motion.div>
            </div>

            {/* Question Breakdown */}
            <motion.div custom={4} variants={fadeUp} initial="hidden" animate="show" className="c-card">
                <div className="c-card-title" style={{ marginBottom: 20 }}>Question Breakdown</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    {(report.question_feedback || []).length > 0 ? report.question_feedback.map((q) => (
                        <div key={q.id || q.question_record_id} style={{ padding: "16px", border: "1px solid var(--border)", borderRadius: 12, background: "var(--surface)" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                                <div>
                                    <span style={{ fontSize: 12, fontWeight: 600, color: "var(--primary)", marginBottom: 4, display: "block" }}>{q.topic || q.topic_id}</span>
                                    <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text)" }}>{q.question}</div>
                                </div>
                                <div style={{ fontSize: 20, fontWeight: 800, color: (q.score_100 || 0) > 75 ? "var(--success)" : (q.score_100 || 0) > 50 ? "var(--warning)" : "var(--danger)" }}>
                                    {q.score_100 || 0}/100
                                </div>
                            </div>
                            <div style={{ padding: "12px", background: "rgba(255,255,255,0.03)", borderRadius: 8, fontSize: 13.5, color: "var(--text-secondary)", lineHeight: 1.6, borderLeft: "3px solid var(--border)" }}>
                                {q.coverage_signal === "qualitatively_covered" ? "Answer was considered comprehensive." 
                                : q.coverage_signal === "insufficient_detail" ? "Answer lacked sufficient detail."
                                : q.coverage_signal === "missing" ? "No valid answer provided."
                                : "Answer partially covered the required areas."} 
                                {/* 
                                   Note: Current real API response from InterviewResultService does not seem to include a rich 'feedback' string per question. 
                                   It includes coverage_signal, follow_up_signal, etc. We map it logically here. 
                                */}
                            </div>
                        </div>
                    )) : (
                        <p style={{ margin: 0, fontSize: 14, color: "var(--text-muted)" }}>No question feedback recorded.</p>
                    )}
                </div>
            </motion.div>
        </div>
    );
}

import { motion } from "framer-motion";
import { 
    Target, Activity, FileText, Zap, BrainCircuit, HeartHandshake, 
    Clock, CheckCircle2, AlertTriangle, Download, Building, Info,
    Lock
} from "lucide-react";
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from "recharts";
import { interviewReportsData, campaignConfig, candidateJourney } from "../../data/candidate/placeholderData";

const fadeUp = {
    hidden: { opacity: 0, y: 16 },
    show: (i = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.38, delay: i * 0.08 } }),
};

export default function Reports() {
    
    // Rich Empty State for Pending Report
    if (!interviewReportsData.hasReport) {
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
                            {candidateJourney.officialCompleted 
                                ? "Your official interview has been recorded. The AI is currently processing the audio and generating a comprehensive score breakdown."
                                : "You have not completed your official interview yet. The report will be generated automatically once your session is finished."
                            }
                        </p>
                    </div>

                    <div className="c-card" style={{ width: "100%", maxWidth: 600, marginTop: 16, textAlign: "left" }}>
                        <div className="c-card-header"><h3 className="c-card-title" style={{ fontSize: 14 }}>Expected Content</h3></div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, padding: "8px 0" }}>
                            <span className="c-tag"><Target size={12} style={{display:"inline"}}/> Overall Score</span>
                            <span className="c-tag"><Activity size={12} style={{display:"inline"}}/> Technical Accuracy</span>
                            <span className="c-tag"><FileText size={12} style={{display:"inline"}}/> Communication</span>
                            <span className="c-tag"><BrainCircuit size={12} style={{display:"inline"}}/> Problem Solving</span>
                            <span className="c-tag"><Clock size={12} style={{display:"inline"}}/> Time Management</span>
                            <span className="c-tag"><Building size={12} style={{display:"inline"}}/> Company Remarks</span>
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="c-page">
            <motion.div className="c-page-header" variants={fadeUp} initial="hidden" animate="show">
                <div>
                    <h1 className="c-page-title">Candidate Report</h1>
                    <p className="c-page-subtitle">Detailed AI analysis of your official interview for {campaignConfig.companyName}</p>
                </div>
                <div className="c-page-actions">
                    <button className="c-btn c-btn-primary" style={{ background: campaignConfig.companyColor }}>
                        <Download size={15} /> Download PDF
                    </button>
                </div>
            </motion.div>

            {/* Top Stats */}
            <motion.div custom={1} variants={fadeUp} initial="hidden" animate="show"
                style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 24 }}>
                {[
                    { label: "Overall Score", value: interviewReportsData.overallScore, color: campaignConfig.companyColor, icon: <Target size={14} /> },
                    { label: "Technical", value: interviewReportsData.technicalScore, color: "#8B5CF6", icon: <Activity size={14} /> },
                    { label: "Communication", value: interviewReportsData.communicationScore, color: "#10B981", icon: <FileText size={14} /> },
                    { label: "Confidence", value: interviewReportsData.confidence, color: "#F59E0B", icon: <Zap size={14} /> },
                    { label: "Problem Solving", value: interviewReportsData.problemSolving, color: "#EC4899", icon: <BrainCircuit size={14} /> },
                    { label: "Soft Skills", value: interviewReportsData.softSkills, color: "#14B8A6", icon: <HeartHandshake size={14} /> },
                    { label: "Time Mgmt", value: interviewReportsData.timeManagement, color: "#6366F1", icon: <Clock size={14} /> },
                    { label: "Resume Match", value: interviewReportsData.resumeMatch, color: "#06B6D4", icon: <FileText size={14} /> },
                ].map((s) => (
                    <div key={s.label} className="c-card" style={{ display: "flex", flexDirection: "column", gap: 12, padding: "16px 20px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "var(--text-secondary)", fontWeight: 500 }}>
                            {s.icon} {s.label}
                        </div>
                        <div style={{ fontSize: 32, fontWeight: 800, color: s.color, lineHeight: 1 }}>{s.value}<span style={{fontSize: 16, color: "var(--text-muted)"}}>/100</span></div>
                    </div>
                ))}
            </motion.div>

            <div className="c-two-col" style={{ marginBottom: 24 }}>
                {/* Radar Chart */}
                <motion.div custom={2} variants={fadeUp} initial="hidden" animate="show" className="c-card">
                    <div className="c-card-title" style={{ marginBottom: 24 }}>Skill Distribution Radar</div>
                    <div style={{ height: 320, width: "100%" }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <RadarChart data={interviewReportsData.radarData} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                                <PolarGrid stroke="var(--border-subtle)" />
                                <PolarAngleAxis dataKey="subject" tick={{ fill: "var(--text-muted)", fontSize: 12 }} />
                                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                <Radar name="Score" dataKey="A" stroke={campaignConfig.companyColor} fill={campaignConfig.companyColor} fillOpacity={0.2} strokeWidth={2} />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* AI Feedback & Company Remarks */}
                <motion.div custom={3} variants={fadeUp} initial="hidden" animate="show" className="c-card" style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                    
                    {interviewReportsData.companyRemarks && (
                        <div style={{ padding: 16, background: "rgba(59, 130, 246, 0.05)", border: "1px solid rgba(59, 130, 246, 0.2)", borderRadius: 8 }}>
                            <div style={{ fontSize: 14, fontWeight: 700, color: "#3B82F6", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                                <Building size={16} /> Hiring Manager Remarks
                            </div>
                            <p style={{ fontSize: 14, color: "var(--text)", lineHeight: 1.5, margin: 0 }}>
                                "{interviewReportsData.companyRemarks}"
                            </p>
                        </div>
                    )}

                    <div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--success)", marginBottom: 12, display: "flex", alignItems: "center", gap: 6 }}>
                            <CheckCircle2 size={16} /> Key Strengths
                        </div>
                        <ul style={{ margin: 0, paddingLeft: 16, fontSize: 14, color: "var(--text)", display: "flex", flexDirection: "column", gap: 10, lineHeight: 1.5 }}>
                            {interviewReportsData.strengths.map((s,i) => <li key={i}>{s}</li>)}
                        </ul>
                    </div>
                    <div className="c-divider" />
                    <div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--danger)", marginBottom: 12, display: "flex", alignItems: "center", gap: 6 }}>
                            <AlertTriangle size={16} /> Areas for Improvement
                        </div>
                        <ul style={{ margin: 0, paddingLeft: 16, fontSize: 14, color: "var(--text)", display: "flex", flexDirection: "column", gap: 10, lineHeight: 1.5 }}>
                            {interviewReportsData.weaknesses.map((w,i) => <li key={i}>{w}</li>)}
                        </ul>
                    </div>
                    <div className="c-divider" />
                    <div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--warning)", marginBottom: 12, display: "flex", alignItems: "center", gap: 6 }}>
                            <Info size={16} /> AI Recommendations
                        </div>
                        <ul style={{ margin: 0, paddingLeft: 16, fontSize: 14, color: "var(--text)", display: "flex", flexDirection: "column", gap: 10, lineHeight: 1.5 }}>
                            {interviewReportsData.improvementSuggestions.map((w,i) => <li key={i}>{w}</li>)}
                        </ul>
                    </div>
                </motion.div>
            </div>

            {/* Question Breakdown */}
            <motion.div custom={4} variants={fadeUp} initial="hidden" animate="show" className="c-card">
                <div className="c-card-title" style={{ marginBottom: 20 }}>Question Breakdown</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    {interviewReportsData.questionFeedback.map((q) => (
                        <div key={q.id} style={{ padding: "16px", border: "1px solid var(--border)", borderRadius: 12, background: "var(--surface)" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                                <div>
                                    <span style={{ fontSize: 12, fontWeight: 600, color: "var(--primary)", marginBottom: 4, display: "block" }}>{q.topic}</span>
                                    <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text)" }}>{q.question}</div>
                                </div>
                                <div style={{ fontSize: 20, fontWeight: 800, color: q.score > 75 ? "var(--success)" : q.score > 50 ? "var(--warning)" : "var(--danger)" }}>
                                    {q.score}/100
                                </div>
                            </div>
                            <div style={{ padding: "12px", background: "rgba(255,255,255,0.03)", borderRadius: 8, fontSize: 13.5, color: "var(--text-secondary)", lineHeight: 1.6, borderLeft: "3px solid var(--border)" }}>
                                {q.feedback}
                            </div>
                        </div>
                    ))}
                </div>
            </motion.div>
        </div>
    );
}

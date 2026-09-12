import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useParams, Link } from "react-router-dom";
import { FaArrowLeft, FaDownload, FaPrint, FaStar, FaCheckCircle, FaTimesCircle, FaSpinner } from "react-icons/fa";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";

import candidateService from "../../services/company/candidateService";
import interviewService from "../../services/company/interviewService";
import Button from "../../components/common/Button";
import StatusBadge from "../../components/common/StatusBadge";

const SCORE_COLOR = (s) => s >= 90 ? "#10B981" : s >= 75 ? "#F59E0B" : "#EF4444";

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

    useEffect(() => {
        const fetchCandidate = async () => {
            try {
                setLoading(true);
                const res = await candidateService.getCandidate(id);
                setCandidate(res.data);

                try {
                    const interviewsRes = await interviewService.getInterviews();
                    const session = interviewsRes.interviews?.find(i => String(i.candidate_id) === String(id) && i.status === "Completed");
                    if (session) {
                        const reportRes = await interviewService.getInterviewResults(session.id);
                        setReport(reportRes);
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
                <p>Generating report...</p>
            </div>
        );
    }

    if (!candidate) return <div style={{ padding: 40, color: "var(--text-secondary)" }}>Candidate report not found.</div>;

    const aiMatch = candidate.aiMatch ?? candidate.match_score ?? 88;
    const resumeScore = candidate.resumeScore ?? 85;
    const interviewScore = candidate.interviewScore ?? 85;

    const scoreData = [
        { label: "AI Match Score", value: aiMatch },
        { label: "Resume Score", value: resumeScore },
        { label: "Interview Score", value: interviewScore },
        { label: "Overall Rating", value: Math.round((aiMatch + resumeScore + interviewScore) / 3) },
    ];

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
                        AI Candidate Report
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
                    <Button variant="primary" icon={<FaDownload />} size="sm">Download PDF</Button>
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
                    {candidate.name.split(" ").map(n => n[0]).join("").slice(0, 2)}
                </div>
                <div style={{ flex: 1 }}>
                    <h2 style={{ fontSize: 20, fontWeight: 800, color: "var(--text)", marginBottom: 4 }}>{candidate.name}</h2>
                    <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 8 }}>{candidate.experience}</p>
                    <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>{candidate.education}</p>
                </div>
                <div style={{ textAlign: "right" }}>
                    <StatusBadge status={candidate.status} />
                    <p style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 8 }}>
                        Applied {new Date(candidate.applicationDate).toLocaleDateString("en-US", { day: "numeric", month: "short" })}
                    </p>
                </div>
            </motion.div>

            {/* Score breakdown */}
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
                    <FaStar style={{ color: "#F59E0B", marginRight: 8 }} />
                    Score Breakdown
                </h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                    {scoreData.map(s => (
                        <div key={s.label}>
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>{s.label}</span>
                                <span style={{ fontSize: 14, fontWeight: 800, color: SCORE_COLOR(s.value) }}>{s.value}%</span>
                            </div>
                            <ScoreBar value={s.value} color={SCORE_COLOR(s.value)} />
                        </div>
                    ))}
                </div>
            </motion.div>

            {/* Skills & AI Rec */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    style={{
                        background: "var(--card)", border: "1px solid var(--border)",
                        borderRadius: "var(--radius-md)", padding: "22px", boxShadow: "var(--shadow)"
                    }}
                >
                    <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 14 }}>Skills Assessed</h4>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                        {candidate.skills.map(skill => (
                            <div key={skill} style={{ display: "flex", alignItems: "center", gap: 6,
                                padding: "5px 12px", background: "rgba(16,185,129,0.1)", color: "#10B981",
                                borderRadius: 999, fontSize: 12, fontWeight: 600,
                                border: "1px solid rgba(16,185,129,0.2)"
                            }}>
                                <FaCheckCircle style={{ fontSize: 10 }} />
                                {skill}
                            </div>
                        ))}
                    </div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.25 }}
                    style={{
                        background: "var(--card)", border: "1px solid var(--border)",
                        borderRadius: "var(--radius-md)", padding: "22px", boxShadow: "var(--shadow)"
                    }}
                >
                    <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 14 }}>AI Recommendation</h4>
                    <p style={{
                        fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.7,
                        padding: 14, background: "rgba(139,92,246,0.06)",
                        border: "1px solid rgba(139,92,246,0.15)", borderRadius: "var(--radius-sm)"
                    }}>
                        {candidate.aiRecommendations}
                    </p>
                </motion.div>
            </div>

            {/* Notes */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                style={{
                    background: "var(--card)", border: "1px solid var(--border)",
                    borderRadius: "var(--radius-md)", padding: "22px", boxShadow: "var(--shadow)"
                }}
            >
                <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 12 }}>Recruiter Notes</h4>
                <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.7 }}>
                    {candidate.notes}
                </p>
            </motion.div>
            {/* Extended AI Evaluation from Phase 12 Result Service */}
            {report && (
                <>
                    {/* Radar Chart & Topic Scores */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.35 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", padding: "22px", boxShadow: "var(--shadow)"
                        }}
                    >
                        <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 12 }}>Detailed Topic Evaluation</h4>
                        <div style={{ display: "flex", gap: 32, flexWrap: "wrap", alignItems: "center", justifyContent: "center" }}>
                            {report.radar_data && (
                                <div style={{ width: 400, height: 350 }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={report.radar_data}>
                                            <PolarGrid stroke="var(--border)" />
                                            <PolarAngleAxis dataKey="subject" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} />
                                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: "var(--text-muted)", fontSize: 10 }} />
                                            <Radar name="Candidate" dataKey="A" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.3} />
                                        </RadarChart>
                                    </ResponsiveContainer>
                                </div>
                            )}
                            
                            <div style={{ flex: 1, minWidth: 280, display: "flex", flexDirection: "column", gap: 16 }}>
                                <div>
                                    <h5 style={{ fontSize: 13, color: "#10B981", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                                        <FaCheckCircle /> Identified Strengths
                                    </h5>
                                    <ul style={{ margin: 0, paddingLeft: 18, color: "var(--text)", fontSize: 13, lineHeight: 1.6 }}>
                                        {report.strengths?.map((str, i) => <li key={i}>{str}</li>)}
                                    </ul>
                                </div>
                                <div>
                                    <h5 style={{ fontSize: 13, color: "#EF4444", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                                        <FaTimesCircle /> Areas for Improvement
                                    </h5>
                                    <ul style={{ margin: 0, paddingLeft: 18, color: "var(--text)", fontSize: 13, lineHeight: 1.6 }}>
                                        {report.weaknesses?.map((wk, i) => <li key={i}>{wk}</li>)}
                                    </ul>
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
                            borderRadius: "var(--radius-md)", padding: "22px", boxShadow: "var(--shadow)",
                            marginBottom: 40
                        }}
                    >
                        <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 16 }}>Question-by-Question Feedback</h4>
                        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                            {report.question_feedback?.map((q, idx) => (
                                <div key={idx} style={{ padding: 16, background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)", borderRadius: 8 }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                                        <span style={{ fontSize: 12, fontWeight: 700, color: "var(--primary)" }}>{q.topic}</span>
                                        <span style={{ fontSize: 12, fontWeight: 800, color: SCORE_COLOR(q.score * 10) }}>Score: {q.score}/10</span>
                                    </div>
                                    <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 8 }}>Q: {q.question}</p>
                                    <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                                        <strong>Feedback: </strong> {q.feedback}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                </>
            )}
        </div>
    );
}

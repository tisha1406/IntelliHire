import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useParams, Link } from "react-router-dom";
import {
    FaUser, FaEnvelope, FaPhone, FaLinkedin,
    FaBriefcase, FaGraduationCap, FaStar, FaArrowLeft,
    FaCheckCircle, FaClock, FaDownload, FaSpinner
} from "react-icons/fa";

import candidateService from "../../services/company/candidateService";
import PageHeader from "../../components/common/PageHeader";
import Button from "../../components/common/Button";
import StatusBadge from "../../components/common/StatusBadge";

const STAGE_COLORS = {
    Applied: "#64748B",
    Screening: "#3B82F6",
    Assessment: "#8B5CF6",
    Interviewing: "#F59E0B",
    Selected: "#10B981",
    Rejected: "#EF4444"
};

export default function CandidateDetails() {
    const { id } = useParams();
    const [candidate, setCandidate] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchCandidate = async () => {
            try {
                setLoading(true);
                const res = await candidateService.getCandidate(id);
                setCandidate(res.data);
            } catch (err) {
                console.error("Failed to fetch candidate:", err);
                setError("Candidate not found or server error.");
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
                <p>Loading candidate details...</p>
            </div>
        );
    }

    if (error || !candidate) {
        return (
            <div style={{ textAlign: "center", padding: "80px", color: "var(--text-secondary)" }}>
                <FaUser style={{ fontSize: 40, marginBottom: 16, opacity: 0.3 }} />
                <h3 style={{ color: "var(--text)", marginBottom: 8 }}>{error || "Candidate not found"}</h3>
                <Link to="/company/candidates">
                    <Button variant="outline" icon={<FaArrowLeft />}>Back to Candidates</Button>
                </Link>
            </div>
        );
    }

    const scoreColor = (s) => s >= 90 ? "#10B981" : s >= 75 ? "#F59E0B" : "#EF4444";

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: 28, animation: "fadeInPage 0.4s ease-out" }}>
            <style>{`@keyframes fadeInPage { from { opacity:0; transform:translateY(12px);} to {opacity:1; transform:translateY(0);}}`}</style>

            <PageHeader
                title={candidate.name}
                subtitle={candidate.experience}
                icon={<FaUser />}
                actions={
                    <div style={{ display: "flex", gap: 10 }}>
                        <Link to="/company/candidates">
                            <Button variant="outline" icon={<FaArrowLeft />} size="sm">Back</Button>
                        </Link>
                        <Button variant="primary" icon={<FaDownload />} size="sm">
                            Download Report
                        </Button>
                    </div>
                }
            />

            <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 24 }}>
                {/* Left Panel */}
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                    {/* Profile Card */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", padding: "28px 22px",
                            display: "flex", flexDirection: "column", alignItems: "center",
                            gap: 14, textAlign: "center", boxShadow: "var(--shadow)"
                        }}
                    >
                        <div style={{
                            width: 80, height: 80, borderRadius: "50%",
                            background: "linear-gradient(135deg, var(--primary), #6366F1)",
                            color: "#fff", fontSize: 26, fontWeight: 800,
                            display: "flex", alignItems: "center", justifyContent: "center",
                            border: "3px solid rgba(255,255,255,0.1)",
                            boxShadow: "0 4px 20px rgba(59,130,246,0.4)"
                        }}>
                            {candidate.name.split(" ").map(n => n[0]).join("").slice(0, 2)}
                        </div>

                        <div>
                            <h3 style={{ fontSize: 17, fontWeight: 800, color: "var(--text)", marginBottom: 4 }}>{candidate.name}</h3>
                            <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>{candidate.education}</p>
                        </div>

                        <StatusBadge status={candidate.status} />

                        {/* AI Match */}
                        <div style={{
                            width: "100%", padding: "14px", borderRadius: "var(--radius-sm)",
                            background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)"
                        }}>
                            <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 6 }}>AI Match Score</p>
                            <div style={{ fontSize: 32, fontWeight: 900, color: scoreColor(candidate.aiMatch) }}>
                                {candidate.aiMatch}%
                            </div>
                        </div>

                        {/* Score Grid */}
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, width: "100%" }}>
                            {[
                                { label: "Resume", value: candidate.resumeScore },
                                { label: "Interview", value: candidate.interviewScore }
                            ].map(s => (
                                <div key={s.label} style={{
                                    background: "rgba(255,255,255,0.03)", borderRadius: "var(--radius-sm)",
                                    border: "1px solid var(--border)", padding: "12px 8px", textAlign: "center"
                                }}>
                                    <div style={{ fontSize: 20, fontWeight: 800, color: scoreColor(s.value) }}>{s.value}%</div>
                                    <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>{s.label}</div>
                                </div>
                            ))}
                        </div>

                        {/* Contact */}
                        <div style={{ display: "flex", flexDirection: "column", gap: 8, width: "100%", borderTop: "1px solid var(--border)", paddingTop: 14 }}>
                            {[
                                { icon: <FaEnvelope />, text: candidate.email },
                                { icon: <FaPhone />, text: candidate.phone },
                            ].map((c, i) => (
                                <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "var(--text-secondary)" }}>
                                    <span style={{ color: "var(--primary)", fontSize: 12 }}>{c.icon}</span>
                                    {c.text}
                                </div>
                            ))}
                        </div>
                    </motion.div>

                    {/* Skills */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", padding: "20px",
                            boxShadow: "var(--shadow)"
                        }}
                    >
                        <h4 style={{ fontSize: 13, fontWeight: 700, color: "var(--text)", marginBottom: 14 }}>Skills</h4>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                            {candidate.skills.map(skill => (
                                <span key={skill} style={{
                                    padding: "5px 12px",
                                    background: "rgba(59,130,246,0.1)",
                                    color: "var(--primary)",
                                    borderRadius: 999, fontSize: 12, fontWeight: 600,
                                    border: "1px solid rgba(59,130,246,0.2)"
                                }}>
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </motion.div>
                </div>

                {/* Right Panel */}
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                    {/* AI Recommendation */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", padding: "22px",
                            boxShadow: "var(--shadow)"
                        }}
                    >
                        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                            <div style={{
                                width: 34, height: 34, borderRadius: "var(--radius-sm)",
                                background: "rgba(139,92,246,0.15)", color: "#8B5CF6",
                                display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15
                            }}>
                                <FaStar />
                            </div>
                            <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)" }}>AI Recommendation</h4>
                        </div>
                        <p style={{
                            fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6,
                            padding: "14px", background: "rgba(139,92,246,0.06)",
                            borderRadius: "var(--radius-sm)", border: "1px solid rgba(139,92,246,0.15)"
                        }}>
                            {candidate.aiRecommendations}
                        </p>
                    </motion.div>

                    {/* Notes */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", padding: "22px",
                            boxShadow: "var(--shadow)"
                        }}
                    >
                        <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 12 }}>Recruiter Notes</h4>
                        <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.7 }}>
                            {candidate.notes}
                        </p>
                    </motion.div>

                    {/* Application Timeline */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.25 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", padding: "22px",
                            boxShadow: "var(--shadow)"
                        }}
                    >
                        <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 20 }}>Application Timeline</h4>
                        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
                            {candidate.timeline?.map((event, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.3 + i * 0.08 }}
                                    style={{ display: "flex", gap: 16, paddingBottom: i < candidate.timeline.length - 1 ? 20 : 0 }}
                                >
                                    {/* Timeline dot & line */}
                                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                                        <div style={{
                                            width: 12, height: 12, borderRadius: "50%",
                                            background: STAGE_COLORS[event.stage] || "var(--primary)",
                                            border: "2px solid var(--card)",
                                            boxShadow: `0 0 0 2px ${STAGE_COLORS[event.stage] || "var(--primary)"}`,
                                            flexShrink: 0, marginTop: 3
                                        }} />
                                        {i < candidate.timeline.length - 1 && (
                                            <div style={{ width: 1, flex: 1, background: "var(--border)", marginTop: 4 }} />
                                        )}
                                    </div>
                                    <div>
                                        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                                            <span style={{
                                                fontSize: 12, fontWeight: 700,
                                                color: STAGE_COLORS[event.stage] || "var(--primary)"
                                            }}>
                                                {event.stage}
                                            </span>
                                            <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>
                                                {new Date(event.date).toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" })}
                                            </span>
                                        </div>
                                        <p style={{ fontSize: 12.5, color: "var(--text-secondary)", lineHeight: 1.4 }}>{event.description}</p>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </motion.div>

                    {/* Action buttons */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.35 }}
                        style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}
                    >
                        <Button variant="primary" icon={<FaCheckCircle />}>Move to Next Stage</Button>
                        <Button variant="outline" icon={<FaClock />}>Schedule Interview</Button>
                    </motion.div>
                </div>
            </div>
        </div>
    );
}
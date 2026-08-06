import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
    FaBullhorn, FaArrowLeft, FaUsers, FaCalendarAlt,
    FaMapMarkerAlt, FaCheckCircle, FaEdit,
    FaPause, FaPlay, FaRobot, FaClock
} from "react-icons/fa";

import campaignService from "../../services/company/campaignService";
import candidateService from "../../services/company/candidateService";
import Button from "../../components/common/Button";
import StatusBadge from "../../components/common/StatusBadge";
import PageHeader from "../../components/common/PageHeader";

export default function CampaignDetail() {
    const { id } = useParams();
    const navigate = useNavigate();

    const [campaign, setCampaign] = useState(null);
    const [relatedCandidates, setRelatedCandidates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [paused, setPaused] = useState(false);

    useEffect(() => {
        if (campaign) {
            setPaused(campaign.status === "paused");
        }
    }, [campaign]);

    const loadCampaign = async () => {
        try {
            setLoading(true);
            const [campRes, candRes] = await Promise.allSettled([
                campaignService.getCampaign(id),
                candidateService.getCandidates({ campaign_id: id }),
            ]);

            if (campRes.status === "fulfilled") {
                const data = {
                    ...campRes.value.data,
                    id: campRes.value.data._id,
                    interviewSettings: campRes.value.data.interview_settings,
                };
                setCampaign(data);
            }

            if (candRes.status === "fulfilled") {
                const cands = candRes.value.data || [];
                setRelatedCandidates(
                    Array.isArray(cands)
                        ? cands.slice(0, 5)
                        : (cands.candidates || []).slice(0, 5)
                );
            }
        } catch (err) {
            console.error("Error loading campaign details:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadCampaign();
    }, [id]);

    const togglePause = async () => {
        try {
            await campaignService.updateCampaign(campaign.id, {
                status: paused ? "active" : "paused",
            });
            loadCampaign();
        } catch (err) {
            console.error("Toggle pause failed:", err);
        }
    };

    if (loading) {
        return (
            <div style={{
                display: "flex", alignItems: "center", justifyContent: "center",
                minHeight: 300, color: "var(--text-secondary)", fontSize: 15
            }}>
                Loading campaign…
            </div>
        );
    }

    if (!campaign) {
        return (
            <div style={{
                display: "flex", alignItems: "center", justifyContent: "center",
                minHeight: 300, color: "var(--text-secondary)", fontSize: 15
            }}>
                Campaign not found.
            </div>
        );
    }

    const daysLeft = Math.max(
        0,
        Math.round((new Date(campaign.deadline) - new Date()) / (1000 * 60 * 60 * 24))
    );

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: 28, animation: "fadeInPage 0.4s ease-out" }}>
            <style>{`@keyframes fadeInPage { from { opacity:0; transform:translateY(12px);} to {opacity:1; transform:translateY(0);}}`}</style>

            <PageHeader
                title={campaign.name}
                subtitle={`${campaign.department} · ${campaign.location}`}
                icon={<FaBullhorn />}
                actions={
                    <div style={{ display: "flex", gap: 10 }}>
                        <Link to="/company/campaigns">
                            <Button variant="outline" icon={<FaArrowLeft />} size="sm">Back</Button>
                        </Link>
                        <Button
                            variant="outline"
                            icon={paused ? <FaPlay /> : <FaPause />}
                            size="sm"
                            onClick={togglePause}
                        >
                            {paused ? "Resume" : "Pause"}
                        </Button>
                        <Button
                            variant="primary"
                            icon={<FaEdit />}
                            size="sm"
                            onClick={() => navigate(`/company/campaigns/edit/${campaign.id}`)}
                        >
                            Edit Campaign
                        </Button>
                    </div>
                }
            />

            {/* Main grid */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 24 }}>

                {/* Left column */}
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

                    {/* Campaign Info */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", padding: "24px", boxShadow: "var(--shadow)"
                        }}
                    >
                        {/* Meta row */}
                        <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 20 }}>
                            {[
                                { icon: <FaUsers />, label: "Applicants", value: campaign.applicants || 0, color: "#3B82F6" },
                                {
                                    icon: <FaCalendarAlt />, label: "Deadline",
                                    value: campaign.deadline
                                        ? new Date(campaign.deadline).toLocaleDateString("en-US", { day: "numeric", month: "short" })
                                        : "—",
                                    color: "#F59E0B"
                                },
                                { icon: <FaClock />, label: "Days Left", value: `${daysLeft}d`, color: daysLeft < 7 ? "#EF4444" : "#10B981" },
                                { icon: <FaMapMarkerAlt />, label: "Location", value: campaign.location, color: "#8B5CF6" },
                            ].map(m => (
                                <div key={m.label} style={{
                                    display: "flex", alignItems: "center", gap: 10,
                                    padding: "10px 16px",
                                    background: "rgba(255,255,255,0.03)",
                                    borderRadius: "var(--radius-sm)",
                                    border: "1px solid var(--border)"
                                }}>
                                    <span style={{ color: m.color, fontSize: 14 }}>{m.icon}</span>
                                    <div>
                                        <div style={{ fontSize: 10, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.5px" }}>{m.label}</div>
                                        <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text)" }}>{m.value}</div>
                                    </div>
                                </div>
                            ))}
                            <StatusBadge status={paused ? "Paused" : campaign.status} />
                        </div>

                        <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 10 }}>Description</h4>
                        <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.7, marginBottom: 20 }}>
                            {campaign.description}
                        </p>

                        <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 12 }}>Requirements</h4>
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                            {(campaign.requirements || []).map((req, i) => (
                                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13, color: "var(--text-secondary)" }}>
                                    <FaCheckCircle style={{ color: "#10B981", flexShrink: 0, fontSize: 12 }} />
                                    {req}
                                </div>
                            ))}
                        </div>
                    </motion.div>

                    {/* AI Screening Progress */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", padding: "22px", boxShadow: "var(--shadow)"
                        }}
                    >
                        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                            <div style={{
                                width: 32, height: 32, borderRadius: "var(--radius-sm)",
                                background: "rgba(139,92,246,0.15)", color: "#8B5CF6",
                                display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14
                            }}>
                                <FaRobot />
                            </div>
                            <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)" }}>AI Screening Progress</h4>
                            <span style={{ marginLeft: "auto", fontSize: 15, fontWeight: 800, color: "#8B5CF6" }}>
                                {campaign.aiScreeningProgress || 0}%
                            </span>
                        </div>
                        <div style={{ width: "100%", height: 10, background: "rgba(255,255,255,0.07)", borderRadius: 999, overflow: "hidden" }}>
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${campaign.aiScreeningProgress || 0}%` }}
                                transition={{ duration: 0.8, delay: 0.3 }}
                                style={{ height: "100%", background: "linear-gradient(90deg, #6366F1, #8B5CF6)", borderRadius: 999 }}
                            />
                        </div>
                        <p style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 10 }}>
                            {Math.round(((campaign.applicants || 0) * (campaign.aiScreeningProgress || 0)) / 100)} of {campaign.applicants || 0} candidates screened
                        </p>
                    </motion.div>

                    {/* Top Candidates */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", overflow: "hidden", boxShadow: "var(--shadow)"
                        }}
                    >
                        <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between" }}>
                            <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)" }}>Top Matching Candidates</h4>
                            <Link to="/company/candidates" style={{ fontSize: 12, color: "var(--primary)", fontWeight: 600 }}>View All</Link>
                        </div>
                        <table style={{ width: "100%", borderCollapse: "collapse" }}>
                            <thead>
                                <tr style={{ background: "rgba(255,255,255,0.02)" }}>
                                    {["Candidate", "Experience", "AI Match", "Status"].map(h => (
                                        <th key={h} style={{
                                            fontSize: 11, fontWeight: 600, color: "var(--text-secondary)",
                                            textTransform: "uppercase", letterSpacing: "0.5px",
                                            padding: "10px 18px", textAlign: "left"
                                        }}>{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {relatedCandidates.length === 0 ? (
                                    <tr>
                                        <td colSpan={4} style={{ padding: "20px 18px", textAlign: "center", fontSize: 13, color: "var(--text-secondary)" }}>
                                            No candidates found for this campaign.
                                        </td>
                                    </tr>
                                ) : (
                                    relatedCandidates.map((cand) => (
                                        <tr key={cand.id || cand._id} style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
                                            <td style={{ padding: "12px 18px" }}>
                                                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                                    <div style={{
                                                        width: 30, height: 30, borderRadius: "50%",
                                                        background: "linear-gradient(135deg, var(--primary), #6366F1)",
                                                        color: "#fff", fontSize: 11, fontWeight: 700,
                                                        display: "flex", alignItems: "center", justifyContent: "center"
                                                    }}>
                                                        {(cand.name || "?").split(" ").map(n => n[0]).join("").slice(0, 2)}
                                                    </div>
                                                    <Link
                                                        to={`/company/candidates/${cand.id || cand._id}`}
                                                        style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}
                                                    >
                                                        {cand.name}
                                                    </Link>
                                                </div>
                                            </td>
                                            <td style={{ padding: "12px 18px", fontSize: 12, color: "var(--text-secondary)" }}>
                                                {(cand.experience || "—").split(" - ")[0]}
                                            </td>
                                            <td style={{ padding: "12px 18px" }}>
                                                <span style={{ fontSize: 13, fontWeight: 800, color: (cand.aiMatch || 0) >= 90 ? "#10B981" : "#F59E0B" }}>
                                                    {cand.aiMatch || 0}%
                                                </span>
                                            </td>
                                            <td style={{ padding: "12px 18px" }}>
                                                <StatusBadge status={cand.status} />
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </motion.div>
                </div>

                {/* Right sidebar */}
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

                    {/* Interview Settings */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.25 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", padding: "22px", boxShadow: "var(--shadow)"
                        }}
                    >
                        <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 16 }}>Interview Settings</h4>
                        {[
                            { label: "Type", value: campaign.interviewSettings?.type || "—" },
                            { label: "Duration", value: campaign.interviewSettings?.duration ? `${campaign.interviewSettings.duration} min` : "—" },
                            { label: "Strictness", value: campaign.interviewSettings?.strictness || "—" },
                        ].map(s => (
                            <div key={s.label} style={{
                                display: "flex", justifyContent: "space-between",
                                padding: "10px 0", borderBottom: "1px solid rgba(255,255,255,0.04)"
                            }}>
                                <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{s.label}</span>
                                <strong style={{ fontSize: 13, color: "var(--text)" }}>{s.value}</strong>
                            </div>
                        ))}
                    </motion.div>

                    {/* Recruiter card */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", padding: "22px", boxShadow: "var(--shadow)"
                        }}
                    >
                        <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 14 }}>Assigned Recruiter</h4>
                        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                            <div style={{
                                width: 44, height: 44, borderRadius: "50%",
                                background: "linear-gradient(135deg, var(--primary), #6366F1)",
                                color: "#fff", fontSize: 15, fontWeight: 800,
                                display: "flex", alignItems: "center", justifyContent: "center"
                            }}>
                                {(campaign.recruiter || "").split(" ").map(n => n[0]).join("").slice(0, 2) || "?"}
                            </div>
                            <div>
                                <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text)" }}>{campaign.recruiter || "Not Assigned"}</div>
                                <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Lead Recruiter</div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Quick Stats */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.35 }}
                        style={{
                            background: "var(--card)", border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)", padding: "22px", boxShadow: "var(--shadow)"
                        }}
                    >
                        <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 16 }}>Quick Stats</h4>
                        {[
                            { label: "Total Applicants", value: campaign.applicants || 0 },
                            { label: "AI Screened", value: Math.round(((campaign.applicants || 0) * (campaign.aiScreeningProgress || 0)) / 100) },
                            { label: "Shortlisted", value: Math.round((campaign.applicants || 0) * 0.18) },
                            { label: "Interviewed", value: Math.round((campaign.applicants || 0) * 0.08) },
                            { label: "Offers Extended", value: Math.round((campaign.applicants || 0) * 0.02) },
                        ].map(stat => (
                            <div key={stat.label} style={{
                                display: "flex", justifyContent: "space-between",
                                padding: "9px 0", borderBottom: "1px solid rgba(255,255,255,0.04)"
                            }}>
                                <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{stat.label}</span>
                                <strong style={{ fontSize: 13, color: "var(--text)", fontWeight: 700 }}>{stat.value}</strong>
                            </div>
                        ))}
                    </motion.div>
                </div>
            </div>
        </div>
    );
}

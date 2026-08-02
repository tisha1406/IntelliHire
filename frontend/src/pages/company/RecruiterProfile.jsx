import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
    FaUsers, FaBriefcase, FaChartLine, FaClock,
    FaHandshake, FaTrophy, FaLinkedin, FaEnvelope, FaSpinner
} from "react-icons/fa";

import PageHeader from "../../components/common/PageHeader";
import Button from "../../components/common/Button";
import { useAuthContext } from "../../context/AuthContext";
import analyticsService from "../../services/company/analyticsService";
import campaignService from "../../services/company/campaignService";

const DEFAULT_RECRUITER = {
    name: "Sarah Jenkins",
    initials: "SJ",
    title: "Director of Talent Acquisition",
    department: "Human Resources",
    email: "sarah.jenkins@intellihire.ai",
    linkedin: "linkedin.com/in/sarahjenkins",
    joined: "March 2021",
    bio: "10+ years building high-performance engineering and product teams using AI-powered recruitment workflows.",
    badge: "Top Recruiter 2026",
};

export default function RecruiterProfile() {
    const { user } = useAuthContext();
    const [recruiter, setRecruiter] = useState(DEFAULT_RECRUITER);
    const [myCampaigns, setMyCampaigns] = useState([]);
    const [myPerf, setMyPerf] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (user) {
            setRecruiter(prev => ({
                ...prev,
                name: user.name || prev.name,
                email: user.email || prev.email,
                initials: user.name ? user.name.split(" ").map(n => n[0]).join("").slice(0, 2) : prev.initials,
            }));
        }

        const loadData = async () => {
            try {
                setLoading(true);
                const [campsRes, perfRes] = await Promise.allSettled([
                    campaignService.getCampaigns(),
                    analyticsService.getRecruiterPerformance()
                ]);

                if (campsRes.status === "fulfilled") {
                    const camps = campsRes.value.data || [];
                    setMyCampaigns(Array.isArray(camps) ? camps.slice(0, 4) : (camps.campaigns || []).slice(0, 4));
                }

                if (perfRes.status === "fulfilled") {
                    const perfs = perfRes.value.data || [];
                    setMyPerf(perfs.length > 0 ? perfs[0] : null);
                }
            } catch (err) {
                console.error("Failed to load recruiter data:", err);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, [user]);

    const METRICS = [
        { label: "Active Campaigns", value: myCampaigns.length || 5, icon: <FaBriefcase />, color: "#3B82F6" },
        { label: "Total Hires Made", value: myPerf?.selections || 48, icon: <FaUsers />, color: "#10B981" },
        { label: "Avg. Time to Hire", value: myPerf?.avgTimeToHire || "19 days", icon: <FaClock />, color: "#8B5CF6" },
        { label: "Offer Acceptance", value: myPerf?.acceptanceRate || "92%", icon: <FaHandshake />, color: "#F59E0B" },
    ];

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: 28, animation: "fadeInPage 0.4s ease-out" }}>
            <style>{`@keyframes fadeInPage { from { opacity:0; transform:translateY(12px);} to {opacity:1; transform:translateY(0);}}`}</style>

            <PageHeader
                title="Recruiter Profile"
                subtitle="Your personal performance dashboard and activity overview."
                icon={<FaUsers />}
            />

            {/* Hero */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                    background: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-md)",
                    overflow: "hidden",
                    boxShadow: "var(--shadow)"
                }}
            >
                {/* Cover */}
                <div style={{
                    height: 120,
                    background: "linear-gradient(135deg, #1D4ED8 0%, #6366F1 50%, #8B5CF6 100%)",
                    position: "relative"
                }}>
                    <div style={{
                        position: "absolute", top: 12, right: 16,
                        background: "rgba(255,255,255,0.2)",
                        backdropFilter: "blur(10px)",
                        padding: "6px 14px",
                        borderRadius: 999,
                        display: "flex", alignItems: "center", gap: 6,
                        fontSize: 12, fontWeight: 700, color: "#fff",
                        border: "1px solid rgba(255,255,255,0.3)"
                    }}>
                        <FaTrophy /> {RECRUITER.badge}
                    </div>
                </div>

                <div style={{ padding: "0 28px 28px", marginTop: -40 }}>
                    <div style={{ display: "flex", alignItems: "flex-end", gap: 20, marginBottom: 20 }}>
                        <div style={{
                            width: 80, height: 80, borderRadius: "50%",
                            background: "linear-gradient(135deg, #1D4ED8, #6366F1)",
                            color: "#fff", fontSize: 28, fontWeight: 800,
                            display: "flex", alignItems: "center", justifyContent: "center",
                            border: "4px solid var(--card)",
                            boxShadow: "0 4px 20px rgba(59,130,246,0.4)"
                        }}>
                            {RECRUITER.initials}
                        </div>
                        <div style={{ paddingBottom: 4 }}>
                            <h2 style={{ fontSize: 20, fontWeight: 800, color: "var(--text)", marginBottom: 4 }}>{RECRUITER.name}</h2>
                            <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>{RECRUITER.title} · {RECRUITER.department}</p>
                        </div>
                        <div style={{ marginLeft: "auto", display: "flex", gap: 10, paddingBottom: 4 }}>
                            <Button variant="outline" icon={<FaEnvelope />} size="sm">Message</Button>
                            <Button variant="outline" icon={<FaLinkedin />} size="sm">LinkedIn</Button>
                        </div>
                    </div>

                    <p style={{ fontSize: 13.5, color: "var(--text-secondary)", lineHeight: 1.7, maxWidth: 600 }}>
                        {RECRUITER.bio}
                    </p>
                </div>
            </motion.div>

            {/* Metrics */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16 }}>
                {METRICS.map((m, i) => (
                    <motion.div
                        key={m.label}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 + i * 0.08 }}
                        style={{
                            background: "var(--card)",
                            border: "1px solid var(--border)",
                            borderRadius: "var(--radius-md)",
                            padding: "20px",
                            boxShadow: "var(--shadow)",
                            display: "flex",
                            gap: 14,
                            alignItems: "center"
                        }}
                    >
                        <div style={{
                            width: 44, height: 44, borderRadius: "var(--radius-sm)",
                            background: `${m.color}18`, color: m.color,
                            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18
                        }}>
                            {m.icon}
                        </div>
                        <div>
                            <div style={{ fontSize: 22, fontWeight: 900, color: "var(--text)" }}>{m.value}</div>
                            <div style={{ fontSize: 11.5, color: "var(--text-secondary)" }}>{m.label}</div>
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* Active Campaigns */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                style={{
                    background: "var(--card)", border: "1px solid var(--border)",
                    borderRadius: "var(--radius-md)", padding: "24px", boxShadow: "var(--shadow)"
                }}
            >
                <h4 style={{ fontSize: 15, fontWeight: 700, color: "var(--text)", marginBottom: 20 }}>My Active Campaigns</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
                    {myCampaigns.map((camp, i) => (
                        <motion.div
                            key={camp.id}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.45 + i * 0.07 }}
                            style={{
                                display: "flex", alignItems: "center", gap: 16,
                                padding: "14px 0",
                                borderBottom: i < myCampaigns.length - 1 ? "1px solid rgba(255,255,255,0.04)" : "none"
                            }}
                        >
                            <div style={{
                                width: 10, height: 10, borderRadius: "50%",
                                background: camp.status === "Active" ? "#10B981" :
                                    camp.status === "Paused" ? "#F59E0B" : "#64748B"
                            }} />
                            <div style={{ flex: 1 }}>
                                <strong style={{ fontSize: 13, color: "var(--text)" }}>{camp.title}</strong>
                                <p style={{ fontSize: 11.5, color: "var(--text-secondary)" }}>
                                    {camp.department} · {camp.applicants} applicants
                                </p>
                            </div>
                            <span style={{
                                fontSize: 11, fontWeight: 600,
                                color: camp.status === "Active" ? "#10B981" :
                                    camp.status === "Paused" ? "#F59E0B" : "#64748B",
                                background: camp.status === "Active" ? "rgba(16,185,129,0.1)" :
                                    camp.status === "Paused" ? "rgba(245,158,11,0.1)" : "rgba(100,116,139,0.1)",
                                padding: "3px 10px", borderRadius: 999
                            }}>
                                {camp.status}
                            </span>
                        </motion.div>
                    ))}
                </div>
            </motion.div>
        </div>
    );
}

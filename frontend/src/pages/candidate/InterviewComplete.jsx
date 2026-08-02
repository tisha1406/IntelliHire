import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
import { CheckCircle, BarChart2, RotateCcw, LayoutDashboard, Download, Star } from "lucide-react";
import { interviewQuestions } from "../../data/candidate/placeholderData";

export default function InterviewComplete() {
    const { id } = useParams();

    const summaryStats = [
        { label: "Questions Answered", value: interviewQuestions.length },
        { label: "Duration", value: "38 min" },
        { label: "Score (Estimated)", value: "—" },
        { label: "Language", value: "English" },
    ];

    return (
        <div className="c-complete-screen">
            <motion.div
                className="c-complete-card"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
            >
                {/* Icon */}
                <motion.div
                    className="c-complete-icon"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
                >
                    🎉
                </motion.div>

                {/* Title */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
                    <div className="c-complete-title">Interview Completed!</div>
                    <div className="c-complete-subtitle">
                        Great effort! Your responses have been recorded. Our AI is analysing your performance and
                        your detailed report will be available shortly.
                    </div>
                </motion.div>

                {/* Stars */}
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}
                    style={{ display: "flex", gap: 6 }}>
                    {[1,2,3,4,5].map((s) => (
                        <Star key={s} size={24} fill={s <= 4 ? "#FBBF24" : "transparent"} color="#FBBF24" />
                    ))}
                </motion.div>

                {/* Stats */}
                <motion.div className="c-complete-stats" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
                    {summaryStats.map((s) => (
                        <div key={s.label} className="c-complete-stat">
                            <strong>{s.value}</strong>
                            <span>{s.label}</span>
                        </div>
                    ))}
                </motion.div>

                {/* Message */}
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}
                    style={{ background: "rgba(59,130,246,0.1)", border: "1px solid rgba(59,130,246,0.2)", borderRadius: 12, padding: "12px 16px", width: "100%", textAlign: "left" }}>
                    <p style={{ fontSize: 13, color: "rgba(255,255,255,0.7)", lineHeight: 1.6, margin: 0 }}>
                        📊 <strong style={{ color: "white" }}>What's next?</strong> Your full report including scores, transcript analysis, strengths, weaknesses, and improvement tips will be ready within 5 minutes.
                    </p>
                </motion.div>

                {/* Actions */}
                <motion.div className="c-complete-actions" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }}>
                    <Link to="/candidate/reports"
                        style={{ padding: "0 24px", height: 44, background: "linear-gradient(135deg,#3B82F6,#8B5CF6)", color: "white", borderRadius: 10, display: "flex", alignItems: "center", gap: 8, fontWeight: 600, fontSize: 14, textDecoration: "none" }}>
                        <BarChart2 size={16} /> View Report
                    </Link>
                    <Link to="/candidate/dashboard"
                        style={{ padding: "0 20px", height: 44, background: "rgba(255,255,255,0.07)", color: "rgba(255,255,255,0.8)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, display: "flex", alignItems: "center", gap: 8, fontWeight: 600, fontSize: 14, textDecoration: "none" }}>
                        <LayoutDashboard size={15} /> Dashboard
                    </Link>
                    <Link to="/candidate/practice"
                        style={{ padding: "0 20px", height: 44, background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.6)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 10, display: "flex", alignItems: "center", gap: 8, fontWeight: 600, fontSize: 14, textDecoration: "none" }}>
                        <RotateCcw size={15} /> Practice Again
                    </Link>
                    <button style={{ padding: "0 18px", height: 44, background: "transparent", color: "rgba(255,255,255,0.4)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 10, display: "flex", alignItems: "center", gap: 8, fontWeight: 500, fontSize: 13, cursor: "pointer" }}>
                        <Download size={14} /> Download
                    </button>
                </motion.div>
            </motion.div>
        </div>
    );
}

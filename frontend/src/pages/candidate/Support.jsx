import { motion } from "framer-motion";
import { MessageSquare, Mail, Phone, ChevronRight, HelpCircle, Video, ShieldAlert, Loader2 } from "lucide-react";
import { useCandidateSupport } from "../../hooks/candidate/useCandidate";

const fadeUp = {
    hidden: { opacity: 0, y: 16 },
    show: (i = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.38, delay: i * 0.08 } }),
};

export default function Support() {
    const { data: support, isLoading } = useCandidateSupport();

    if (isLoading) {
        return <div className="c-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Loader2 className="c-pulse-icon" /></div>;
    }

    return (
        <div className="c-page">
            <div className="c-page-header">
                <div>
                    <h1 className="c-page-title">Help & Support</h1>
                    <p className="c-page-subtitle">Find answers to common questions or contact support for {support?.company_name || "IntelliHire"}.</p>
                </div>
            </div>

            <div className="c-two-col" style={{ alignItems: "start" }}>
                {/* Left: FAQ & Docs */}
                <motion.div custom={0} variants={fadeUp} initial="hidden" animate="show" style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                    <div className="c-card">
                        <div className="c-card-header" style={{ marginBottom: 24 }}>
                            <h3 className="c-card-title">Frequently Asked Questions</h3>
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                            {support?.faqs?.map((faq, idx) => (
                                <div key={idx} style={{ paddingBottom: 16, borderBottom: "1px solid var(--border)" }}>
                                    <h4 style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 8, display: "flex", alignItems: "flex-start", gap: 8 }}>
                                        <HelpCircle size={16} color="var(--primary)" style={{ flexShrink: 0, marginTop: 2 }} />
                                        {faq.question}
                                    </h4>
                                    <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5, paddingLeft: 24 }}>
                                        {faq.answer}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="c-card">
                        <div className="c-card-header" style={{ marginBottom: 24 }}>
                            <h3 className="c-card-title">Video Tutorials</h3>
                        </div>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                            <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: 8, padding: 12, cursor: "pointer", transition: "border-color 0.2s" }} onMouseOver={e => e.currentTarget.style.borderColor="var(--primary)"} onMouseOut={e => e.currentTarget.style.borderColor="var(--border)"}>
                                <div style={{ height: 100, background: "rgba(0,0,0,0.5)", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 12 }}>
                                    <Video size={24} color="var(--text-muted)" />
                                </div>
                                <h4 style={{ fontSize: 13, fontWeight: 600 }}>How to take the AI Interview</h4>
                                <p style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 4 }}>3:45 mins</p>
                            </div>
                            <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: 8, padding: 12, cursor: "pointer", transition: "border-color 0.2s" }} onMouseOver={e => e.currentTarget.style.borderColor="var(--primary)"} onMouseOut={e => e.currentTarget.style.borderColor="var(--border)"}>
                                <div style={{ height: 100, background: "rgba(0,0,0,0.5)", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 12 }}>
                                    <Video size={24} color="var(--text-muted)" />
                                </div>
                                <h4 style={{ fontSize: 13, fontWeight: 600 }}>Troubleshooting Audio Issues</h4>
                                <p style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 4 }}>2:10 mins</p>
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* Right: Contact Options */}
                <motion.div custom={1} variants={fadeUp} initial="hidden" animate="show" style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                    <div className="c-card">
                        <div className="c-card-header" style={{ marginBottom: 24 }}>
                            <h3 className="c-card-title">Contact Support</h3>
                        </div>
                        <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 20, lineHeight: 1.5 }}>
                            If you are experiencing technical difficulties with the AI Interview, please reach out to our dedicated support team immediately.
                        </p>
                        
                        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                            <button style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: 16, background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: 8, cursor: "pointer", transition: "all 0.2s" }} onMouseOver={e => e.currentTarget.style.borderColor="var(--primary)"} onMouseOut={e => e.currentTarget.style.borderColor="var(--border)"}>
                                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                    <div style={{ width: 36, height: 36, borderRadius: 8, background: "rgba(59, 130, 246, 0.1)", color: "#3B82F6", display: "flex", alignItems: "center", justifyContent: "center" }}><MessageSquare size={16} /></div>
                                    <div style={{ textAlign: "left" }}>
                                        <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>Live Chat</div>
                                        <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Available 24/7 during campaigns</div>
                                    </div>
                                </div>
                                <ChevronRight size={16} color="var(--text-muted)" />
                            </button>

                            <button style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: 16, background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: 8, cursor: "pointer", transition: "all 0.2s" }} onMouseOver={e => e.currentTarget.style.borderColor="var(--primary)"} onMouseOut={e => e.currentTarget.style.borderColor="var(--border)"}>
                                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                    <div style={{ width: 36, height: 36, borderRadius: 8, background: "rgba(16, 185, 129, 0.1)", color: "#10B981", display: "flex", alignItems: "center", justifyContent: "center" }}><Mail size={16} /></div>
                                    <div style={{ textAlign: "left" }}>
                                        <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>Email Support</div>
                                        <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Response within 2 hours</div>
                                    </div>
                                </div>
                                <ChevronRight size={16} color="var(--text-muted)" />
                            </button>

                            <button style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: 16, background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: 8, cursor: "pointer", transition: "all 0.2s" }} onMouseOver={e => e.currentTarget.style.borderColor="var(--primary)"} onMouseOut={e => e.currentTarget.style.borderColor="var(--border)"}>
                                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                    <div style={{ width: 36, height: 36, borderRadius: 8, background: "rgba(245, 158, 11, 0.1)", color: "#F59E0B", display: "flex", alignItems: "center", justifyContent: "center" }}><Phone size={16} /></div>
                                    <div style={{ textAlign: "left" }}>
                                        <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>Emergency Contact</div>
                                        <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>For critical interruptions</div>
                                    </div>
                                </div>
                                <ChevronRight size={16} color="var(--text-muted)" />
                            </button>
                        </div>
                    </div>

                    <div className="c-card" style={{ background: "rgba(239, 68, 68, 0.05)", border: "1px solid rgba(239, 68, 68, 0.2)" }}>
                        <div className="c-card-header" style={{ marginBottom: 16 }}>
                            <h3 className="c-card-title" style={{ display: "flex", alignItems: "center", gap: 8, color: "#EF4444" }}>
                                <ShieldAlert size={18} /> Company HR Contact
                            </h3>
                        </div>
                        <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: 16 }}>
                            If you have questions regarding the interview format, campaign timeline, or the role itself, please contact {support?.company_name || "the hiring company"}'s HR department directly.
                        </p>
                        <a href={`mailto:${support?.support_email}`} className="c-btn c-btn-danger c-btn-sm" style={{width: "100%", textDecoration: "none", display: "flex", justifyContent: "center"}}>Email Hiring Manager</a>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}

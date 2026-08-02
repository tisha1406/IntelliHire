import { useState } from "react";
import { motion } from "framer-motion";
import { Bell, Lock, Globe, Monitor, ShieldAlert, Download, Loader2 } from "lucide-react";
import { useCandidateSettings, useUpdateSettings } from "../../hooks/candidate/useCandidate";

const fadeUp = {
    hidden: { opacity: 0, y: 16 },
    show: (i = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.38, delay: i * 0.08 } }),
};

export default function Settings() {
    const [activeTab, setActiveTab] = useState("preferences");
    const { data: settings, isLoading } = useCandidateSettings();
    const { mutate: updateSettings, isPending } = useUpdateSettings();

    const handleToggle = (key) => {
        if (!settings) return;
        updateSettings({ [key]: !settings[key] });
    };

    if (isLoading) {
        return <div className="c-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Loader2 className="c-pulse-icon" /></div>;
    }

    return (
        <div className="c-page">
            <div className="c-page-header">
                <div>
                    <h1 className="c-page-title">Settings</h1>
                    <p className="c-page-subtitle">Manage your portal preferences and configurations.</p>
                </div>
                <div className="c-page-actions">
                    <button className="c-btn c-btn-primary" disabled={isPending}>{isPending ? "Saving..." : "Settings Saved Automatically"}</button>
                </div>
            </div>

            <div className="c-two-col" style={{ gridTemplateColumns: "250px 1fr", alignItems: "start" }}>
                {/* Settings Sidebar */}
                <motion.div className="c-card" custom={0} variants={fadeUp} initial="hidden" animate="show" style={{ padding: "16px 8px" }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                        {[
                            { id: "preferences", label: "Preferences", icon: <Monitor size={16} /> },
                            { id: "notifications", label: "Notifications", icon: <Bell size={16} /> },
                            { id: "privacy", label: "Privacy & Data", icon: <Lock size={16} /> },
                            { id: "language", label: "Language", icon: <Globe size={16} /> },
                        ].map((t) => (
                            <button 
                                key={t.id} 
                                onClick={() => setActiveTab(t.id)}
                                style={{ 
                                    display: "flex", alignItems: "center", gap: 12, 
                                    padding: "10px 16px", borderRadius: 8, 
                                    background: activeTab === t.id ? "rgba(255,255,255,0.06)" : "transparent",
                                    color: activeTab === t.id ? "var(--text)" : "var(--text-secondary)",
                                    border: "none", cursor: "pointer", fontSize: 14, fontWeight: 500,
                                    textAlign: "left", transition: "all 0.2s"
                                }}
                            >
                                {t.icon} {t.label}
                            </button>
                        ))}
                    </div>
                </motion.div>

                {/* Settings Content */}
                <motion.div custom={1} variants={fadeUp} initial="hidden" animate="show">
                    <div className="c-card">
                        <div className="c-card-header" style={{ marginBottom: 24 }}>
                            <h3 className="c-card-title">{activeTab === "preferences" ? "System Preferences" : activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h3>
                        </div>
                        
                        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                            
                            {/* Preferences Tab */}
                            {activeTab === "preferences" && (
                                <>
                                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                        <div>
                                            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>High Contrast Mode</div>
                                            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>Increase text contrast for better readability.</div>
                                        </div>
                                        <div style={{ width: 44, height: 24, borderRadius: 12, background: settings?.high_contrast ? "#3B82F6" : "rgba(255,255,255,0.1)", position: "relative", cursor: "pointer" }} onClick={() => handleToggle('high_contrast')}>
                                            <div style={{ width: 20, height: 20, borderRadius: "50%", background: settings?.high_contrast ? "white" : "var(--text-secondary)", position: "absolute", top: 2, left: settings?.high_contrast ? 22 : 2, transition: 'all 0.2s' }} />
                                        </div>
                                    </div>
                                    <div className="c-divider" />
                                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                        <div>
                                            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>Reduced Motion</div>
                                            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>Disable complex animations in the portal.</div>
                                        </div>
                                        <div style={{ width: 44, height: 24, borderRadius: 12, background: settings?.reduced_motion ? "#3B82F6" : "rgba(255,255,255,0.1)", position: "relative", cursor: "pointer" }} onClick={() => handleToggle('reduced_motion')}>
                                            <div style={{ width: 20, height: 20, borderRadius: "50%", background: settings?.reduced_motion ? "white" : "var(--text-secondary)", position: "absolute", top: 2, left: settings?.reduced_motion ? 22 : 2, transition: 'all 0.2s' }} />
                                        </div>
                                    </div>
                                    <div className="c-divider" />
                                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                        <div>
                                            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>Sidebar Auto-Collapse</div>
                                            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>Automatically collapse the sidebar on small screens.</div>
                                        </div>
                                        <div style={{ width: 44, height: 24, borderRadius: 12, background: settings?.sidebar_collapsed ? "#3B82F6" : "rgba(255,255,255,0.1)", position: "relative", cursor: "pointer" }} onClick={() => handleToggle('sidebar_collapsed')}>
                                            <div style={{ width: 20, height: 20, borderRadius: "50%", background: settings?.sidebar_collapsed ? "white" : "var(--text-secondary)", position: "absolute", top: 2, left: settings?.sidebar_collapsed ? 22 : 2, transition: 'all 0.2s' }} />
                                        </div>
                                    </div>
                                </>
                            )}

                            {/* Notifications Tab */}
                            {activeTab === "notifications" && (
                                <>
                                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                        <div>
                                            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>Interview Reminders</div>
                                            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>Receive email and SMS reminders before the deadline.</div>
                                        </div>
                                        <div style={{ width: 44, height: 24, borderRadius: 12, background: settings?.email_notifications ? "#3B82F6" : "rgba(255,255,255,0.1)", position: "relative", cursor: "pointer" }} onClick={() => handleToggle('email_notifications')}>
                                            <div style={{ width: 20, height: 20, borderRadius: "50%", background: settings?.email_notifications ? "white" : "var(--text-secondary)", position: "absolute", top: 2, left: settings?.email_notifications ? 22 : 2, transition: 'all 0.2s' }} />
                                        </div>
                                    </div>
                                    <div className="c-divider" />
                                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                        <div>
                                            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>Company Updates</div>
                                            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>Get notified when the hiring team adds instructions.</div>
                                        </div>
                                        <div style={{ width: 44, height: 24, borderRadius: 12, background: settings?.sms_notifications ? "#3B82F6" : "rgba(255,255,255,0.1)", position: "relative", cursor: "pointer" }} onClick={() => handleToggle('sms_notifications')}>
                                            <div style={{ width: 20, height: 20, borderRadius: "50%", background: settings?.sms_notifications ? "white" : "var(--text-secondary)", position: "absolute", top: 2, left: settings?.sms_notifications ? 22 : 2, transition: 'all 0.2s' }} />
                                        </div>
                                    </div>
                                    <div className="c-divider" />
                                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                        <div>
                                            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>Result Notifications</div>
                                            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>Get notified immediately when your AI report is generated.</div>
                                        </div>
                                        <div style={{ width: 44, height: 24, borderRadius: 12, background: settings?.result_notifications ? "#3B82F6" : "rgba(255,255,255,0.1)", position: "relative", cursor: "pointer" }} onClick={() => handleToggle('result_notifications')}>
                                            <div style={{ width: 20, height: 20, borderRadius: "50%", background: settings?.result_notifications ? "white" : "var(--text-secondary)", position: "absolute", top: 2, left: settings?.result_notifications ? 22 : 2, transition: 'all 0.2s' }} />
                                        </div>
                                    </div>
                                </>
                            )}

                            {/* Language Tab */}
                            {activeTab === "language" && (
                                <>
                                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                        <div>
                                            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>Portal Language</div>
                                            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>The language of the dashboard interface.</div>
                                        </div>
                                        <select 
                                            value={settings?.language}
                                            onChange={(e) => updateSettings({ language: e.target.value })}
                                            style={{ padding: "8px 12px", background: "rgba(255,255,255,0.05)", border: "1px solid var(--border)", color: "white", borderRadius: 8 }}
                                        >
                                            <option value="en">English</option>
                                            <option value="es">Spanish</option>
                                            <option value="fr">French</option>
                                        </select>
                                    </div>
                                    <div className="c-divider" />
                                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                        <div>
                                            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>Live Subtitles</div>
                                            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>Show AI-generated text subtitles during the interview.</div>
                                        </div>
                                        <div style={{ width: 44, height: 24, borderRadius: 12, background: settings?.subtitles ? "#3B82F6" : "rgba(255,255,255,0.1)", position: "relative", cursor: "pointer" }} onClick={() => handleToggle('subtitles')}>
                                            <div style={{ width: 20, height: 20, borderRadius: "50%", background: settings?.subtitles ? "white" : "var(--text-secondary)", position: "absolute", top: 2, left: settings?.subtitles ? 22 : 2, transition: 'all 0.2s' }} />
                                        </div>
                                    </div>
                                </>
                            )}

                            {/* Privacy Tab */}
                            {activeTab === "privacy" && (
                                <>
                                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                        <div>
                                            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>Download My Data</div>
                                            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>Export all your resume data, logs, and reports as JSON.</div>
                                        </div>
                                        <button className="c-btn c-btn-secondary c-btn-sm" style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                            <Download size={14} /> Export
                                        </button>
                                    </div>
                                    <div className="c-divider" />
                                    <div style={{ padding: 16, background: "rgba(239, 68, 68, 0.05)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: 8 }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#EF4444", fontWeight: 600, marginBottom: 8, fontSize: 14 }}>
                                            <ShieldAlert size={16} /> Data Deletion Request
                                        </div>
                                        <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 16, lineHeight: 1.5 }}>
                                            You can request the hiring company to delete your resume and interview recordings. This action cannot be undone.
                                        </p>
                                        <button className="c-btn c-btn-danger c-btn-sm">Request Deletion</button>
                                    </div>
                                </>
                            )}

                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}

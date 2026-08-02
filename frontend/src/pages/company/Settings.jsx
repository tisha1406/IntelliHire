export default function Settings.jsx() { return null; }
import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    FaCog, FaPalette, FaBell, FaShieldAlt, FaPlug,
    FaBriefcase, FaKey, FaTrash, FaSave, FaCheck,
    FaSlack, FaGithub, FaGoogle, FaLinkedin, FaTimes
} from "react-icons/fa";

import PageHeader from "../../components/common/PageHeader";

import "../../styles/company/Settings.css";

const NAV_ITEMS = [
    { id: "general",       label: "General",         icon: <FaCog /> },
    { id: "appearance",    label: "Appearance",       icon: <FaPalette /> },
    { id: "notifications", label: "Notifications",    icon: <FaBell /> },
    { id: "security",      label: "Security",         icon: <FaShieldAlt /> },
    { id: "integrations",  label: "Integrations",     icon: <FaPlug /> },
    { id: "company",       label: "Company Profile",  icon: <FaBriefcase /> },
    { id: "api",           label: "API & Webhooks",   icon: <FaKey /> },
    { id: "danger",        label: "Danger Zone",      icon: <FaTrash /> },
];

const INTEGRATIONS = [
    { name: "Slack",              desc: "Team notifications & alerts",         icon: <FaSlack />,    color: "#4A154B", bg: "rgba(74,21,75,0.15)",    connected: true  },
    { name: "Google Workspace",   desc: "Calendar & meet integrations",        icon: <FaGoogle />,   color: "#EA4335", bg: "rgba(234,67,53,0.12)",    connected: true  },
    { name: "LinkedIn Recruiter", desc: "Sync job postings automatically",     icon: <FaLinkedin />, color: "#0A66C2", bg: "rgba(10,102,194,0.12)",   connected: false },
    { name: "GitHub",             desc: "Code assessment integration",         icon: <FaGithub />,   color: "#fff",    bg: "rgba(255,255,255,0.07)",  connected: false },
];

/* Sections that have a save action */
const SAVEABLE = ["general", "appearance", "notifications", "security", "company", "api"];

export default function Settings() {
    const [activeSection, setActiveSection] = useState("general");

    const DEFAULTS = {
        emailDigest:     true,
        aiScoring:       true,
        autoShortlist:   false,
        twoFactor:       true,
        sessionTimeout:  false,
        slackAlerts:     true,
        candidateAlerts: true,
        interviewAlerts: true,
        marketingEmails: false,
    };

    const loadSettings = () => {
        try {
            const stored = localStorage.getItem("intellihire_settings");
            return stored ? { ...DEFAULTS, ...JSON.parse(stored) } : { ...DEFAULTS };
        } catch { return { ...DEFAULTS }; }
    };

    const [settings, setSettings] = useState(loadSettings);
    const [savedSnapshot, setSavedSnapshot] = useState(loadSettings);
    const [saved, setSaved] = useState(false);
    const [saving, setSaving] = useState(false);
    const [toast, setToast] = useState("");
    const [theme, setTheme] = useState("dark");

    const toggle = (key) => setSettings(prev => ({ ...prev, [key]: !prev[key] }));

    const showToast = (msg) => {
        setToast(msg);
        setTimeout(() => setToast(""), 3000);
    };

    const handleSave = async () => {
        setSaving(true);
        // Simulate brief async save (localStorage is synchronous)
        await new Promise(r => setTimeout(r, 300));
        try {
            localStorage.setItem("intellihire_settings", JSON.stringify(settings));
            setSavedSnapshot({ ...settings });
            setSaved(true);
            showToast("Settings saved successfully!");
            setTimeout(() => setSaved(false), 2000);
        } catch {
            showToast("Failed to save settings.");
        } finally {
            setSaving(false);
        }
    };

    const handleCancel = () => {
        setSettings({ ...savedSnapshot });
        setSaved(false);
    };

    /* ── Shared footer shown for sections that have saveable state ── */
    const SaveFooter = () => (
        <div className="settings-save-footer">
            <button className="settings-cancel-btn" onClick={handleCancel} disabled={saving}>
                Cancel
            </button>
            <button
                className={`settings-save-btn ${saved ? "saved" : ""}`}
                onClick={handleSave}
                disabled={saving}
            >
                {saving ? <><FaSave style={{ animation: "spin 1s linear infinite" }} /> Saving…</> : saved ? <><FaCheck /> Saved!</> : <><FaSave /> Save Changes</>}
            </button>
        </div>
    );

    const renderContent = () => {
        switch (activeSection) {

            /* ── GENERAL ─────────────────────────────────────────── */
            case "general":
                return (
                    <motion.div className="settings-panel" key="general"
                        initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}>

                        <div className="settings-section">
                            <div className="settings-section-header">
                                <div className="settings-section-icon" style={{ background: "rgba(59,130,246,0.12)", color: "#3B82F6" }}><FaCog /></div>
                                <div>
                                    <h4>General Settings</h4>
                                    <p>Basic workspace and account preferences</p>
                                </div>
                            </div>
                            <div className="settings-section-body">
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Weekly Email Digest</h6>
                                        <p>Receive a weekly summary of hiring activity</p>
                                    </div>
                                    <label className="settings-toggle">
                                        <input type="checkbox" checked={settings.emailDigest} onChange={() => toggle("emailDigest")} />
                                        <span className="settings-toggle-slider" />
                                    </label>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>AI Auto-Scoring</h6>
                                        <p>Automatically score new candidates using AI</p>
                                    </div>
                                    <label className="settings-toggle">
                                        <input type="checkbox" checked={settings.aiScoring} onChange={() => toggle("aiScoring")} />
                                        <span className="settings-toggle-slider" />
                                    </label>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Auto-Shortlist (AI Threshold ≥ 80%)</h6>
                                        <p>Automatically move top-scoring candidates forward</p>
                                    </div>
                                    <label className="settings-toggle">
                                        <input type="checkbox" checked={settings.autoShortlist} onChange={() => toggle("autoShortlist")} />
                                        <span className="settings-toggle-slider" />
                                    </label>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Default Language</h6>
                                        <p>Interface language for all users</p>
                                    </div>
                                    <select className="settings-select">
                                        <option>English (US)</option>
                                        <option>English (UK)</option>
                                        <option>German</option>
                                        <option>French</option>
                                    </select>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Time Zone</h6>
                                        <p>Used for scheduling interviews and reminders</p>
                                    </div>
                                    <select className="settings-select">
                                        <option>UTC+05:30 – India Standard Time</option>
                                        <option>UTC+00:00 – Greenwich Mean Time</option>
                                        <option>UTC-05:00 – Eastern Time</option>
                                        <option>UTC-08:00 – Pacific Time</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        <SaveFooter />
                    </motion.div>
                );

            /* ── APPEARANCE ──────────────────────────────────────── */
            case "appearance":
                return (
                    <motion.div className="settings-panel" key="appearance"
                        initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}>

                        <div className="settings-section">
                            <div className="settings-section-header">
                                <div className="settings-section-icon" style={{ background: "rgba(139,92,246,0.12)", color: "#8B5CF6" }}><FaPalette /></div>
                                <div>
                                    <h4>Appearance</h4>
                                    <p>Customize the look and feel of your workspace</p>
                                </div>
                            </div>
                            <div className="settings-section-body">
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Theme Mode</h6>
                                        <p>Choose between dark or light interface</p>
                                    </div>
                                    <div style={{ display: "flex", gap: 8 }}>
                                        {["dark", "light"].map(t => (
                                            <button
                                                key={t}
                                                onClick={() => setTheme(t)}
                                                className={`settings-theme-btn ${theme === t ? "active" : ""}`}
                                            >
                                                {t.charAt(0).toUpperCase() + t.slice(1)}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Accent Color</h6>
                                        <p>Primary color used for buttons and highlights</p>
                                    </div>
                                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                                        {["#3B82F6", "#6366F1", "#10B981", "#F59E0B", "#EC4899"].map(color => (
                                            <div
                                                key={color}
                                                className="settings-color-swatch"
                                                style={{
                                                    background: color,
                                                    outline: color === "#3B82F6" ? "2px solid white" : "2px solid transparent",
                                                    outlineOffset: "2px",
                                                }}
                                                onMouseEnter={e => e.currentTarget.style.transform = "scale(1.2)"}
                                                onMouseLeave={e => e.currentTarget.style.transform = "scale(1)"}
                                            />
                                        ))}
                                    </div>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Compact Mode</h6>
                                        <p>Reduce spacing for higher information density</p>
                                    </div>
                                    <label className="settings-toggle">
                                        <input type="checkbox" defaultChecked={false} />
                                        <span className="settings-toggle-slider" />
                                    </label>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Font Size</h6>
                                        <p>Adjust the base font size across the dashboard</p>
                                    </div>
                                    <select className="settings-select">
                                        <option>Small (13px)</option>
                                        <option selected>Default (14px)</option>
                                        <option>Large (15px)</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        <SaveFooter />
                    </motion.div>
                );

            /* ── NOTIFICATIONS ───────────────────────────────────── */
            case "notifications":
                return (
                    <motion.div className="settings-panel" key="notifications"
                        initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}>

                        <div className="settings-section">
                            <div className="settings-section-header">
                                <div className="settings-section-icon" style={{ background: "rgba(245,158,11,0.12)", color: "#F59E0B" }}><FaBell /></div>
                                <div>
                                    <h4>Notification Preferences</h4>
                                    <p>Control what alerts and digests you receive</p>
                                </div>
                            </div>
                            <div className="settings-section-body">
                                <div className="settings-notif-group-label">Email Notifications</div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>New Candidate Applications</h6>
                                        <p>Email me when a candidate applies to a job</p>
                                    </div>
                                    <label className="settings-toggle">
                                        <input type="checkbox" checked={settings.candidateAlerts} onChange={() => toggle("candidateAlerts")} />
                                        <span className="settings-toggle-slider" />
                                    </label>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Interview Scheduled</h6>
                                        <p>Email me when an interview is booked</p>
                                    </div>
                                    <label className="settings-toggle">
                                        <input type="checkbox" checked={settings.interviewAlerts} onChange={() => toggle("interviewAlerts")} />
                                        <span className="settings-toggle-slider" />
                                    </label>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Weekly Digest</h6>
                                        <p>Receive a weekly summary of all hiring activity</p>
                                    </div>
                                    <label className="settings-toggle">
                                        <input type="checkbox" checked={settings.emailDigest} onChange={() => toggle("emailDigest")} />
                                        <span className="settings-toggle-slider" />
                                    </label>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Marketing & Product Updates</h6>
                                        <p>News about IntelliHire features and announcements</p>
                                    </div>
                                    <label className="settings-toggle">
                                        <input type="checkbox" checked={settings.marketingEmails} onChange={() => toggle("marketingEmails")} />
                                        <span className="settings-toggle-slider" />
                                    </label>
                                </div>

                                <div className="settings-notif-group-label" style={{ marginTop: 8 }}>In-App Notifications</div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Slack Integration Alerts</h6>
                                        <p>Push alerts to the connected Slack workspace</p>
                                    </div>
                                    <label className="settings-toggle">
                                        <input type="checkbox" checked={settings.slackAlerts} onChange={() => toggle("slackAlerts")} />
                                        <span className="settings-toggle-slider" />
                                    </label>
                                </div>
                            </div>
                        </div>

                        <SaveFooter />
                    </motion.div>
                );

            /* ── SECURITY ────────────────────────────────────────── */
            case "security":
                return (
                    <motion.div className="settings-panel" key="security"
                        initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}>

                        <div className="settings-section">
                            <div className="settings-section-header">
                                <div className="settings-section-icon" style={{ background: "rgba(16,185,129,0.12)", color: "#10B981" }}><FaShieldAlt /></div>
                                <div>
                                    <h4>Security</h4>
                                    <p>Manage authentication and session security</p>
                                </div>
                            </div>
                            <div className="settings-section-body">
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Two-Factor Authentication (2FA)</h6>
                                        <p>Require OTP on every login</p>
                                    </div>
                                    <label className="settings-toggle">
                                        <input type="checkbox" checked={settings.twoFactor} onChange={() => toggle("twoFactor")} />
                                        <span className="settings-toggle-slider" />
                                    </label>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Auto Session Timeout (30 min)</h6>
                                        <p>Automatically log out after 30 minutes of inactivity</p>
                                    </div>
                                    <label className="settings-toggle">
                                        <input type="checkbox" checked={settings.sessionTimeout} onChange={() => toggle("sessionTimeout")} />
                                        <span className="settings-toggle-slider" />
                                    </label>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Active Sessions</h6>
                                        <p>2 active sessions — Chrome/macOS, Chrome/Windows</p>
                                    </div>
                                    <button className="settings-ghost-btn settings-ghost-btn--danger">Revoke All</button>
                                </div>
                            </div>
                        </div>

                        <SaveFooter />
                    </motion.div>
                );

            /* ── INTEGRATIONS ────────────────────────────────────── */
            case "integrations":
                return (
                    <motion.div className="settings-panel" key="integrations"
                        initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}>

                        <div className="settings-section">
                            <div className="settings-section-header">
                                <div className="settings-section-icon" style={{ background: "rgba(245,158,11,0.12)", color: "#F59E0B" }}><FaPlug /></div>
                                <div>
                                    <h4>Integrations</h4>
                                    <p>Connect IntelliHire with your existing tools</p>
                                </div>
                            </div>
                            <div className="settings-section-body">
                                <div className="integration-list">
                                    {INTEGRATIONS.map((int, i) => (
                                        <motion.div
                                            key={int.name}
                                            className="integration-item"
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.08 }}
                                        >
                                            <div className="integration-logo" style={{ background: int.bg, color: int.color }}>
                                                {int.icon}
                                            </div>
                                            <div className="integration-meta">
                                                <strong>{int.name}</strong>
                                                <span>{int.desc}</span>
                                            </div>
                                            <span className={`integration-status ${int.connected ? "connected" : "not-connected"}`}>
                                                {int.connected ? "Connected" : "Not Connected"}
                                            </span>
                                            <button className="integration-connect-btn">
                                                {int.connected ? "Manage" : "Connect"}
                                            </button>
                                        </motion.div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </motion.div>
                );

            /* ── COMPANY PROFILE ─────────────────────────────────── */
            case "company":
                return (
                    <motion.div className="settings-panel" key="company"
                        initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}>

                        <div className="settings-section">
                            <div className="settings-section-header">
                                <div className="settings-section-icon" style={{ background: "rgba(99,102,241,0.12)", color: "#6366F1" }}><FaBriefcase /></div>
                                <div>
                                    <h4>Company Profile</h4>
                                    <p>Update your public company information</p>
                                </div>
                            </div>
                            <div className="settings-section-body">
                                <div className="setting-row setting-row--column">
                                    <div className="setting-row-info">
                                        <h6>Company Name</h6>
                                    </div>
                                    <input className="settings-input" defaultValue="TechCorp Solutions" />
                                </div>
                                <div className="setting-row setting-row--column">
                                    <div className="setting-row-info">
                                        <h6>Industry</h6>
                                    </div>
                                    <select className="settings-select settings-select--full">
                                        <option>Software / Technology</option>
                                        <option>Finance</option>
                                        <option>Healthcare</option>
                                        <option>Education</option>
                                        <option>E-Commerce</option>
                                    </select>
                                </div>
                                <div className="setting-row setting-row--column">
                                    <div className="setting-row-info">
                                        <h6>Company Size</h6>
                                    </div>
                                    <select className="settings-select settings-select--full">
                                        <option>1–10 employees</option>
                                        <option>11–50 employees</option>
                                        <option selected>51–200 employees</option>
                                        <option>201–500 employees</option>
                                        <option>500+ employees</option>
                                    </select>
                                </div>
                                <div className="setting-row setting-row--column">
                                    <div className="setting-row-info">
                                        <h6>Website</h6>
                                    </div>
                                    <input className="settings-input" defaultValue="https://techcorp.io" />
                                </div>
                                <div className="setting-row setting-row--column">
                                    <div className="setting-row-info">
                                        <h6>About the Company</h6>
                                        <p>Shown to candidates on job listings</p>
                                    </div>
                                    <textarea
                                        className="settings-input settings-textarea"
                                        defaultValue="TechCorp Solutions builds next-gen SaaS platforms for enterprise clients worldwide. We value innovation, diversity, and continuous learning."
                                    />
                                </div>
                            </div>
                        </div>

                        <SaveFooter />
                    </motion.div>
                );

            /* ── API & WEBHOOKS ──────────────────────────────────── */
            case "api":
                return (
                    <motion.div className="settings-panel" key="api"
                        initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}>

                        <div className="settings-section">
                            <div className="settings-section-header">
                                <div className="settings-section-icon" style={{ background: "rgba(236,72,153,0.12)", color: "#EC4899" }}><FaKey /></div>
                                <div>
                                    <h4>API & Webhooks</h4>
                                    <p>Manage API keys and webhook endpoints</p>
                                </div>
                            </div>
                            <div className="settings-section-body">
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Production API Key</h6>
                                        <p style={{ fontFamily: "monospace", letterSpacing: "0.05em" }}>
                                            ih_live_••••••••••••••••••••••XXXX
                                        </p>
                                    </div>
                                    <div style={{ display: "flex", gap: 8 }}>
                                        <button className="integration-connect-btn">Reveal</button>
                                        <button className="integration-connect-btn">Regenerate</button>
                                    </div>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Webhook URL</h6>
                                        <p style={{ fontFamily: "monospace", fontSize: 11 }}>
                                            https://api.yourcompany.com/intellihire/events
                                        </p>
                                    </div>
                                    <button className="integration-connect-btn">Edit</button>
                                </div>
                                <div className="setting-row">
                                    <div className="setting-row-info">
                                        <h6>Rate Limit Usage</h6>
                                        <p>14,820 / 50,000 requests this month</p>
                                    </div>
                                    <div className="settings-progress-bar">
                                        <div className="settings-progress-fill" style={{ width: "29.6%" }} />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <SaveFooter />
                    </motion.div>
                );

            /* ── DANGER ZONE ─────────────────────────────────────── */
            case "danger":
                return (
                    <motion.div className="settings-panel" key="danger"
                        initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}>

                        <div className="settings-section">
                            <div className="settings-section-header">
                                <div className="settings-section-icon" style={{ background: "rgba(239,68,68,0.12)", color: "#EF4444" }}><FaTrash /></div>
                                <div>
                                    <h4>Danger Zone</h4>
                                    <p>Irreversible and destructive account actions</p>
                                </div>
                            </div>
                            <div className="danger-zone-body">
                                {[
                                    { title: "Export All Data",            desc: "Download a complete archive of all company data",              label: "Export"         },
                                    { title: "Clear All Candidate Data",   desc: "Permanently delete all candidate profiles and applications",   label: "Clear Data"     },
                                    { title: "Deactivate Company Account", desc: "Suspend the IntelliHire subscription immediately",             label: "Deactivate"     },
                                    { title: "Delete Company Account",     desc: "Permanently delete all data. This cannot be undone.",          label: "Delete Account" },
                                ].map(item => (
                                    <div key={item.title} className="danger-item">
                                        <div className="danger-item-info">
                                            <h6>{item.title}</h6>
                                            <p>{item.desc}</p>
                                        </div>
                                        <button className="danger-btn">{item.label}</button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </motion.div>
                );

            /* ── FALLBACK ────────────────────────────────────────── */
            default:
                return (
                    <motion.div className="settings-panel" key="default"
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                        <div style={{ textAlign: "center", padding: "60px", color: "var(--text-secondary)" }}>
                            <FaCog style={{ fontSize: 32, marginBottom: 12, opacity: 0.3 }} />
                            <p>This settings section is coming soon.</p>
                        </div>
                    </motion.div>
                );
        }
    };

    return (
        <div className="settings-page">
            {/* Toast Notification */}
            {toast && (
                <div style={{
                    position: "fixed", top: 20, right: 20, zIndex: 9999,
                    background: "var(--success, #22c55e)", color: "#fff",
                    padding: "10px 20px", borderRadius: 8,
                    fontSize: 14, fontWeight: 600, boxShadow: "0 4px 20px rgba(0,0,0,0.3)"
                }}>
                    {toast}
                </div>
            )}

            <PageHeader
                title="Settings"
                subtitle="Configure workspace and integrations."
                icon={<FaCog />}
            />

            <div className="settings-body">
                {/* Left Nav */}
                <motion.nav
                    className="settings-nav"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    {NAV_ITEMS.map(item => (
                        <button
                            key={item.id}
                            className={`settings-nav-item ${activeSection === item.id ? "active" : ""}`}
                            onClick={() => setActiveSection(item.id)}
                        >
                            {item.icon}
                            {item.label}
                        </button>
                    ))}
                </motion.nav>

                {/* Right Panel */}
                <AnimatePresence mode="wait">
                    {renderContent()}
                </AnimatePresence>
            </div>
        </div>
    );
}

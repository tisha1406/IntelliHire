import { useState, useEffect } from "react";
import { Save } from "lucide-react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import Toggle from "../../components/common/Toggle";
import Button from "../../components/common/Button";
import { SettingsAPI } from "../../api/settings";
import "../../styles/admin/form.css";

const TABS = ["General", "AI Configuration", "Voices", "Languages", "Interview Modes", "Strategies", "Notifications", "Security", "Appearance"];

export default function PlatformSettings() {
    const [activeTab, setActiveTab] = useState("General");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [settings, setSettings] = useState(null);

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const data = await SettingsAPI.getPlatformSettings();
                setSettings(data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchSettings();
    }, []);

    const handleSave = async () => {
        setSaving(true);
        try {
            await SettingsAPI.updatePlatformSettings(settings);
            alert("Settings saved successfully.");
        } catch (err) {
            console.error(err);
            alert("Failed to save settings.");
        } finally {
            setSaving(false);
        }
    };

    const handleToggle = (section, key, value) => {
        setSettings(prev => ({ ...prev, [section]: { ...prev[section], [key]: value } }));
    };

    const handleInput = (section, key, value) => {
        setSettings(prev => ({ ...prev, [section]: { ...prev[section], [key]: value } }));
    };

    const ToggleRow = ({ label, description, section, field }) => (
        <Toggle
            label={label}
            description={description}
            checked={settings[section][field]}
            onChange={(val) => handleToggle(section, field, val)}
        />
    );

    const renderTab = () => {
        switch (activeTab) {
            case "General": return (
                <SectionCard>
                    <h3 style={{ fontWeight: '600', color: 'var(--text)', marginBottom: '20px', padding: '20px 24px 0' }}>General Platform Settings</h3>
                    <div style={{ padding: '0 24px 24px' }}>
                        <form className="ih-form">
                            <div className="ih-form-row">
                                <div className="ih-form-group">
                                    <label>Platform Name</label>
                                    <input type="text" value={settings.general?.platform_name || ''} onChange={e => handleInput('general', 'platform_name', e.target.value)} />
                                </div>
                                <div className="ih-form-group">
                                    <label>Support Email</label>
                                    <input type="email" value={settings.general?.support_email || ''} onChange={e => handleInput('general', 'support_email', e.target.value)} />
                                </div>
                            </div>
                            <div className="ih-form-row">
                                <div className="ih-form-group">
                                    <label>Max Companies</label>
                                    <input type="number" value={settings.general?.max_companies || ''} onChange={e => handleInput('general', 'max_companies', e.target.value)} />
                                </div>
                                <div className="ih-form-group">
                                    <label>Default Interview Duration (min)</label>
                                    <input type="number" value={settings.general?.default_interview_duration || ''} onChange={e => handleInput('general', 'default_interview_duration', e.target.value)} />
                                </div>
                            </div>
                            <div className="ih-form-group">
                                <label>Platform Description</label>
                                <textarea rows={3} value={settings.general?.description || ''} onChange={e => handleInput('general', 'description', e.target.value)} />
                            </div>
                        </form>
                    </div>
                </SectionCard>
            );
            case "AI Configuration": return (
                <SectionCard>
                    <h3 style={{ fontWeight: '600', color: 'var(--text)', marginBottom: '20px', padding: '20px 24px 0' }}>AI Model Configuration</h3>
                    <div style={{ padding: '0 24px 24px' }}>
                        <form className="ih-form">
                            <div className="ih-form-row">
                                <div className="ih-form-group">
                                    <label>Primary LLM</label>
                                    <select value={settings.ai?.primary_llm || ''} onChange={e => handleInput('ai', 'primary_llm', e.target.value)}>
                                        <option value="llama3">Llama 3.3 (Groq)</option>
                                        <option value="gemini">Gemini 1.5 Flash</option>
                                    </select>
                                </div>
                                <div className="ih-form-group">
                                    <label>STT Engine</label>
                                    <select value={settings.ai?.stt_engine || ''} onChange={e => handleInput('ai', 'stt_engine', e.target.value)}>
                                        <option value="whisper">OpenAI Whisper v3</option>
                                        <option value="sarvam">Sarvam AI (Indic)</option>
                                    </select>
                                </div>
                            </div>
                            <div className="ih-form-row">
                                <div className="ih-form-group">
                                    <label>Max Questions per Interview</label>
                                    <input type="number" value={settings.ai?.max_questions || ''} onChange={e => handleInput('ai', 'max_questions', e.target.value)} />
                                </div>
                                <div className="ih-form-group">
                                    <label>Confidence Threshold (%)</label>
                                    <input type="number" value={settings.ai?.confidence_threshold || ''} onChange={e => handleInput('ai', 'confidence_threshold', e.target.value)} />
                                </div>
                            </div>
                            <div className="ih-form-row">
                                <div className="ih-form-group">
                                    <label>Groq API Key</label>
                                    <input type="password" value={settings.ai?.groq_api_key || ''} onChange={e => handleInput('ai', 'groq_api_key', e.target.value)} />
                                </div>
                                <div className="ih-form-group">
                                    <label>Gemini API Key</label>
                                    <input type="password" value={settings.ai?.gemini_api_key || ''} onChange={e => handleInput('ai', 'gemini_api_key', e.target.value)} />
                                </div>
                            </div>
                        </form>
                    </div>
                </SectionCard>
            );
            case "Voices": return (
                <SectionCard>
                    <h3 style={{ fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0' }}>Voice Management</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '4px 24px 20px' }}>Enable or disable TTS voices globally.</p>
                    <div style={{ padding: '0 24px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        <ToggleRow label="English (US) — Default" description="Standard American English voice." section="voices" field="en_us" />
                        <ToggleRow label="English (UK)" description="British English accent." section="voices" field="en_uk" />
                        <ToggleRow label="Hindi (IN)" description="Standard Hindi via Sarvam AI." section="voices" field="hi_in" />
                    </div>
                </SectionCard>
            );
            case "Languages": return (
                <SectionCard>
                    <h3 style={{ fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0' }}>Language Management</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '4px 24px 20px' }}>Available interview languages for candidates.</p>
                    <div style={{ padding: '0 24px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        <ToggleRow label="English" description="Full support, all interview modes." section="languages" field="english" />
                        <ToggleRow label="Hindi" description="Full support via Sarvam AI." section="languages" field="hindi" />
                        <ToggleRow label="Spanish" description="Experimental — limited mode support." section="languages" field="spanish" />
                        <ToggleRow label="French" description="Coming soon — not yet available." section="languages" field="french" />
                    </div>
                </SectionCard>
            );
            case "Interview Modes": return (
                <SectionCard>
                    <h3 style={{ fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0' }}>Interview Mode Configuration</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '4px 24px 20px' }}>Enable interview styles available to companies.</p>
                    <div style={{ padding: '0 24px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        <ToggleRow label="Structured" description="Strict Q&A with scoring rubric." section="modes" field="structured" />
                        <ToggleRow label="Conversational" description="Fluid chat-style interview flow." section="modes" field="conversational" />
                        <ToggleRow label="Deep Technical" description="Heavy problem solving focus." section="modes" field="technical" />
                        <ToggleRow label="HR Behavioral" description="Soft skills and culture fit." section="modes" field="behavioral" />
                        <ToggleRow label="Campus Recruitment" description="High-volume screening mode." section="modes" field="campus" />
                    </div>
                </SectionCard>
            );
            case "Strategies": return (
                <SectionCard>
                    <h3 style={{ fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0' }}>AI Strategy Configuration</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '4px 24px 20px' }}>Control how the AI reasons and evaluates candidates.</p>
                    <div style={{ padding: '0 24px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        <ToggleRow label="Default Strategy" description="Balanced evaluation approach." section="strategies" field="default" />
                        <ToggleRow label="Aggressive Evaluation" description="Strict grading, deep follow-ups." section="strategies" field="aggressive" />
                        <ToggleRow label="Supportive Evaluation" description="Encouraging, hints when stuck." section="strategies" field="supportive" />
                        <ToggleRow label="Exploratory Mode" description="Open-ended, discovery-driven flow." section="strategies" field="exploratory" />
                    </div>
                </SectionCard>
            );
            case "Notifications": return (
                <SectionCard>
                    <h3 style={{ fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0' }}>Notification Settings</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '4px 24px 20px' }}>Configure email and system alert preferences.</p>
                    <div style={{ padding: '0 24px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        <ToggleRow label="Email Alerts" description="Send email for critical system events." section="notifications" field="email_alerts" />
                        <ToggleRow label="Incident Alerts" description="Notify on security incidents or guardrail events." section="notifications" field="incident_alerts" />
                        <ToggleRow label="API Usage Alerts" description="Alert when API rate limits are approached." section="notifications" field="api_alerts" />
                        <ToggleRow label="Weekly Digest" description="Send a weekly summary of platform activity." section="notifications" field="weekly_digest" />
                    </div>
                </SectionCard>
            );
            case "Security": return (
                <SectionCard>
                    <h3 style={{ fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0' }}>Security Settings</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '4px 24px 20px' }}>Platform-wide authentication and access security.</p>
                    <div style={{ padding: '0 24px 24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <ToggleRow label="Require MFA for Admins" description="Two-factor authentication for all admin accounts." section="security" field="mfa_required" />
                        <ToggleRow label="Rate Limiting" description="Enforce API rate limits per company." section="security" field="rate_limiting" />
                        <ToggleRow label="IP Whitelist" description="Restrict platform access to approved IP addresses." section="security" field="ip_whitelist" />
                        <form className="ih-form">
                            <div className="ih-form-group">
                                <label>Session Timeout (minutes)</label>
                                <input type="number" value={settings.security.session_timeout}
                                    onChange={e => setSettings(p => ({ ...p, security: { ...p.security, session_timeout: e.target.value } }))} />
                            </div>
                        </form>
                    </div>
                </SectionCard>
            );
            case "Appearance": return (
                <SectionCard>
                    <h3 style={{ fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0' }}>Appearance Settings</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '4px 24px 20px' }}>Theme and display preferences.</p>
                    <div style={{ padding: '0 24px 24px' }}>
                        <form className="ih-form">
                            <div className="ih-form-row">
                                <div className="ih-form-group">
                                    <label>Default Theme</label>
                                    <select value={settings.appearance.theme} onChange={e => setSettings(p => ({ ...p, appearance: { ...p.appearance, theme: e.target.value } }))}>
                                        <option value="dark">Dark Mode</option>
                                        <option value="light">Light Mode</option>
                                        <option value="system">System Preference</option>
                                    </select>
                                </div>
                                <div className="ih-form-group">
                                    <label>Accent Color</label>
                                    <select value={settings.appearance.accent} onChange={e => setSettings(p => ({ ...p, appearance: { ...p.appearance, accent: e.target.value } }))}>
                                        <option value="blue">Electric Blue</option>
                                        <option value="violet">Violet</option>
                                        <option value="cyan">Cyan</option>
                                        <option value="green">Green</option>
                                    </select>
                                </div>
                            </div>
                            <ToggleRow label="Compact Mode" description="Reduce padding and whitespace across the UI." section="appearance" field="compact_mode" />
                        </form>
                    </div>
                </SectionCard>
            );
            default: return null;
        }
    };

    if (loading) {
        return (
            <DashboardGrid>
                <PageHeader title="Platform Settings" description="Loading configuration..." />
                <div style={{ padding: '24px', textAlign: 'center' }}>Loading platform settings from database...</div>
            </DashboardGrid>
        );
    }

    return (
        <DashboardGrid>
            <PageHeader
                title="Platform Settings"
                description="Configure global platform behaviour, AI models, voices, security, and appearance."
                rightContent={<Button variant="primary" onClick={handleSave} disabled={saving}><Save size={16} /> {saving ? "Saving..." : "Save Changes"}</Button>}
            />

            <div style={{ display: 'flex', gap: '24px', alignItems: 'flex-start' }}>
                {/* Sidebar tabs */}
                <div style={{ width: '200px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    {TABS.map(t => (
                        <button key={t} onClick={() => setActiveTab(t)} style={{
                            padding: '10px 14px', borderRadius: '8px', border: 'none', cursor: 'pointer', textAlign: 'left',
                            background: activeTab === t ? 'var(--primary-subtle)' : 'transparent',
                            color: activeTab === t ? 'var(--primary)' : 'var(--text-secondary)',
                            fontWeight: activeTab === t ? '600' : '400', fontSize: '14px',
                            borderLeft: activeTab === t ? '3px solid var(--primary)' : '3px solid transparent',
                            transition: 'all 0.15s ease',
                        }}>{t}</button>
                    ))}
                </div>
                {/* Content area */}
                <div style={{ flex: 1 }}>
                    {renderTab()}
                </div>
            </div>
        </DashboardGrid>
    );
}
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Edit, Trash2, Key, Mail, Phone, Globe, CheckCircle, XCircle, Database, Users, Activity, Sparkles, Server, Calendar, Clock, AlertTriangle } from "lucide-react";
import { useEffect, useState } from "react";
import PageHeader from "../../components/layout/PageHeader";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import { CompaniesAPI } from "../../api/companies";
import "../../styles/admin/companydetail.css";

export default function CompanyDetail() {
    const { companyId } = useParams();
    const navigate = useNavigate();
    
    const [company, setCompany] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [resetPasswordLoading, setResetPasswordLoading] = useState(false);

    // New tabs state
    const [activeTab, setActiveTab] = useState("overview");
    const [recruiters, setRecruiters] = useState([]);
    const [campaigns, setCampaigns] = useState([]);
    const [candidates, setCandidates] = useState([]);
    const [interviews, setInterviews] = useState([]);
    const [auditLogs, setAuditLogs] = useState([]);
    const [tabLoading, setTabLoading] = useState(false);

    const fetchCompany = async () => {
        try {
            setError(null);
            setLoading(true);
            const data = await CompaniesAPI.getCompany(companyId);
            setCompany(data);
        } catch (err) {
            console.error("Failed to load company:", err);
            setError("Unable to load company information.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCompany();
    }, [companyId]);

    useEffect(() => {
        const fetchTabData = async () => {
            if (activeTab === "overview") return;
            setTabLoading(true);
            try {
                if (activeTab === "recruiters" && recruiters.length === 0) {
                    const res = await CompaniesAPI.getRecruiters(companyId);
                    setRecruiters(res.data || res);
                } else if (activeTab === "campaigns" && campaigns.length === 0) {
                    const res = await CompaniesAPI.getCampaigns(companyId);
                    setCampaigns(res.data || res);
                } else if (activeTab === "candidates" && candidates.length === 0) {
                    const res = await CompaniesAPI.getCandidates(companyId);
                    setCandidates(res.data || res);
                } else if (activeTab === "interviews" && interviews.length === 0) {
                    const res = await CompaniesAPI.getInterviews(companyId);
                    setInterviews(res.data || res);
                } else if (activeTab === "auditLogs" && auditLogs.length === 0) {
                    const res = await CompaniesAPI.getAuditLogs(companyId);
                    setAuditLogs(res.data || res);
                }
            } catch (err) {
                console.error(`Failed to load ${activeTab}:`, err);
            } finally {
                setTabLoading(false);
            }
        };
        fetchTabData();
    }, [activeTab, companyId]);

    const handleSuspend = async () => {
        try {
            await CompaniesAPI.suspendCompany(companyId);
            fetchCompany();
        } catch (err) {
            console.error("Failed to suspend company:", err);
        }
    };

    const handleActivate = async () => {
        try {
            await CompaniesAPI.activateCompany(companyId);
            fetchCompany();
        } catch (err) {
            console.error("Failed to activate company:", err);
        }
    };

    const handleDelete = async () => {
        if (window.confirm("Are you sure you want to delete this company? This will hide them from the platform and invalidate their tokens.")) {
            try {
                await CompaniesAPI.deleteCompany(companyId);
                navigate("/admin/companies");
            } catch (err) {
                console.error("Failed to delete company:", err);
                alert("Failed to delete company");
            }
        }
    };

    const handleResetPassword = async () => {
        if (window.confirm("Are you sure you want to reset the admin password for this company?")) {
            setResetPasswordLoading(true);
            try {
                const res = await CompaniesAPI.resetPassword(companyId);
                alert(`Password Reset Successful!\n\nNew Temporary Password: ${res.temporary_password}\n\nPlease share this securely with the company admin.`);
            } catch (err) {
                console.error("Failed to reset password:", err);
                alert("Failed to reset password");
            } finally {
                setResetPasswordLoading(false);
            }
        }
    };

    const handleRestore = async () => {
        try {
            await CompaniesAPI.restoreCompany(companyId);
            fetchCompany();
        } catch (err) {
            console.error("Failed to restore company:", err);
            alert("Failed to restore company");
        }
    };

    if (loading) {
        return (
            <div className="cd-container">
                <PageHeader title="Loading..." />
                <div style={{ padding: '20px', color: 'var(--text-secondary)' }}>Loading company details...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="cd-container">
                <PageHeader title="Error" />
                <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'flex-start' }}>
                    <span style={{ color: 'var(--danger)' }}>{error}</span>
                    <Button variant="outline" onClick={fetchCompany}>Retry</Button>
                </div>
            </div>
        );
    }

    if (!company) {
        return <div className="cd-container"><PageHeader title="Company Not Found" /></div>;
    }

    const rightContent = (
        <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="outline" onClick={() => navigate(`/admin/companies/edit/${companyId}`)}>
                <Edit size={16} /> Edit Configuration
            </Button>
            
            {company.deleted_at ? (
                <Button variant="success" onClick={handleRestore}>
                    Restore
                </Button>
            ) : (
                <>
                    {company.subscription?.status === 'active' ? (
                        <Button variant="outline" onClick={handleSuspend}>
                            Suspend
                        </Button>
                    ) : (
                        <Button variant="success" onClick={handleActivate}>
                            Activate
                        </Button>
                    )}
                    <Button variant="danger" onClick={handleDelete}>
                        <Trash2 size={16} /> Delete
                    </Button>
                </>
            )}
        </div>
    );

    const titleContent = (
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button 
                onClick={() => navigate("/admin/companies")}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
            >
                <ArrowLeft size={20} />
            </button>
            {company.general?.name}
            <Badge variant={company.subscription?.status === 'active' ? 'success' : 'danger'}>{company.subscription?.status?.toUpperCase()}</Badge>
            {company.subscription?.plan && <Badge variant="outline">{company.subscription?.plan}</Badge>}
        </div>
    );

    const FeatureItem = ({ label, enabled }) => (
        <div className="cd-feature-item">
            {enabled ? <CheckCircle size={16} color="var(--success)" /> : <XCircle size={16} color="var(--text-muted)" />}
            <span style={{ color: enabled ? 'var(--text)' : 'var(--text-muted)' }}>{label}</span>
        </div>
    );

    const ProgressBar = ({ label, value, max }) => {
        if (value === undefined || max === undefined || max === null) {
            return (
                <div className="cd-progress-item">
                    <div className="cd-progress-header">
                        <span className="label">{label}</span>
                        <span className="value" style={{ color: 'var(--text-muted)' }}>-- / --</span>
                    </div>
                    <div className="cd-progress-bar">
                        <div className="cd-progress-fill" style={{ width: '0%', background: 'var(--border)' }}></div>
                    </div>
                </div>
            );
        }
        
        const percentage = max > 0 ? Math.min((value / max) * 100, 100) : 0;
        return (
            <div className="cd-progress-item">
                <div className="cd-progress-header">
                    <span className="label">{label}</span>
                    <span className="value">{value} / {max} ({Math.round(percentage)}%)</span>
                </div>
                <div className="cd-progress-bar">
                    <div className="cd-progress-fill" style={{ width: `${percentage}%` }}></div>
                </div>
            </div>
        );
    };

    return (
        <div className="cd-container">
            <PageHeader 
                title={titleContent}
                description={`Industry: ${company.general?.industry || 'Not Specified'} • ID: ${company._id || company.id}`}
                rightContent={rightContent}
            />

            {/* Tabs Navigation */}
            <div className="cd-tabs-nav" style={{ display: 'flex', gap: '16px', borderBottom: '1px solid var(--border)', marginBottom: '24px', overflowX: 'auto', paddingBottom: '8px' }}>
                {["overview", "recruiters", "campaigns", "candidates", "interviews", "auditLogs"].map((tab) => (
                    <button 
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        style={{ 
                            background: 'none', border: 'none', padding: '12px 16px', cursor: 'pointer',
                            color: activeTab === tab ? 'var(--primary)' : 'var(--text-secondary)',
                            borderBottom: activeTab === tab ? '2px solid var(--primary)' : '2px solid transparent',
                            fontWeight: activeTab === tab ? '600' : '400',
                            textTransform: 'capitalize', whiteSpace: 'nowrap'
                        }}
                    >
                        {tab === "auditLogs" ? "Audit Logs" : tab}
                    </button>
                ))}
            </div>

            {/* Tabs Content */}
            {activeTab === "overview" && (
            <div className="cd-grid">
                
                {/* KPI Cards */}
                <div className="cd-col-3">
                    <div className="cd-kpi">
                        <span className="cd-kpi-label">Total Interviews</span>
                        <span className="cd-kpi-value">{company.stats?.total_interviews ?? "--"}</span>
                    </div>
                </div>
                <div className="cd-col-3">
                    <div className="cd-kpi">
                        <span className="cd-kpi-label">Active Candidates</span>
                        <span className="cd-kpi-value">{company.stats?.active_candidates ?? "--"}</span>
                    </div>
                </div>
                <div className="cd-col-3">
                    <div className="cd-kpi">
                        <span className="cd-kpi-label">Monthly Usage</span>
                        <span className="cd-kpi-value">
                            {company.stats?.monthly_usage ?? "--"} 
                            {company.limits?.monthly_interviews ? ` / ${company.limits.monthly_interviews}` : ''}
                        </span>
                    </div>
                </div>
                <div className="cd-col-3">
                    <div className="cd-kpi">
                        <span className="cd-kpi-label">Storage Used</span>
                        <span className="cd-kpi-value">
                            {company.stats?.storage_used_gb !== undefined ? `${company.stats.storage_used_gb}GB` : "--"}
                            {company.limits?.storage_limit_gb ? ` / ${company.limits.storage_limit_gb}GB` : ''}
                        </span>
                    </div>
                </div>

                {/* Left Column: General Info & AI Config */}
                <div className="cd-col-6" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <div className="cd-card">
                        <div className="cd-card-header">
                            <span className="cd-card-title">Company Information</span>
                        </div>
                        <div className="cd-info-list">
                            <div className="cd-info-item">
                                <div className="cd-info-icon"><Mail size={16}/></div>
                                <div className="cd-info-text">
                                    <span>Primary Email</span>
                                    <span>{company.general?.contact_email || "--"}</span>
                                </div>
                            </div>
                            <div className="cd-info-item">
                                <div className="cd-info-icon"><Phone size={16}/></div>
                                <div className="cd-info-text">
                                    <span>Phone Number</span>
                                    <span>{company.general?.phone || '--'}</span>
                                </div>
                            </div>
                            <div className="cd-info-item">
                                <div className="cd-info-icon"><Globe size={16}/></div>
                                <div className="cd-info-text">
                                    <span>Website</span>
                                    <span>{company.general?.website || '--'}</span>
                                </div>
                            </div>
                            <div className="cd-info-item">
                                <div className="cd-info-icon"><Calendar size={16}/></div>
                                <div className="cd-info-text">
                                    <span>Created Date</span>
                                    <span>{company.created_at ? new Date(company.created_at).toLocaleDateString() : '--'}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="cd-card">
                        <div className="cd-card-header">
                            <span className="cd-card-title"><Sparkles size={18}/> AI Configuration</span>
                        </div>
                        <div className="cd-feature-group">
                            <h5 className="cd-feature-title">LLM Providers</h5>
                            <div className="cd-badge-list">
                                {company.allowed_llm_tiers?.length > 0 
                                    ? company.allowed_llm_tiers.map((t, i) => <Badge key={i} variant="outline">{t}</Badge>)
                                    : <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Not Configured</span>}
                            </div>
                        </div>
                        <div className="cd-feature-group">
                            <h5 className="cd-feature-title">Supported Languages</h5>
                            <div className="cd-badge-list">
                                {company.allowed_languages?.length > 0 
                                    ? company.allowed_languages.map((l, i) => <Badge key={i} variant="outline">{l}</Badge>)
                                    : <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Not Configured</span>}
                            </div>
                        </div>
                        <div className="cd-feature-group">
                            <h5 className="cd-feature-title">Voices</h5>
                            <div className="cd-badge-list">
                                {company.allowed_voices?.length > 0 
                                    ? company.allowed_voices.map((v, i) => <Badge key={i} variant="outline">{v}</Badge>)
                                    : <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Not Configured</span>}
                            </div>
                        </div>
                        <div className="cd-feature-group">
                            <h5 className="cd-feature-title">Interview Strategies</h5>
                            <div className="cd-badge-list">
                                {company.allowed_strategies?.length > 0 
                                    ? company.allowed_strategies.map((s, i) => <Badge key={i} variant="outline">{s}</Badge>)
                                    : <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Not Configured</span>}
                            </div>
                        </div>
                        <div className="cd-feature-group" style={{ marginBottom: 0 }}>
                            <h5 className="cd-feature-title">Interview Modes</h5>
                            <div className="cd-badge-list">
                                {company.allowed_interview_modes?.length > 0 
                                    ? company.allowed_interview_modes.map((m, i) => <Badge key={i} variant="outline">{m}</Badge>)
                                    : <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Not Configured</span>}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column: Security, Usage, Features */}
                <div className="cd-col-6" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <div className="cd-card">
                        <div className="cd-card-header">
                            <span className="cd-card-title">Security & Access</span>
                        </div>
                        <div className="cd-info-list" style={{ marginBottom: '16px' }}>
                            <div className="cd-info-item">
                                <div className="cd-info-icon"><AlertTriangle size={16} /></div>
                                <div className="cd-info-text">
                                    <span>MFA Status</span>
                                    <span>{company.security?.mfa_required ? "Enabled" : "Disabled"}</span>
                                </div>
                            </div>
                            <div className="cd-info-item">
                                <div className="cd-info-icon"><Clock size={16}/></div>
                                <div className="cd-info-text">
                                    <span>Session Timeout</span>
                                    <span>{company.security?.session_timeout_minutes ? `${company.security.session_timeout_minutes} Minutes` : "Not Configured"}</span>
                                </div>
                            </div>
                            <div className="cd-info-item">
                                <div className="cd-info-icon"><Key size={16}/></div>
                                <div className="cd-info-text">
                                    <span>Login Policy</span>
                                    <span>{company.security?.password_policy || "Not Configured"}</span>
                                </div>
                            </div>
                        </div>
                        <Button variant="outline" onClick={handleResetPassword} disabled={resetPasswordLoading} style={{ width: '100%', justifyContent: 'center' }}>
                            <Key size={16} />
                            {resetPasswordLoading ? "Resetting..." : "Reset Admin Password"}
                        </Button>
                    </div>

                    <div className="cd-card">
                        <div className="cd-card-header">
                            <span className="cd-card-title"><Activity size={18}/> Usage & Limits</span>
                        </div>
                        <div className="cd-progress-group">
                            <ProgressBar label="Campaigns" value={company.usage?.campaigns} max={company.limits?.max_campaigns} />
                            <ProgressBar label="Recruiters" value={company.usage?.recruiters} max={company.limits?.max_recruiters} />
                            <ProgressBar label="Candidates" value={company.usage?.candidates} max={company.limits?.max_candidates} />
                            <ProgressBar label="Interviews" value={company.usage?.interviews} max={company.limits?.monthly_interviews} />
                        </div>
                    </div>
                </div>

                {/* Full Width: Enabled Features */}
                <div className="cd-col-12">
                    <div className="cd-card">
                        <div className="cd-card-header">
                            <span className="cd-card-title"><Server size={18}/> Platform Capabilities</span>
                        </div>
                        <div className="cd-grid" style={{ gap: '0' }}>
                            <div className="cd-col-6">
                                <div className="cd-feature-group">
                                    <h5 className="cd-feature-title">AI Features</h5>
                                    <div className="cd-feature-grid">
                                        <FeatureItem label="Resume Screening" enabled={company.features?.resume_screening ?? false} />
                                        <FeatureItem label="Voice Interviews" enabled={company.features?.voice_interview ?? false} />
                                        <FeatureItem label="Interview Analysis" enabled={company.features?.interview_analysis ?? false} />
                                        <FeatureItem label="Explainability Engine" enabled={company.features?.explainability ?? false} />
                                    </div>
                                </div>
                            </div>
                            <div className="cd-col-6">
                                <div className="cd-feature-group">
                                    <h5 className="cd-feature-title">Platform Features</h5>
                                    <div className="cd-feature-grid">
                                        <FeatureItem label="Reports & Analytics" enabled={company.features?.reports ?? false} />
                                        <FeatureItem label="API Access" enabled={company.features?.api_access ?? false} />
                                        <FeatureItem label="SSO Integration" enabled={company.security?.sso_enabled ?? false} />
                                        <FeatureItem label="Custom Branding" enabled={company.features?.branding ?? false} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                {/* Full Width: Company Health */}
                <div className="cd-col-12">
                    <div className="cd-card">
                        <div className="cd-card-header">
                            <span className="cd-card-title"><Activity size={18}/> Company Health & Activity</span>
                        </div>
                        <div className="cd-grid">
                            <div className="cd-col-6">
                                <h5 className="cd-feature-title">Recent Activity</h5>
                                {company.recent_activity?.length > 0 ? (
                                    <div className="cd-info-list">
                                        {company.recent_activity.map((activity, index) => (
                                            <div className="cd-info-item" key={index}>
                                                <div className="cd-info-icon" style={{background: 'var(--surface-elevated)'}}><Users size={16}/></div>
                                                <div className="cd-info-text">
                                                    <span>{activity.timestamp ? new Date(activity.timestamp).toLocaleString() : '--'}</span>
                                                    <span>{activity.description || '--'}</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No recent activity.</div>
                                )}
                            </div>
                            <div className="cd-col-6">
                            </div>
                        </div>
                    </div>
                </div>

            </div>
            )}

            {activeTab !== "overview" && (
                <div className="cd-card" style={{ padding: '24px' }}>
                    {tabLoading ? (
                        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading...</div>
                    ) : (
                        <div style={{ overflowX: 'auto' }}>
                            {activeTab === "recruiters" && (
                                <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                                    <thead>
                                        <tr style={{ borderBottom: '1px solid var(--border)' }}>
                                            <th style={{ padding: '12px' }}>Name</th>
                                            <th style={{ padding: '12px' }}>Email</th>
                                            <th style={{ padding: '12px' }}>Role</th>
                                            <th style={{ padding: '12px' }}>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {recruiters.length > 0 ? recruiters.map((r, i) => (
                                            <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                                                <td style={{ padding: '12px' }}>{r.name}</td>
                                                <td style={{ padding: '12px' }}>{r.email}</td>
                                                <td style={{ padding: '12px' }}><Badge>{r.role}</Badge></td>
                                                <td style={{ padding: '12px' }}><Badge variant={r.status === 'active' ? 'success' : 'outline'}>{r.status}</Badge></td>
                                            </tr>
                                        )) : (<tr><td colSpan="4" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No recruiters found.</td></tr>)}
                                    </tbody>
                                </table>
                            )}

                            {activeTab === "campaigns" && (
                                <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                                    <thead>
                                        <tr style={{ borderBottom: '1px solid var(--border)' }}>
                                            <th style={{ padding: '12px' }}>Title</th>
                                            <th style={{ padding: '12px' }}>Department</th>
                                            <th style={{ padding: '12px' }}>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {campaigns.length > 0 ? campaigns.map((c, i) => (
                                            <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                                                <td style={{ padding: '12px' }}>{c.title}</td>
                                                <td style={{ padding: '12px' }}>{c.department || '--'}</td>
                                                <td style={{ padding: '12px' }}><Badge>{c.status}</Badge></td>
                                            </tr>
                                        )) : (<tr><td colSpan="3" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No campaigns found.</td></tr>)}
                                    </tbody>
                                </table>
                            )}

                            {activeTab === "candidates" && (
                                <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                                    <thead>
                                        <tr style={{ borderBottom: '1px solid var(--border)' }}>
                                            <th style={{ padding: '12px' }}>Name</th>
                                            <th style={{ padding: '12px' }}>Email</th>
                                            <th style={{ padding: '12px' }}>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {candidates.length > 0 ? candidates.map((c, i) => (
                                            <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                                                <td style={{ padding: '12px' }}>{c.full_name || c.name || '--'}</td>
                                                <td style={{ padding: '12px' }}>{c.email || '--'}</td>
                                                <td style={{ padding: '12px' }}><Badge>{c.status || 'unknown'}</Badge></td>
                                            </tr>
                                        )) : (<tr><td colSpan="3" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No candidates found.</td></tr>)}
                                    </tbody>
                                </table>
                            )}

                            {activeTab === "interviews" && (
                                <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                                    <thead>
                                        <tr style={{ borderBottom: '1px solid var(--border)' }}>
                                            <th style={{ padding: '12px' }}>Candidate</th>
                                            <th style={{ padding: '12px' }}>Campaign</th>
                                            <th style={{ padding: '12px' }}>Score</th>
                                            <th style={{ padding: '12px' }}>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {interviews.length > 0 ? interviews.map((iv, i) => (
                                            <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                                                <td style={{ padding: '12px' }}>{iv.candidate_name || '--'}</td>
                                                <td style={{ padding: '12px' }}>{iv.campaign_name || '--'}</td>
                                                <td style={{ padding: '12px' }}>{iv.score ? `${iv.score}%` : '--'}</td>
                                                <td style={{ padding: '12px' }}><Badge variant={iv.status === 'completed' ? 'success' : 'outline'}>{iv.status || 'unknown'}</Badge></td>
                                            </tr>
                                        )) : (<tr><td colSpan="4" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No interviews found.</td></tr>)}
                                    </tbody>
                                </table>
                            )}

                            {activeTab === "auditLogs" && (
                                <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                                    <thead>
                                        <tr style={{ borderBottom: '1px solid var(--border)' }}>
                                            <th style={{ padding: '12px' }}>Action</th>
                                            <th style={{ padding: '12px' }}>User ID</th>
                                            <th style={{ padding: '12px' }}>Timestamp</th>
                                            <th style={{ padding: '12px' }}>Details</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {auditLogs.length > 0 ? auditLogs.map((log, i) => (
                                            <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                                                <td style={{ padding: '12px' }}><strong>{log.action}</strong></td>
                                                <td style={{ padding: '12px', fontSize: '13px' }}>{log.user_id}</td>
                                                <td style={{ padding: '12px', fontSize: '13px' }}>{new Date(log.timestamp).toLocaleString()}</td>
                                                <td style={{ padding: '12px', fontSize: '13px', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                    {log.details ? JSON.stringify(log.details) : '--'}
                                                </td>
                                            </tr>
                                        )) : (<tr><td colSpan="4" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No audit logs found.</td></tr>)}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
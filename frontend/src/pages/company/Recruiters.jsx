import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    FaUserPlus, FaEdit, FaTrash, FaKey, FaCopy, FaSearch, FaUserTie, FaBan, FaCheck, FaRedo,
    FaChartBar, FaCircle, FaTimes, FaTasks, FaThLarge, FaList, FaEnvelope, FaPhone, FaUsers, FaSpinner
} from "react-icons/fa";
import recruiterManagementService from "../../services/company/recruiterManagementService";
import campaignService from "../../services/company/campaignService";
import analyticsService from "../../services/company/analyticsService";
import PageHeader from "../../components/common/PageHeader";
import Button from "../../components/common/Button";
import StatusBadge from "../../components/common/StatusBadge";
import StatsCard from "../../components/common/StatsCard";
import Toast from "../../components/common/Toast";

import "../../styles/company/Team.css";

// F-01: Recruiters.jsx and Team.jsx consolidated into this single page.
// Both previously hit the exact same backend resource (/company/team --
// see backend/app/api/company/team.py's own docstring: "Decision: Team
// Members == Recruiters. One collection, one concept."). This page keeps
// the union of both pages' prior functionality:
//   - from Recruiters.jsx: suspend/activate, force password reset, reset
//     password, delete, campaign assignment, the activity/candidates/
//     interviews drawer, and performance-metric merge.
//   - from Team.jsx: the stats row, the grid/list view toggle, the
//     server-side search + role filter, and the invite form's role picker.
// `recruiterManagementService` (not `teamService`, now retired) is the
// single canonical client, since it already had the full endpoint surface
// and is also depended on by CandidateDetails.jsx/NewCampaign.jsx/
// EditCampaign.jsx for an unrelated recruiter dropdown -- untouched here.

const ROLE_COLORS = {
    Admin: { bg: "rgba(59,130,246,0.15)", color: "#3B82F6" },
    Recruiter: { bg: "rgba(16,185,129,0.15)", color: "#10B981" },
    "Hiring Manager": { bg: "rgba(139,92,246,0.15)", color: "#8B5CF6" },
    Viewer: { bg: "rgba(100,116,139,0.15)", color: "#64748B" },
};

const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: (i) => ({ opacity: 1, y: 0, transition: { delay: i * 0.07, duration: 0.35 } })
};

export default function Recruiters() {
    const [recruiters, setRecruiters] = useState([]);
    const [performance, setPerformance] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const [roleFilter, setRoleFilter] = useState("All");
    const [view, setView] = useState("list");
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [credentialsModal, setCredentialsModal] = useState(null);
    const [toast, setToast] = useState(null);
    const [assignModal, setAssignModal] = useState(null);
    const [campaigns, setCampaigns] = useState([]);
    const [selectedCampaigns, setSelectedCampaigns] = useState([]);
    const [formData, setFormData] = useState({
        name: "", email: "", phone: "", department: "", designation: "", role: "Recruiter"
    });

    const [drawerOpen, setDrawerOpen] = useState(false);
    const [selectedRecruiter, setSelectedRecruiter] = useState(null);
    const [recruiterActivity, setRecruiterActivity] = useState([]);
    const [recruiterCandidates, setRecruiterCandidates] = useState([]);
    const [recruiterInterviews, setRecruiterInterviews] = useState([]);

    const openDrawer = async (recruiter) => {
        setSelectedRecruiter(recruiter);
        setDrawerOpen(true);
        try {
            const [actRes, candRes, intRes] = await Promise.all([
                recruiterManagementService.getRecruiterActivity(recruiter.id),
                recruiterManagementService.getRecruiterCandidates(recruiter.id),
                recruiterManagementService.getRecruiterInterviews(recruiter.id)
            ]);
            setRecruiterActivity(actRes.data?.data || actRes.data || []);
            setRecruiterCandidates(candRes.data?.data || candRes.data || []);
            setRecruiterInterviews(intRes.data?.data || intRes.data || []);
        } catch (err) {
            console.error("Failed to fetch recruiter details", err);
        }
    };

    const loadRecruiters = async () => {
        try {
            setLoading(true);
            const params = {};
            if (searchTerm) params.search = searchTerm;
            if (roleFilter !== "All") params.role = roleFilter;

            const [teamRes, perfRes] = await Promise.all([
                recruiterManagementService.getRecruiters(params),
                analyticsService.getRecruiterPerformance()
            ]);

            const team = teamRes.data?.data || teamRes.data || [];
            const perf = perfRes.data?.data || perfRes.data || [];
            setPerformance(perf);

            // Merge performance data into team data
            const merged = team.map(member => {
                const pData = perf.find(p => p.id === member.id) || {};
                return { ...member, performance: pData };
            });

            setRecruiters(merged);
        } catch (err) {
            console.error(err);
            showToast("Failed to load recruiters", "error");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadRecruiters();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchTerm, roleFilter]);

    useEffect(() => {
        loadCampaigns();
    }, []);

    const loadCampaigns = async () => {
        try {
            const res = await campaignService.getCampaigns();
            setCampaigns(res.data?.data || res.data || []);
        } catch (err) {
            console.error(err);
        }
    };

    const showToast = (msg, type = "success") => {
        setToast({ message: msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    // Stats reflect the currently loaded (search/role-filtered) set, exactly
    // as Team.jsx's stats row did.
    const totalActive = recruiters.filter(r => r.status === "active").length;
    const totalRecruiters = recruiters.filter(r => r.role === "Recruiter").length;
    const totalManagers = recruiters.filter(r => r.role === "Hiring Manager").length;
    const totalAdmins = recruiters.filter(r => r.role === "Admin").length;

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            const res = await recruiterManagementService.createRecruiter(formData);
            // /company/team returns TeamMemberResponse directly (not wrapped)
            const data = res.data;
            setIsModalOpen(false);
            setCredentialsModal({
                username: data.email || formData.email,
                password: data.temporary_password
            });
            loadRecruiters();
            showToast("Recruiter created successfully", "success");
            setFormData({ name: "", email: "", phone: "", department: "", designation: "", role: "Recruiter" });
        } catch (err) {
            console.error(err);
            const errorMsg = err.response?.data?.message || err.response?.data?.detail || "Failed to create recruiter";
            showToast(errorMsg, "error");
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to remove this recruiter?")) return;
        try {
            await recruiterManagementService.deleteRecruiter(id);
            showToast("Recruiter removed", "success");
            loadRecruiters();
        } catch (err) {
            console.error(err);
            showToast("Failed to remove recruiter", "error");
        }
    };

    const handleResetPassword = async (id) => {
        if (!window.confirm("Are you sure you want to reset this recruiter's password?")) return;
        try {
            const res = await recruiterManagementService.resetPassword(id);
            const data = res.data?.data || res.data;
            setCredentialsModal({
                username: "Existing Email",
                password: data.temporary_password
            });
            showToast("Password reset successfully", "success");
        } catch (err) {
            console.error(err);
            showToast("Failed to reset password", "error");
        }
    };

    const copyCredentials = () => {
        navigator.clipboard.writeText(`Username: ${credentialsModal.username}\nPassword: ${credentialsModal.password}`);
        showToast("Credentials copied to clipboard", "success");
    };

    const handleOpenAssign = async (recruiter) => {
        try {
            const res = await recruiterManagementService.getRecruiterCampaigns(recruiter.id);
            const assigned = (res.data?.data || res.data || []).map(c => c._id);
            setSelectedCampaigns(assigned);
            setAssignModal(recruiter);
        } catch (err) {
            showToast("Failed to load recruiter campaigns", "error");
        }
    };

    const handleSaveAssign = async () => {
        try {
            await recruiterManagementService.updateRecruiterCampaigns(assignModal.id, selectedCampaigns);
            showToast("Campaigns assigned successfully", "success");
            setAssignModal(null);
        } catch (err) {
            showToast("Failed to assign campaigns", "error");
        }
    };

    const handleSuspend = async (id) => {
        if (!window.confirm("Suspend this recruiter? They will be unable to login.")) return;
        try {
            await recruiterManagementService.suspendRecruiter(id);
            showToast("Recruiter suspended", "success");
            loadRecruiters();
        } catch {
            showToast("Failed to suspend recruiter", "error");
        }
    };

    const handleActivate = async (id) => {
        try {
            await recruiterManagementService.activateRecruiter(id);
            showToast("Recruiter activated", "success");
            loadRecruiters();
        } catch {
            showToast("Failed to activate recruiter", "error");
        }
    };

    const handleForceReset = async (id) => {
        if (!window.confirm("Force recruiter to change password on next login?")) return;
        try {
            await recruiterManagementService.forcePasswordReset(id);
            showToast("Password reset required on next login", "success");
        } catch {
            showToast("Failed to set force reset", "error");
        }
    };

    // The backend already applies `search`/`role` server-side (see
    // loadRecruiters); `recruiters` is the result set as returned.
    const filtered = recruiters;

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: 24, animation: "fadeInPage 0.4s ease-out" }}>
            {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

            <PageHeader
                title="Recruiters"
                subtitle="Manage your recruitment team"
                actions={
                    <Button variant="primary" icon={<FaUserPlus />} onClick={() => setIsModalOpen(true)}>Add Recruiter</Button>
                }
            />

            {/* Stats */}
            <div className="team-stats-row">
                {[
                    { title: "Total Members", value: recruiters.length, icon: <FaUsers />, color: "#3B82F6" },
                    { title: "Active", value: totalActive, icon: <FaCheck />, color: "#10B981" },
                    { title: "Recruiters", value: totalRecruiters, icon: <FaUsers />, color: "#8B5CF6" },
                    { title: "Hiring Managers", value: totalManagers, icon: <FaUsers />, color: "#F59E0B" },
                    { title: "Admins", value: totalAdmins, icon: <FaUsers />, color: "#EC4899" },
                ].map((s, i) => (
                    <motion.div key={s.title} custom={i} variants={cardVariants} initial="hidden" animate="visible">
                        <StatsCard {...s} />
                    </motion.div>
                ))}
            </div>

            <div style={{
                background: "var(--card)", padding: 20, borderRadius: "var(--radius-lg)",
                border: "1px solid var(--border)", boxShadow: "var(--shadow)"
            }}>
                <div style={{ marginBottom: 20, display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
                    <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
                        <div style={{ position: "relative", flex: 1, minWidth: 220, maxWidth: 300 }}>
                            <FaSearch style={{ position: "absolute", left: 14, top: 14, color: "var(--text-muted)" }} />
                            <input
                                type="text"
                                placeholder="Search recruiters..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                style={{
                                    width: "100%", padding: "10px 16px 10px 40px",
                                    background: "var(--bg)", border: "1px solid var(--border)",
                                    borderRadius: "var(--radius-md)", color: "var(--text)", outline: "none"
                                }}
                            />
                        </div>
                        <select
                            value={roleFilter}
                            onChange={(e) => setRoleFilter(e.target.value)}
                            style={{
                                padding: "10px 14px", borderRadius: "var(--radius-md)",
                                border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)"
                            }}
                        >
                            <option value="All">All Roles</option>
                            <option value="Admin">Admin</option>
                            <option value="Recruiter">Recruiter</option>
                            <option value="Hiring Manager">Hiring Manager</option>
                            <option value="Viewer">Viewer</option>
                        </select>
                    </div>

                    <div className="team-view-toggle">
                        <button
                            className={`view-toggle-btn ${view === "list" ? "active" : ""}`}
                            onClick={() => setView("list")}
                            title="List view"
                            type="button"
                        >
                            <FaList />
                        </button>
                        <button
                            className={`view-toggle-btn ${view === "grid" ? "active" : ""}`}
                            onClick={() => setView("grid")}
                            title="Grid view"
                            type="button"
                        >
                            <FaThLarge />
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div style={{ textAlign: "center", padding: 40, color: "var(--text-secondary)" }}>Loading recruiters...</div>
                ) : filtered.length === 0 ? (
                    <div style={{ textAlign: "center", padding: 60, color: "var(--text-muted)" }}>
                        <FaUserTie size={40} style={{ marginBottom: 16, opacity: 0.5 }} />
                        <p>No recruiters found.</p>
                    </div>
                ) : view === "list" ? (
                    <div style={{ overflowX: "auto" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 900 }}>
                            <thead>
                                <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left", color: "var(--text-secondary)", fontSize: 13, textTransform: "uppercase", letterSpacing: 0.5 }}>
                                    <th style={{ padding: "16px", fontWeight: 600 }}>Name</th>
                                    <th style={{ padding: "16px", fontWeight: 600 }}>Role & Dept</th>
                                    <th style={{ padding: "16px", fontWeight: 600 }}>KPIs & Workload</th>
                                    <th style={{ padding: "16px", fontWeight: 600 }}>Status</th>
                                    <th style={{ padding: "16px", fontWeight: 600 }}>Last Active</th>
                                    <th style={{ padding: "16px", fontWeight: 600, textAlign: "right" }}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map(r => (
                                    <tr key={r.id} style={{ borderBottom: "1px solid var(--border)", cursor: "pointer" }} onClick={(e) => {
                                        if (e.target.closest('button')) return;
                                        openDrawer(r);
                                    }}>
                                        <td style={{ padding: "16px" }}>
                                            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                                <div style={{
                                                    width: 36, height: 36, borderRadius: "50%",
                                                    background: "var(--primary-light)", color: "var(--primary)",
                                                    display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 600
                                                }}>
                                                    {(r.name || r.email || "?")[0].toUpperCase()}
                                                </div>
                                                <div>
                                                    <div style={{ fontWeight: 600, color: "var(--text)", fontSize: 15 }}>{r.name || `${r.first_name || ""} ${r.last_name || ""}`.trim()}</div>
                                                    <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{r.email}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td style={{ padding: "16px" }}>
                                            <div style={{ color: "var(--text-secondary)", fontSize: 14, fontWeight: 500 }}>{r.designation || r.role || "Recruiter"}</div>
                                            <div style={{ color: "var(--text-muted)", fontSize: 12 }}>{r.department || "HR"}</div>
                                        </td>
                                        <td style={{ padding: "16px", minWidth: 200 }}>
                                            <div style={{ display: "flex", gap: "12px", marginBottom: "6px" }}>
                                                <div style={{ flex: 1 }}>
                                                    <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase" }}>Added</div>
                                                    <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text)" }}>{r.performance?.candidatesAdded || 0}</div>
                                                </div>
                                                <div style={{ flex: 1 }}>
                                                    <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase" }}>Conv. Rate</div>
                                                    <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text)" }}>{r.performance?.conversionRate || 0}%</div>
                                                </div>
                                                <div style={{ flex: 1 }}>
                                                    <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase" }}>Avg AI</div>
                                                    <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text)" }}>{r.performance?.averageAiScore || 0}</div>
                                                </div>
                                            </div>
                                            {/* Workload Progress Bar */}
                                            <div style={{ width: "100%", background: "var(--border)", height: 4, borderRadius: 2, marginTop: 4, overflow: "hidden" }}>
                                                <div style={{ width: `${Math.min(100, (r.performance?.candidatesAdded || 0) * 5)}%`, height: "100%", background: "var(--primary)" }} />
                                            </div>
                                        </td>
                                        <td style={{ padding: "16px" }}>
                                            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                                {r.is_online ? <FaCircle size={8} color="var(--success)" /> : <FaCircle size={8} color="var(--text-muted)" />}
                                                <StatusBadge status={r.status || "active"} />
                                            </div>
                                        </td>
                                        <td style={{ padding: "16px", color: "var(--text-secondary)", fontSize: 13 }}>
                                            {r.last_active ? new Date(r.last_active).toLocaleString() : (r.last_login ? new Date(r.last_login).toLocaleString() : "Never")}
                                        </td>
                                        <td style={{ padding: "16px", textAlign: "right" }}>
                                            <div style={{ display: "flex", gap: 6, justifyContent: "flex-end", flexWrap: "wrap" }}>
                                                <button onClick={() => handleOpenAssign(r)} style={{ background: "none", border: "none", color: "var(--primary)", cursor: "pointer", padding: 6 }} title="Assign Campaigns"><FaUserPlus /></button>
                                                <button onClick={() => handleResetPassword(r.id)} style={{ background: "none", border: "none", color: "var(--text-secondary)", cursor: "pointer", padding: 6 }} title="Reset Password"><FaKey /></button>
                                                <button onClick={() => handleForceReset(r.id)} style={{ background: "none", border: "none", color: "var(--warning, #f59e0b)", cursor: "pointer", padding: 6 }} title="Force Password Reset on Next Login"><FaRedo /></button>
                                                {r.status === "suspended" ? (
                                                    <button onClick={() => handleActivate(r.id)} style={{ background: "none", border: "none", color: "var(--success, #22c55e)", cursor: "pointer", padding: 6 }} title="Activate"><FaCheck /></button>
                                                ) : (
                                                    <button onClick={() => handleSuspend(r.id)} style={{ background: "none", border: "none", color: "var(--warning, #f59e0b)", cursor: "pointer", padding: 6 }} title="Suspend"><FaBan /></button>
                                                )}
                                                <button onClick={() => handleDelete(r.id)} style={{ background: "none", border: "none", color: "var(--danger)", cursor: "pointer", padding: 6 }} title="Remove"><FaTrash /></button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="team-grid">
                        {filtered.map((member, i) => {
                            const roleStyle = ROLE_COLORS[member.role] || ROLE_COLORS.Viewer;
                            return (
                                <motion.div
                                    key={member.id}
                                    className="team-member-card"
                                    custom={i}
                                    variants={cardVariants}
                                    initial="hidden"
                                    animate="visible"
                                >
                                    <div className="team-member-avatar">
                                        {(member.name || member.email || "?")[0].toUpperCase()}
                                        <div className={`team-member-status-dot ${member.status === "active" ? "active" : "inactive"}`} />
                                    </div>

                                    <div className="team-member-info">
                                        <h4>{member.name}</h4>
                                        <p>{member.designation}</p>
                                    </div>

                                    <span className="team-member-dept">{member.department}</span>

                                    <span
                                        className="team-member-role-badge"
                                        style={{ background: roleStyle.bg, color: roleStyle.color }}
                                    >
                                        {member.role}
                                    </span>

                                    <div className="team-member-contact">
                                        <div className="contact-row">
                                            <FaEnvelope size={10} />
                                            <span style={{ fontSize: "11px" }}>{member.email}</span>
                                        </div>
                                        <div className="contact-row">
                                            <FaPhone size={10} />
                                            <span style={{ fontSize: "11px" }}>{member.phone}</span>
                                        </div>
                                    </div>

                                    <div className="team-card-actions">
                                        {/* Pre-existing from Team.jsx: this button has never had a handler
                                            (no edit flow exists on either prior page). Carried over as-is --
                                            wiring a real edit flow is a new feature, outside this
                                            consolidation's scope. */}
                                        <Button variant="outline" size="sm" icon={<FaEdit />}>Edit</Button>
                                        <Button variant="ghost" size="sm" icon={<FaTrash />} onClick={() => handleDelete(member.id)}>Remove</Button>
                                    </div>
                                </motion.div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Create Modal */}
            <AnimatePresence>
                {isModalOpen && (
                    <div style={{
                        position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
                        background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000
                    }}>
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            style={{
                                background: "var(--card)", padding: 32, borderRadius: "var(--radius-lg)",
                                width: "100%", maxWidth: 500, border: "1px solid var(--border)", boxShadow: "0 20px 40px rgba(0,0,0,0.2)"
                            }}
                        >
                            <h2 style={{ marginBottom: 24, fontSize: 20, color: "var(--text)", fontWeight: 700 }}>Add Recruiter</h2>
                            <form onSubmit={handleCreate} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                                <input
                                    required
                                    placeholder="Full Name"
                                    value={formData.name}
                                    onChange={e => setFormData({...formData, name: e.target.value})}
                                    style={{ padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
                                />
                                <input
                                    required
                                    type="email"
                                    placeholder="Email Address"
                                    value={formData.email}
                                    onChange={e => setFormData({...formData, email: e.target.value})}
                                    style={{ padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
                                />
                                <input
                                    type="tel"
                                    placeholder="Phone Number (optional)"
                                    value={formData.phone}
                                    onChange={e => setFormData({...formData, phone: e.target.value})}
                                    style={{ padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
                                />
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                                    <input
                                        placeholder="Department (optional)"
                                        value={formData.department}
                                        onChange={e => setFormData({...formData, department: e.target.value})}
                                        style={{ padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
                                    />
                                    <input
                                        placeholder="Designation (optional)"
                                        value={formData.designation}
                                        onChange={e => setFormData({...formData, designation: e.target.value})}
                                        style={{ padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
                                    />
                                </div>
                                <select
                                    value={formData.role}
                                    onChange={e => setFormData({...formData, role: e.target.value})}
                                    style={{ padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
                                >
                                    <option value="Recruiter">Recruiter</option>
                                    <option value="Hiring Manager">Hiring Manager</option>
                                    <option value="Viewer">Viewer</option>
                                    <option value="Admin">Admin</option>
                                </select>
                                <div style={{ display: "flex", gap: 12, justifyContent: "flex-end", marginTop: 16 }}>
                                    <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                                    <Button type="submit" variant="primary">Create Recruiter</Button>
                                </div>
                            </form>
                        </motion.div>
                    </div>
                )}

                {credentialsModal && (
                    <div style={{
                        position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
                        background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1100
                    }}>
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            style={{
                                background: "var(--card)", padding: 40, borderRadius: "var(--radius-lg)", textAlign: "center",
                                width: "100%", maxWidth: 450, border: "1px solid var(--primary)", boxShadow: "0 20px 40px rgba(0,0,0,0.3)"
                            }}
                        >
                            <div style={{
                                width: 64, height: 64, borderRadius: "50%", background: "rgba(16, 185, 129, 0.1)",
                                color: "#10B981", display: "flex", alignItems: "center", justifyContent: "center",
                                fontSize: 32, margin: "0 auto 20px"
                            }}>
                                <FaKey />
                            </div>
                            <h2 style={{ marginBottom: 12, fontSize: 24, color: "var(--text)", fontWeight: 700 }}>Credentials Generated</h2>
                            <p style={{ color: "var(--text-secondary)", marginBottom: 24, fontSize: 14 }}>
                                Please copy these credentials now. For security reasons, the password will not be shown again. The recruiter will be required to change this password on their first login.
                            </p>

                            <div style={{
                                background: "var(--bg)", padding: 20, borderRadius: "var(--radius-md)",
                                border: "1px solid var(--border)", marginBottom: 24, textAlign: "left"
                            }}>
                                <div style={{ marginBottom: 12 }}>
                                    <label style={{ fontSize: 12, textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 600 }}>Username</label>
                                    <div style={{ fontSize: 16, color: "var(--text)", fontWeight: 500, fontFamily: "monospace" }}>{credentialsModal.username}</div>
                                </div>
                                <div>
                                    <label style={{ fontSize: 12, textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 600 }}>Temporary Password</label>
                                    <div style={{ fontSize: 16, color: "var(--text)", fontWeight: 500, fontFamily: "monospace" }}>{credentialsModal.password}</div>
                                </div>
                            </div>

                            <div style={{ display: "flex", gap: 12 }}>
                                <Button variant="outline" icon={<FaCopy />} onClick={copyCredentials} style={{ flex: 1 }}>Copy</Button>
                                <Button variant="primary" onClick={() => setCredentialsModal(null)} style={{ flex: 1 }}>Done</Button>
                            </div>
                        </motion.div>
                    </div>
                )}

                {assignModal && (
                    <div style={{
                        position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
                        background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000
                    }}>
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
                            style={{
                                background: "var(--card)", padding: 32, borderRadius: "var(--radius-lg)",
                                width: "100%", maxWidth: 500, border: "1px solid var(--border)", boxShadow: "0 20px 40px rgba(0,0,0,0.2)"
                            }}
                        >
                            <h2 style={{ marginBottom: 8, fontSize: 20, color: "var(--text)", fontWeight: 700 }}>Assign Campaigns</h2>
                            <p style={{ color: "var(--text-secondary)", marginBottom: 24, fontSize: 14 }}>
                                Select campaigns for {assignModal.name || `${assignModal.first_name || ""} ${assignModal.last_name || ""}`.trim()}. They will only have access to these selected campaigns.
                            </p>

                            <div style={{ maxHeight: 300, overflowY: "auto", marginBottom: 24, border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
                                {campaigns.map(c => (
                                    <div key={c._id} style={{
                                        display: "flex", alignItems: "center", gap: 12, padding: "12px 16px",
                                        borderBottom: "1px solid var(--border)", cursor: "pointer",
                                        background: selectedCampaigns.includes(c._id) ? "rgba(16, 185, 129, 0.05)" : "transparent"
                                    }} onClick={() => {
                                        if (selectedCampaigns.includes(c._id)) {
                                            setSelectedCampaigns(selectedCampaigns.filter(id => id !== c._id));
                                        } else {
                                            setSelectedCampaigns([...selectedCampaigns, c._id]);
                                        }
                                    }}>
                                        <input
                                            type="checkbox"
                                            checked={selectedCampaigns.includes(c._id)}
                                            onChange={() => {}}
                                            style={{ cursor: "pointer", width: 16, height: 16 }}
                                        />
                                        <div>
                                            <div style={{ fontWeight: 500, color: "var(--text)" }}>{c.name || c.title || "Untitled"}</div>
                                            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{c.department} &bull; {c.status}</div>
                                        </div>
                                    </div>
                                ))}
                                {campaigns.length === 0 && (
                                    <div style={{ padding: 20, textAlign: "center", color: "var(--text-muted)" }}>No campaigns available.</div>
                                )}
                            </div>

                            <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
                                <Button variant="outline" onClick={() => setAssignModal(null)}>Cancel</Button>
                                <Button variant="primary" onClick={handleSaveAssign}>Save Assignments</Button>
                            </div>
                        </motion.div>
                    </div>
                )}

                {/* Drawer */}
                <AnimatePresence>
                    {drawerOpen && selectedRecruiter && (
                        <>
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                onClick={() => setDrawerOpen(false)}
                                style={{
                                    position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
                                    background: "rgba(0,0,0,0.4)", zIndex: 1200
                                }}
                            />
                            <motion.div
                                initial={{ x: "100%" }}
                                animate={{ x: 0 }}
                                exit={{ x: "100%" }}
                                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                                style={{
                                    position: "fixed", top: 0, right: 0, bottom: 0, width: "100%", maxWidth: 500,
                                    background: "var(--card)", boxShadow: "-4px 0 24px rgba(0,0,0,0.1)", zIndex: 1201,
                                    display: "flex", flexDirection: "column", borderLeft: "1px solid var(--border)",
                                    overflowY: "auto"
                                }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '24px', borderBottom: '1px solid var(--border)', background: 'var(--bg)' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                                        <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, fontWeight: 700 }}>
                                            {(selectedRecruiter.name || selectedRecruiter.email || "?")[0].toUpperCase()}
                                        </div>
                                        <div>
                                            <h2 style={{ fontSize: 20, fontWeight: 700, margin: 0, color: 'var(--text)' }}>{selectedRecruiter.name || `${selectedRecruiter.first_name || ""} ${selectedRecruiter.last_name || ""}`.trim()}</h2>
                                            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{selectedRecruiter.designation || 'Recruiter'} • {selectedRecruiter.department || 'Talent Acquisition'}</div>
                                        </div>
                                    </div>
                                    <button onClick={() => setDrawerOpen(false)} style={{ background: 'none', border: 'none', fontSize: 20, color: 'var(--text-muted)', cursor: 'pointer' }}>
                                        <FaTimes />
                                    </button>
                                </div>

                                <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 24 }}>

                                    {/* Action bar */}
                                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                                        <Button variant="outline" size="sm" iconLeft={<FaChartBar />} onClick={() => handleOpenAssign(selectedRecruiter)}>Assign Campaigns</Button>
                                        <Button variant="outline" size="sm" iconLeft={<FaRedo />} onClick={() => handleForceReset(selectedRecruiter.id)}>Force Password Reset</Button>
                                        <Button variant="danger" size="sm" iconLeft={selectedRecruiter.status === 'suspended' ? <FaCheck /> : <FaBan />}
                                                onClick={() => selectedRecruiter.status === 'suspended' ? handleActivate(selectedRecruiter.id) : handleSuspend(selectedRecruiter.id)}>
                                            {selectedRecruiter.status === 'suspended' ? 'Activate' : 'Suspend'}
                                        </Button>
                                    </div>

                                    {/* Stats overview */}
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                                        <div style={{ background: 'var(--bg)', padding: 16, borderRadius: 'var(--radius-md)', textAlign: 'center', border: '1px solid var(--border)' }}>
                                            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--primary)', marginBottom: 4 }}>{selectedRecruiter.performance?.candidatesAdded || recruiterCandidates.length}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Candidates</div>
                                        </div>
                                        <div style={{ background: 'var(--bg)', padding: 16, borderRadius: 'var(--radius-md)', textAlign: 'center', border: '1px solid var(--border)' }}>
                                            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--primary)', marginBottom: 4 }}>{selectedRecruiter.performance?.interviewsConducted || recruiterInterviews.length}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Interviews</div>
                                        </div>
                                        <div style={{ background: 'var(--bg)', padding: 16, borderRadius: 'var(--radius-md)', textAlign: 'center', border: '1px solid var(--border)' }}>
                                            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--primary)', marginBottom: 4 }}>{selectedRecruiter.performance?.conversionRate || 0}%</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Conv. Rate</div>
                                        </div>
                                    </div>

                                    {/* Details */}
                                    <div>
                                        <h4 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text)', marginBottom: 12 }}>Contact Info</h4>
                                        <div style={{ fontSize: 14, color: 'var(--text-secondary)', display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
                                            <strong>Email:</strong> <span>{selectedRecruiter.email}</span>
                                            <strong>Phone:</strong> <span>{selectedRecruiter.phone || '—'}</span>
                                            <strong>Status:</strong> <span><StatusBadge status={selectedRecruiter.status} /></span>
                                        </div>
                                    </div>

                                    {/* Activity Timeline */}
                                    <div>
                                        <h4 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text)', marginBottom: 16 }}>Recent Activity</h4>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                            {recruiterActivity.length > 0 ? recruiterActivity.map((act, i) => (
                                                <div key={i} style={{ display: 'flex', gap: 16, position: 'relative' }}>
                                                    {i !== recruiterActivity.length - 1 && <div style={{ position: 'absolute', left: 19, top: 32, bottom: -16, width: 2, background: 'var(--border)' }} />}
                                                    <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1 }}>
                                                        <FaTasks />
                                                    </div>
                                                    <div style={{ paddingTop: 8 }}>
                                                        <div style={{ fontWeight: 600, color: 'var(--text)', fontSize: 14, marginBottom: 4 }}>
                                                            {act.action}
                                                        </div>
                                                        <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                                                            {act.target_entity} {act.target_name ? `(${act.target_name})` : ''}
                                                        </div>
                                                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                                                            {new Date(act.created_at).toLocaleString()}
                                                        </div>
                                                    </div>
                                                </div>
                                            )) : (
                                                <div style={{ fontSize: 13, color: 'var(--text-muted)', fontStyle: 'italic' }}>No recent activity.</div>
                                            )}
                                        </div>
                                    </div>

                                </div>
                            </motion.div>
                        </>
                    )}
                </AnimatePresence>

            </AnimatePresence>
        </div>
    );
}

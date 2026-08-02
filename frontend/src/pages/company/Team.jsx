import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    FaUsers, FaThLarge, FaList, FaSearch, FaPlus,
    FaEnvelope, FaPhone, FaEdit, FaTrash, FaUserPlus,
    FaTimes, FaCheck, FaSpinner
} from "react-icons/fa";

import PageHeader from "../../components/common/PageHeader";
import Button from "../../components/common/Button";
import StatusBadge from "../../components/common/StatusBadge";
import StatsCard from "../../components/common/StatsCard";
import Toast from "../../components/common/Toast";
import teamService from "../../services/company/teamService";

import "../../styles/company/Team.css";

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

export default function Team() {
    const [view, setView] = useState("grid");
    const [search, setSearch] = useState("");
    const [roleFilter, setRoleFilter] = useState("All");
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [inviteForm, setInviteForm] = useState({ name: "", email: "", role: "Recruiter" });
    const [invited, setInvited] = useState(false);
    const [inviting, setInviting] = useState(false);
    const [toast, setToast] = useState(null);
    const [teamMembers, setTeamMembers] = useState([]);
    const [loading, setLoading] = useState(true);

    const showToast = (message, type = "success") => setToast({ message, type });

    const fetchTeam = async () => {
        try {
            setLoading(true);
            const res = await teamService.getTeamMembers(
                search,
                roleFilter === "All" ? "" : roleFilter
            );
            setTeamMembers(res.data || []);
        } catch (err) {
            console.error("Failed to load team:", err);
            showToast("Failed to load team members", "error");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTeam();
    }, [search, roleFilter]);

    // Derive stats from live data
    const filtered = teamMembers; // already filtered by backend
    const totalActive = teamMembers.filter(m => m.status === "Active").length;
    const totalRecruiters = teamMembers.filter(m => m.role === "Recruiter").length;
    const totalManagers = teamMembers.filter(m => m.role === "Hiring Manager").length;
    const totalAdmins = teamMembers.filter(m => m.role === "Admin").length;

    const handleInvite = async () => {
        if (!inviteForm.name || !inviteForm.email) {
            showToast("Name and email are required", "error");
            return;
        }
        try {
            setInviting(true);
            await teamService.inviteMember(inviteForm);
            setInvited(true);
            showToast(`Invitation sent to ${inviteForm.email}`, "success");
            fetchTeam();
            setTimeout(() => {
                setInvited(false);
                setShowInviteModal(false);
                setInviteForm({ name: "", email: "", role: "Recruiter" });
            }, 1500);
        } catch (err) {
            console.error("Invite failed:", err);
            showToast(err?.response?.data?.detail || "Failed to send invite", "error");
        } finally {
            setInviting(false);
        }
    };

    const handleRemove = async (memberId) => {
        try {
            await teamService.removeMember(memberId);
            showToast("Team member removed", "success");
            fetchTeam();
        } catch (err) {
            console.error("Remove failed:", err);
            showToast("Failed to remove team member", "error");
        }
    };

    return (
        <div className="team-page">
            {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
            <PageHeader
                title="Team"
                subtitle="Manage recruitment team and roles."
                icon={<FaUsers />}
                actions={
                    <Button variant="primary" icon={<FaUserPlus />} size="sm" onClick={() => setShowInviteModal(true)}>
                        Invite Member
                    </Button>
                }
            />

            {/* Stats */}
            <div className="team-stats-row">
                {[
                    { title: "Total Members", value: teamMembers.length, icon: <FaUsers />, iconColor: "#3B82F6" },
                    { title: "Active", value: totalActive, icon: <FaCheck />, iconColor: "#10B981" },
                    { title: "Recruiters", value: totalRecruiters, icon: <FaUsers />, iconColor: "#8B5CF6" },
                    { title: "Hiring Managers", value: totalManagers, icon: <FaUsers />, iconColor: "#F59E0B" },
                    { title: "Admins", value: totalAdmins, icon: <FaUsers />, iconColor: "#EC4899" },
                ].map((s, i) => (
                    <motion.div key={s.title} custom={i} variants={cardVariants} initial="hidden" animate="visible">
                        <StatsCard {...s} />
                    </motion.div>
                ))}
            </div>

            {/* Toolbar */}
            <div className="team-toolbar">
                <div className="team-toolbar-left">
                    <div className="team-search-wrap">
                        <FaSearch className="team-search-icon" />
                        <input
                            type="text"
                            className="team-search-input"
                            placeholder="Search members..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                        />
                    </div>
                    <select
                        className="team-role-filter"
                        value={roleFilter}
                        onChange={e => setRoleFilter(e.target.value)}
                    >
                        <option value="All">All Roles</option>
                        <option value="Admin">Admin</option>
                        <option value="Recruiter">Recruiter</option>
                        <option value="Hiring Manager">Hiring Manager</option>
                        <option value="Viewer">Viewer</option>
                    </select>
                </div>
                <div className="team-toolbar-right">
                    <div className="team-view-toggle">
                        <button
                            className={`view-toggle-btn ${view === "grid" ? "active" : ""}`}
                            onClick={() => setView("grid")}
                            title="Grid view"
                        >
                            <FaThLarge />
                        </button>
                        <button
                            className={`view-toggle-btn ${view === "list" ? "active" : ""}`}
                            onClick={() => setView("list")}
                            title="List view"
                        >
                            <FaList />
                        </button>
                    </div>
                </div>
            </div>

            {/* Grid View */}
            <AnimatePresence mode="wait">
                {view === "grid" && (
                    <motion.div
                        key="grid"
                        className="team-grid"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
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
                                        {member.avatar}
                                        <div className={`team-member-status-dot ${member.status === "Active" ? "active" : "inactive"}`} />
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
                                        <Button variant="outline" size="sm" icon={<FaEdit />}>Edit</Button>
                                        <Button variant="ghost" size="sm" icon={<FaTrash />} onClick={() => handleRemove(member.id)}>Remove</Button>
                                    </div>
                                </motion.div>
                            );
                        })}
                    </motion.div>
                )}

                {/* List View */}
                {view === "list" && (
                    <motion.div
                        key="list"
                        className="team-list-table-wrap"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <table className="team-list-table">
                            <thead>
                                <tr>
                                    <th>Member</th>
                                    <th>Department</th>
                                    <th>Role</th>
                                    <th>Email</th>
                                    <th>Phone</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map((member, i) => {
                                    const roleStyle = ROLE_COLORS[member.role] || ROLE_COLORS.Viewer;
                                    return (
                                        <motion.tr
                                            key={member.id}
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ delay: i * 0.05 }}
                                        >
                                            <td>
                                                <div className="tl-member-cell">
                                                    <div className="tl-avatar">{member.name ? member.name.split(" ").map(n => n[0]).join("").slice(0, 2) : "?"}</div>
                                                    <div className="tl-info">
                                                        <strong>{member.name}</strong>
                                                        <span>{member.designation}</span>
                                                    </div>
                                                </div>
                                            </td>
                                            <td style={{ color: "var(--text-secondary)", fontSize: 12 }}>{member.department}</td>
                                            <td>
                                                <span
                                                    style={{
                                                        ...roleStyle, fontSize: "11px", fontWeight: 600,
                                                        padding: "3px 10px", borderRadius: "999px"
                                                    }}
                                                >
                                                    {member.role}
                                                </span>
                                            </td>
                                            <td style={{ fontSize: 12, color: "var(--text-secondary)" }}>{member.email}</td>
                                            <td style={{ fontSize: 12, color: "var(--text-secondary)" }}>{member.phone}</td>
                                            <td>
                                                <StatusBadge status={member.status} />
                                            </td>
                                            <td>
                                                <div className="tl-actions">
                                                    <button className="tl-icon-btn" title="Edit"><FaEdit /></button>
                                                    <button className="tl-icon-btn" title="Message"><FaEnvelope /></button>
                                                    <button className="tl-icon-btn" title="Remove" onClick={() => handleRemove(member.id)}><FaTrash /></button>
                                                </div>
                                            </td>
                                        </motion.tr>
                                    );
                                })}
                            </tbody>
                        </table>
                        {filtered.length === 0 && (
                            <div style={{ textAlign: "center", padding: 40, color: "var(--text-secondary)" }}>
                                No team members found.
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Invite Modal */}
            <AnimatePresence>
                {showInviteModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        style={{
                            position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
                            zIndex: 9999, display: "flex", alignItems: "center", justifyContent: "center"
                        }}
                        onClick={() => setShowInviteModal(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0, y: 30 }}
                            animate={{ scale: 1, opacity: 1, y: 0 }}
                            exit={{ scale: 0.9, opacity: 0, y: 30 }}
                            transition={{ type: "spring", damping: 20 }}
                            onClick={e => e.stopPropagation()}
                            style={{
                                background: "var(--card)", border: "1px solid var(--border)",
                                borderRadius: "var(--radius-lg)", padding: "32px", width: "100%",
                                maxWidth: 440, boxShadow: "0 25px 80px rgba(0,0,0,0.5)"
                            }}
                        >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                                <div>
                                    <h3 style={{ color: "var(--text)", fontWeight: 700, fontSize: 18 }}>Invite Team Member</h3>
                                    <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>
                                        Send an invitation email to a new member.
                                    </p>
                                </div>
                                <button onClick={() => setShowInviteModal(false)} style={{
                                    background: "transparent", border: "none", color: "var(--text-secondary)",
                                    cursor: "pointer", fontSize: 18
                                }}>
                                    <FaTimes />
                                </button>
                            </div>

                            <div className="team-invite-form">
                                <div className="team-invite-form-group">
                                    <label>Full Name</label>
                                    <input
                                        type="text"
                                        placeholder="e.g. John Smith"
                                        value={inviteForm.name}
                                        onChange={e => setInviteForm(f => ({ ...f, name: e.target.value }))}
                                    />
                                </div>
                                <div className="team-invite-form-group">
                                    <label>Work Email</label>
                                    <input
                                        type="email"
                                        placeholder="e.g. john@company.ai"
                                        value={inviteForm.email}
                                        onChange={e => setInviteForm(f => ({ ...f, email: e.target.value }))}
                                    />
                                </div>
                                <div className="team-invite-form-group">
                                    <label>Role</label>
                                    <select value={inviteForm.role} onChange={e => setInviteForm(f => ({ ...f, role: e.target.value }))}>
                                        <option value="Recruiter">Recruiter</option>
                                        <option value="Hiring Manager">Hiring Manager</option>
                                        <option value="Viewer">Viewer</option>
                                        <option value="Admin">Admin</option>
                                    </select>
                                </div>

                                <div style={{ display: "flex", gap: 10, marginTop: 16, justifyContent: "flex-end" }}>
                                    <Button variant="outline" onClick={() => setShowInviteModal(false)}>Cancel</Button>
                                    <Button
                                        variant="primary"
                                        icon={invited ? <FaCheck /> : inviting ? <FaSpinner /> : <FaUserPlus />}
                                        onClick={handleInvite}
                                        disabled={inviting}
                                    >
                                        {invited ? "Invitation Sent!" : inviting ? "Sending..." : "Send Invite"}
                                    </Button>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

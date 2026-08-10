import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
    FaUser, FaEdit, FaEnvelope, FaPhone, FaMapMarkerAlt,
    FaLinkedin, FaBriefcase, FaSave, FaCamera, FaShieldAlt, FaCalendarAlt,
    FaSpinner
} from "react-icons/fa";

import { useAuthContext } from "../../context/AuthContext";
import PageHeader from "../../components/common/PageHeader";
import Button from "../../components/common/Button";
import profileService from "../../services/company/profileService";
import recruiterService from "../../services/recruiter/recruiterService";

import "../../styles/company/Profile.css";


const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: (i) => ({ opacity: 1, y: 0, transition: { delay: i * 0.1 } })
};

function Toast({ message, type = "success" }) {
    if (!message) return null;
    return (
        <div style={{
            position: "fixed", top: 20, right: 20, zIndex: 9999,
            background: type === "error" ? "var(--danger, #ef4444)" : "var(--success, #22c55e)",
            color: "#fff", padding: "10px 20px", borderRadius: 8,
            fontSize: 14, fontWeight: 600, boxShadow: "0 4px 20px rgba(0,0,0,0.3)"
        }}>
            {message}
        </div>
    );
}

export default function Profile() {
    const { user, setCompanyProfile, isRecruiter, recruiterProfile, setRecruiterProfile } = useAuthContext();

    // ── Recruiter profile view ────────────────────────────────────────────────
    if (isRecruiter) {
        return <RecruiterProfileView user={user} recruiterProfile={recruiterProfile} setRecruiterProfile={setRecruiterProfile} />;
    }

    // ── Company Admin profile view (existing) ─────────────────────────────────

    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [savingPwd, setSavingPwd] = useState(false);
    const [toast, setToast] = useState({ message: "", type: "success" });

    // Controlled form fields
    const [formData, setFormData] = useState({
        company_name: "",
        contact_person: "",
        phone: "",
        industry: "",
        website: "",
    });

    const [pwdData, setPwdData] = useState({
        current_password: "",
        new_password: "",
        confirm_password: "",
    });

    const showToast = (message, type = "success") => {
        setToast({ message, type });
        setTimeout(() => setToast({ message: "", type: "success" }), 3000);
    };

    // Load profile from backend
    useEffect(() => {
        setLoading(true);
        profileService.getProfile()
            .then(data => {
                setProfile(data);
                setFormData({
                    company_name: data.company_name || "",
                    contact_person: data.contact_person || "",
                    phone: data.phone || "",
                    industry: data.industry || "",
                    website: data.website || "",
                });
            })
            .catch(() => {
                // Fallback: use JWT-decoded user data
                if (user) {
                    setFormData(prev => ({
                        ...prev,
                        company_name: user.name || "",
                    }));
                    setProfile({ company_name: user.name, contact_email: user.email });
                }
            })
            .finally(() => setLoading(false));
    }, []);

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const updated = await profileService.updateProfile({
                company_name: formData.company_name || undefined,
                contact_person: formData.contact_person || undefined,
                phone: formData.phone || undefined,
                industry: formData.industry || undefined,
                website: formData.website || undefined,
            });
            setProfile(updated);
            if (setCompanyProfile) setCompanyProfile(updated);
            showToast("Profile saved successfully!");
        } catch (err) {
            showToast(err?.response?.data?.detail || "Failed to save profile.", "error");
        } finally {
            setSaving(false);
        }
    };

    const handlePasswordChange = async () => {
        if (pwdData.new_password !== pwdData.confirm_password) {
            showToast("New passwords do not match.", "error");
            return;
        }
        setSavingPwd(true);
        try {
            await profileService.changePassword(pwdData);
            showToast("Password updated successfully!");
            setPwdData({ current_password: "", new_password: "", confirm_password: "" });
        } catch (err) {
            showToast(err?.response?.data?.detail || "Failed to update password.", "error");
        } finally {
            setSavingPwd(false);
        }
    };

    // Derived display values
    const displayName = profile?.company_name || user?.name || "Company";
    const displayEmail = profile?.contact_email || user?.email || "";
    const initials = displayName.split(" ").filter(Boolean).map(n => n[0]).join("").slice(0, 2).toUpperCase();

    return (
        <div className="profile-page">
            <Toast message={toast.message} type={toast.type} />

            <PageHeader
                title="My Profile"
                subtitle="Manage your personal profile and activity."
                icon={<FaUser />}
                actions={
                    <Button
                        variant="primary"
                        icon={saving ? <FaSpinner className="spin" /> : <FaSave />}
                        size="sm"
                        onClick={handleSave}
                        disabled={saving || loading}
                    >
                        {saving ? "Saving…" : "Save Changes"}
                    </Button>
                }
            />

            {loading ? (
                <div style={{ display: "flex", justifyContent: "center", padding: "60px 0" }}>
                    <FaSpinner style={{ fontSize: 32, animation: "spin 1s linear infinite", color: "var(--accent)" }} />
                </div>
            ) : (
                <div className="profile-body">
                    {/* Left: Profile Card */}
                    <motion.div
                        className="profile-card"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <div className="profile-cover-bar" />

                        <div className="profile-avatar-wrap">
                            <div className="profile-avatar">{initials}</div>
                            <div className="profile-avatar-edit" title="Change photo">
                                <FaCamera />
                            </div>
                        </div>

                        <div className="profile-name">{displayName}</div>
                        <div className="profile-title">{profile?.industry || formData.industry || "—"}</div>
                        <div className="profile-dept-badge">{profile?.status || "Active"}</div>

                        <div className="profile-contact-list">
                            <div className="profile-contact-item">
                                <FaUser />
                                <span>{formData.contact_person || "—"}</span>
                            </div>
                            <div className="profile-contact-item">
                                <FaEnvelope />
                                <span>{displayEmail}</span>
                            </div>
                            <div className="profile-contact-item">
                                <FaPhone />
                                <span>{formData.phone || "—"}</span>
                            </div>
                            <div className="profile-contact-item">
                                <FaMapMarkerAlt />
                                <span>{formData.website || "—"}</span>
                            </div>
                        </div>
                    </motion.div>

                    {/* Right: Edit Panels */}
                    <div className="profile-edit-panels">
                        {/* Personal Info */}
                        <motion.div className="edit-panel" custom={0} variants={cardVariants} initial="hidden" animate="visible">
                            <div className="edit-panel-header">
                                <h4>Company Information</h4>
                                <FaEdit style={{ color: "var(--text-secondary)", fontSize: 14 }} />
                            </div>
                            <div className="edit-panel-body">
                                <div className="form-grid-2">
                                    <div className="form-field">
                                        <label>Company Name</label>
                                        <input
                                            type="text"
                                            value={formData.company_name}
                                            onChange={e => handleChange("company_name", e.target.value)}
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>Contact Person</label>
                                        <input
                                            type="text"
                                            value={formData.contact_person}
                                            onChange={e => handleChange("contact_person", e.target.value)}
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>Contact Email</label>
                                        <input type="email" value={displayEmail} disabled style={{ opacity: 0.6 }} />
                                    </div>
                                    <div className="form-field">
                                        <label>Phone</label>
                                        <input
                                            type="text"
                                            value={formData.phone}
                                            onChange={e => handleChange("phone", e.target.value)}
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>Industry</label>
                                        <input
                                            type="text"
                                            value={formData.industry}
                                            onChange={e => handleChange("industry", e.target.value)}
                                            placeholder="e.g. Technology"
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>Website</label>
                                        <input
                                            type="text"
                                            value={formData.website}
                                            onChange={e => handleChange("website", e.target.value)}
                                            placeholder="e.g. https://example.com"
                                        />
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        {/* Security */}
                        <motion.div className="edit-panel" custom={2} variants={cardVariants} initial="hidden" animate="visible">
                            <div className="edit-panel-header">
                                <h4>Security &amp; Password</h4>
                                <FaShieldAlt style={{ color: "var(--text-secondary)", fontSize: 14 }} />
                            </div>
                            <div className="edit-panel-body">
                                <div className="form-grid-2">
                                    <div className="form-field">
                                        <label>Current Password</label>
                                        <input
                                            type="password"
                                            placeholder="••••••••"
                                            value={pwdData.current_password}
                                            onChange={e => setPwdData(p => ({ ...p, current_password: e.target.value }))}
                                        />
                                    </div>
                                    <div className="form-field" />
                                    <div className="form-field">
                                        <label>New Password</label>
                                        <input
                                            type="password"
                                            placeholder="••••••••"
                                            value={pwdData.new_password}
                                            onChange={e => setPwdData(p => ({ ...p, new_password: e.target.value }))}
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>Confirm New Password</label>
                                        <input
                                            type="password"
                                            placeholder="••••••••"
                                            value={pwdData.confirm_password}
                                            onChange={e => setPwdData(p => ({ ...p, confirm_password: e.target.value }))}
                                        />
                                    </div>
                                </div>
                                <div>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={handlePasswordChange}
                                        disabled={savingPwd}
                                        icon={savingPwd ? <FaSpinner className="spin" /> : null}
                                    >
                                        {savingPwd ? "Updating…" : "Update Password"}
                                    </Button>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            )}
        </div>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// Recruiter Profile View — rendered when isRecruiter === true
// ─────────────────────────────────────────────────────────────────────────────
function RecruiterProfileView({ user, recruiterProfile, setRecruiterProfile }) {
    const [formData, setFormData] = useState({
        first_name: "",
        last_name: "",
        phone: "",
        designation: "",
        department: "",
        employee_id: "",
        timezone: "",
        language: "",
        bio: "",
        skills: "",
    });
    const [editing, setEditing] = useState(false);
    const [saving, setSaving] = useState(false);
    const [toast, setToast] = useState({ message: "", type: "success" });

    useEffect(() => {
        if (recruiterProfile) {
            let parsedSkills = recruiterProfile.skills;
            if (Array.isArray(parsedSkills)) parsedSkills = parsedSkills.join(", ");
            else if (!parsedSkills) parsedSkills = "";
            
            setFormData({
                first_name: recruiterProfile.first_name || recruiterProfile.name?.split(' ')[0] || "",
                last_name: recruiterProfile.last_name || recruiterProfile.name?.split(' ').slice(1).join(' ') || "",
                phone: recruiterProfile.phone || "",
                designation: recruiterProfile.designation || "",
                department: recruiterProfile.department || "",
                employee_id: recruiterProfile.employee_id || "",
                timezone: recruiterProfile.timezone || "",
                language: recruiterProfile.language || "",
                bio: recruiterProfile.bio || "",
                skills: parsedSkills,
            });
        }
    }, [recruiterProfile]);

    const handleSave = async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
            const submitData = { 
                ...formData, 
                name: `${formData.first_name} ${formData.last_name}`.trim(),
                skills: formData.skills.split(',').map(s => s.trim()).filter(Boolean)
            };
            const res = await recruiterService.updateProfile(submitData);
            setRecruiterProfile(res.data?.data || res.data || formData);
            setEditing(false);
            setToast({ message: "Profile updated successfully!", type: "success" });
        } catch {
            setToast({ message: "Failed to update profile.", type: "error" });
        } finally {
            setSaving(false);
            setTimeout(() => setToast({ message: "" }), 3000);
        }
    };

    const initials = `${formData.first_name?.[0] || ""}${formData.last_name?.[0] || ""}`.toUpperCase() || "R";

    return (
        <div className="profile-page">
            <Toast message={toast.message} type={toast.type} />
            <PageHeader
                title="My Profile"
                subtitle="Manage your recruiter profile"
                breadcrumbs={[{ label: "Profile" }]}
                actions={
                    !editing ? (
                        <Button variant="outline" iconLeft={<FaEdit />} onClick={() => setEditing(true)}>
                            Edit Profile
                        </Button>
                    ) : null
                }
            />
            <div className="profile-grid">
                {/* Avatar card */}
                <motion.div
                    className="profile-avatar-card"
                    variants={cardVariants}
                    custom={0}
                    initial="hidden"
                    animate="visible"
                >
                    <div className="profile-avatar-large">{initials}</div>
                    <h3>{formData.first_name} {formData.last_name}</h3>
                    <span style={{ color: "var(--text-muted)", fontSize: 14 }}>{formData.designation}</span>
                    <span style={{ display: "block", color: "var(--primary)", fontSize: 13, marginTop: 4 }}>
                        {formData.department}
                    </span>
                    <span style={{ display: "block", color: "var(--text-muted)", fontSize: 12, marginTop: 6 }}>
                        {user?.email}
                    </span>
                </motion.div>

                {/* Edit form */}
                <motion.div
                    className="profile-form-card"
                    variants={cardVariants}
                    custom={1}
                    initial="hidden"
                    animate="visible"
                >
                    <h4><FaUser style={{ marginRight: 8 }} />Personal Information</h4>
                    <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 16 }}>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                            <div>
                                <label style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6, display: "block" }}>First Name</label>
                                <input
                                    value={formData.first_name}
                                    onChange={e => setFormData({ ...formData, first_name: e.target.value })}
                                    disabled={!editing}
                                    style={{ width: "100%", padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", boxSizing: "border-box" }}
                                />
                            </div>
                            <div>
                                <label style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6, display: "block" }}>Last Name</label>
                                <input
                                    value={formData.last_name}
                                    onChange={e => setFormData({ ...formData, last_name: e.target.value })}
                                    disabled={!editing}
                                    style={{ width: "100%", padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", boxSizing: "border-box" }}
                                />
                            </div>
                        </div>
                        <div>
                            <label style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6, display: "block" }}>Phone</label>
                            <input
                                value={formData.phone}
                                onChange={e => setFormData({ ...formData, phone: e.target.value })}
                                disabled={!editing}
                                style={{ width: "100%", padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", boxSizing: "border-box" }}
                            />
                        </div>
                        <div>
                            <label style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6, display: "block" }}>Designation</label>
                            <input
                                value={formData.designation}
                                onChange={e => setFormData({ ...formData, designation: e.target.value })}
                                disabled={!editing}
                                style={{ width: "100%", padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", boxSizing: "border-box" }}
                            />
                        </div>
                        <div>
                            <label style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6, display: "block" }}>Department</label>
                            <input
                                value={formData.department}
                                onChange={e => setFormData({ ...formData, department: e.target.value })}
                                disabled={!editing}
                                style={{ width: "100%", padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", boxSizing: "border-box" }}
                            />
                        </div>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                            <div>
                                <label style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6, display: "block" }}>Timezone</label>
                                <input
                                    value={formData.timezone}
                                    onChange={e => setFormData({ ...formData, timezone: e.target.value })}
                                    disabled={!editing}
                                    placeholder="e.g. UTC, PST, IST"
                                    style={{ width: "100%", padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", boxSizing: "border-box" }}
                                />
                            </div>
                            <div>
                                <label style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6, display: "block" }}>Language</label>
                                <input
                                    value={formData.language}
                                    onChange={e => setFormData({ ...formData, language: e.target.value })}
                                    disabled={!editing}
                                    placeholder="e.g. English"
                                    style={{ width: "100%", padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", boxSizing: "border-box" }}
                                />
                            </div>
                        </div>
                        <div>
                            <label style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6, display: "block" }}>Skills (comma separated)</label>
                            <input
                                value={formData.skills}
                                onChange={e => setFormData({ ...formData, skills: e.target.value })}
                                disabled={!editing}
                                placeholder="e.g. Technical Recruiting, Sourcing, JavaScript"
                                style={{ width: "100%", padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", boxSizing: "border-box" }}
                            />
                        </div>
                        <div>
                            <label style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6, display: "block" }}>Bio / Signature</label>
                            <textarea
                                value={formData.bio}
                                onChange={e => setFormData({ ...formData, bio: e.target.value })}
                                disabled={!editing}
                                rows={3}
                                placeholder="Tell candidates about yourself..."
                                style={{ width: "100%", padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", boxSizing: "border-box", resize: "vertical" }}
                            />
                        </div>
                        {editing && (
                            <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
                                <Button type="button" variant="outline" onClick={() => setEditing(false)}>Cancel</Button>
                                <Button type="submit" variant="primary" disabled={saving}>
                                    {saving ? "Saving..." : "Save Changes"}
                                </Button>
                            </div>
                        )}
                    </form>
                </motion.div>
            </div>
        </div>
    );
}
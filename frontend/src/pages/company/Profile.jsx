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

import "../../styles/company/Profile.css";

const SKILLS = [
    "Talent Acquisition", "AI Sourcing", "Pipeline Management",
    "Behavioral Interviews", "Employer Branding", "Technical Recruiting",
    "Diversity & Inclusion", "ATS Optimization"
];

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
    const { user } = useAuthContext();

    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [savingPwd, setSavingPwd] = useState(false);
    const [toast, setToast] = useState({ message: "", type: "success" });

    // Controlled form fields
    const [formData, setFormData] = useState({
        firstName: "",
        lastName: "",
        phone: "",
        location: "",
        linkedin: "",
        bio: "",
        title: "",
        department: "",
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
                const nameParts = (data.name || "").split(" ");
                setFormData({
                    firstName: nameParts[0] || "",
                    lastName: nameParts.slice(1).join(" ") || "",
                    phone: data.phone || "",
                    location: data.location || "",
                    linkedin: data.linkedin || "",
                    bio: data.bio || "",
                    title: data.title || "",
                    department: data.department || "",
                });
            })
            .catch(() => {
                // Fallback: use JWT-decoded user data
                if (user) {
                    const nameParts = (user.name || "").split(" ");
                    setFormData(prev => ({
                        ...prev,
                        firstName: nameParts[0] || "",
                        lastName: nameParts.slice(1).join(" ") || "",
                    }));
                    setProfile({ name: user.name, email: user.email });
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
            const fullName = [formData.firstName, formData.lastName].filter(Boolean).join(" ");
            const updated = await profileService.updateProfile({
                name: fullName || undefined,
                phone: formData.phone || undefined,
                location: formData.location || undefined,
                linkedin: formData.linkedin || undefined,
                bio: formData.bio || undefined,
                title: formData.title || undefined,
                department: formData.department || undefined,
            });
            setProfile(updated);
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
    const displayName = profile?.name || user?.name || "User";
    const displayEmail = profile?.email || user?.email || "";
    const initials = displayName.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase();

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
                        <div className="profile-title">{profile?.title || formData.title || "—"}</div>
                        <div className="profile-dept-badge">{profile?.department || formData.department || "—"}</div>

                        <div className="profile-contact-list">
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
                                <span>{formData.location || "—"}</span>
                            </div>
                            <div className="profile-contact-item">
                                <FaLinkedin />
                                <span>{formData.linkedin || "—"}</span>
                            </div>
                            {profile?.joined_date && (
                                <div className="profile-contact-item">
                                    <FaCalendarAlt />
                                    <span>Joined {profile.joined_date}</span>
                                </div>
                            )}
                        </div>
                    </motion.div>

                    {/* Right: Edit Panels */}
                    <div className="profile-edit-panels">
                        {/* Personal Info */}
                        <motion.div className="edit-panel" custom={0} variants={cardVariants} initial="hidden" animate="visible">
                            <div className="edit-panel-header">
                                <h4>Personal Information</h4>
                                <FaEdit style={{ color: "var(--text-secondary)", fontSize: 14 }} />
                            </div>
                            <div className="edit-panel-body">
                                <div className="form-grid-2">
                                    <div className="form-field">
                                        <label>First Name</label>
                                        <input
                                            type="text"
                                            value={formData.firstName}
                                            onChange={e => handleChange("firstName", e.target.value)}
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>Last Name</label>
                                        <input
                                            type="text"
                                            value={formData.lastName}
                                            onChange={e => handleChange("lastName", e.target.value)}
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>Email</label>
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
                                        <label>Job Title</label>
                                        <input
                                            type="text"
                                            value={formData.title}
                                            onChange={e => handleChange("title", e.target.value)}
                                            placeholder="e.g. Director of Talent Acquisition"
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>Department</label>
                                        <input
                                            type="text"
                                            value={formData.department}
                                            onChange={e => handleChange("department", e.target.value)}
                                            placeholder="e.g. Human Resources"
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>Location</label>
                                        <input
                                            type="text"
                                            value={formData.location}
                                            onChange={e => handleChange("location", e.target.value)}
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>LinkedIn</label>
                                        <input
                                            type="text"
                                            value={formData.linkedin}
                                            onChange={e => handleChange("linkedin", e.target.value)}
                                        />
                                    </div>
                                    <div className="form-field full-width">
                                        <label>Bio</label>
                                        <textarea
                                            value={formData.bio}
                                            onChange={e => handleChange("bio", e.target.value)}
                                            rows={4}
                                        />
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        {/* Professional Skills */}
                        <motion.div className="edit-panel" custom={1} variants={cardVariants} initial="hidden" animate="visible">
                            <div className="edit-panel-header">
                                <h4>Professional Skills</h4>
                            </div>
                            <div className="edit-panel-body">
                                <div className="skills-tag-list">
                                    {SKILLS.map(skill => (
                                        <span key={skill} className="skill-tag">{skill}</span>
                                    ))}
                                    <span className="skill-tag" style={{ borderStyle: "dashed", opacity: 0.6 }}>+ Add Skill</span>
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
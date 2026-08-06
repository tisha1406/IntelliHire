import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FaUserPlus, FaEdit, FaTrash, FaKey, FaCopy, FaSearch, FaUserTie } from "react-icons/fa";
import recruiterManagementService from "../../services/company/recruiterManagementService";
import Button from "../../components/common/Button";
import StatusBadge from "../../components/common/StatusBadge";
import Toast from "../../components/common/Toast";

export default function Recruiters() {
    const [recruiters, setRecruiters] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [credentialsModal, setCredentialsModal] = useState(null);
    const [toast, setToast] = useState(null);
    const [formData, setFormData] = useState({
        first_name: "", last_name: "", email: "", phone: "", department: "", designation: "", status: "active"
    });

    const loadRecruiters = async () => {
        try {
            setLoading(true);
            const res = await recruiterManagementService.getRecruiters();
            setRecruiters(res.data?.data || res.data || []);
        } catch (err) {
            console.error(err);
            showToast("Failed to load recruiters", "error");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadRecruiters();
    }, []);

    const showToast = (msg, type = "success") => {
        setToast({ message: msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            const res = await recruiterManagementService.createRecruiter(formData);
            const data = res.data?.data || res.data;
            setIsModalOpen(false);
            setCredentialsModal({
                username: data.username,
                password: data.temporary_password
            });
            loadRecruiters();
            showToast("Recruiter created successfully", "success");
            setFormData({ first_name: "", last_name: "", email: "", phone: "", department: "", designation: "", status: "active" });
        } catch (err) {
            console.error(err);
            showToast(err.response?.data?.detail || "Failed to create recruiter", "error");
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to delete this recruiter?")) return;
        try {
            await recruiterManagementService.deleteRecruiter(id);
            showToast("Recruiter deleted", "success");
            loadRecruiters();
        } catch (err) {
            console.error(err);
            showToast("Failed to delete recruiter", "error");
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

    const filtered = recruiters.filter(r => 
        r.first_name.toLowerCase().includes(searchTerm.toLowerCase()) || 
        r.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.email.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: 24, animation: "fadeInPage 0.4s ease-out" }}>
            {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                    <h1 style={{ fontSize: 28, fontWeight: 700, color: "var(--text)", marginBottom: 8 }}>Recruiters</h1>
                    <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>Manage your recruitment team</p>
                </div>
                <Button variant="primary" icon={<FaUserPlus />} onClick={() => setIsModalOpen(true)}>Add Recruiter</Button>
            </div>

            <div style={{ 
                background: "var(--card)", padding: 20, borderRadius: "var(--radius-lg)", 
                border: "1px solid var(--border)", boxShadow: "var(--shadow)" 
            }}>
                <div style={{ marginBottom: 20, display: "flex", gap: 16 }}>
                    <div style={{ position: "relative", flex: 1, maxWidth: 300 }}>
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
                </div>

                {loading ? (
                    <div style={{ textAlign: "center", padding: 40, color: "var(--text-secondary)" }}>Loading recruiters...</div>
                ) : filtered.length === 0 ? (
                    <div style={{ textAlign: "center", padding: 60, color: "var(--text-muted)" }}>
                        <FaUserTie size={40} style={{ marginBottom: 16, opacity: 0.5 }} />
                        <p>No recruiters found.</p>
                    </div>
                ) : (
                    <div style={{ overflowX: "auto" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse" }}>
                            <thead>
                                <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left", color: "var(--text-secondary)", fontSize: 13, textTransform: "uppercase", letterSpacing: 0.5 }}>
                                    <th style={{ padding: "16px", fontWeight: 600 }}>Name</th>
                                    <th style={{ padding: "16px", fontWeight: 600 }}>Role</th>
                                    <th style={{ padding: "16px", fontWeight: 600 }}>Department</th>
                                    <th style={{ padding: "16px", fontWeight: 600 }}>Status</th>
                                    <th style={{ padding: "16px", fontWeight: 600, textAlign: "right" }}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map(r => (
                                    <tr key={r.id} style={{ borderBottom: "1px solid var(--border)" }}>
                                        <td style={{ padding: "16px" }}>
                                            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                                <div style={{
                                                    width: 36, height: 36, borderRadius: "50%",
                                                    background: "var(--primary-light)", color: "var(--primary)",
                                                    display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 600
                                                }}>
                                                    {r.first_name[0]}{r.last_name[0]}
                                                </div>
                                                <div>
                                                    <div style={{ fontWeight: 600, color: "var(--text)", fontSize: 15 }}>{r.first_name} {r.last_name}</div>
                                                    <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{r.email}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td style={{ padding: "16px", color: "var(--text-secondary)", fontSize: 14 }}>{r.designation}</td>
                                        <td style={{ padding: "16px", color: "var(--text-secondary)", fontSize: 14 }}>{r.department}</td>
                                        <td style={{ padding: "16px" }}>
                                            <StatusBadge status={r.status} />
                                        </td>
                                        <td style={{ padding: "16px", textAlign: "right" }}>
                                            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                                                <button onClick={() => handleResetPassword(r.id)} style={{ background: "none", border: "none", color: "var(--text-secondary)", cursor: "pointer", padding: 6 }} title="Reset Password"><FaKey /></button>
                                                <button onClick={() => handleDelete(r.id)} style={{ background: "none", border: "none", color: "var(--danger)", cursor: "pointer", padding: 6 }} title="Delete"><FaTrash /></button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
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
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                                    <input required placeholder="First Name" value={formData.first_name} onChange={e => setFormData({...formData, first_name: e.target.value})} style={{ padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }} />
                                    <input required placeholder="Last Name" value={formData.last_name} onChange={e => setFormData({...formData, last_name: e.target.value})} style={{ padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }} />
                                </div>
                                <input required type="email" placeholder="Email Address" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} style={{ padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }} />
                                <input required type="tel" placeholder="Phone Number" value={formData.phone} onChange={e => setFormData({...formData, phone: e.target.value})} style={{ padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }} />
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                                    <input required placeholder="Department" value={formData.department} onChange={e => setFormData({...formData, department: e.target.value})} style={{ padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }} />
                                    <input required placeholder="Designation" value={formData.designation} onChange={e => setFormData({...formData, designation: e.target.value})} style={{ padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }} />
                                </div>
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
            </AnimatePresence>
        </div>
    );
}

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthContext } from "../../context/AuthContext";
import recruiterService from "../../services/recruiter/recruiterService";
import { FaLock, FaEye, FaEyeSlash } from "react-icons/fa";
import "../../styles/company/Settings.css";

/**
 * ChangePassword — Recruiter First-Login Required Password Change
 *
 * This page is shown to recruiters who log in for the first time
 * with a temporary password (must_change_password === true).
 *
 * It lives at /company/change-password, inside the Company Portal,
 * so the recruiter always feels they are within the same workspace.
 */
export default function ChangePassword() {
    const { logout, refreshUser } = useAuthContext();
    const navigate = useNavigate();

    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");

        if (password.length < 8) {
            setError("Password must be at least 8 characters long.");
            return;
        }

        if (password !== confirmPassword) {
            setError("Passwords do not match.");
            return;
        }

        setLoading(true);
        try {
            await recruiterService.changePassword({ new_password: password });
            setSuccess(true);
            setTimeout(() => {
                logout(); // Force re-login to get a new token without must_change_password
                navigate("/login");
            }, 2000);
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to change password. Please try again.");
            setLoading(false);
        }
    };

    return (
        <div style={{
            maxWidth: 500, margin: "60px auto", padding: "24px",
            background: "var(--bg)", borderRadius: "var(--radius-lg)",
            border: "1px solid var(--border)", boxShadow: "0 8px 24px rgba(0,0,0,0.12)"
        }}>
            <h2 style={{ marginBottom: 8, display: "flex", alignItems: "center", gap: 12 }}>
                <FaLock style={{ color: "var(--primary)" }} /> Set New Password
            </h2>
            <p style={{ color: "var(--text-muted)", marginBottom: 24, fontSize: 14 }}>
                For security reasons, you must change your temporary password before accessing the platform.
            </p>

            {success ? (
                <div style={{
                    padding: "16px", background: "rgba(16, 185, 129, 0.1)",
                    color: "#10b981", borderRadius: 8, border: "1px solid rgba(16, 185, 129, 0.2)"
                }}>
                    Password updated successfully. Redirecting to login...
                </div>
            ) : (
                <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    
                    {error && (
                        <div style={{
                            padding: "12px", background: "rgba(239, 68, 68, 0.1)",
                            color: "#ef4444", borderRadius: 8, fontSize: 14
                        }}>
                            {error}
                        </div>
                    )}

                    <div style={{ position: "relative" }}>
                        <label style={{ display: "block", marginBottom: 8, fontSize: 14, fontWeight: 500 }}>
                            New Password
                        </label>
                        <input
                            type={showPassword ? "text" : "password"}
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            required
                            style={{
                                width: "100%", padding: "12px 16px", paddingRight: 40,
                                background: "var(--bg-card)", border: "1px solid var(--border)",
                                borderRadius: "var(--radius-md)", color: "var(--text)", boxSizing: "border-box"
                            }}
                            placeholder="Enter new password"
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            style={{
                                position: "absolute", right: 12, top: 40,
                                background: "none", border: "none",
                                color: "var(--text-muted)", cursor: "pointer"
                            }}
                        >
                            {showPassword ? <FaEyeSlash /> : <FaEye />}
                        </button>
                    </div>

                    <div style={{ position: "relative" }}>
                        <label style={{ display: "block", marginBottom: 8, fontSize: 14, fontWeight: 500 }}>
                            Confirm Password
                        </label>
                        <input
                            type={showPassword ? "text" : "password"}
                            value={confirmPassword}
                            onChange={e => setConfirmPassword(e.target.value)}
                            required
                            style={{
                                width: "100%", padding: "12px 16px",
                                background: "var(--bg-card)", border: "1px solid var(--border)",
                                borderRadius: "var(--radius-md)", color: "var(--text)", boxSizing: "border-box"
                            }}
                            placeholder="Confirm new password"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        style={{
                            marginTop: 8, padding: "12px",
                            background: "var(--primary)", color: "white",
                            border: "none", borderRadius: "var(--radius-md)",
                            fontWeight: 600, cursor: loading ? "not-allowed" : "pointer",
                            opacity: loading ? 0.7 : 1
                        }}
                    >
                        {loading ? "Updating..." : "Update Password"}
                    </button>
                </form>
            )}
        </div>
    );
}

import { motion } from "framer-motion";
import {
    FaEnvelope,
    FaLock,
    FaRobot,
    FaShieldAlt,
    FaChartLine,
    FaMicrophone,
    FaArrowRight,
    FaEye,
    FaEyeSlash,
} from "react-icons/fa";

import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiRequest } from "../api/client";
import { useAuthContext } from "../context/AuthContext";
import "../styles/login.css";

export default function Login() {

    const navigate = useNavigate();
    const { login } = useAuthContext();

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [rememberMe, setRememberMe] = useState(false);

    // ============================
    // Main Login Handler
    // ============================
    const handleLogin = async (e) => {

        e.preventDefault();
        setLoading(true);
        setError("");

        try {

            const response = await apiRequest(
                "/api/auth/login",
                {
                    method: "POST",
                    body: JSON.stringify({
                        email,
                        password,
                    }),
                }
            );

            const payload = response?.data ?? response;
            const accessToken = payload?.access_token || payload?.accessToken;
            const companyName = payload?.company_name || payload?.companyName || null;

            if (!accessToken) {
                throw new Error("No authentication token received from the server.");
            }

            login(accessToken, payload?.refresh_token || payload?.refreshToken || null, companyName);

            switch (payload.role) {

                case "admin":
                    navigate("/admin");
                    break;

                case "company":
                    navigate("/company");
                    break;

                case "candidate":
                    navigate("/candidate");
                    break;

                default:
                    navigate("/");
            }

        } catch (err) {

            setError(err.message || "Invalid email or password.");

        } finally {

            setLoading(false);

        }

    };

    // ============================
    // Demo Candidate Login
    // ============================
    const handleDemoLogin = async () => {

        setLoading(true);
        setError("");

        try {

            const response = await apiRequest("/api/auth/login", {
                method: "POST",
                body: JSON.stringify({
                    email: "candidate@intellihire.dev",
                    password: "TestCandidate123!",
                }),
            });

            const payload = response?.data ?? response;
            const accessToken = payload?.access_token || payload?.accessToken;
            const companyName = payload?.company_name || payload?.companyName || null;

            if (!accessToken) {
                throw new Error("No authentication token received from the server.");
            }

            login(accessToken, payload?.refresh_token || payload?.refreshToken || null, companyName);
            navigate("/candidate");

        } catch (err) {

            setError(err.message || "Invalid demo credentials.");

        } finally {

            setLoading(false);

        }

    };

    return (

        <div className="login-page">

            <div className="background-glow glow-left"></div>
            <div className="background-glow glow-right"></div>

            {/* ─── Left Brand Panel ─── */}
            <motion.section
                className="login-left"
                initial={{ opacity: 0, x: -60 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8 }}
            >

                <div className="brand-block">

                    <div className="robot-circle">
                        <FaRobot />
                    </div>

                    <h1>IntelliHire</h1>

                    <p>
                        AI-Powered Recruitment &amp; Interview Intelligence Platform
                    </p>

                </div>

                <div className="feature-list">

                    <motion.div whileHover={{ x: 8 }} className="feature-item">
                        <div className="feature-icon">
                            <FaMicrophone />
                        </div>
                        <div className="feature-content">
                            <h3>Voice Interviews</h3>
                            <span>
                                Conduct AI-powered voice interviews with real-time analysis.
                            </span>
                        </div>
                    </motion.div>

                    <motion.div whileHover={{ x: 8 }} className="feature-item">
                        <div className="feature-icon">
                            <FaChartLine />
                        </div>
                        <div className="feature-content">
                            <h3>AI Evaluation</h3>
                            <span>
                                Automated candidate scoring with intelligent insights.
                            </span>
                        </div>
                    </motion.div>

                    <motion.div whileHover={{ x: 8 }} className="feature-item">
                        <div className="feature-icon">
                            <FaShieldAlt />
                        </div>
                        <div className="feature-content">
                            <h3>Secure Authentication</h3>
                            <span>
                                Enterprise-grade JWT authentication with encrypted sessions.
                            </span>
                        </div>
                    </motion.div>

                </div>

            </motion.section>

            {/* ─── Right Login Card ─── */}
            <motion.section
                className="login-card"
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
            >

                <div className="login-header">

                    <span className="welcome-tag">Welcome Back</span>

                    <h2>Sign in to IntelliHire</h2>

                    <p>
                        Access your recruitment dashboard and continue hiring smarter.
                    </p>

                </div>

                <form onSubmit={handleLogin} className="login-form">

                    {/* Email */}
                    <div className="input-group">
                        <div className="icon-container">
                            <FaEnvelope className="input-icon" />
                        </div>
                        <div className="input-wrapper">
                            <input
                                type="email"
                                placeholder="Email Address"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    {/* Password */}
                    <div className="input-group">
                        <div className="icon-container">
                            <FaLock className="input-icon" />
                        </div>
                        <div className="input-wrapper">
                            <input
                                type={showPassword ? "text" : "password"}
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                            <button
                                type="button"
                                className="password-toggle"
                                onClick={() => setShowPassword(!showPassword)}
                                aria-label={showPassword ? "Hide password" : "Show password"}
                            >
                                {showPassword ? <FaEyeSlash /> : <FaEye />}
                            </button>
                        </div>
                    </div>

                    {/* Options row */}
                    <div className="login-options">
                        <label className="remember-me">
                            <input
                                type="checkbox"
                                checked={rememberMe}
                                onChange={(e) => setRememberMe(e.target.checked)}
                            />
                            <span>Remember Me</span>
                        </label>

                        <button
                            type="button"
                            className="forgot-password"
                            onClick={() => {/* Forgot password flow */ }}
                        >
                            Forgot Password?
                        </button>
                    </div>

                    {/* Error message */}
                    {error && (
                        <div className="login-error" role="alert">
                            {error}
                        </div>
                    )}

                    {/* Primary submit */}
                    <div className="button-group">
                        <button
                            type="submit"
                            className="login-button primary"
                            disabled={loading}
                        >
                            {loading ? (
                                "Signing In..."
                            ) : (
                                <>
                                    <span>Sign In</span>
                                    <FaArrowRight />
                                </>
                            )}
                        </button>

                        {/* Demo Candidate Login */}
                        <button
                            type="button"
                            className="login-button secondary"
                            onClick={handleDemoLogin}
                            disabled={loading}
                        >
                            <span>Demo Candidate Login</span>
                            <FaArrowRight />
                        </button>
                    </div>

                </form>

                {/* Footer */}
                <div className="login-divider">
                    <span>Protected by JWT Authentication</span>
                </div>

                <div className="login-help">
                    <div className="help-card">
                        <div className="help-header">
                            <span className="help-emoji">🎤</span>
                            <h4>Candidate</h4>
                        </div>
                        <p>
                            Use the interview invitation link shared by your recruiter to
                            begin your AI-powered interview session.
                        </p>
                    </div>
                </div>

            </motion.section>

        </div>

    );

}
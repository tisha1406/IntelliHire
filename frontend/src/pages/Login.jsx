import { motion } from "framer-motion";
import {
    FaEnvelope,
    FaLock,
    FaRobot,
    FaShieldAlt,
    FaChartLine,
    FaMicrophone,
    FaArrowRight,
} from "react-icons/fa";

import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiRequest } from "../api/client";
import { useAuthContext } from "../context/AuthContext";

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

            login(response.access_token);

            switch (response.role) {

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

            setError("Invalid email or password.");

        } finally {

            setLoading(false);

        }

    };

    return (

        <div className="login-page">

            <div className="background-glow glow-left"></div>

            <div className="background-glow glow-right"></div>

            <motion.section

                className="login-left"

                initial={{
                    opacity:0,
                    x:-60
                }}

                animate={{
                    opacity:1,
                    x:0
                }}

                transition={{
                    duration:.8
                }}

            >

                <div className="brand-block">

                    <div className="robot-circle">

                        <FaRobot />

                    </div>

                    <h1>

                        IntelliHire

                    </h1>

                    <p>

                        AI-Powered Recruitment & Interview Intelligence Platform

                    </p>

                </div>

                <div className="feature-list">

                    <motion.div

                        whileHover={{
                            x:8
                        }}

                        className="feature-item"

                    >

                        <div className="feature-icon">

                            <FaMicrophone />

                        </div>

                        <div className="feature-content">

                            <h3>

                                Voice Interviews

                            </h3>

                            <span>

                                Conduct AI-powered voice interviews with real-time analysis.

                            </span>

                        </div>

                    </motion.div>

                    <motion.div

                        whileHover={{
                            x:8
                        }}

                        className="feature-item"

                    >

                        <div className="feature-icon">

                            <FaChartLine />

                        </div>

                        <div className="feature-content">

                            <h3>

                                AI Evaluation

                            </h3>

                            <span>

                                Automated candidate scoring with intelligent insights.

                            </span>

                        </div>

                    </motion.div>

                    <motion.div

                        whileHover={{
                            x:8
                        }}

                        className="feature-item"

                    >

                        <div className="feature-icon">

                            <FaShieldAlt />

                        </div>

                        <div className="feature-content">

                            <h3>

                                Secure Authentication

                            </h3>

                            <span>

                                Enterprise-grade JWT authentication with encrypted sessions.

                            </span>

                        </div>

                    </motion.div>

                </div>

            </motion.section>

            <motion.section

                className="login-card"

                initial={{
                    opacity:0,
                    y:40
                }}

                animate={{
                    opacity:1,
                    y:0
                }}

                transition={{
                    duration:.8
                }}

            >

                <div className="login-header">

                    <span className="welcome-tag">

                        Welcome Back

                    </span>

                    <h2>

                        Sign in to IntelliHire

                    </h2>

                    <p>

                        Access your recruitment dashboard and continue hiring smarter.

                    </p>

                </div>

                <form onSubmit={handleLogin}>

                    <div className="input-group">

                        <FaEnvelope />

                        <input

                            type="email"

                            placeholder="Email Address"

                            value={email}

                            onChange={(e)=>setEmail(e.target.value)}

                            required

                        />

                    </div>

                    <div className="input-group">

                        <FaLock />

                        <input

                            type="password"

                            placeholder="Password"

                            value={password}

                            onChange={(e)=>setPassword(e.target.value)}

                            required

                        />

                    </div>

                    <div className="login-options">

                                            <label className="remember-me">

                        <input type="checkbox" />

                        <span>Remember Me</span>

                    </label>

                    <button
                        type="button"
                        className="forgot-password"
                    >
                        Forgot Password?
                        </label>

                        <a href="#">

                            Forgot Password?

                        </a>

                    {error && (
                        <p
                            style={{
                                color: "#ff6b6b",
                                marginBottom: "15px",
                                textAlign: "center",
                            }}
                        >
                            {error}
                        </p>
                    )}
                    </div>

                    <button disabled={loading}>
                        {loading ? "Signing In..." : "Sign In"}
                    </button>

                </div>

                {error && (

                    <div className="login-error">

                        {error}

                    </div>

                )}

                <button

                    type="submit"

                    className="login-button"

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

                <button
                    type="button"
                    className="login-button"
                    style={{
                        marginTop: 12,
                        background: "linear-gradient(135deg, #10B981 0%, #3B82F6 100%)",
                        boxShadow: "0 4px 12px rgba(16,185,129,0.3)"
                    }}
                    onClick={async () => {
                        console.log("Demo Login clicked");
                        console.log("Sending login request...");
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
                            console.log("Login response received");
                            console.log("JWT received", response.access_token);
                            console.log("Saving authentication");
                            login(response.access_token);
                            console.log("Redirecting");
                            navigate("/candidate");
                        } catch (err) {
                            console.error("Login failed:", err);
                            setError(err.message || "Invalid demo credentials.");
                        } finally {
                            setLoading(false);
                        }
                    }}
                    disabled={loading}
                >
                    <span>Demo Candidate Login</span>
                    <FaArrowRight />
                </button>

            </form>

            <div className="login-divider">

                <span>

                    Protected by JWT Authentication

                </span>

            </div>

            <div className="login-help">

                <div className="help-card">

                    <div className="help-header">

                        <span className="help-emoji">

                            🎤

                        </span>

                        <h4>

                            Candidate

                        </h4>

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
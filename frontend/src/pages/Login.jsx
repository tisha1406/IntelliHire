import { motion } from "framer-motion";
import {
    FaEnvelope,
    FaLock,
    FaRobot,
    FaShieldAlt,
    FaChartLine,
    FaMicrophone,
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

            <div className="background-circle one"></div>
            <div className="background-circle two"></div>

            <motion.div

                className="left-panel"

                initial={{ x: -100, opacity: 0 }}

                animate={{ x: 0, opacity: 1 }}

                transition={{ duration: 0.8 }}

            >

                <div className="brand">

                    <FaRobot className="robot-icon"/>

                    <h1>IntelliHire</h1>

                    <p>

                        AI-Powered Recruitment & Interview Intelligence Platform

                    </p>

                </div>

                <div className="features">

                    <div>

                        <FaMicrophone/>

                        <span>Voice Interviews</span>

                    </div>

                    <div>

                        <FaChartLine/>

                        <span>AI Evaluation</span>

                    </div>

                    <div>

                        <FaShieldAlt/>

                        <span>Secure Authentication</span>

                    </div>

                </div>

            </motion.div>

            <motion.div

                className="login-card"

                initial={{ y: 60, opacity: 0 }}

                animate={{ y: 0, opacity: 1 }}

                transition={{ duration: .8 }}

            >

                <h2>

                    Welcome Back

                </h2>

                <p>

                    Sign in to continue to IntelliHire

                </p>

                <form onSubmit={handleLogin}>

                    <div className="input-box">

                        <FaEnvelope/>

                        <input

                            type="email"

                            placeholder="Email"

                            value={email}

                            onChange={(e)=>setEmail(e.target.value)}

                            required

                        />

                    </div>

                    <div className="input-box">

                        <FaLock/>

                        <input

                            type="password"

                            placeholder="Password"

                            value={password}

                            onChange={(e)=>setPassword(e.target.value)}

                            required

                        />

                    </div>

                    <div className="remember">

                        <label>

                            <input type="checkbox"/>

                            Remember Me

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

                </form>

                <small>

                    Protected by JWT Authentication

                </small>

                <div className="login-help">

                    <div className="help-card">

                        <h4>🎤 Candidate</h4>

                        <p>
                            Use the interview invitation link shared by the recruiter.
                        </p>

                    </div>

                </div>

            </motion.div>

        </div>

    );

}
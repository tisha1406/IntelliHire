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

import "../styles/login.css";

export default function Login() {

    const navigate = useNavigate();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleLogin = (e) => {
        e.preventDefault();

        /*
            TODO:
            Replace this once backend login is ready.
        */

        console.log(email, password);

        navigate("/admin");
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

                        AI Powered Interview Intelligence Platform

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

                    </div>

                    <button>

                        Sign In

                    </button>

                </form>

                <small>

                    Protected by JWT Authentication

                </small>

            </motion.div>

        </div>

    );

}
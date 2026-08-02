import {
    User,
    ChevronDown,
    Settings,
    LogOut,
    SunMoon
} from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthContext } from "../../context/AuthContext";
import useTheme from "../../hooks/useTheme";
import { useAdminProfile } from "../../hooks/useAdminProfile";
import { useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "../../api/client";

import "../../styles/admin/topbar.css";

export default function UserMenu() {
    const { logout } = useAuthContext();
    const { data: profile } = useAdminProfile();
    const { theme, toggleTheme } = useTheme();
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef(null);
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    const name = profile?.name || "Administrator";
    const role = profile?.role || "System Administrator";

    const initials = name
        .split(" ")
        .map((word) => word[0])
        .join("")
        .substring(0, 2)
        .toUpperCase();

    useEffect(() => {
        function handleClickOutside(event) {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleLogout = async () => {
        setIsOpen(false);
        try {
            const token = localStorage.getItem("accessToken");
            await apiRequest("/api/auth/logout", { method: "POST" }, token);
        } catch (e) {} // ignore error on logout
        logout();
        queryClient.clear(); // Clear all react query cache
        navigate("/login");
    };

    return (
        <div className="user-menu-container" ref={menuRef} style={{ position: 'relative' }}>
            <button
                className={`user-menu ${isOpen ? "active" : ""}`}
                onClick={() => setIsOpen(!isOpen)}
            >
                <div className="user-avatar">
                    {initials}
                    <span className="online-indicator"></span>
                </div>
                <div className="user-info">
                    <span className="user-name">{name}</span>
                    <small className="user-role">{role}</small>
                </div>
                <ChevronDown
                    size={16}
                    className="user-arrow"
                    style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0)' }}
                />
            </button>

            {isOpen && (
                <div className="dropdown-menu">
                    <div className="dropdown-header">
                        <strong>{name}</strong>
                        <span>{profile?.email || "admin@intellihire.ai"}</span>
                    </div>
                    <div className="dropdown-divider"></div>
                    <button className="dropdown-item" onClick={() => { setIsOpen(false); navigate("/admin/profile"); }}>
                        <User size={16}/> Profile
                    </button>
                    <button className="dropdown-item" onClick={() => { setIsOpen(false); navigate("/admin/platform-settings"); }}>
                        <Settings size={16}/> Settings
                    </button>
                    <button className="dropdown-item" onClick={() => { setIsOpen(false); toggleTheme(); }}>
                        <SunMoon size={16}/> Theme ({theme})
                    </button>
                    <div className="dropdown-divider"></div>
                    <button className="dropdown-item danger" onClick={handleLogout}>
                        <LogOut size={16}/> Logout
                    </button>
                </div>
            )}
        </div>
    );
}

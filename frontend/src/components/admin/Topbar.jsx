import {
    Sun,
    Moon,
    Menu,
    Search,
    Sparkles
} from "lucide-react";

import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import useTheme from "../../hooks/useTheme";
import useSidebar from "../../hooks/useSidebar";

import NotificationMenu from "./NotificationMenu";
import UserMenu from "./UserMenu";
import Drawer from "../common/Drawer";

import "../../styles/admin/topbar.css";

export default function Topbar() {

    const { theme, toggleTheme } = useTheme();

    const { toggleSidebar } = useSidebar();

    const location = useLocation();

    const pageName = location.pathname
        .split("/")
        .pop()
        .replaceAll("-", " ");

    const title =
        pageName.length
            ? pageName.charAt(0).toUpperCase() + pageName.slice(1)
            : "Dashboard";

    const [searchQuery, setSearchQuery] = useState("");
    const [isAiDrawerOpen, setIsAiDrawerOpen] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.ctrlKey && e.key === "k") {
                e.preventDefault();
                document.getElementById("global-search-input")?.focus();
            }
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, []);

    useEffect(() => {
        const timeout = setTimeout(() => {
            if (searchQuery.trim().length > 0) {
                // Could implement live search dropdown here
            }
        }, 300); // debounce
        return () => clearTimeout(timeout);
    }, [searchQuery]);

    const handleSearchKeyDown = (e) => {
        if (e.key === "Enter" && searchQuery.trim().length > 0) {
            navigate(`/admin/companies?search=${encodeURIComponent(searchQuery)}`);
            setSearchQuery("");
        }
    };

    return (

        <header className="topbar">

            {/* LEFT */}

            <div className="topbar-left">

                <button
                    className="topbar-icon-btn"
                    onClick={toggleSidebar}
                >
                    <Menu size={18}/>
                </button>

                <div className="page-heading">

                    <h2>Administrator</h2>

                    <small>{title}</small>

                </div>

            </div>

            {/* CENTER */}

            <div className="topbar-search">

                <Search
                    size={18}
                    className="search-icon"
                />

                <input
                    id="global-search-input"
                    type="text"
                    placeholder="Search candidates, interviews, companies..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={handleSearchKeyDown}
                />
                <span className="shortcut">Ctrl + K</span>
            </div>

            {/* RIGHT */}
            <div className="topbar-right">
                <button className="ai-button" onClick={() => setIsAiDrawerOpen(true)}>
                    <Sparkles size={17}/>
                    <span>Ask AI</span>
                </button>

                <button

                    className="topbar-icon-btn"

                    onClick={toggleTheme}

                >

                    {

                        theme === "dark"

                            ?

                            <Sun size={18}/>

                            :

                            <Moon size={18}/>

                    }

                </button>

                <NotificationMenu />

                <UserMenu />
            </div>

            <Drawer 
                isOpen={isAiDrawerOpen} 
                onClose={() => setIsAiDrawerOpen(false)} 
                title="AI Assistant"
                width={400}
            >
                <div style={{ padding: '16px', color: 'var(--text-secondary)' }}>
                    <p>How can I help you today? (AI Assistant Integration Placeholder)</p>
                </div>
            </Drawer>
        </header>

    );

}
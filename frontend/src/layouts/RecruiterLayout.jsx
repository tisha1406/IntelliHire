import { useState, useEffect } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import useAuth from "../../hooks/useAuth";

import CompanyNavbar from "../../components/company/CompanyNavbar";
import RecruiterSidebar from "../../components/recruiter/RecruiterSidebar";

import "../../styles/company/CompanyLayout.css";

function RecruiterLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const { user } = useAuth();
    const navigate = useNavigate();
    
    // Redirect logic for must_change_password is handled in Login.jsx, 
    // but we can add a check here if needed.
    
    return (
        <div className="company-layout">
            <RecruiterSidebar
                sidebarOpen={sidebarOpen}
                setSidebarOpen={setSidebarOpen}
            />
            <div className="company-main">
                <CompanyNavbar
                    sidebarOpen={sidebarOpen}
                    setSidebarOpen={setSidebarOpen}
                />
                <main className="company-content">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}

export default RecruiterLayout;

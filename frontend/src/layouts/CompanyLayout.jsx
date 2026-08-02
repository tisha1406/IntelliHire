import { useState } from "react";
import { Outlet } from "react-router-dom";

import CompanyNavbar from "../components/company/CompanyNavbar";
import CompanySidebar from "../components/company/CompanySidebar";

import "../styles/company/CompanyLayout.css";

function CompanyLayout() {

    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (

        <div className="company-layout">

            <CompanySidebar
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

export default CompanyLayout;
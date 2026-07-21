import { Outlet } from "react-router-dom";

export default function CompanyLayout() {
    return (
        <div
            style={{
                minHeight: "100vh",
                background: "#f8fafc",
                padding: "40px",
            }}
        >
            <h1>Company Dashboard</h1>

            <Outlet />
        </div>
    );
}
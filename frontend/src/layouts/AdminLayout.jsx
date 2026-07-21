import { Outlet } from "react-router-dom";

export default function AdminLayout() {
    return (
        <div
            style={{
                minHeight: "100vh",
                background: "#f8fafc",
                padding: "40px",
            }}
        >
            <h1>Admin Dashboard</h1>

            <Outlet />
        </div>
    );
}
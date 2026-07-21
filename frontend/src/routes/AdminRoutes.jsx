import { Routes, Route } from "react-router-dom";

import Dashboard from "../pages/admin/Dashboard";

export default function AdminRoutes() {
    return (
        <Routes>
            <Route
                path="/"
                element={<Dashboard />}
            />
        </Routes>
    );
}
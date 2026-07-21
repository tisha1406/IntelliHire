import { Routes, Route } from "react-router-dom";

import Dashboard from "../pages/company/Dashboard";

export default function CompanyRoutes() {
    return (
        <Routes>
            <Route
                path="/"
                element={<Dashboard />}
            />
        </Routes>
    );
}
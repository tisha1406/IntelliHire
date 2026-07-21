import { Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";

import ProtectedRoute from "./routes/ProtectedRoute";

import AdminLayout from "./layouts/AdminLayout";
import CompanyLayout from "./layouts/CompanyLayout";
import CandidateLayout from "./layouts/CandidateLayout";

function App() {
    return (
        <Routes>

            <Route
                path="/login"
                element={<Login />}
            />

            <Route
                path="/admin/*"
                element={
                    <ProtectedRoute role="admin">
                        <AdminLayout />
                    </ProtectedRoute>
                }
            />

            <Route
                path="/company/*"
                element={
                    <ProtectedRoute role="company">
                        <CompanyLayout />
                    </ProtectedRoute>
                }
            />

            <Route
                path="/candidate/*"
                element={
                    <ProtectedRoute role="candidate">
                        <CandidateLayout />
                    </ProtectedRoute>
                }
            />

            <Route
                path="*"
                element={<Navigate to="/login" replace />}
            />

        </Routes>
    );
}

export default App;
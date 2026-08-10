import { Navigate } from "react-router-dom";
import useAuth from "../hooks/useAuth";

export default function ProtectedRoute({
    children,
    role,
    roles = [],
}) {

    const {

        isAuthenticated,

        user,

        loading,

    } = useAuth();

    // ======================================
    // Wait until authentication is restored
    // ======================================
    if (loading) {

        return null;
        // Replace later with <LoadingScreen />

    }

    // ======================================
    // User is not logged in
    // ======================================
    if (!isAuthenticated) {

        return <Navigate to="/login" replace />;

    }

    // ======================================
    // Single role support
    // Example:
    // role="admin"
    // ======================================
    if (role && user?.role !== role) {

        return <Navigate to="/unauthorized" replace />;

    }

    // ======================================
    // Multiple role support
    // Example:
    // roles={["company","recruiter"]}
    // ======================================
    if (
        roles.length > 0 &&
        !roles.includes(user?.role)
    ) {

        return <Navigate to="/unauthorized" replace />;

    }

    // ======================================
    // Intercept Recruiter First Login
    // ======================================
    if (user?.role === "recruiter" && user?.must_change_password) {
        const currentPath = window.location.pathname;
        if (currentPath !== "/company/change-password") {
            return <Navigate to="/company/change-password" replace />;
        }
    }

    return children;

}
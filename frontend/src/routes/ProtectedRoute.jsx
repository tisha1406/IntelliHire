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
        companyProfile,
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
    // Intercept Company Subscription Status
    // ======================================
    if (user?.role === "company" && companyProfile) {
        const subStatus = companyProfile?.subscription?.status || "active";
        const currentPath = window.location.pathname;
        
        if (subStatus === "pending_verification" && !currentPath.includes("/subscription/verify")) {
            return <Navigate to="/company/subscription/verify" replace />;
        }
        if (subStatus === "pending_payment" && !currentPath.includes("/subscription/payment")) {
            return <Navigate to="/company/subscription/payment" replace />;
        }
        if (subStatus === "expired" && !currentPath.includes("/subscription/renew") && !currentPath.includes("/subscription/payment") && currentPath !== "/company/subscription") {
            return <Navigate to="/company/subscription/renew" replace />;
        }
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
import api from "../api";

const dashboardService = {
    /**
     * Fetch all dashboard data in one aggregated call.
     * The backend endpoint /company/dashboard computes everything from MongoDB
     * scoped to the authenticated company — no multiple round-trips needed.
     */
    getDashboard() {
        return api.get("/company/dashboard");
    },

    // ── Legacy individual calls kept for Analytics page compatibility ────────

    /** KPI metrics (used by Analytics page) */
    getStats() {
        return api.get("/company/analytics/kpis");
    },

    /** Monthly hiring trend (used by Analytics page) */
    getHiringTrend() {
        return api.get("/company/analytics/hiring-trend");
    },

    /** Hiring funnel (used by Analytics page) */
    getHiringFunnel() {
        return api.get("/company/analytics/hiring-funnel");
    },

    /** Department breakdown (used by Analytics page) */
    getDepartmentBreakdown() {
        return api.get("/company/analytics/department-breakdown");
    },

    /** Recruiter performance (used by Analytics page) */
    getRecruiterPerformance() {
        return api.get("/company/analytics/recruiter-performance");
    },
};

export default dashboardService;

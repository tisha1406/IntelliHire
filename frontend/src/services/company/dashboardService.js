import api from "../api";

const dashboardService = {
    /**
     * Company Admin: fetch all dashboard data aggregated for the company.
     */
    getDashboard() {
        return api.get("/company/dashboard");
    },

    /**
     * Recruiter: fetch recruiter-scoped dashboard stats.
     * Backend scopes by recruiter_id from JWT automatically.
     */
    getRecruiterDashboard() {
        return api.get("/company/dashboard");
    },

    // ── Analytics page endpoints ─────────────────────────────────────────────

    /** KPI metrics */
    getStats() {
        return api.get("/company/analytics/kpis");
    },

    /** Monthly hiring trend */
    getHiringTrend() {
        return api.get("/company/analytics/hiring-trend");
    },

    /** Hiring funnel */
    getHiringFunnel() {
        return api.get("/company/analytics/hiring-funnel");
    },

    /** Department breakdown */
    getDepartmentBreakdown() {
        return api.get("/company/analytics/department-breakdown");
    },

    /** Recruiter performance */
    getRecruiterPerformance() {
        return api.get("/company/analytics/recruiter-performance");
    },
};

export default dashboardService;


import api from "../api";

const dashboardService = {
    /**
     * Fetch live dashboard stats: candidates, campaigns, interviews, hiring rate
     */
    getStats() {
        return api.get("/company/analytics/kpis");
    },

    /**
     * Fetch recent candidates (last 4)
     */
    getRecentCandidates() {
        return api.get("/company/candidates/", { params: { limit: 4, sort: "newest" } });
    },

    /**
     * Fetch upcoming scheduled interview sessions
     */
    getUpcomingInterviews() {
        return api.get("/company/candidates/interviews", { params: { limit: 4 } });
    },

    /**
     * Fetch hiring funnel counts for bar chart
     */
    getHiringFunnel() {
        return api.get("/company/analytics/hiring-funnel");
    },

    /**
     * Fetch monthly hiring trend for line chart
     */
    getHiringTrend() {
        return api.get("/company/analytics/hiring-trend");
    },

    /**
     * Fetch department breakdown for doughnut chart
     */
    getDepartmentBreakdown() {
        return api.get("/company/analytics/department-breakdown");
    },

    /**
     * Fetch top recruiter performance data
     */
    getRecruiterPerformance() {
        return api.get("/company/analytics/recruiter-performance");
    },
};

export default dashboardService;

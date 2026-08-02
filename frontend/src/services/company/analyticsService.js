import api from "../api";

const BASE = "/company/analytics";

const analyticsService = {
    getKPIs() {
        return api.get(`${BASE}/kpis`);
    },

    getHiringTrend() {
        return api.get(`${BASE}/hiring-trend`);
    },

    getCandidateSources() {
        return api.get(`${BASE}/candidate-sources`);
    },

    getHiringFunnel() {
        return api.get(`${BASE}/hiring-funnel`);
    },

    getDepartmentBreakdown() {
        return api.get(`${BASE}/department-breakdown`);
    },

    getRecruiterPerformance() {
        return api.get(`${BASE}/recruiter-performance`);
    },

    getYearlyComparison() {
        return api.get(`${BASE}/yearly-comparison`);
    },
};

export default analyticsService;

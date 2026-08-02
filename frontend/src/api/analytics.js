import { apiRequest } from "./client";

export const AnalyticsAPI = {
    getDashboardStats: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/analytics/dashboard", {}, token);
    },
    getHiringAnalytics: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/analytics/hiring", {}, token);
    },
    getPerformanceMetrics: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/analytics/performance", {}, token);
    },
    getReports: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/analytics/reports", {}, token);
    }
};


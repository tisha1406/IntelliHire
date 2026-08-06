import { apiRequest } from "./client";

const getToken = () => localStorage.getItem("accessToken");

export const AIReportsAPI = {
    getScoreDistribution: async (range) => {
        return await apiRequest(`/admin/ai-reports/score-distribution?range=${range}`, {}, getToken());
    },
    getCompanyCompletion: async (range) => {
        return await apiRequest(`/admin/ai-reports/company-completion?range=${range}`, {}, getToken());
    },
    getReport: async (reportType, range) => {
        return await apiRequest(`/admin/ai-reports/${reportType}?range=${range}`, {}, getToken());
    }
};

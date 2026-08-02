import { apiRequest } from "./client";

export const AIReportsAPI = {
    getScoreDistribution: async (range, token) => {
        return await apiRequest(`/admin/ai-reports/score-distribution?range=${range}`, {}, token);
    },
    getCompanyCompletion: async (range, token) => {
        return await apiRequest(`/admin/ai-reports/company-completion?range=${range}`, {}, token);
    },
    getReport: async (reportType, range, token) => {
        return await apiRequest(`/admin/ai-reports/${reportType}?range=${range}`, {}, token);
    }
};

import { apiRequest } from "./client";

export const AICenterAPI = {
    getUsage: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/ai-center/insights/usage`, {}, token);
    },

    getResumeScreening: async (params = {}) => {
        const token = localStorage.getItem("accessToken");
        const searchParams = new URLSearchParams();
        if (params.status) searchParams.append("status", params.status);
        if (params.limit) searchParams.append("limit", params.limit);
        if (params.offset) searchParams.append("offset", params.offset);
        
        const qs = searchParams.toString();
        const url = `/admin/ai-center/resume-screening${qs ? `?${qs}` : ""}`;
        return await apiRequest(url, {}, token);
    },

    getInterviewAnalysis: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/ai-center/interview-analysis`, {}, token);
    },

    getInterviewAnalysisRecords: async (params = {}) => {
        const token = localStorage.getItem("accessToken");
        const searchParams = new URLSearchParams();
        if (params.limit) searchParams.append("limit", params.limit);
        if (params.offset) searchParams.append("offset", params.offset);
        
        const qs = searchParams.toString();
        const url = `/admin/ai-center/interview-analysis/records${qs ? `?${qs}` : ""}`;
        return await apiRequest(url, {}, token);
    },

    getReports: async (params = {}) => {
        const token = localStorage.getItem("accessToken");
        const searchParams = new URLSearchParams();
        if (params.limit) searchParams.append("limit", params.limit);
        if (params.offset) searchParams.append("offset", params.offset);
        
        const qs = searchParams.toString();
        const url = `/admin/ai-center/reports${qs ? `?${qs}` : ""}`;
        return await apiRequest(url, {}, token);
    }
};

import { apiRequest } from "./client";

export const MonitoringAPI = {
    getCandidates: async (params = {}) => {
        const token = localStorage.getItem("accessToken");
        const searchParams = new URLSearchParams();
        if (params.search) searchParams.append("search", params.search);
        if (params.status) searchParams.append("status", params.status);
        if (params.limit) searchParams.append("limit", params.limit);
        if (params.offset) searchParams.append("offset", params.offset);
        
        const qs = searchParams.toString();
        const url = `/admin/candidates${qs ? `?${qs}` : ""}`;
        return await apiRequest(url, {}, token);
    },

    getCandidate: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/candidates/${id}`, {}, token);
    },

    getInterviews: async (params = {}) => {
        const token = localStorage.getItem("accessToken");
        const searchParams = new URLSearchParams();
        if (params.status) searchParams.append("status", params.status);
        if (params.company_id) searchParams.append("company_id", params.company_id);
        if (params.limit) searchParams.append("limit", params.limit);
        if (params.offset) searchParams.append("offset", params.offset);
        
        const qs = searchParams.toString();
        const url = `/admin/interviews${qs ? `?${qs}` : ""}`;
        return await apiRequest(url, {}, token);
    },

    getInterview: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/interviews/${id}`, {}, token);
    },

    getCalendarEvents: async (params = {}) => {
        const token = localStorage.getItem("accessToken");
        const searchParams = new URLSearchParams();
        if (params.start_date) searchParams.append("start_date", params.start_date);
        if (params.end_date) searchParams.append("end_date", params.end_date);
        
        const qs = searchParams.toString();
        const url = `/admin/interviews/calendar/events${qs ? `?${qs}` : ""}`;
        return await apiRequest(url, {}, token);
    },

    getStorageUsage: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/storage", {}, token);
    }
};

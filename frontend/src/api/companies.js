import { apiRequest } from "./client";

export const CompaniesAPI = {
    getCompanies: async (params = {}) => {
        const token = localStorage.getItem("accessToken");
        const searchParams = new URLSearchParams();
        if (params.search) searchParams.append("search", params.search);
        if (params.status) searchParams.append("status", params.status);
        if (params.subscription) searchParams.append("subscription", params.subscription);
        if (params.limit) searchParams.append("limit", params.limit);
        if (params.offset) searchParams.append("offset", params.offset);
        

        const qs = searchParams.toString();
        const url = `/admin/companies${qs ? `?${qs}` : ""}`;
        return await apiRequest(url, {}, token);
    },

    getCompany: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/companies/${id}`, {}, token);
    },

    createCompany: async (data) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/companies", {
            method: "POST",
            body: JSON.stringify(data)
        }, token);
    },

    updateCompany: async (id, data) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/companies/${id}`, {
            method: "PATCH",
            body: JSON.stringify(data)
        }, token);
    },

    deleteCompany: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/companies/${id}`, {
            method: "DELETE"
        }, token);
    },

    restoreCompany: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/companies/${id}/restore`, {
            method: "POST"
        }, token);
    },

    suspendCompany: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/companies/${id}/suspend`, {
            method: "POST"
        }, token);
    },

    activateCompany: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/companies/${id}/activate`, {
            method: "POST"
        }, token);
    },

    resetPassword: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/companies/${id}/reset-password`, {
            method: "POST"
        }, token);
    },

    getRecruiters: async (id, limit = 50, offset = 0) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/companies/${id}/recruiters?limit=${limit}&offset=${offset}`, {}, token);
    },

    getCampaigns: async (id, limit = 50, offset = 0) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/companies/${id}/campaigns?limit=${limit}&offset=${offset}`, {}, token);
    },

    getCandidates: async (id, limit = 50, offset = 0) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/companies/${id}/candidates?limit=${limit}&offset=${offset}`, {}, token);
    },

    getAuditLogs: async (id, limit = 50, offset = 0) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/companies/${id}/audit-logs?limit=${limit}&offset=${offset}`, {}, token);
    },

    getInterviews: async (id, limit = 50, offset = 0) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/companies/${id}/interviews?limit=${limit}&offset=${offset}`, {}, token);
    }
};


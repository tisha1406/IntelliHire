import { apiRequest } from "./client";

export const RecruitersAPI = {
    getRecruiters: async (params = {}) => {
        const token = localStorage.getItem("accessToken");
        const searchParams = new URLSearchParams();
        if (params.search) searchParams.append("search", params.search);
        if (params.status) searchParams.append("status", params.status);
        if (params.company_id) searchParams.append("company_id", params.company_id);
        if (params.limit) searchParams.append("limit", params.limit);
        if (params.offset) searchParams.append("offset", params.offset);
        
        const qs = searchParams.toString();
        const url = `/admin/recruiters${qs ? `?${qs}` : ""}`;
        return await apiRequest(url, {}, token);
    },

    getRecruiter: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/recruiters/${id}`, {}, token);
    },

    createRecruiter: async (data) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/recruiters", {
            method: "POST",
            body: JSON.stringify(data)
        }, token);
    },

    updateRecruiter: async (id, data) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/recruiters/${id}`, {
            method: "PATCH",
            body: JSON.stringify(data)
        }, token);
    },

    deleteRecruiter: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/recruiters/${id}`, {
            method: "DELETE"
        }, token);
    },

    suspendRecruiter: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/recruiters/${id}/suspend`, {
            method: "POST"
        }, token);
    },

    activateRecruiter: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/recruiters/${id}/activate`, {
            method: "POST"
        }, token);
    }
};

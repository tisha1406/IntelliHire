import { apiRequest } from "./client";

export const UsersAPI = {
    getUsers: async (params = {}) => {
        const token = localStorage.getItem("accessToken");
        const searchParams = new URLSearchParams();
        if (params.role) searchParams.append("role", params.role);
        if (params.status) searchParams.append("status", params.status);
        if (params.limit) searchParams.append("limit", params.limit);
        if (params.offset) searchParams.append("offset", params.offset);
        
        const qs = searchParams.toString();
        const url = `/admin/users${qs ? `?${qs}` : ""}`;
        return await apiRequest(url, {}, token);
    },
    suspendUser: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/users/${id}/suspend`, { method: "POST" }, token);
    },
    activateUser: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/users/${id}/activate`, { method: "POST" }, token);
    },
    deleteUser: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/users/${id}`, { method: "DELETE" }, token);
    },
    resetPassword: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/users/${id}/reset-password`, { method: "POST" }, token);
    },
    forceLogout: async (id) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/users/${id}/force-logout`, { method: "POST" }, token);
    },
    updateRole: async (id, role) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/users/${id}/role`, {
            method: "PATCH",
            body: JSON.stringify({ role })
        }, token);
    }
};

import { apiRequest } from "./client";

export const SystemAPI = {
    getHealth: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/system/health", {}, token);
    },
    getAuditLogs: async (params = {}) => {
        const token = localStorage.getItem("accessToken");
        const searchParams = new URLSearchParams();
        if (params.limit) searchParams.append("limit", params.limit);
        if (params.offset) searchParams.append("offset", params.offset);
        
        const qs = searchParams.toString();
        const url = `/admin/system/audit-logs${qs ? `?${qs}` : ""}`;
        return await apiRequest(url, {}, token);
    },
    getSecurityLogs: async (params = {}) => {
        const token = localStorage.getItem("accessToken");
        const searchParams = new URLSearchParams();
        if (params.limit) searchParams.append("limit", params.limit);
        if (params.offset) searchParams.append("offset", params.offset);
        
        const qs = searchParams.toString();
        const url = `/admin/system/security-logs${qs ? `?${qs}` : ""}`;
        return await apiRequest(url, {}, token);
    },
    getNotifications: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/system/notifications", {}, token);
    }
};

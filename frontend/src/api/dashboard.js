import { apiRequest } from "./client";

const getToken = () => localStorage.getItem("accessToken");

export const DashboardAPI = {
    getDashboard: async () => {
        return await apiRequest("/admin/dashboard", { method: "GET" }, getToken());
    },
    getNotifications: async () => {
        return await apiRequest("/admin/notifications", { method: "GET" }, getToken());
    }
};

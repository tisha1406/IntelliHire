import { apiRequest } from "./client";

const getToken = () => localStorage.getItem("accessToken");

export const ProfileAPI = {
    getProfile: async () => {
        return await apiRequest("/admin/profile", { method: "GET" }, getToken());
    },
    updateProfile: async (data) => {
        return await apiRequest("/admin/profile", { method: "PUT", body: JSON.stringify(data) }, getToken());
    }
};

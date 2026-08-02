import { apiRequest } from "./client";

export const SettingsAPI = {
    getMasterSettings: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/settings/master", {}, token);
    },
    getPlatformSettings: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/settings/platform", {}, token);
    },
    updatePlatformSettings: async (payload) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/settings/platform", {
            method: "PATCH",
            body: JSON.stringify(payload)
        }, token);
    },
    updateMasterSettings: async (payload) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/settings/master", {
            method: "PATCH",
            body: JSON.stringify(payload)
        }, token);
    },
    getVoices: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/settings/voices", {}, token);
    },
    getLanguages: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/settings/languages", {}, token);
    },
    getStrategies: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/strategies", {}, token);
    },
    getInterviewModes: async () => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest("/admin/interview-modes", {}, token);
    }
};

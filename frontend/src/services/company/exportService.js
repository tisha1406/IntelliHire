import api from "../api";

const BASE = "/company/exports";

const exportService = {
    getSummaryCounts() {
        return api.get(`${BASE}/summary`);
    },

    getHistory() {
        return api.get(`${BASE}/history`);
    },

    createExport(data) {
        return api.post(BASE, data);
    },

    downloadExport(exportId) {
        return api.get(`${BASE}/download/${exportId}`, { responseType: "blob" });
    },

    deleteExport(exportId) {
        return api.delete(`${BASE}/${exportId}`);
    }
};

export default exportService;

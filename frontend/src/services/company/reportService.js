import api from "../api";

const BASE = "/company/reports";

const reportService = {
    getReports(type = "", search = "") {
        const params = {};
        if (type) params.type = type;
        if (search) params.search = search;
        return api.get(BASE, { params });
    },

    getStatistics() {
        return api.get(`${BASE}/statistics`);
    },

    generateReport(data) {
        return api.post(BASE, data);
    },

    downloadReport(reportId) {
        return api.get(`${BASE}/download/${reportId}`, { responseType: "blob" });
    },

    deleteReport(reportId) {
        return api.delete(`${BASE}/${reportId}`);
    }
};

export default reportService;

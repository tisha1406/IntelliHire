import api from "../api";

const BASE = "/company/recruiters";

const recruiterManagementService = {
    getRecruiters() {
        return api.get(`${BASE}/`);
    },

    getRecruiter(id) {
        return api.get(`${BASE}/${id}`);
    },

    createRecruiter(data) {
        return api.post(`${BASE}/`, data);
    },

    updateRecruiter(id, data) {
        return api.put(`${BASE}/${id}`, data);
    },

    deleteRecruiter(id) {
        return api.delete(`${BASE}/${id}`);
    },

    resetPassword(id) {
        return api.post(`${BASE}/${id}/reset-password`);
    }
};

export default recruiterManagementService;

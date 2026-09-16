import api from "../api";

const BASE = "/company/candidates";

const candidateService = {

    getCandidates(params = {}) {
        return api.get(`${BASE}/`, { params });
    },

    getCandidate(id) {
        return api.get(`${BASE}/${id}`);
    },

    createCandidate(data) {
        return api.post(`${BASE}/`, data);
    },

    updateCandidate(id, data) {
        return api.put(`${BASE}/${id}`, data);
    },

    deleteCandidate(id) {
        return api.delete(`${BASE}/${id}`);
    },

    shortlistCandidate(id) {
        return api.patch(`${BASE}/${id}/shortlist`);
    },

    rejectCandidate(id) {
        return api.patch(`${BASE}/${id}/reject`);
    },

    scheduleInterview(id) {
        return api.patch(`${BASE}/${id}/schedule`);
    },

    sendInvite(id) {
        return api.post(`${BASE}/${id}/send-invite`);
    },
    downloadResume(id) {
        return api.get(`${BASE}/${id}/resume`, {
            responseType: "blob",
        });
    },

    downloadReport(id) {
        return api.get(`${BASE}/${id}/report`, {
            responseType: "blob",
        });
    },
};

export default candidateService;
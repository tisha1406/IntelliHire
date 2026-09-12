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

    bulkAssignCandidates(candidateIds, recruiterId) {
        return api.post(`${BASE}/bulk-assign`, { candidate_ids: candidateIds, recruiter_id: recruiterId });
    },

    inviteCandidate(data) {
        return api.post(`${BASE}/invite`, data);
    },

    suspendCandidate(id) {
        return api.patch(`${BASE}/${id}/suspend`);
    },

    activateCandidate(id) {
        return api.patch(`${BASE}/${id}/activate`);
    },

    resetCredentials(id) {
        return api.post(`${BASE}/${id}/reset-credentials`);
    }
};

export default candidateService;
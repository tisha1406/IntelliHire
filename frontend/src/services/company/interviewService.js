import api from "../api";

const BASE = "/company/candidates/interviews";

const interviewService = {
    getInterviews() {
        return api.get(`${BASE}`);
    },

    cancelInterview(sessionId) {
        return api.patch(`${BASE}/${sessionId}/cancel`);
    },

    scheduleInterview(data) {
        return api.post(`${BASE}/schedule`, data);
    },

    getInterviewResults(sessionId) {
        return api.get(`${BASE}/${sessionId}/results`);
    }
};

export default interviewService;

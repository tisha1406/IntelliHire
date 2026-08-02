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
    }
};

export default interviewService;

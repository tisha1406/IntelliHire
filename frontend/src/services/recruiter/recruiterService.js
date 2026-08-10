import api from "../api";

const BASE = "/api/recruiter/profile";

const recruiterService = {
    getProfile() {
        return api.get(BASE);
    },

    updateProfile(data) {
        return api.put(BASE, data);
    },

    changePassword(data) {
        return api.post(`${BASE}/change-password`, data);
    }
};

export default recruiterService;

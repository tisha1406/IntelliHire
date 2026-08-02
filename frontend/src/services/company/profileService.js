import api from "../api";

const BASE = "/company/profile";

const profileService = {
    /** Fetch the current user's profile from the backend */
    getProfile: () => api.get(BASE).then(r => r.data),

    /** Update editable profile fields */
    updateProfile: (fields) => api.patch(BASE, fields).then(r => r.data),

    /** Change password (requires current_password, new_password, confirm_password) */
    changePassword: (payload) =>
        api.post(`${BASE}/change-password`, payload).then(r => r.data),
};

export default profileService;

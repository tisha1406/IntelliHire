import api from "../api";

/**
 * Recruiter Management Service
 *
 * Unified service using the /company/team endpoint.
 * - Expects JWT-scoped company context (no company_id param needed)
 * - Backend enforces limits (max_recruiters) via check_limit middleware
 * - All data scoped to the authenticated company's JWT
 */

const BASE = "/company/team";

const recruiterManagementService = {
    getRecruiters(params = {}) {
        return api.get(BASE, { params });
    },

    getRecruiter(id) {
        return api.get(`${BASE}/${id}`);
    },

    /**
     * Create a new recruiter.
     * Payload: { name, email, role?, designation?, department?, phone? }
     */
    createRecruiter(data) {
        return api.post(BASE, data);
    },

    /**
     * Update a recruiter's profile.
     * Payload: { name?, role?, designation?, department?, phone?, status? }
     */
    updateRecruiter(id, data) {
        return api.patch(`${BASE}/${id}`, data);
    },

    deleteRecruiter(id) {
        return api.delete(`${BASE}/${id}`);
    },

    // ─── Password Management ────────────────────────────────────────────────
    // These are still on the /company/recruiters endpoint since team.py
    // doesn't have them yet. Falls back to the old endpoint for these ops.

    resetPassword(id) {
        return api.post(`${BASE}/${id}/reset-password`);
    },

    /** Suspend a recruiter account (disables login) */
    suspendRecruiter(id) {
        return api.post(`${BASE}/${id}/suspend`);
    },

    /** Reactivate a suspended recruiter account */
    activateRecruiter(id) {
        return api.post(`${BASE}/${id}/activate`);
    },

    /** Force recruiter to change password on next login */
    forcePasswordReset(id) {
        return api.post(`${BASE}/${id}/force-reset`);
    },

    // ─── Campaign Assignment ────────────────────────────────────────────────
    getRecruiterCampaigns(id) {
        return api.get(`${BASE}/${id}/campaigns`);
    },

    updateRecruiterCampaigns(id, campaign_ids) {
        return api.post(`${BASE}/${id}/campaigns`, { campaign_ids });
    },
    
    getRecruiterActivity(id) {
        return api.get(`${BASE}/${id}/activity`);
    },
    
    getRecruiterCandidates(id) {
        return api.get(`${BASE}/${id}/candidates`);
    },
    
    getRecruiterInterviews(id) {
        return api.get(`${BASE}/${id}/interviews`);
    }
};

export default recruiterManagementService;

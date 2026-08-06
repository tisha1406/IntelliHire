import api from "../api";

const BASE = "/company/notifications";

const notificationService = {
    /**
     * Fetch paginated notifications for the authenticated company.
     * Includes broadcast (target=all) and company-specific notifications.
     */
    getNotifications(limit = 50, offset = 0) {
        return api.get(BASE, { params: { limit, offset } });
    },

    /**
     * Mark a specific notification as read.
     */
    markRead(notificationId) {
        return api.patch(`${BASE}/${notificationId}/read`);
    },

    /**
     * Mark all notifications as read.
     */
    markAllRead() {
        return api.post(`${BASE}/read-all`);
    },
};

export default notificationService;

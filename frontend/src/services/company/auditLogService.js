import api from "../api";

const BASE = "/company/audit-logs";

const auditLogService = {
    getLogs(params = { limit: 100, skip: 0 }) {
        return api.get(`${BASE}/`, { params });
    },
};

export default auditLogService;

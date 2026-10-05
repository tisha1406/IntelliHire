import { apiRequest } from "./client";

// Client for backend/app/api/admin/strategies.py.
// Read endpoints added in Task E-01. createStrategy (POST /admin/strategies/,
// creates version 1) added in Task E-02. createStrategyVersion and
// activateVersion (POST .../versions, PATCH .../versions/{v}/activate) added
// in Task E-03.
export const StrategiesAPI = {
    getStrategies: async (params = {}) => {
        const token = localStorage.getItem("accessToken");
        const searchParams = new URLSearchParams();
        searchParams.append("limit", params.limit || 50);
        searchParams.append("offset", params.offset || 0);

        const url = `/admin/strategies/?${searchParams.toString()}`;
        return await apiRequest(url, {}, token);
    },

    getStrategy: async (strategyId) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/strategies/${strategyId}`, {}, token);
    },

    getStrategyVersions: async (strategyId) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/strategies/${strategyId}/versions`, {}, token);
    },

    getStrategyVersion: async (strategyId, version) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(`/admin/strategies/${strategyId}/versions/${version}`, {}, token);
    },

    // Creates a brand-new strategy at version 1 (POST /admin/strategies/).
    // Backend returns 409 if strategy_id already exists — use
    // createStrategyVersion for an existing strategy instead.
    createStrategy: async (data) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(
            "/admin/strategies/",
            {
                method: "POST",
                body: JSON.stringify(data),
            },
            token
        );
    },

    // Creates a new version of an EXISTING strategy (POST
    // /admin/strategies/{strategy_id}/versions). The backend auto-increments
    // the version number server-side and never mutates the prior version —
    // it is purely additive. data.strategy_id must match strategyId or the
    // backend returns 400.
    createStrategyVersion: async (strategyId, data) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(
            `/admin/strategies/${strategyId}/versions`,
            {
                method: "POST",
                body: JSON.stringify(data),
            },
            token
        );
    },

    // Activates or deactivates one specific, already-existing version
    // (PATCH /admin/strategies/{strategy_id}/versions/{version}/activate).
    // The backend is the sole authority over version state; this only
    // forwards the requested is_active value.
    activateVersion: async (strategyId, version, isActive) => {
        const token = localStorage.getItem("accessToken");
        return await apiRequest(
            `/admin/strategies/${strategyId}/versions/${version}/activate`,
            {
                method: "PATCH",
                body: JSON.stringify({ is_active: isActive }),
            },
            token
        );
    },
};

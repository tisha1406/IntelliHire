import api from "../api";

const BASE = "/company/campaigns";

const campaignService = {

    getCampaigns(params = {}) {
        return api.get(BASE, {
            params,
        });
    },

    getCampaign(id) {
        return api.get(`${BASE}/${id}`);
    },

    createCampaign(data) {
        return api.post(BASE, data);
    },

    updateCampaign(id, data) {
        return api.patch(`${BASE}/${id}`, data);
    },

    deleteCampaign(id) {
        return api.delete(`${BASE}/${id}`);
    }

};

export default campaignService;
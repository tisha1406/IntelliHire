import api from "../api";

const BASE = "/company/team";

const teamService = {
    getTeamMembers(search = "", role = "") {
        const params = {};
        if (search) params.search = search;
        if (role) params.role = role;
        return api.get(BASE, { params });
    },

    inviteMember(data) {
        return api.post(BASE, data);
    },

    removeMember(memberId) {
        return api.delete(`${BASE}/${memberId}`);
    },
};

export default teamService;

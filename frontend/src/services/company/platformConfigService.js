import api from "../api";

class PlatformConfigService {
    async getPlatformConfig() {
        const response = await api.get("/company/platform-config");
        return response.data;
    }
}

export default new PlatformConfigService();

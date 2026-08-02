import axios from "axios";

const api = axios.create({
    baseURL: "http://127.0.0.1:8000",
    headers: {
        "Content-Type": "application/json",
    },
});

// Attach JWT automatically — reads whichever key the auth system used
api.interceptors.request.use((config) => {
    const token =
        localStorage.getItem("accessToken") ||
        localStorage.getItem("access_token");

    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
});

export default api;
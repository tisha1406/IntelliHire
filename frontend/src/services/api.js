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

// Global error handler for subscription issues
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response) {
            const { status } = error.response;
            
            // Payment Required (Subscription Pending)
            if (status === 402) {
                if (!window.location.pathname.includes('/subscription/verify') && !window.location.pathname.includes('/subscription/renew')) {
                    window.location.href = '/subscription/verify';
                }
            }
            
            // Forbidden (Subscription Expired or Unauthorized)
            if (status === 403) {
                const detail = error.response.data?.detail;
                if (typeof detail === 'string' && detail.toLowerCase().includes('subscription')) {
                    if (!window.location.pathname.includes('/subscription/renew')) {
                        window.location.href = '/subscription/renew';
                    }
                }
            }
        }
        return Promise.reject(error);
    }
);

export default api;
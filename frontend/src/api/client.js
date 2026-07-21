const BASE_URL =
    import.meta.env.VITE_API_BASE_URL ||
    "http://127.0.0.1:8000";

export async function apiRequest(
    endpoint,
    options = {},
    token = null
) {

    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(
        `${BASE_URL}${endpoint}`,
        {
            ...options,
            headers,
        }
    );

    if (response.status === 401) {

        localStorage.removeItem("accessToken");

        window.location.href = "/login";

        return;
    }

    if (response.status === 403) {

        throw new Error("Forbidden");

    }

    const data = await response.json();

    if (!response.ok) {

        throw new Error(
            data.detail || "Request failed"
        );

    }

    return data;
}
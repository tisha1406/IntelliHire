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

    if (options.body instanceof FormData) {
        delete headers["Content-Type"];
    }

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

    // If HTTP error or our standard response indicates failure
    if (!response.ok || (data.success !== undefined && !data.success)) {
        throw new Error(
            data.message || data.detail || "Request failed"
        );
    }

    // Return the inner data from the standard APIResponse wrapper if present
    if (data.success !== undefined && data.data !== undefined) {
        return data.data;
    }

    if (!response.ok) {

        throw new Error(
            data.detail || "Request failed"
        );

    }

    return data;
}
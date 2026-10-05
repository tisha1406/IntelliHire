export const BASE_URL =
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
        
        // Don't redirect if we are already on the login page to avoid infinite loops
        if (window.location.pathname !== "/login" && window.location.pathname !== "/") {
            window.location.href = "/login";
        }

        // We must throw an error so callers (like the login form) can catch and display it
        // Check if there's a JSON body with a specific message first
        try {
            const errData = await response.json();
            throw new Error(errData.detail || errData.message || "Unauthorized");
        } catch (e) {
            throw new Error(e.message === "Unexpected end of JSON input" ? "Unauthorized" : e.message);
        }
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
        // Preserve the wrapper metadata for callers that need it, but return the
        // inner payload so login/auth flows can read nested fields like access_token.
        return data.data;
    }

    if (!response.ok) {

        throw new Error(
            data.detail || "Request failed"
        );

    }

    return data;
}

/**
 * G-04: best-effort server-side logout, shared by every role's logout
 * button (mirrors the call UserMenu.jsx already made for admin -- see
 * G-02 for the real revocation behavior this now reaches consistently).
 *
 * Deliberately never throws: callers must clear local auth state and let
 * the user leave the authenticated UI even if this request fails (network
 * error, already-expired token, etc.) -- a failed backend call must not
 * trap the user in a logged-in-looking screen. Failures are logged, not
 * silently discarded, per the G-04 requirement to fix that exact pattern.
 */
export async function logoutFromServer(token) {
    if (!token) return;

    try {
        await apiRequest("/api/auth/logout", { method: "POST" }, token);
    } catch (error) {
        console.error("Server-side logout failed (local session will still be cleared):", error);
    }
}
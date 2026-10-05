/**
 * @vitest-environment jsdom
 *
 * G-04 regression: shared server-side logout helper.
 *
 * specs.md confirmed only the admin UserMenu.jsx ever called
 * POST /api/auth/logout; every other role only cleared local storage, so
 * G-02's server-side refresh-token revocation never actually ran for them.
 * logoutFromServer() is the one shared implementation every role's logout
 * button now calls (see CandidateSidebar.jsx, CandidateTopbar.jsx,
 * admin Sidebar.jsx, CompanySidebar.jsx, CompanyNavbar.jsx).
 *
 * logoutFromServer is built on the real apiRequest (not re-mocked here) and
 * exercised through a mocked global fetch, so this proves the actual HTTP
 * call shape reaching the network, not just an internal function call.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { logoutFromServer } from "./client";

function mockFetchOk() {
    global.fetch = vi.fn().mockResolvedValue({
        status: 200,
        ok: true,
        json: async () => ({ success: true, message: "Logged out successfully", data: null }),
    });
}

function mockFetchNetworkError() {
    global.fetch = vi.fn().mockRejectedValue(new Error("network down"));
}

describe("logoutFromServer (G-04)", () => {
    afterEach(() => {
        vi.restoreAllMocks();
        delete global.fetch;
    });

    it("POSTs to /api/auth/logout with the given access token as a Bearer header", async () => {
        mockFetchOk();

        await logoutFromServer("abc.def.ghi");

        expect(global.fetch).toHaveBeenCalledTimes(1);
        const [url, options] = global.fetch.mock.calls[0];
        expect(url).toContain("/api/auth/logout");
        expect(options.method).toBe("POST");
        expect(options.headers.Authorization).toBe("Bearer abc.def.ghi");
    });

    it("does nothing (no request) when there is no token", async () => {
        mockFetchOk();

        await logoutFromServer(null);
        await logoutFromServer(undefined);
        await logoutFromServer("");

        expect(global.fetch).not.toHaveBeenCalled();
    });

    it("never throws when the backend request fails", async () => {
        mockFetchNetworkError();

        await expect(logoutFromServer("abc.def.ghi")).resolves.toBeUndefined();
    });

    it("logs (does not silently swallow) a failed backend logout", async () => {
        const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
        mockFetchNetworkError();

        await logoutFromServer("abc.def.ghi");

        expect(errorSpy).toHaveBeenCalled();
    });
});

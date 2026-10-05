/**
 * @vitest-environment jsdom
 *
 * G-04 regression: UserMenu.jsx's existing (already-working) backend logout
 * call is explicitly NOT to be redesigned here -- the only required fix is
 * removing its over-broad `catch(e){}` so a failed revocation is logged,
 * not silently discarded, while still completing the local logout + redirect
 * exactly as before.
 */
import { MemoryRouter } from "react-router-dom";
import { fireEvent, render, screen, cleanup, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import UserMenu from "./UserMenu";

const mockLogout = vi.fn();
const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
    const actual = await vi.importActual("react-router-dom");
    return { ...actual, useNavigate: () => mockNavigate };
});
vi.mock("../../context/AuthContext", () => ({ useAuthContext: () => ({ logout: mockLogout }) }));
vi.mock("../../hooks/useTheme", () => ({ default: () => ({ theme: "light", toggleTheme: vi.fn() }) }));
vi.mock("../../hooks/useAdminProfile", () => ({
    useAdminProfile: () => ({ data: { name: "System Administrator", email: "admin@intellihire.com", role: "admin" } }),
}));
vi.mock("@tanstack/react-query", () => ({ useQueryClient: () => ({ clear: vi.fn() }) }));

function setup() {
    return render(<MemoryRouter><UserMenu /></MemoryRouter>);
}

function openMenuAndClickLogout() {
    fireEvent.click(screen.getByText("System Administrator"));
    fireEvent.click(screen.getByText("Logout"));
}

describe("UserMenu logout (G-04 -- catch(e){} fix only)", () => {
    afterEach(() => {
        cleanup();
        mockLogout.mockReset();
        mockNavigate.mockReset();
        vi.restoreAllMocks();
        delete global.fetch;
    });

    it("still completes local logout and redirects when the backend call fails", async () => {
        global.fetch = vi.fn().mockRejectedValue(new Error("network down"));
        setup();

        openMenuAndClickLogout();

        await waitFor(() => expect(mockLogout).toHaveBeenCalled());
        expect(mockNavigate).toHaveBeenCalledWith("/login");
    });

    it("logs the failure instead of silently swallowing it", async () => {
        const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
        global.fetch = vi.fn().mockRejectedValue(new Error("network down"));
        setup();

        openMenuAndClickLogout();

        await waitFor(() => expect(mockLogout).toHaveBeenCalled());
        expect(errorSpy).toHaveBeenCalled();
    });

    it("still calls the backend logout endpoint with the stored access token on success", async () => {
        localStorage.setItem("accessToken", "tok-admin-menu");
        global.fetch = vi.fn().mockResolvedValue({
            status: 200, ok: true, json: async () => ({ success: true, message: "Logged out successfully", data: null }),
        });
        setup();

        openMenuAndClickLogout();

        await waitFor(() => expect(mockLogout).toHaveBeenCalled());
        const [url, options] = global.fetch.mock.calls[0];
        expect(url).toContain("/api/auth/logout");
        expect(options.headers.Authorization).toBe("Bearer tok-admin-menu");
    });
});

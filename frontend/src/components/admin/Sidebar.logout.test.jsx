/**
 * @vitest-environment jsdom
 *
 * G-04 regression: admin sidebar logout must reach the backend before
 * clearing local auth state (this button already worked via UserMenu.jsx
 * for the user-menu entry point -- this is the separate sidebar logout
 * button, which specs.md confirmed only cleared local storage).
 */
import { MemoryRouter } from "react-router-dom";
import { fireEvent, render, screen, cleanup, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import Sidebar from "./Sidebar";

const mockLogout = vi.fn();
const mockLogoutFromServer = vi.fn();

vi.mock("../../hooks/useSidebar", () => ({ default: () => ({ collapsed: false, toggleSidebar: vi.fn() }) }));
vi.mock("../../context/AuthContext", () => ({ useAuthContext: () => ({ logout: mockLogout }) }));
vi.mock("../../api/monitoring", () => ({ MonitoringAPI: { getStorageUsage: vi.fn().mockResolvedValue({ data: {} }) } }));
vi.mock("../../api/client", () => ({ logoutFromServer: (...args) => mockLogoutFromServer(...args) }));

function setup() {
    return render(<MemoryRouter><Sidebar /></MemoryRouter>);
}

describe("Admin Sidebar logout (G-04)", () => {
    afterEach(() => {
        cleanup();
        mockLogout.mockReset();
        mockLogoutFromServer.mockReset();
        localStorage.clear();
    });

    it("calls the backend logout with the stored access token, then clears local state", async () => {
        localStorage.setItem("accessToken", "tok-admin");
        mockLogoutFromServer.mockResolvedValue(undefined);
        setup();

        fireEvent.click(screen.getByText("Logout"));

        await waitFor(() => expect(mockLogout).toHaveBeenCalled());
        expect(mockLogoutFromServer).toHaveBeenCalledWith("tok-admin");
    });

    it("still clears local state when the backend logout call fails", async () => {
        localStorage.setItem("accessToken", "tok-admin");
        mockLogoutFromServer.mockRejectedValue(new Error("network down"));
        setup();

        fireEvent.click(screen.getByText("Logout"));

        await waitFor(() => expect(mockLogout).toHaveBeenCalled());
    });
});

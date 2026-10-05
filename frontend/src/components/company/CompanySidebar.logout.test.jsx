/**
 * @vitest-environment jsdom
 *
 * G-04 regression: company sidebar logout (covers both the Company Admin
 * and Recruiter roles, which share this component) must reach the backend
 * before clearing local auth state.
 */
import { MemoryRouter } from "react-router-dom";
import { fireEvent, render, screen, cleanup, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import CompanySidebar from "./CompanySidebar";

const mockLogout = vi.fn();
const mockSetSidebarOpen = vi.fn();
const mockLogoutFromServer = vi.fn();

vi.mock("../../hooks/useAuth", () => ({
    default: () => ({
        logout: mockLogout, companyProfile: { company_name: "Acme" }, user: { name: "Owner" },
        isRecruiter: false, recruiterProfile: null,
    }),
}));
vi.mock("../../context/PermissionsContext", () => ({ usePermissions: () => ({ hasFeature: () => true }) }));
vi.mock("../../api/client", () => ({ logoutFromServer: (...args) => mockLogoutFromServer(...args) }));

function setup() {
    return render(
        <MemoryRouter>
            <CompanySidebar sidebarOpen={true} setSidebarOpen={mockSetSidebarOpen} />
        </MemoryRouter>
    );
}

describe("CompanySidebar logout (G-04)", () => {
    afterEach(() => {
        cleanup();
        mockLogout.mockReset();
        mockSetSidebarOpen.mockReset();
        mockLogoutFromServer.mockReset();
        localStorage.clear();
    });

    it("calls the backend logout with the stored access token, then clears local state", async () => {
        localStorage.setItem("accessToken", "tok-company");
        mockLogoutFromServer.mockResolvedValue(undefined);
        setup();

        fireEvent.click(screen.getByText("Logout"));

        await waitFor(() => expect(mockLogout).toHaveBeenCalled());
        expect(mockLogoutFromServer).toHaveBeenCalledWith("tok-company");
        expect(mockSetSidebarOpen).toHaveBeenCalledWith(false);
    });

    it("still clears local state when the backend logout call fails", async () => {
        localStorage.setItem("accessToken", "tok-company");
        mockLogoutFromServer.mockRejectedValue(new Error("network down"));
        setup();

        fireEvent.click(screen.getByText("Logout"));

        await waitFor(() => expect(mockLogout).toHaveBeenCalled());
    });
});

/**
 * @vitest-environment jsdom
 *
 * G-04 regression: company navbar logout (covers both the Company Admin
 * and Recruiter roles) must reach the backend before clearing local auth
 * state, while preserving its existing immediate redirect to /login.
 */
import { MemoryRouter } from "react-router-dom";
import { fireEvent, render, screen, cleanup, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import CompanyNavbar from "./CompanyNavbar";

const mockLogout = vi.fn();
const mockNavigate = vi.fn();
const mockLogoutFromServer = vi.fn();

vi.mock("react-router-dom", async () => {
    const actual = await vi.importActual("react-router-dom");
    return { ...actual, useNavigate: () => mockNavigate };
});
vi.mock("../../context/ThemeContext", () => ({ useTheme: () => ({ toggleTheme: vi.fn(), theme: "light" }) }));
vi.mock("../../context/AuthContext", () => ({
    useAuthContext: () => ({
        user: { name: "Owner", email: "owner@example.com" }, logout: mockLogout,
        companyProfile: { company_name: "Acme" }, recruiterProfile: null, isRecruiter: false,
    }),
}));
vi.mock("../../api/client", () => ({ logoutFromServer: (...args) => mockLogoutFromServer(...args) }));

function setup() {
    return render(
        <MemoryRouter>
            <CompanyNavbar sidebarOpen={true} setSidebarOpen={vi.fn()} />
        </MemoryRouter>
    );
}

function openProfileAndClickLogout(container) {
    fireEvent.click(container.querySelector(".profile-trigger"));
    fireEvent.click(screen.getByText("Logout"));
}

describe("CompanyNavbar logout (G-04)", () => {
    afterEach(() => {
        cleanup();
        mockLogout.mockReset();
        mockNavigate.mockReset();
        mockLogoutFromServer.mockReset();
        localStorage.clear();
    });

    it("calls the backend logout with the stored access token, then clears local state and redirects", async () => {
        localStorage.setItem("accessToken", "tok-navbar");
        mockLogoutFromServer.mockResolvedValue(undefined);
        const { container } = setup();

        openProfileAndClickLogout(container);

        await waitFor(() => expect(mockLogout).toHaveBeenCalled());
        expect(mockLogoutFromServer).toHaveBeenCalledWith("tok-navbar");
        expect(mockNavigate).toHaveBeenCalledWith("/login");
    });

    it("still clears local state and redirects when the backend logout call fails", async () => {
        localStorage.setItem("accessToken", "tok-navbar");
        mockLogoutFromServer.mockRejectedValue(new Error("network down"));
        const { container } = setup();

        openProfileAndClickLogout(container);

        await waitFor(() => expect(mockLogout).toHaveBeenCalled());
        expect(mockNavigate).toHaveBeenCalledWith("/login");
    });
});

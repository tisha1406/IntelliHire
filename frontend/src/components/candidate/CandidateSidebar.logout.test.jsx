/**
 * @vitest-environment jsdom
 *
 * G-04 regression: candidate logout must reach the backend before clearing
 * local auth state (see src/api/client.logout.test.js for the shared
 * logoutFromServer helper's own behavior).
 */
import { MemoryRouter } from "react-router-dom";
import { fireEvent, render, screen, cleanup, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import CandidateSidebar from "./CandidateSidebar";

const mockLogout = vi.fn();
const mockLogoutFromServer = vi.fn();
const callOrder = [];

vi.mock("../../hooks/useSidebar", () => ({
    default: () => ({ collapsed: false, toggleSidebar: vi.fn() }),
}));
vi.mock("../../context/AuthContext", () => ({
    useAuthContext: () => ({ logout: mockLogout, user: { name: "Jane" } }),
}));
vi.mock("../../hooks/candidate/useCandidate", () => ({
    useCandidateDashboard: () => ({ data: { candidate_name: "Jane" }, isLoading: false }),
}));
vi.mock("../../api/client", () => ({
    logoutFromServer: (...args) => mockLogoutFromServer(...args),
}));

function setup() {
    return render(<MemoryRouter><CandidateSidebar /></MemoryRouter>);
}

describe("CandidateSidebar logout (G-04)", () => {
    afterEach(() => {
        cleanup();
        mockLogout.mockReset();
        mockLogoutFromServer.mockReset();
        localStorage.clear();
        callOrder.length = 0;
    });

    it("calls the backend logout with the stored access token, then clears local state", async () => {
        localStorage.setItem("accessToken", "tok-123");
        mockLogoutFromServer.mockImplementation(async () => { callOrder.push("server"); });
        mockLogout.mockImplementation(() => { callOrder.push("local"); });
        setup();

        fireEvent.click(screen.getByTitle("Log Out"));

        await waitFor(() => expect(mockLogout).toHaveBeenCalled());
        expect(mockLogoutFromServer).toHaveBeenCalledWith("tok-123");
        expect(callOrder).toEqual(["server", "local"]);
    });

    it("still clears local state when the backend logout call fails", async () => {
        localStorage.setItem("accessToken", "tok-123");
        mockLogoutFromServer.mockRejectedValue(new Error("network down"));
        setup();

        fireEvent.click(screen.getByTitle("Log Out"));

        await waitFor(() => expect(mockLogout).toHaveBeenCalled());
    });
});

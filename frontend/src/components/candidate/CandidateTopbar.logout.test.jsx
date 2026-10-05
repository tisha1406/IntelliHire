/**
 * @vitest-environment jsdom
 *
 * G-04 regression: candidate topbar logout must reach the backend before
 * clearing local auth state.
 */
import { MemoryRouter } from "react-router-dom";
import { fireEvent, render, screen, cleanup, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import CandidateTopbar from "./CandidateTopbar";

const mockLogout = vi.fn();
const mockLogoutFromServer = vi.fn();

vi.mock("../../hooks/useTheme", () => ({ default: () => ({ theme: "light", toggleTheme: vi.fn() }) }));
vi.mock("../../hooks/useSidebar", () => ({ default: () => ({ toggleSidebar: vi.fn() }) }));
vi.mock("../../context/AuthContext", () => ({
    useAuthContext: () => ({ logout: mockLogout, user: { name: "Jane", email: "jane@example.com" } }),
}));
vi.mock("../../hooks/candidate/useCandidate", () => ({
    useCandidateDashboard: () => ({ data: { candidate_name: "Jane" }, isLoading: false }),
    useCandidateNotifications: () => ({ data: { notifications: [], unread_count: 0 } }),
    useMarkNotificationsRead: () => ({ mutate: vi.fn() }),
}));
vi.mock("../../api/client", () => ({
    logoutFromServer: (...args) => mockLogoutFromServer(...args),
}));

function setup() {
    return render(<MemoryRouter><CandidateTopbar /></MemoryRouter>);
}

function openProfileAndClickLogout() {
    const [avatarBtn] = screen.getAllByText("J"); // avatar initial from "Jane"
    fireEvent.click(avatarBtn.closest("button"));
    fireEvent.click(screen.getByText("Log Out"));
}

describe("CandidateTopbar logout (G-04)", () => {
    afterEach(() => {
        cleanup();
        mockLogout.mockReset();
        mockLogoutFromServer.mockReset();
        localStorage.clear();
    });

    it("calls the backend logout with the stored access token, then clears local state", async () => {
        localStorage.setItem("accessToken", "tok-456");
        mockLogoutFromServer.mockResolvedValue(undefined);
        setup();

        openProfileAndClickLogout();

        await waitFor(() => expect(mockLogout).toHaveBeenCalled());
        expect(mockLogoutFromServer).toHaveBeenCalledWith("tok-456");
    });

    it("still clears local state when the backend logout call fails", async () => {
        localStorage.setItem("accessToken", "tok-456");
        mockLogoutFromServer.mockRejectedValue(new Error("network down"));
        setup();

        openProfileAndClickLogout();

        await waitFor(() => expect(mockLogout).toHaveBeenCalled());
    });
});

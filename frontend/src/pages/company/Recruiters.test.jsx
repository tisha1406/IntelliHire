/**
 * @vitest-environment jsdom
 *
 * F-01 regression: Recruiters.jsx and Team.jsx are consolidated into this
 * one page. These tests cover:
 *  - the B-02 status-casing fix (Team.jsx's own regression test, re-pointed
 *    at the merged page's grid view, which now renders that same DOM shape),
 *  - the role filter and search actually reaching the backend as
 *    `role`/`search` params (Team.jsx's server-side filtering),
 *  - the "Assign Campaigns" button inside the drawer, which previously
 *    called an undefined `handleAssignClick` in Recruiters.jsx and would
 *    have thrown a ReferenceError on click.
 *
 * Not re-tested here (unchanged, already covered by the pages' own prior
 * behavior and the live backend contract): suspend/activate/force-reset/
 * reset-password/delete and the create-recruiter flow.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import Recruiters from "./Recruiters";

vi.mock("framer-motion", () => ({
    motion: {
        div: ({ children, className, ...props }) => <div className={className} {...props}>{children}</div>,
        tr: ({ children, className, ...props }) => <tr className={className} {...props}>{children}</tr>,
        button: ({ children, className, ...props }) => <button className={className} {...props}>{children}</button>,
    },
    AnimatePresence: ({ children }) => <>{children}</>,
}));

const mockGetRecruiters = vi.fn();
const mockGetRecruiterCampaigns = vi.fn();
const mockGetRecruiterActivity = vi.fn();
const mockGetRecruiterCandidates = vi.fn();
const mockGetRecruiterInterviews = vi.fn();

vi.mock("../../services/company/recruiterManagementService", () => ({
    default: {
        getRecruiters: (...args) => mockGetRecruiters(...args),
        getRecruiterCampaigns: (...args) => mockGetRecruiterCampaigns(...args),
        getRecruiterActivity: (...args) => mockGetRecruiterActivity(...args),
        getRecruiterCandidates: (...args) => mockGetRecruiterCandidates(...args),
        getRecruiterInterviews: (...args) => mockGetRecruiterInterviews(...args),
    },
}));
vi.mock("../../services/company/campaignService", () => ({
    default: { getCampaigns: vi.fn().mockResolvedValue({ data: [] }) },
}));
vi.mock("../../services/company/analyticsService", () => ({
    default: { getRecruiterPerformance: vi.fn().mockResolvedValue({ data: [] }) },
}));

const MEMBERS = [
    { id: "1", name: "John Active", role: "Recruiter", status: "active", email: "john@active.com", phone: "123", department: "HR", designation: "Recruiter" },
    { id: "2", name: "Jane Inactive", role: "Hiring Manager", status: "inactive", email: "jane@inactive.com", phone: "456", department: "HR", designation: "Manager" },
];

function switchToGridView() {
    fireEvent.click(screen.getByTitle("Grid view"));
}

describe("Recruiters page (F-01 consolidation)", () => {
    afterEach(() => {
        cleanup();
        vi.clearAllMocks();
    });

    it("counts active status correctly with lowercase 'active' (B-02 regression)", async () => {
        mockGetRecruiters.mockResolvedValue({ data: MEMBERS });
        render(<Recruiters />);

        await waitFor(() => expect(screen.getAllByText("Total Members").length).toBeGreaterThan(0));
        expect(screen.getByText("2")).toBeTruthy(); // Total Members

        switchToGridView();

        await waitFor(() => {
            const dots = document.querySelectorAll(".team-member-status-dot");
            expect(dots.length).toBe(2);
        });
        expect(document.querySelectorAll(".team-member-status-dot.active").length).toBe(1);
        expect(document.querySelectorAll(".team-member-status-dot.inactive").length).toBe(1);
    });

    it("sends search and role filter to the backend as params", async () => {
        mockGetRecruiters.mockResolvedValue({ data: MEMBERS });
        render(<Recruiters />);
        await waitFor(() => expect(mockGetRecruiters).toHaveBeenCalled());

        fireEvent.change(screen.getByPlaceholderText("Search recruiters..."), { target: { value: "jane" } });
        await waitFor(() =>
            expect(mockGetRecruiters).toHaveBeenLastCalledWith(expect.objectContaining({ search: "jane" }))
        );

        fireEvent.change(screen.getByDisplayValue("All Roles"), { target: { value: "Hiring Manager" } });
        await waitFor(() =>
            expect(mockGetRecruiters).toHaveBeenLastCalledWith(
                expect.objectContaining({ search: "jane", role: "Hiring Manager" })
            )
        );
    });

    it("the drawer's Assign Campaigns button opens the assign modal instead of throwing (handleAssignClick regression)", async () => {
        mockGetRecruiters.mockResolvedValue({ data: MEMBERS });
        mockGetRecruiterActivity.mockResolvedValue({ data: [] });
        mockGetRecruiterCandidates.mockResolvedValue({ data: [] });
        mockGetRecruiterInterviews.mockResolvedValue({ data: [] });
        mockGetRecruiterCampaigns.mockResolvedValue({ data: [] });
        render(<Recruiters />);

        await waitFor(() => expect(screen.getByText("John Active")).toBeTruthy());
        fireEvent.click(screen.getByText("John Active"));

        await waitFor(() => expect(screen.getByText("Force Password Reset")).toBeTruthy());

        // Previously: onClick={() => handleAssignClick(selectedRecruiter)} -- undefined
        // function, so this click would throw a ReferenceError.
        expect(() => fireEvent.click(screen.getByText("Assign Campaigns"))).not.toThrow();

        await waitFor(() => expect(mockGetRecruiterCampaigns).toHaveBeenCalledWith("1"));
        await waitFor(() => expect(screen.getByText("Save Assignments")).toBeTruthy());
    });
});

/**
 * @vitest-environment jsdom
 *
 * Main Workflow Checkpoint 1 regression test.
 *
 * Root cause: the "Add Candidate" button/modal (the only frontend entry
 * point to POST /company/candidates/invite) was gated to isRecruiter only,
 * so a Company-role user had no way to invite a candidate anywhere in the
 * app, even though the backend endpoint already accepts both roles
 * (require_company_or_recruiter) and specs.md's own demo script expects a
 * working Company invite flow.
 */
import React from "react";
import { render, screen, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi, describe, it, expect, afterEach } from "vitest";
import Candidates from "./Candidates";

function renderWithRouter(ui) {
    return render(<MemoryRouter>{ui}</MemoryRouter>);
}

let mockAuth;

vi.mock("../../context/AuthContext", () => ({
    useAuthContext: () => mockAuth,
}));

vi.mock("../../services/company/candidateService", () => ({
    default: {
        getCandidates: vi.fn().mockResolvedValue({ data: [] }),
    },
}));

vi.mock("../../services/company/campaignService", () => ({
    default: {
        getCampaigns: vi.fn().mockResolvedValue({ data: [] }),
    },
}));

describe("Candidates.jsx — Add Candidate access (Checkpoint 1)", () => {
    afterEach(() => {
        cleanup();
        vi.clearAllMocks();
    });

    it("shows the Add Candidate button for a Company-role user", async () => {
        mockAuth = { isRecruiter: false, isCompany: true };
        renderWithRouter(<Candidates />);

        expect(await screen.findByRole("button", { name: /add candidate/i })).toBeTruthy();
    });

    it("still shows the Add Candidate button for a Recruiter (existing behavior unchanged)", async () => {
        mockAuth = { isRecruiter: true, isCompany: false };
        renderWithRouter(<Candidates />);

        expect(await screen.findByRole("button", { name: /add candidate/i })).toBeTruthy();
    });

    it("does not show the Add Candidate button for a Candidate-role user", async () => {
        mockAuth = { isRecruiter: false, isCompany: false };
        renderWithRouter(<Candidates />);

        // Let the initial fetchCandidates() effect settle before asserting absence.
        await screen.findByText("No candidates found");
        expect(screen.queryByRole("button", { name: /add candidate/i })).toBeNull();
    });
});

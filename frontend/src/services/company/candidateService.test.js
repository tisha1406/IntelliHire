/**
 * C-01 regression test.
 *
 * Candidates.jsx/CandidateDetails.jsx call candidateService.suspendCandidate,
 * .activateCandidate, .resetCredentials, .inviteCandidate, and
 * .bulkAssignCandidates — none of which were previously defined on this
 * service (calling them threw TypeError before ever reaching the network).
 * The backend routes already existed; this only adds the missing wrapper
 * methods using the exact same api.* pattern as the rest of this file.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockPatch = vi.fn();
const mockPost = vi.fn();
vi.mock("../api", () => ({
    default: {
        get: vi.fn(),
        post: (...args) => mockPost(...args),
        put: vi.fn(),
        delete: vi.fn(),
        patch: (...args) => mockPatch(...args),
    },
}));

import candidateService from "./candidateService";

describe("candidateService — previously-missing methods (C-01)", () => {
    beforeEach(() => {
        mockPatch.mockReset();
        mockPost.mockReset();
    });

    it("suspendCandidate PATCHes /company/candidates/{id}/suspend", () => {
        candidateService.suspendCandidate("cand_1");
        expect(mockPatch).toHaveBeenCalledWith("/company/candidates/cand_1/suspend");
    });

    it("activateCandidate PATCHes /company/candidates/{id}/activate", () => {
        candidateService.activateCandidate("cand_1");
        expect(mockPatch).toHaveBeenCalledWith("/company/candidates/cand_1/activate");
    });

    it("resetCredentials POSTs /company/candidates/{id}/reset-credentials", () => {
        candidateService.resetCredentials("cand_1");
        expect(mockPost).toHaveBeenCalledWith("/company/candidates/cand_1/reset-credentials");
    });

    it("inviteCandidate POSTs the form data to /company/candidates/invite", () => {
        const form = { name: "Jane", email: "jane@example.com", phone: "", campaign_id: "camp_1", interview_type: "ai" };
        candidateService.inviteCandidate(form);
        expect(mockPost).toHaveBeenCalledWith("/company/candidates/invite", form);
    });

    it("bulkAssignCandidates POSTs {candidate_ids, recruiter_id} to /company/candidates/bulk-assign", () => {
        candidateService.bulkAssignCandidates(["c1", "c2"], "recruiter_9");
        expect(mockPost).toHaveBeenCalledWith("/company/candidates/bulk-assign", {
            candidate_ids: ["c1", "c2"],
            recruiter_id: "recruiter_9",
        });
    });
});

describe("candidateService — dead methods removed (C-02)", () => {
    // sendInvite, downloadResume, and downloadReport all targeted backend
    // endpoints that never existed (/send-invite, /resume, /report under
    // /company/candidates/{id}) and had zero real callers anywhere in the
    // frontend. Per the C-02 product decision, they were removed rather than
    // given new backend routes — invitation already goes through
    // inviteCandidate(), and report download is session-based elsewhere
    // (services/company/reportService.js), not candidate-id based.
    it("no longer exposes sendInvite, downloadResume, or downloadReport", () => {
        expect(candidateService.sendInvite).toBeUndefined();
        expect(candidateService.downloadResume).toBeUndefined();
        expect(candidateService.downloadReport).toBeUndefined();
    });

    it("still exposes every live candidate service method", () => {
        const liveMethods = [
            "getCandidates", "getCandidate", "createCandidate", "updateCandidate",
            "deleteCandidate", "shortlistCandidate", "rejectCandidate", "scheduleInterview",
            "inviteCandidate", "suspendCandidate", "activateCandidate", "resetCredentials",
            "bulkAssignCandidates",
        ];
        for (const method of liveMethods) {
            expect(typeof candidateService[method]).toBe("function");
        }
    });
});

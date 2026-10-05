/**
 * @vitest-environment jsdom
 *
 * B-06 regression — API Trailing Slash standardization.
 *
 * Verifies that the specific API endpoints fixed in B-06 now include their
 * canonical trailing slashes to match the backend route definitions.
 */
import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

const frontendSrcDir = path.resolve(__dirname, "../../src");

function readSrc(relPath) {
    return fs.readFileSync(path.join(frontendSrcDir, relPath), "utf8");
}

describe("B-06 — API endpoint trailing slashes", () => {
    it("monitoring.js calls /admin/candidates/ and /admin/interviews/ with trailing slashes", () => {
        const src = readSrc("api/monitoring.js");
        // Ensure qs concatenation uses trailing slash
        expect(src).toContain("`/admin/candidates/${qs ? `?${qs}` : \"\"}`");
        expect(src).toContain("`/admin/interviews/${qs ? `?${qs}` : \"\"}`");
    });

    it("settings.js calls /admin/strategies/ and /admin/interview-modes/ with trailing slashes", () => {
        const src = readSrc("api/settings.js");
        expect(src).toContain("\"/admin/strategies/\"");
        expect(src).toContain("\"/admin/interview-modes/\"");
    });

    it("recruiterService.js calls getProfile and updateProfile with trailing slash", () => {
        const src = readSrc("services/recruiter/recruiterService.js");
        expect(src).toContain("api.get(`${BASE}/`)");
        expect(src).toContain("api.put(`${BASE}/`, data)");
    });
});

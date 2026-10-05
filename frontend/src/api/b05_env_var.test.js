/**
 * @vitest-environment jsdom
 *
 * B-05 regression — VITE_API_BASE_URL canonical variable.
 *
 * Verifies that the two production API clients (fetch-based client.js and
 * axios-based services/api.js) both read VITE_API_BASE_URL and NOT any
 * obsolete VITE_API_URL variable.
 *
 * The test checks source text rather than executing the modules, because
 * import.meta.env is resolved at Vite build time and cannot be overridden
 * per-test in JSDOM without a full Vite plugin mock — making source
 * verification the accurate, non-flaky approach for this specific task.
 */
import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

// __dirname resolves to frontend/src/api; go up one level to reach frontend/src
const srcDir = path.resolve(__dirname, "../");

function readSrc(relPath) {
    return fs.readFileSync(path.join(srcDir, relPath), "utf8");
}

describe("B-05 — VITE_API_BASE_URL is the canonical API base URL variable", () => {
    it("api/client.js uses VITE_API_BASE_URL and NOT VITE_API_URL", () => {
        const src = readSrc("api/client.js");
        expect(src).toContain("VITE_API_BASE_URL");
        expect(src).not.toContain("VITE_API_URL");
    });

    it("api/reports.js uses VITE_API_BASE_URL and NOT VITE_API_URL", () => {
        const src = readSrc("api/reports.js");
        expect(src).toContain("VITE_API_BASE_URL");
        expect(src).not.toContain("VITE_API_URL");
    });

    it("services/api.js uses VITE_API_BASE_URL and NOT a bare hard-coded URL as its only baseURL value", () => {
        const src = readSrc("services/api.js");
        expect(src).toContain("VITE_API_BASE_URL");
        // The only hard-coded URL should be the fallback after ||, not the
        // sole value. A line like: baseURL: "http://..." with no env var is wrong.
        expect(src).not.toMatch(/baseURL:\s*["']http:\/\//);
    });
});

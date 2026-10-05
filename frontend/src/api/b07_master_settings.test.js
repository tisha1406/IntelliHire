/**
 * @vitest-environment jsdom
 *
 * B-07 regression test — PATCH /admin/settings/master contract.
 *
 * Verifies that the dead/unwired updateMasterSettings function has been
 * removed, preventing 404/405 errors by eliminating the invalid contract.
 */
import { describe, it, expect } from "vitest";
import { SettingsAPI } from "./settings";

describe("B-07 — updateMasterSettings", () => {
    it("SettingsAPI no longer exposes the dead updateMasterSettings function", () => {
        expect(SettingsAPI).toBeDefined();
        expect(SettingsAPI.updateMasterSettings).toBeUndefined();
    });

    it("SettingsAPI still exposes the valid getMasterSettings function", () => {
        expect(typeof SettingsAPI.getMasterSettings).toBe("function");
    });
});

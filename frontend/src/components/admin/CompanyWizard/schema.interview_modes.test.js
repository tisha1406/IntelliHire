/**
 * Regression for the Admin Company Provisioning blocker.
 *
 * Root cause: GET /admin/settings/master used to return
 * interview_modes[i].name = null (backend read the wrong field,
 * `display_name` instead of `name`). CompanyWizard/index.jsx does
 * `allowed_interview_modes: config.interview_modes.map(m => m.name)` on
 * every new provisioning session, so the form was seeded with
 * [null, null, null, null] the moment it loaded -- which companySchema's
 * `z.array(z.string())` rejects, silently blocking handleSubmit(onSubmit)
 * before POST /admin/companies was ever called (no visible error, since the
 * Interview Modes tab has no error indicator in the left nav).
 *
 * The backend fix (`m.get("name")` instead of `m.get("display_name")`) is
 * proven server-side in
 * backend/tests/integration/test_admin_master_settings_interview_modes.py.
 * This test proves the other half of the contract: once given real,
 * non-null names, the frontend schema that previously blocked submission
 * now accepts them.
 */
import { describe, it, expect } from "vitest";
import { companySchema, defaultValues } from "./schema";

function buildFormData(interviewModeNames) {
    return {
        ...defaultValues,
        general: { ...defaultValues.general, name: "Acme Corp", contact_email: "admin@acme.com" },
        allowed_interview_modes: interviewModeNames,
    };
}

describe("companySchema — interview mode names (provisioning blocker regression)", () => {
    it("rejects the pre-fix shape: null names from config.interview_modes.map(m => m.name)", () => {
        const preFixNames = [null, null, null, null]; // what the buggy backend used to return
        const result = companySchema.safeParse(buildFormData(preFixNames));

        expect(result.success).toBe(false);
    });

    it("accepts the post-fix shape: real interview_mode_definitions.name values", () => {
        const postFixNames = ["Balanced", "Structured", "Technical", "Deep Technical"];
        const result = companySchema.safeParse(buildFormData(postFixNames));

        expect(result.success).toBe(true);
        expect(result.data.allowed_interview_modes).toEqual(postFixNames);
    });

    it("still accepts an empty interview-modes selection (unrelated to this bug)", () => {
        const result = companySchema.safeParse(buildFormData([]));

        expect(result.success).toBe(true);
    });
});

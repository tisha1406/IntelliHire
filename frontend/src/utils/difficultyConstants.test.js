import { describe, it, expect } from "vitest";
import { DIFFICULTY_LEVELS } from "./difficultyConstants";

describe("DIFFICULTY_LEVELS (B-03 regression)", () => {
    it("matches backend DifficultyLevel exactly: easy, medium, hard — no adaptive", () => {
        const values = DIFFICULTY_LEVELS.map((o) => o.value);
        expect(values).toEqual(["easy", "medium", "hard"]);
        expect(values).not.toContain("adaptive");
    });

    it("is the single source both NewCampaign.jsx and EditCampaign.jsx import (no per-page duplication)", async () => {
        const newCampaignSource = await import("fs").then((fs) =>
            fs.readFileSync(new URL("../pages/company/NewCampaign.jsx", import.meta.url), "utf-8")
        );
        const editCampaignSource = await import("fs").then((fs) =>
            fs.readFileSync(new URL("../pages/company/EditCampaign.jsx", import.meta.url), "utf-8")
        );
        expect(newCampaignSource).toContain('from "../../utils/difficultyConstants"');
        expect(editCampaignSource).toContain('from "../../utils/difficultyConstants"');
        expect(newCampaignSource).not.toMatch(/label:\s*"Adaptive"/);
        expect(editCampaignSource).not.toMatch(/label:\s*"Adaptive"/);
    });
});

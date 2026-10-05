/**
 * B-09 regression test.
 *
 * Contract being verified: ChangeSubscription.jsx computes
 * allowed_languages/allowed_voices/allowed_llm_tiers/allowed_interview_modes
 * and passes them into subscriptionApi.changeSubscription(...)/
 * verifyChangePayment(...). The backend's SubscriptionChangeRequest /
 * ChangePaymentVerifyRequest (backend/app/api/company/company_subscription.py)
 * already accept all four fields as optional — the bug was purely that these
 * wrapper functions' signatures didn't declare/forward the extra arguments,
 * so they were silently dropped before ever reaching the HTTP request body.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockPost = vi.fn();
const mockGet = vi.fn();
vi.mock("../services/api", () => ({
    default: { post: (...args) => mockPost(...args), get: (...args) => mockGet(...args) },
}));

import subscriptionApi from "./subscription";

describe("subscriptionApi — AI-config field forwarding (B-09)", () => {
    beforeEach(() => {
        mockPost.mockReset();
        mockPost.mockResolvedValue({ data: {} });
    });

    it("changeSubscription forwards all four AI-config fields in the request body", async () => {
        await subscriptionApi.changeSubscription(
            { reports: true },
            { max_recruiters: 10 },
            "annual",
            ["en", "es"],
            ["shubh", "simran"],
            ["standard"],
            ["technical", "mixed"]
        );

        expect(mockPost).toHaveBeenCalledTimes(1);
        const [url, body] = mockPost.mock.calls[0];
        expect(url).toBe("/company/subscription/change");
        expect(body).toEqual({
            features: { reports: true },
            limits: { max_recruiters: 10 },
            billing_cycle: "annual",
            allowed_languages: ["en", "es"],
            allowed_voices: ["shubh", "simran"],
            allowed_llm_tiers: ["standard"],
            allowed_interview_modes: ["technical", "mixed"],
        });
    });

    it("verifyChangePayment forwards all four AI-config fields in the request body", async () => {
        const pricing = { is_upgrade: true, difference: 500, currency: "INR" };
        await subscriptionApi.verifyChangePayment(
            "pay_123",
            "order_456",
            { reports: true },
            { max_recruiters: 10 },
            "annual",
            pricing,
            ["en"],
            ["shubh"],
            ["standard"],
            ["technical"]
        );

        expect(mockPost).toHaveBeenCalledTimes(1);
        const [url, body] = mockPost.mock.calls[0];
        expect(url).toBe("/company/subscription/change/verify");
        expect(body).toEqual({
            payment_id: "pay_123",
            order_id: "order_456",
            features: { reports: true },
            limits: { max_recruiters: 10 },
            billing_cycle: "annual",
            pricing,
            allowed_languages: ["en"],
            allowed_voices: ["shubh"],
            allowed_llm_tiers: ["standard"],
            allowed_interview_modes: ["technical"],
        });
    });

    it("changeSubscription still works with no AI-config fields (optional, backward compatible)", async () => {
        await subscriptionApi.changeSubscription({ reports: true }, { max_recruiters: 10 }, "annual");

        const [, body] = mockPost.mock.calls[0];
        expect(body.features).toEqual({ reports: true });
        expect(body.billing_cycle).toBe("annual");
        // Serialized as undefined — JSON.stringify (axios's default
        // transform) omits these keys entirely, matching the backend's
        // Optional[...] = None default.
        expect(body.allowed_languages).toBeUndefined();
    });
});

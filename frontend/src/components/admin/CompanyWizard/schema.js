import { z } from "zod";

export const companySchema = z.object({
    general: z.object({
        name: z.string().min(2, "Company name must be at least 2 characters"),
        contact_email: z.string().email("Invalid email format"),
        industry: z.string().optional(),
        size: z.string().optional(),
        website: z.string().url("Must be a valid URL").optional().or(z.literal("")),
        phone: z.string().optional(),
        country: z.string().optional(),
        timezone: z.string().optional(),
        currency: z.string().optional(),
        address: z.string().optional(),
        contact_person: z.string().optional(),
        tax_id: z.string().optional(),
        notes: z.string().optional(),
        logo_url: z.string().optional(),
    }),
    subscription: z.object({
        plan: z.string().min(1, "Plan is required"),
        status: z.string().min(1, "Status is required"),
        billing_cycle: z.string(),
        expiry_date: z.string().optional().or(z.literal("")),
        seat_count: z.coerce.number().min(1, "Must have at least 1 seat")
    }),
    limits: z.object({
        max_recruiters: z.coerce.number().min(1),
        max_candidates: z.coerce.number().min(1),
        max_campaigns: z.coerce.number().min(1),
        monthly_interviews: z.coerce.number().min(1),
        concurrent_interviews: z.coerce.number().min(1),
        storage_limit_gb: z.coerce.number().min(0.1),
        api_requests_per_month: z.coerce.number().min(0),
        ai_credits: z.coerce.number().min(0),
        resume_uploads: z.coerce.number().min(0)
    }),
    security: z.object({
        login_enabled: z.boolean(),
        mfa_required: z.boolean(),
        password_policy: z.string(),
        session_timeout_minutes: z.coerce.number().min(5),
        jwt_lifetime_hours: z.coerce.number().min(1),
        refresh_token_lifetime_days: z.coerce.number().min(1),
        sso_enabled: z.boolean(),
        allowed_domains: z.array(z.string()).default([]),
        ip_whitelist: z.array(z.string()).default([]),
        concurrent_sessions_allowed: z.coerce.number().min(1),
        remember_me_allowed: z.boolean(),
        login_attempts_before_lockout: z.coerce.number().min(3)
    }),
    features: z.record(z.boolean()).default({}),
    allowed_languages: z.array(z.string()).default([]),
    allowed_voices: z.array(z.string()).default([]),
    allowed_strategies: z.array(z.string()).default([]),
    allowed_interview_modes: z.array(z.string()).default([]),
    allowed_llm_tiers: z.array(z.string()).default([])
});

export const defaultValues = {
    general: {
        name: "",
        contact_email: "",
        industry: "",
        size: "",
        website: "",
        phone: "",
        country: "",
        timezone: "",
        currency: "",
        address: "",
        contact_person: "",
        tax_id: "",
        notes: "",
        logo_url: ""
    },
    subscription: {
        plan: "Enterprise",
        status: "active",
        billing_cycle: "annual",
        expiry_date: "",
        seat_count: 5
    },
    limits: {
        max_recruiters: 5,
        max_candidates: 500,
        max_campaigns: 10,
        monthly_interviews: 100,
        concurrent_interviews: 5,
        storage_limit_gb: 10.0,
        api_requests_per_month: 10000,
        ai_credits: 1000,
        resume_uploads: 5000
    },
    security: {
        login_enabled: true,
        mfa_required: false,
        password_policy: "standard",
        session_timeout_minutes: 60,
        jwt_lifetime_hours: 24,
        refresh_token_lifetime_days: 7,
        sso_enabled: false,
        allowed_domains: [],
        ip_whitelist: [],
        concurrent_sessions_allowed: 3,
        remember_me_allowed: true,
        login_attempts_before_lockout: 5
    },
    features: {},
    allowed_languages: [],
    allowed_voices: [],
    allowed_strategies: [],
    allowed_interview_modes: [],
    allowed_llm_tiers: []
};

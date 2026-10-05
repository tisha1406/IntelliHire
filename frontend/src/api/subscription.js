import api from "../services/api";

const subscriptionApi = {
    getCurrentSubscription: () => api.get("/company/subscription").then(res => res.data),
    
    getOptions: () => api.get("/company/subscription/options").then(res => res.data),
    
    calculatePrice: (features, limits, billing_cycle, is_upgrade = false) => 
        api.post("/company/subscription/calculate", { features, limits, billing_cycle, is_upgrade }).then(res => res.data),
        
    // allowed_languages/allowed_voices/allowed_llm_tiers/allowed_interview_modes
    // are optional (backend: SubscriptionChangeRequest) — the AI-config fields
    // a company narrows/widens as part of a plan change. Previously this
    // function's signature only declared the first 3 params, so callers
    // passing these (e.g. ChangeSubscription.jsx) had them silently dropped.
    changeSubscription: (features, limits, billing_cycle, allowed_languages, allowed_voices, allowed_llm_tiers, allowed_interview_modes) =>
        api.post("/company/subscription/change", {
            features, limits, billing_cycle,
            allowed_languages, allowed_voices, allowed_llm_tiers, allowed_interview_modes,
        }).then(res => res.data),

    createChangePayment: (amount, currency = "INR") =>
        api.post("/company/subscription/change/payment", { amount, currency }).then(res => res.data),

    // Same optional AI-config fields as changeSubscription above (backend:
    // ChangePaymentVerifyRequest).
    verifyChangePayment: (payment_id, order_id, features, limits, billing_cycle, pricing, allowed_languages, allowed_voices, allowed_llm_tiers, allowed_interview_modes) =>
        api.post("/company/subscription/change/verify", {
            payment_id, order_id, features, limits, billing_cycle, pricing,
            allowed_languages, allowed_voices, allowed_llm_tiers, allowed_interview_modes,
        }).then(res => res.data),
        
    createRenewalPayment: (amount, currency = "INR") => 
        api.post("/company/subscription/renew/payment", { amount, currency }).then(res => res.data),
        
    verifyRenewalPayment: (payment_id, order_id) => 
        api.post("/company/subscription/renew/verify", { payment_id, order_id }).then(res => res.data),
        
    confirmSubscription: () => 
        api.post("/company/subscription/confirm").then(res => res.data),
        
    createPaymentOrder: (amount, currency = "INR") => 
        api.post("/company/subscription/payment/order", { amount, currency }).then(res => res.data),
        
    verifyPayment: (payment_id, order_id) => 
        api.post("/company/subscription/payment/verify", { payment_id, order_id }).then(res => res.data),
        
    getPaymentHistory: () => api.get("/company/subscription/payments").then(res => res.data),
    
    getSubscriptionHistory: () => api.get("/company/subscription/history").then(res => res.data),
};

export default subscriptionApi;

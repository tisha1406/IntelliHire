import api from "../services/api";

const subscriptionApi = {
    getCurrentSubscription: () => api.get("/company/subscription").then(res => res.data),
    
    getOptions: () => api.get("/company/subscription/options").then(res => res.data),
    
    calculatePrice: (features, limits, billing_cycle, is_upgrade = false) => 
        api.post("/company/subscription/calculate", { features, limits, billing_cycle, is_upgrade }).then(res => res.data),
        
    changeSubscription: (features, limits, billing_cycle) => 
        api.post("/company/subscription/change", { features, limits, billing_cycle }).then(res => res.data),
        
    createChangePayment: (amount, currency = "INR") => 
        api.post("/company/subscription/change/payment", { amount, currency }).then(res => res.data),
        
    verifyChangePayment: (payment_id, order_id, features, limits, billing_cycle, pricing) => 
        api.post("/company/subscription/change/verify", { payment_id, order_id, features, limits, billing_cycle, pricing }).then(res => res.data),
        
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

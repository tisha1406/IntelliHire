import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import subscriptionApi from "../../../api/subscription";
import { useAuthContext } from "../../../context/AuthContext";
import PageHeader from "../../../components/common/PageHeader";
import PaymentGateway from "../../../components/company/subscription/PaymentGateway";

export default function RenewSubscription() {
    const navigate = useNavigate();
    const { companyProfile } = useAuthContext();
    
    const [subData, setSubData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);
    
    const [billingCycle, setBillingCycle] = useState("annual");
    const [pricing, setPricing] = useState(null);
    const [calculating, setCalculating] = useState(false);

    const [isGatewayOpen, setIsGatewayOpen] = useState(false);
    const [orderId, setOrderId] = useState(null);

    useEffect(() => {
        const fetchSub = async () => {
            try {
                const res = await subscriptionApi.getCurrentSubscription();
                const data = res.data || res;
                setSubData(data);
                setBillingCycle(data?.pending_subscription?.billing_cycle || data?.subscription?.billing_cycle || "annual");
            } catch (err) {
                console.error("Failed to load subscription:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchSub();
    }, [companyProfile]);
    
    useEffect(() => {
        if (!loading && subData) {
            calculatePrice();
        }
    }, [billingCycle, subData]);

    const calculatePrice = async () => {
        if (!subData) return;
        setCalculating(true);
        try {
            // Use pending config if it exists, otherwise current config
            const features = subData.pending_subscription?.features || subData.features;
            const limits = subData.pending_subscription?.limits || subData.limits;
            
            const res = await subscriptionApi.calculatePrice(features, limits, billingCycle, false);
            setPricing(res.data || res);
        } catch (err) {
            console.error("Failed to calculate price", err);
        } finally {
            setCalculating(false);
        }
    };

    const handleRenewClick = async () => {
        if (!pricing) return;
        setProcessing(true);
        try {
            // Create payment order
            const orderRes = await subscriptionApi.createRenewalPayment(pricing.total, pricing.currency);
            const order = orderRes.data || orderRes;
            
            setOrderId(order.id);
            setIsGatewayOpen(true);
        } catch (err) {
            console.error("Renewal failed", err);
            alert("An error occurred during checkout.");
        } finally {
            setProcessing(false);
        }
    };

    const handleGatewaySuccess = async (paymentId, orderId) => {
        setIsGatewayOpen(false);
        setProcessing(true);
        try {
            await subscriptionApi.verifyRenewalPayment(paymentId, orderId);
            alert("Subscription Renewed!");
            navigate("/company/subscription");
        } catch (err) {
            alert(err?.response?.data?.detail || "Payment Verification Failed. Contact support.");
        } finally {
            setProcessing(false);
        }
    };

    const handleGatewayCancel = () => {
        setIsGatewayOpen(false);
    };

    if (loading || !subData) return <div style={{ padding: "2rem" }}>Loading...</div>;

    const { subscription, pending_subscription } = subData;
    const isExpired = subscription?.status === "expired";

    return (
        <div style={{ maxWidth: 800, margin: "0 auto", padding: "2rem" }}>
            <PageHeader 
                title={isExpired ? "Renew Expired Subscription" : "Renew Subscription"}
                subtitle="Extend your subscription billing cycle."
                onBack={() => navigate("/company/subscription")}
            />
            
            {pending_subscription && (
                <div style={{ background: "var(--warning-light)", color: "var(--warning-dark)", padding: "1rem", borderRadius: "8px", marginBottom: "1.5rem", border: "1px solid var(--warning)" }}>
                    <strong>Pending Downgrade Notice:</strong> You have a pending downgrade scheduled. Renewing now will apply the new reduced limits and pricing.
                </div>
            )}
            
            <div style={{ background: "var(--surface)", padding: "1.5rem", borderRadius: "8px", marginBottom: "2rem", boxShadow: "0 2px 4px rgba(0,0,0,0.05)" }}>
                <h3>Select Renewal Cycle</h3>
                <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "1rem" }}>Choose how long you'd like to extend your subscription.</p>
                
                <select 
                    className="form-control" 
                    style={{ width: "100%", padding: "0.75rem", marginBottom: "1.5rem" }}
                    value={billingCycle} 
                    onChange={(e) => setBillingCycle(e.target.value)}
                >
                    <option value="1_year">1 Year</option>
                    <option value="2_years">2 Years</option>
                    <option value="3_years">3 Years</option>
                    <option value="monthly">Monthly</option>
                </select>
                
                <hr style={{ border: "0", borderTop: "1px solid var(--border)", margin: "1.5rem 0" }} />
                
                <h3 style={{ marginBottom: "1rem" }}>Renewal Summary</h3>
                <div style={{ background: "var(--background)", padding: "1rem", borderRadius: "8px" }}>
                    {calculating || !pricing ? (
                        <div style={{ textAlign: "center" }}>Calculating...</div>
                    ) : (
                        <>
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                                <span>Base Price</span>
                                <span>₹{pricing.base_price.toFixed(2)}</span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                                <span>Features Cost</span>
                                <span>₹{pricing.feature_cost.toFixed(2)}</span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                                <span>Limits Cost</span>
                                <span>₹{pricing.limit_cost.toFixed(2)}</span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                                <span>Tax (18%)</span>
                                <span>₹{pricing.tax.toFixed(2)}</span>
                            </div>
                            <hr style={{ border: "0", borderTop: "1px solid var(--border)", margin: "0.5rem 0" }} />
                            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "1rem", fontSize: "1.2rem", fontWeight: "bold" }}>
                                <span>Total to Pay</span>
                                <span>₹{pricing.total.toFixed(2)}</span>
                            </div>
                        </>
                    )}
                </div>
            </div>

            <button 
                className="btn btn-primary" 
                style={{ width: "100%", padding: "1rem", fontSize: "1.1rem" }}
                disabled={calculating || processing || !pricing}
                onClick={handleRenewClick}
            >
                {processing ? "Processing..." : `Pay ₹${pricing?.total?.toFixed(2) || "0.00"}`}
            </button>

            <PaymentGateway 
                isOpen={isGatewayOpen}
                onClose={handleGatewayCancel}
                onSuccess={handleGatewaySuccess}
                amount={pricing?.total || 0}
                orderId={orderId}
                pricing={pricing}
            />
        </div>
    );
}

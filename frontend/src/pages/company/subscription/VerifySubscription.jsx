import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import subscriptionApi from "../../../api/subscription";
import { useAuthContext } from "../../../context/AuthContext";
import { FaCheckCircle, FaRupeeSign, FaServer, FaShieldAlt } from "react-icons/fa";

export default function VerifySubscription() {
    const navigate = useNavigate();
    const { companyProfile, setCompanyProfile } = useAuthContext();
    const [loading, setLoading] = useState(false);
    const [sub, setSub] = useState(null);
    const [pricing, setPricing] = useState(null);

    useEffect(() => {
        const fetchSub = async () => {
            let currentSub = companyProfile?.subscription;
            if (!currentSub) {
                try {
                    const res = await subscriptionApi.getCurrentSubscription();
                    currentSub = res.data?.data?.subscription || res.data?.subscription || res.data?.data || res.data;
                } catch (err) {
                    console.error("Failed to load subscription:", err);
                    return;
                }
            }
            setSub(currentSub);

            if (currentSub?.pricing) {
                setPricing(currentSub.pricing);
            } else if (companyProfile?.features && companyProfile?.limits) {
                try {
                    const priceRes = await subscriptionApi.calculatePrice(
                        companyProfile.features, 
                        companyProfile.limits, 
                        currentSub?.billing_cycle || "annual",
                        false
                    );
                    setPricing(priceRes.data || priceRes);
                } catch (err) {
                    console.error("Failed to calculate price:", err);
                }
            }
        };
        fetchSub();
    }, [companyProfile]);

    const handleConfirm = async () => {
        setLoading(true);
        try {
            await subscriptionApi.confirmSubscription();
            setCompanyProfile(prev => ({
                ...prev, 
                subscription: { ...(prev?.subscription || {}), status: "pending_payment" }
            }));
            navigate("/company/subscription/payment");
        } catch (err) {
            alert(err.message || "Failed to confirm subscription.");
        } finally {
            setLoading(false);
        }
    };

    if (!sub) return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", background: "var(--background)" }}>
            <div className="spinner" style={{ width: "40px", height: "40px", border: "4px solid rgba(0,0,0,0.1)", borderLeftColor: "var(--primary)", borderRadius: "50%", animation: "spin 1s linear infinite" }}></div>
            <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
        </div>
    );

    return (
        <div style={{ 
            minHeight: "100vh", 
            background: "var(--background)", 
            display: "flex", 
            alignItems: "center", 
            justifyContent: "center", 
            padding: "2rem" 
        }}>
            <style>{`
                @keyframes fadeInUp {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .verify-card {
                    background: var(--surface);
                    backdrop-filter: blur(16px);
                    -webkit-backdrop-filter: blur(16px);
                    border: 1px solid var(--border);
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
                    border-radius: 24px;
                    padding: 3rem;
                    width: 100%;
                    max-width: 850px;
                    animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
                }
                .verify-header {
                    text-align: center;
                    margin-bottom: 2.5rem;
                }
                .verify-header h1 {
                    font-size: 2.2rem;
                    font-weight: 800;
                    background: linear-gradient(90deg, var(--primary), #6366f1);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 0.5rem;
                }
                .verify-header p {
                    color: var(--text-muted);
                    font-size: 1.1rem;
                }
                .info-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 2rem;
                    margin-bottom: 2.5rem;
                }
                .info-panel {
                    background: var(--background);
                    border-radius: 16px;
                    padding: 1.5rem;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                    border: 1px solid var(--border);
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }
                .info-panel:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 10px 25px rgba(0,0,0,0.06);
                }
                .info-panel h3 {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    color: var(--text);
                    margin-bottom: 1.5rem;
                    font-size: 1.2rem;
                    border-bottom: 1px solid var(--border);
                    padding-bottom: 0.8rem;
                }
                .price-row {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 1rem;
                    color: var(--text);
                    font-size: 1.05rem;
                }
                .price-row.total {
                    font-weight: 800;
                    font-size: 1.4rem;
                    color: var(--primary);
                    margin-top: 1.5rem;
                    padding-top: 1.5rem;
                    border-top: 2px dashed var(--border);
                }
                .btn-verify {
                    width: 100%;
                    padding: 1.2rem;
                    font-size: 1.1rem;
                    font-weight: 600;
                    background: linear-gradient(135deg, var(--primary), #4f46e5);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 10px 20px rgba(79, 70, 229, 0.3);
                }
                .btn-verify:hover:not(:disabled) {
                    transform: translateY(-2px);
                    box-shadow: 0 15px 25px rgba(79, 70, 229, 0.4);
                }
                .btn-verify:disabled {
                    opacity: 0.7;
                    cursor: not-allowed;
                }
                .checkbox-wrapper {
                    display: flex;
                    align-items: center;
                    gap: 0.8rem;
                    margin: 2rem 0;
                    padding: 1rem;
                    background: var(--background);
                    border-radius: 12px;
                    border: 1px solid var(--border);
                }
                .checkbox-wrapper input[type="checkbox"] {
                    width: 20px;
                    height: 20px;
                    accent-color: var(--primary);
                    cursor: pointer;
                }
            `}</style>
            
            <div className="verify-card">
                <div className="verify-header">
                    <h1>Verify Your Subscription</h1>
                    <p>Please review the subscription configuration prepared for your workspace.</p>
                </div>

                <div className="info-grid">
                    <div className="info-panel">
                        <h3><FaServer style={{ color: "var(--primary)" }} /> Plan Configuration</h3>
                        <div className="price-row">
                            <span style={{ color: "var(--text-muted)" }}>Selected Plan</span>
                            <span style={{ fontWeight: 600 }}>{sub?.plan || "Premium"}</span>
                        </div>
                        <div className="price-row">
                            <span style={{ color: "var(--text-muted)" }}>Billing Cycle</span>
                            <span style={{ fontWeight: 600, textTransform: "capitalize" }}>{(sub?.billing_cycle || "annual").replace("_", " ")}</span>
                        </div>
                        <div className="price-row">
                            <span style={{ color: "var(--text-muted)" }}>Recruiter Seats</span>
                            <span style={{ fontWeight: 600 }}>{sub?.seat_count || companyProfile?.limits?.max_recruiters || 5} Included</span>
                        </div>
                    </div>

                    <div className="info-panel">
                        <h3><FaRupeeSign style={{ color: "var(--success)" }} /> Price Breakdown</h3>
                        <div className="price-row">
                            <span>Base Platform</span>
                            <span>₹{pricing?.base_price?.toFixed(2)}</span>
                        </div>
                        <div className="price-row">
                            <span>Features Cost</span>
                            <span>₹{pricing?.feature_cost?.toFixed(2)}</span>
                        </div>
                        <div className="price-row">
                            <span>Limits Addition</span>
                            <span>₹{pricing?.limit_cost?.toFixed(2)}</span>
                        </div>
                        
                        <div className="price-row" style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid var(--border)", color: "var(--text-muted)" }}>
                            <span>Tax (18% GST)</span>
                            <span>₹{pricing?.tax?.toFixed(2)}</span>
                        </div>
                        
                        <div className="price-row total">
                            <span>Total Due</span>
                            <span>₹{pricing?.total?.toFixed(2)}</span>
                        </div>
                    </div>
                </div>

                <div className="checkbox-wrapper">
                    <input type="checkbox" id="agree" required />
                    <label htmlFor="agree" style={{ color: "var(--text)", cursor: "pointer", fontWeight: 500 }}>
                        <FaShieldAlt style={{ color: "var(--success)", marginRight: "0.5rem", verticalAlign: "middle" }} />
                        I have reviewed the above configuration and agree to proceed with the subscription.
                    </label>
                </div>

                <button 
                    className="btn-verify" 
                    onClick={() => {
                        if (!document.getElementById("agree").checked) {
                            alert("Please agree to the configuration before proceeding.");
                            return;
                        }
                        handleConfirm();
                    }}
                    disabled={loading}
                >
                    {loading ? "Confirming..." : "Confirm & Continue to Payment"}
                </button>
            </div>
        </div>
    );
}

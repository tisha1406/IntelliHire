import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import subscriptionApi from "../../../api/subscription";
import { useAuthContext } from "../../../context/AuthContext";
import PageHeader from "../../../components/common/PageHeader";
import { FaCheck, FaTimes, FaSpinner, FaRocket, FaShieldAlt } from "react-icons/fa";
import PaymentGateway from "../../../components/company/subscription/PaymentGateway";

export default function ChangeSubscription() {
    const navigate = useNavigate();
    const { companyProfile, refreshUser } = useAuthContext();
    
    const [options, setOptions] = useState(null);
    const [loading, setLoading] = useState(true);
    
    const [features, setFeatures] = useState({});
    const [limits, setLimits] = useState({});
    const [billingCycle, setBillingCycle] = useState("annual");
    
    const [allowedLanguages, setAllowedLanguages] = useState([]);
    const [allowedVoices, setAllowedVoices] = useState([]);
    const [allowedLlmTiers, setAllowedLlmTiers] = useState([]);
    const [allowedInterviewModes, setAllowedInterviewModes] = useState([]);
    
    const [pricing, setPricing] = useState(null);
    const [calculating, setCalculating] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [isGatewayOpen, setIsGatewayOpen] = useState(false);
    const [orderId, setOrderId] = useState(null);

    useEffect(() => {
        const fetchOptions = async () => {
            try {
                const res = await subscriptionApi.getOptions();
                setOptions(res.data || res);
                
                // Init state from current profile
                setFeatures(companyProfile?.features || {});
                setLimits(companyProfile?.limits || {});
                setBillingCycle(companyProfile?.subscription?.billing_cycle || "annual");
                
                setAllowedLanguages(companyProfile?.allowed_languages || []);
                setAllowedVoices(companyProfile?.allowed_voices || []);
                setAllowedLlmTiers(companyProfile?.allowed_llm_tiers || []);
                setAllowedInterviewModes(companyProfile?.allowed_interview_modes || []);
            } catch (err) {
                console.error("Failed to load options", err);
            } finally {
                setLoading(false);
            }
        };
        fetchOptions();
    }, [companyProfile]);

    useEffect(() => {
        if (!loading && options) {
            calculatePrice();
        }
    }, [features, limits, billingCycle]);

    const calculatePrice = async () => {
        setCalculating(true);
        try {
            const res = await subscriptionApi.calculatePrice(features, limits, billingCycle, true);
            setPricing(res.data || res);
        } catch (err) {
            console.error("Failed to calculate price", err);
        } finally {
            setCalculating(false);
        }
    };

    const toggleFeature = (feat) => {
        setFeatures(prev => ({ ...prev, [feat]: !prev[feat] }));
    };

    const handleLimitChange = (limitKey, val) => {
        setLimits(prev => ({ ...prev, [limitKey]: parseInt(val, 10) }));
    };
    
    const handleArrayToggle = (item, currentList, setter) => {
        if (currentList.includes(item)) {
            setter(currentList.filter(i => i !== item));
        } else {
            setter([...currentList, item]);
        }
    };
    
    const handleProceed = async () => {
        if (!pricing) return;
        setProcessing(true);
        try {
            const reqData = {
                features,
                limits,
                billing_cycle: billingCycle,
                allowed_languages: allowedLanguages,
                allowed_voices: allowedVoices,
                allowed_llm_tiers: allowedLlmTiers,
                allowed_interview_modes: allowedInterviewModes
            };

            if (pricing.is_upgrade) {
                if (pricing.difference > 0) {
                    const orderRes = await subscriptionApi.createChangePayment(pricing.difference, pricing.currency);
                    const order = orderRes.data || orderRes;
                    
                    setOrderId(order.id);
                    setIsGatewayOpen(true);
                } else {
                    await subscriptionApi.changeSubscription(
                        features, limits, billingCycle, allowedLanguages, allowedVoices, allowedLlmTiers, allowedInterviewModes
                    );
                    refreshUser();
                    alert("Subscription Upgraded!");
                    navigate("/company/subscription");
                }
            } else {
                await subscriptionApi.changeSubscription(
                    features, limits, billingCycle, allowedLanguages, allowedVoices, allowedLlmTiers, allowedInterviewModes
                );
                alert("Downgrade scheduled for next renewal cycle.");
                navigate("/company/subscription");
            }
        } catch (err) {
            console.error("Change failed", err);
            alert("An error occurred while changing subscription.");
            setProcessing(false);
        }
    };

    const handleGatewaySuccess = async (paymentId, orderId) => {
        setIsGatewayOpen(false);
        setProcessing(true);
        try {
            await subscriptionApi.verifyChangePayment(
                paymentId,
                orderId,
                features,
                limits,
                billingCycle,
                pricing,
                allowedLanguages,
                allowedVoices,
                allowedLlmTiers,
                allowedInterviewModes
            );
            alert("Subscription Upgraded!");
            refreshUser();
            navigate("/company/subscription");
        } catch (err) {
            alert("Payment Verification Failed");
            setProcessing(false);
        }
    };

    const handleGatewayCancel = () => {
        setIsGatewayOpen(false);
        setProcessing(false);
    };

    if (loading) return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "50vh", color: "var(--primary)" }}>
            <FaSpinner className="spin-icon" style={{ fontSize: "2.5rem" }} />
            <style>{`.spin-icon { animation: spin 1s linear infinite; } @keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
        </div>
    );

    return (
        <div style={{ 
            maxWidth: 1200, 
            margin: "0 auto", 
            padding: "2rem",
            animation: "fadeIn 0.5s ease-out"
        }}>
            <style>{`
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .config-panel {
                    background: var(--surface);
                    backdrop-filter: blur(10px);
                    border: 1px solid var(--border);
                    border-radius: 20px;
                    padding: 2rem;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                    margin-bottom: 2rem;
                    transition: all 0.3s ease;
                }
                .config-panel:hover {
                    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
                }
                .feature-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 1rem;
                    margin-top: 1rem;
                }
                .feature-item {
                    display: flex;
                    align-items: center;
                    padding: 1rem;
                    border-radius: 12px;
                    border: 2px solid var(--border);
                    background: var(--background);
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                .feature-item:hover {
                    transform: scale(1.02);
                }
                .feature-item.active {
                    background: rgba(79, 70, 229, 0.1);
                    border-color: var(--primary);
                }
                .feature-icon {
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 1rem;
                    background: var(--background);
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                }
                .premium-select {
                    width: 100%;
                    padding: 1rem;
                    min-height: 56px;
                    border-radius: 12px;
                    border: 2px solid var(--border);
                    background: var(--surface);
                    color: var(--text);
                    font-size: 1.05rem;
                    font-weight: 500;
                    outline: none;
                    transition: border-color 0.3s;
                    appearance: none;
                    background-image: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%234F46E5%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E');
                    background-repeat: no-repeat;
                    background-position: right 1rem top 50%;
                    background-size: 0.65rem auto;
                }
                .premium-select:focus {
                    border-color: var(--primary);
                }
                .premium-select option {
                    background: var(--surface);
                    color: var(--text);
                    font-weight: 500;
                }
                .sticky-summary {
                    position: sticky;
                    top: 2rem;
                    background: var(--surface);
                    border: 1px solid var(--border);
                    color: var(--text);
                    padding: 2rem;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.2);
                }
                .btn-action {
                    width: 100%;
                    padding: 1.2rem;
                    font-size: 1.1rem;
                    font-weight: 700;
                    background: linear-gradient(135deg, var(--primary), #4f46e5);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    margin-top: 1.5rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                }
                .btn-action:hover:not(:disabled) {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(79, 70, 229, 0.4);
                }
                .btn-action:disabled {
                    background: #475569;
                    cursor: not-allowed;
                    box-shadow: none;
                }
                .pill-btn {
                    padding: 0.6rem 1.2rem;
                    border-radius: 20px;
                    border: 1px solid var(--border);
                    background: var(--background);
                    color: var(--text);
                    cursor: pointer;
                    font-weight: 500;
                    transition: all 0.2s;
                }
                .pill-btn.active {
                    background: var(--primary);
                    color: white;
                    border-color: var(--primary);
                }
            `}</style>
            
            <PageHeader 
                title="Configure Workspace Subscription" 
                subtitle="Tailor your platform features, AI configurations, and capacity. Upgrades apply immediately."
                onBack={() => navigate("/company/subscription")}
            />
            
            <div style={{ display: "grid", gridTemplateColumns: "1fr 400px", gap: "2.5rem", marginTop: "1rem" }}>
                <div>
                    <div className="config-panel">
                        <h3 style={{ fontSize: "1.4rem", color: "var(--text)", marginBottom: "0.5rem" }}>Capacity Limits</h3>
                        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", marginBottom: "1.5rem" }}>Adjust your team size and usage limits.</p>
                        
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                            <div>
                                <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600", color: "var(--text)" }}>Max Recruiters</label>
                                <select 
                                    className="premium-select" 
                                    value={limits.max_recruiters || 5} 
                                    onChange={(e) => handleLimitChange("max_recruiters", e.target.value)}
                                >
                                    <option value={5}>Up to 5 (Included)</option>
                                    <option value={20}>Up to 20 (+₹5,000/yr)</option>
                                    <option value={999999}>Unlimited (+₹15,000/yr)</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600", color: "var(--text)" }}>Max Candidates</label>
                                <select 
                                    className="premium-select" 
                                    value={limits.max_candidates || 500} 
                                    onChange={(e) => handleLimitChange("max_candidates", e.target.value)}
                                >
                                    <option value={500}>Up to 500 (Included)</option>
                                    <option value={2000}>Up to 2,000 (+₹5,000/yr)</option>
                                    <option value={999999}>Unlimited (+₹10,000/yr)</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600", color: "var(--text)" }}>Max Campaigns</label>
                                <select 
                                    className="premium-select" 
                                    value={limits.max_campaigns || 5} 
                                    onChange={(e) => handleLimitChange("max_campaigns", e.target.value)}
                                >
                                    <option value={5}>Up to 5 (Included)</option>
                                    <option value={20}>Up to 20 (+₹4,000/yr)</option>
                                    <option value={999999}>Unlimited (+₹12,000/yr)</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600", color: "var(--text)" }}>Monthly AI Interviews</label>
                                <select 
                                    className="premium-select" 
                                    value={limits.monthly_interviews || 100} 
                                    onChange={(e) => handleLimitChange("monthly_interviews", e.target.value)}
                                >
                                    <option value={100}>Up to 100 (Included)</option>
                                    <option value={300}>Up to 300 (+₹10,000/yr)</option>
                                    <option value={1000}>Up to 1,000 (+₹20,000/yr)</option>
                                    <option value={999999}>Unlimited (+₹50,000/yr)</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="config-panel">
                        <h3 style={{ fontSize: "1.4rem", color: "var(--text)", marginBottom: "0.5rem" }}>Platform & AI Features</h3>
                        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>Enable premium modules for your workspace.</p>
                        
                        <div className="feature-grid">
                            {options && Object.keys(options.features).map(feat => (
                                <div 
                                    key={feat} 
                                    className={`feature-item ${features[feat] ? 'active' : ''}`}
                                    onClick={() => toggleFeature(feat)}
                                >
                                    <div className="feature-icon">
                                        {features[feat] ? <FaCheck style={{ color: "var(--primary)", fontSize: "0.8rem" }} /> : <FaTimes style={{ color: "#cbd5e1", fontSize: "0.8rem" }} />}
                                    </div>
                                    <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
                                        <span style={{ fontWeight: 600, color: "var(--text)", textTransform: "capitalize" }}>
                                            {feat.replace(/_/g, ' ')}
                                        </span>
                                        <span style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "0.2rem" }}>
                                            ₹{options.features[feat]}/yr
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="config-panel">
                        <h3 style={{ fontSize: "1.4rem", color: "var(--text)", marginBottom: "0.5rem" }}>AI Configuration Options</h3>
                        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", marginBottom: "1.5rem" }}>Tailor the languages, models, and modes available to your recruiters.</p>
                        
                        <div style={{ marginBottom: "1.5rem" }}>
                            <label style={{ display: "block", marginBottom: "0.8rem", fontWeight: "600", color: "var(--text)" }}>Allowed LLM Tiers</label>
                            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                                {options?.config_options?.llm_tiers.map(llm => (
                                    <button 
                                        key={llm} 
                                        className={`pill-btn ${allowedLlmTiers.includes(llm) ? 'active' : ''}`}
                                        onClick={() => handleArrayToggle(llm, allowedLlmTiers, setAllowedLlmTiers)}
                                    >
                                        {llm}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div style={{ marginBottom: "1.5rem" }}>
                            <label style={{ display: "block", marginBottom: "0.8rem", fontWeight: "600", color: "var(--text)" }}>Supported Languages</label>
                            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                                {options?.config_options?.languages.map(lang => (
                                    <button 
                                        key={lang} 
                                        className={`pill-btn ${allowedLanguages.includes(lang) ? 'active' : ''}`}
                                        onClick={() => handleArrayToggle(lang, allowedLanguages, setAllowedLanguages)}
                                    >
                                        {lang}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div style={{ marginBottom: "1.5rem" }}>
                            <label style={{ display: "block", marginBottom: "0.8rem", fontWeight: "600", color: "var(--text)" }}>AI Voices</label>
                            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                                {options?.config_options?.voices.map(voice => (
                                    <button 
                                        key={voice} 
                                        className={`pill-btn ${allowedVoices.includes(voice) ? 'active' : ''}`}
                                        onClick={() => handleArrayToggle(voice, allowedVoices, setAllowedVoices)}
                                    >
                                        {voice}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div>
                            <label style={{ display: "block", marginBottom: "0.8rem", fontWeight: "600", color: "var(--text)" }}>Interview Modes</label>
                            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                                {options?.config_options?.interview_modes.map(mode => (
                                    <button 
                                        key={mode} 
                                        className={`pill-btn ${allowedInterviewModes.includes(mode) ? 'active' : ''}`}
                                        onClick={() => handleArrayToggle(mode, allowedInterviewModes, setAllowedInterviewModes)}
                                    >
                                        {mode}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div>
                    <div className="sticky-summary">
                        <div style={{ display: "flex", alignItems: "center", gap: "0.8rem", marginBottom: "2rem" }}>
                            <FaShieldAlt style={{ fontSize: "1.5rem", color: "#818cf8" }} />
                            <h3 style={{ margin: 0, fontSize: "1.4rem" }}>Order Summary</h3>
                        </div>
                        
                        {calculating || !pricing ? (
                            <div style={{ display: "flex", justifyContent: "center", padding: "3rem 0" }}>
                                <FaSpinner className="spin-icon" style={{ fontSize: "2rem", color: "#818cf8" }} />
                            </div>
                        ) : (
                            <>
                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem", color: "var(--text-muted)" }}>
                                    <span>Current Value</span>
                                    <span>₹{pricing.current_price.toFixed(2)}/yr</span>
                                </div>
                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1.5rem", color: "var(--text)", fontWeight: "bold" }}>
                                    <span>New Configuration</span>
                                    <span>₹{pricing.new_price.toFixed(2)}/yr</span>
                                </div>
                                
                                <div style={{ borderTop: "1px dashed var(--border)", margin: "1.5rem 0" }}></div>
                                
                                {pricing.is_upgrade ? (
                                    <>
                                        <div style={{ background: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.2)", padding: "1rem", borderRadius: "12px", marginBottom: "1.5rem" }}>
                                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem", color: "#34d399", fontWeight: "600" }}>
                                                <span>Prorated Upgrade</span>
                                                <span>₹{(pricing.difference - pricing.tax).toFixed(2)}</span>
                                            </div>
                                            <div style={{ display: "flex", justifyContent: "space-between", color: "#94a3b8", fontSize: "0.9rem" }}>
                                                <span>Taxes (18%)</span>
                                                <span>₹{pricing.tax.toFixed(2)}</span>
                                            </div>
                                        </div>
                                        
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "1.5rem", fontWeight: "800", color: "var(--text)" }}>
                                            <span>Total Due</span>
                                            <span>₹{pricing.final_amount.toFixed(2)}</span>
                                        </div>
                                        
                                        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "1rem", lineHeight: 1.4 }}>
                                            You are paying the difference for the remaining days of your current cycle. Expiry date remains unchanged.
                                        </p>
                                    </>
                                ) : (
                                    <div style={{ background: "rgba(245, 158, 11, 0.1)", border: "1px solid rgba(245, 158, 11, 0.2)", padding: "1.2rem", borderRadius: "12px", color: "#fbbf24" }}>
                                        <h4 style={{ margin: "0 0 0.5rem 0" }}>Downgrade Detected</h4>
                                        <p style={{ margin: 0, fontSize: "0.9rem", lineHeight: 1.4, color: "#fcd34d" }}>
                                            No payment is required today. This new configuration will automatically take effect on your next renewal date.
                                        </p>
                                    </div>
                                )}
                            </>
                        )}
                        
                        <button 
                            className="btn-action" 
                            disabled={calculating || processing || !pricing}
                            onClick={handleProceed}
                        >
                            {processing ? (
                                <><FaSpinner className="spin-icon" /> Processing...</>
                            ) : pricing?.is_upgrade ? (
                                <><FaRocket /> Pay & Upgrade</>
                            ) : (
                                "Schedule Downgrade"
                            )}
                        </button>
                    </div>
                </div>
            </div>
            
            <PaymentGateway 
                isOpen={isGatewayOpen}
                onClose={handleGatewayCancel}
                onSuccess={handleGatewaySuccess}
                amount={pricing?.difference || 0}
                orderId={orderId}
                pricing={pricing}
            />
        </div>
    );
}

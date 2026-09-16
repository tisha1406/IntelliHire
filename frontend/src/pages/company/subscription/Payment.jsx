import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import subscriptionApi from "../../../api/subscription";
import { useAuthContext } from "../../../context/AuthContext";
import { FaLock, FaCheckCircle, FaTimesCircle, FaSpinner } from "react-icons/fa";
import PaymentGateway from "../../../components/company/subscription/PaymentGateway";

export default function Payment() {
    const navigate = useNavigate();
    const { companyProfile, refreshUser, setCompanyProfile } = useAuthContext();
    const [loading, setLoading] = useState(false);
    const [sub, setSub] = useState(null);
    const [paymentStatus, setPaymentStatus] = useState("idle"); // idle, processing, success, failed
    const [isGatewayOpen, setIsGatewayOpen] = useState(false);
    const [orderId, setOrderId] = useState(null);

    useEffect(() => {
        if (companyProfile?.subscription) {
            setSub(companyProfile.subscription);
        } else {
            subscriptionApi.getCurrentSubscription()
                .then(res => setSub(res.data?.data || res.data))
                .catch(err => console.error("Failed to load subscription:", err));
        }
    }, [companyProfile]);

    const handlePaymentClick = async () => {
        setLoading(true);
        try {
            const amount = sub?.pricing?.total || 0;
            const orderRes = await subscriptionApi.createPaymentOrder(amount);
            const order = orderRes.data?.data || orderRes.data;
            
            setOrderId(order.id);
            setIsGatewayOpen(true);
        } catch (err) {
            console.error(err);
            setPaymentStatus("failed");
            alert(err.message || "Payment initialization failed.");
        } finally {
            setLoading(false);
        }
    };

    const handleGatewaySuccess = async (paymentId, orderId) => {
        setIsGatewayOpen(false);
        setPaymentStatus("processing");
        try {
            await subscriptionApi.verifyPayment(paymentId, orderId);
            setPaymentStatus("success");
            refreshUser();
            setCompanyProfile(prev => ({
                ...prev,
                subscription: { ...(prev?.subscription || {}), status: "active" }
            }));
            setTimeout(() => navigate("/company"), 3000);
        } catch (err) {
            console.error("Verification failed:", err);
            setPaymentStatus("failed");
            alert("Verification failed. If amount was deducted, it will be refunded.");
        }
    };

    const handleGatewayCancel = () => {
        setIsGatewayOpen(false);
        setPaymentStatus("idle");
    };

    if (!sub) return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", background: "var(--background)" }}>
            <FaSpinner className="spin-icon" style={{ fontSize: "2.5rem", color: "var(--primary)" }} />
            <style>{`.spin-icon { animation: spin 1s linear infinite; } @keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
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
                @keyframes scaleIn {
                    0% { transform: scale(0.9); opacity: 0; }
                    100% { transform: scale(1); opacity: 1; }
                }
                @keyframes pulse {
                    0% { box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.4); }
                    70% { box-shadow: 0 0 0 15px rgba(79, 70, 229, 0); }
                    100% { box-shadow: 0 0 0 0 rgba(79, 70, 229, 0); }
                }
                .payment-card {
                    background: var(--surface);
                    border-radius: 24px;
                    padding: 3.5rem 2.5rem;
                    width: 100%;
                    max-width: 500px;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                    border: 1px solid var(--border);
                    text-align: center;
                    animation: scaleIn 0.5s cubic-bezier(0.16, 1, 0.3, 1);
                    position: relative;
                    overflow: hidden;
                }
                .payment-card::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 6px;
                    background: linear-gradient(90deg, var(--primary), #6366f1, #818cf8);
                }
                .amount-display {
                    font-size: 3.5rem;
                    font-weight: 800;
                    color: var(--text);
                    margin: 1.5rem 0 0.5rem 0;
                }
                .amount-label {
                    color: var(--text-muted);
                    font-size: 1.1rem;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-bottom: 2.5rem;
                }
                .btn-pay {
                    width: 100%;
                    padding: 1.25rem;
                    font-size: 1.2rem;
                    font-weight: 700;
                    background: var(--primary);
                    color: white;
                    border: none;
                    border-radius: 16px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.8rem;
                }
                .btn-pay:hover:not(:disabled) {
                    transform: translateY(-3px);
                    background: #4338ca;
                    box-shadow: 0 10px 25px rgba(79, 70, 229, 0.4);
                }
                .btn-pay:disabled {
                    opacity: 0.7;
                    cursor: not-allowed;
                }
                .status-box {
                    padding: 2rem;
                    border-radius: 16px;
                    margin-top: 1rem;
                    animation: scaleIn 0.4s ease;
                }
                .status-box.processing {
                    background: var(--background);
                    color: var(--text);
                    border: 1px solid var(--border);
                }
                .status-box.success {
                    background: rgba(16, 185, 129, 0.1);
                    color: #34d399;
                    border: 1px solid rgba(16, 185, 129, 0.3);
                }
                .status-box.failed {
                    background: rgba(239, 68, 68, 0.1);
                    color: #ef4444;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                }
                .secure-badge {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                    color: var(--text-muted);
                    font-size: 0.9rem;
                    margin-top: 2rem;
                }
            `}</style>
            
            <div className="payment-card">
                <div style={{ width: "60px", height: "60px", background: "var(--background)", border: "1px solid var(--border)", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto", color: "var(--primary)", fontSize: "1.5rem" }}>
                    <FaLock />
                </div>
                
                <h1 className="amount-display">₹{sub?.pricing?.total?.toFixed(2)}</h1>
                <p className="amount-label">Total Amount Due</p>
                
                {paymentStatus === "idle" && (
                    <button 
                        className="btn-pay" 
                        onClick={handlePaymentClick}
                        disabled={loading}
                    >
                        <FaLock /> {loading ? "Processing..." : "Pay Securely"}
                    </button>
                )}
                
                {paymentStatus === "processing" && (
                    <div className="status-box processing">
                        <FaSpinner className="spin-icon" style={{ fontSize: "2rem", marginBottom: "1rem", color: "var(--primary)" }} />
                        <h3 style={{ fontSize: "1.2rem", marginBottom: "0.5rem" }}>Processing Payment...</h3>
                        <p style={{ fontSize: "0.9rem" }}>Please do not close or refresh this window.</p>
                    </div>
                )}
                
                {paymentStatus === "success" && (
                    <div className="status-box success">
                        <FaCheckCircle style={{ fontSize: "2.5rem", marginBottom: "1rem" }} />
                        <h3 style={{ fontSize: "1.3rem", marginBottom: "0.5rem" }}>Payment Successful!</h3>
                        <p style={{ fontSize: "0.95rem" }}>Your workspace is now active. Redirecting to your dashboard...</p>
                    </div>
                )}
                
                {paymentStatus === "failed" && (
                    <div className="status-box failed">
                        <FaTimesCircle style={{ fontSize: "2.5rem", marginBottom: "1rem" }} />
                        <h3 style={{ fontSize: "1.3rem", marginBottom: "0.5rem" }}>Payment Failed</h3>
                        <p style={{ fontSize: "0.95rem", marginBottom: "1.5rem" }}>We couldn't process your payment. Please try again.</p>
                        <button 
                            style={{ padding: "0.8rem 1.5rem", background: "var(--background)", border: "1px solid rgba(239, 68, 68, 0.5)", borderRadius: "8px", color: "#ef4444", fontWeight: "bold", cursor: "pointer" }} 
                            onClick={() => setPaymentStatus("idle")}
                        >
                            Try Again
                        </button>
                    </div>
                )}
                
                <div className="secure-badge">
                    <FaLock /> <span>256-bit SSL Encrypted</span>
                </div>
            </div>

            <PaymentGateway 
                isOpen={isGatewayOpen}
                onClose={handleGatewayCancel}
                onSuccess={handleGatewaySuccess}
                amount={sub?.pricing?.total || 0}
                orderId={orderId}
                pricing={sub?.pricing}
            />
        </div>
    );
}

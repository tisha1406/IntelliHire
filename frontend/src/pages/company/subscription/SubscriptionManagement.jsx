import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import subscriptionApi from "../../../api/subscription";
import { useAuthContext } from "../../../context/AuthContext";
import PageHeader from "../../../components/common/PageHeader";
import { FaSpinner, FaCheck, FaTimes, FaHistory, FaCreditCard, FaBolt } from "react-icons/fa";

export default function SubscriptionManagement() {
    const navigate = useNavigate();
    const { companyProfile } = useAuthContext();
    const [subData, setSubData] = useState(null);
    const [paymentHistory, setPaymentHistory] = useState([]);
    const [subHistory, setSubHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            try {
                const subRes = await subscriptionApi.getCurrentSubscription();
                setSubData(subRes.data || subRes);
                
                const payRes = await subscriptionApi.getPaymentHistory();
                setPaymentHistory(payRes.data || payRes);
                
                const histRes = await subscriptionApi.getSubscriptionHistory();
                setSubHistory(histRes.data || histRes);
            } catch (err) {
                console.error("Failed to load subscription data", err);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    if (loading || !subData) return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "50vh", color: "var(--primary)" }}>
            <FaSpinner className="spin-icon" style={{ fontSize: "2.5rem" }} />
            <style>{`.spin-icon { animation: spin 1s linear infinite; } @keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
        </div>
    );

    const { subscription, limits, features, pending_subscription, usage, days_remaining } = subData;
    const isActive = subscription?.status === "active";
    const isExpired = subscription?.status === "expired";

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
                .dashboard-panel {
                    background: var(--surface);
                    backdrop-filter: blur(10px);
                    border: 1px solid var(--border);
                    border-radius: 20px;
                    padding: 2rem;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                    transition: all 0.3s ease;
                }
                .dashboard-panel:hover {
                    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
                }
                .panel-header {
                    display: flex;
                    align-items: center;
                    gap: 0.8rem;
                    border-bottom: 1px solid var(--border);
                    padding-bottom: 1rem;
                    margin-bottom: 1.5rem;
                    font-size: 1.25rem;
                    font-weight: 600;
                    color: var(--text);
                }
                .info-row {
                    display: flex;
                    justify-content: space-between;
                    padding: 0.8rem 0;
                    border-bottom: 1px dashed var(--border);
                    color: var(--text);
                }
                .info-row:last-child {
                    border-bottom: none;
                }
                .info-label {
                    color: var(--text-muted);
                    font-weight: 500;
                }
                .progress-container {
                    margin-bottom: 1.5rem;
                }
                .progress-header {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 0.5rem;
                    color: var(--text);
                    font-weight: 500;
                }
                .progress-bar-bg {
                    width: 100%;
                    height: 10px;
                    background: var(--border);
                    border-radius: 5px;
                    overflow: hidden;
                }
                .progress-bar-fill {
                    height: 100%;
                    background: linear-gradient(90deg, var(--primary), #818cf8);
                    border-radius: 5px;
                    transition: width 1s ease-in-out;
                }
                .feature-pill {
                    display: flex;
                    align-items: center;
                    gap: 0.6rem;
                    padding: 0.8rem 1rem;
                    background: var(--background);
                    border: 1px solid var(--border);
                    border-radius: 10px;
                    color: var(--text);
                    font-weight: 500;
                    transition: all 0.2s ease;
                }
                .feature-pill:hover {
                    transform: translateY(-2px);
                    border-color: var(--primary);
                }
                .history-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .history-table th {
                    text-align: left;
                    padding: 1rem 0.5rem;
                    color: var(--text-muted);
                    font-weight: 600;
                    border-bottom: 1px solid var(--border);
                }
                .history-table td {
                    padding: 1rem 0.5rem;
                    color: var(--text);
                    border-bottom: 1px dashed var(--border);
                }
                .history-table tr:last-child td {
                    border-bottom: none;
                }
                .status-badge {
                    padding: 0.3rem 0.8rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    text-transform: uppercase;
                }
            `}</style>
            
            <PageHeader 
                title="Subscription Management" 
                subtitle="Manage your workspace plan, track feature usage, and view your billing history."
            />
            
            <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem" }}>
                <button 
                    className="btn btn-primary" 
                    style={{ padding: "0.8rem 1.5rem", borderRadius: "10px", display: "flex", alignItems: "center", gap: "0.5rem" }}
                    onClick={() => navigate("/company/subscription/change")}
                >
                    <FaBolt /> Change Subscription
                </button>
                {(days_remaining <= 30 || isExpired) && (
                    <button 
                        className="btn btn-outline" 
                        style={{ padding: "0.8rem 1.5rem", borderRadius: "10px", borderColor: "var(--primary)", color: "var(--primary)" }}
                        onClick={() => navigate("/company/subscription/renew")}
                    >
                        Renew Subscription
                    </button>
                )}
            </div>
            
            {pending_subscription && (
                <div style={{ background: "rgba(245, 158, 11, 0.1)", color: "#fbbf24", padding: "1.2rem", borderRadius: "12px", marginBottom: "2rem", border: "1px solid rgba(245, 158, 11, 0.3)", display: "flex", alignItems: "center", gap: "1rem" }}>
                    <FaHistory style={{ fontSize: "1.5rem" }} />
                    <div>
                        <strong style={{ display: "block", marginBottom: "0.2rem" }}>Pending Downgrade Scheduled</strong>
                        <span style={{ fontSize: "0.95rem" }}>A downgrade has been scheduled and will take effect automatically on your next renewal date.</span>
                    </div>
                </div>
            )}
            
            {isExpired && (
                <div style={{ background: "rgba(239, 68, 68, 0.1)", color: "#ef4444", padding: "1.2rem", borderRadius: "12px", marginBottom: "2rem", border: "1px solid rgba(239, 68, 68, 0.3)", display: "flex", alignItems: "center", gap: "1rem" }}>
                    <FaTimes style={{ fontSize: "1.5rem" }} />
                    <div>
                        <strong style={{ display: "block", marginBottom: "0.2rem" }}>Subscription Expired</strong>
                        <span style={{ fontSize: "0.95rem" }}>Your subscription has expired. Premium features are locked. Please renew to regain full access to IntelliHire.</span>
                    </div>
                </div>
            )}
            
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem", marginBottom: "2rem" }}>
                <div className="dashboard-panel">
                    <div className="panel-header">
                        <FaBolt style={{ color: "var(--primary)" }} /> Plan Overview
                    </div>
                    
                    <div className="info-row">
                        <span className="info-label">Status</span>
                        <span style={{ color: isActive ? "#34d399" : "#ef4444", fontWeight: "bold" }}>
                            {subscription?.status?.toUpperCase()}
                        </span>
                    </div>
                    <div className="info-row">
                        <span className="info-label">Billing Cycle</span>
                        <span style={{ textTransform: "capitalize" }}>{subscription?.billing_cycle?.replace("_", " ")}</span>
                    </div>
                    <div className="info-row">
                        <span className="info-label">Start Date</span>
                        <span>{subscription?.start_date ? new Date(subscription.start_date).toLocaleDateString() : 'N/A'}</span>
                    </div>
                    <div className="info-row">
                        <span className="info-label">Expiry Date</span>
                        <span>{subscription?.expiry_date ? new Date(subscription.expiry_date).toLocaleDateString() : 'N/A'}</span>
                    </div>
                    <div className="info-row">
                        <span className="info-label">Days Remaining</span>
                        <span style={{ fontWeight: "bold", color: days_remaining <= 30 ? "#fbbf24" : "var(--text)" }}>{days_remaining} days</span>
                    </div>
                    <div className="info-row">
                        <span className="info-label">Current Value</span>
                        <span>₹{subscription?.pricing?.total?.toFixed(2) || "0.00"}/yr</span>
                    </div>
                </div>
                
                <div className="dashboard-panel">
                    <div className="panel-header">
                        <FaCheck style={{ color: "var(--primary)" }} /> Usage & Limits
                    </div>
                    
                    <div className="progress-container">
                        <div className="progress-header">
                            <span>Recruiter Seats</span>
                            <span>{usage?.recruiters} / {limits?.max_recruiters === Infinity || limits?.max_recruiters === 999999 ? '∞' : limits?.max_recruiters}</span>
                        </div>
                        <div className="progress-bar-bg">
                            <div 
                                className="progress-bar-fill" 
                                style={{ width: `${Math.min(100, (usage?.recruiters / (limits?.max_recruiters === 999999 ? usage?.recruiters + 1 : limits?.max_recruiters || 1)) * 100)}%` }}
                            ></div>
                        </div>
                    </div>
                    
                    <div className="progress-container" style={{ marginBottom: 0 }}>
                        <div className="progress-header">
                            <span>Candidate Profiles</span>
                            <span>{usage?.candidates} / {limits?.max_candidates === Infinity || limits?.max_candidates === 999999 ? '∞' : limits?.max_candidates}</span>
                        </div>
                        <div className="progress-bar-bg">
                            <div 
                                className="progress-bar-fill" 
                                style={{ width: `${Math.min(100, (usage?.candidates / (limits?.max_candidates === 999999 ? usage?.candidates + 1 : limits?.max_candidates || 1)) * 100)}%` }}
                            ></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div className="dashboard-panel" style={{ marginBottom: "2rem" }}>
                <div className="panel-header">
                    <FaCheck style={{ color: "var(--primary)" }} /> Active Features
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "1rem" }}>
                    {Object.keys(features || {}).map(key => (
                        <div key={key} className="feature-pill" style={{ opacity: features[key] ? 1 : 0.5 }}>
                            {features[key] ? (
                                <FaCheck style={{ color: "#34d399" }} />
                            ) : (
                                <FaTimes style={{ color: "#ef4444" }} />
                            )}
                            <span style={{ textTransform: "capitalize", textDecoration: features[key] ? "none" : "line-through" }}>
                                {key.replace(/_/g, ' ')}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
            
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
                <div className="dashboard-panel">
                    <div className="panel-header">
                        <FaCreditCard style={{ color: "var(--primary)" }} /> Payment History
                    </div>
                    {paymentHistory.length === 0 ? <p style={{ color: "var(--text-muted)" }}>No payments found.</p> : (
                        <div style={{ overflowX: "auto" }}>
                            <table className="history-table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Type</th>
                                        <th>Amount</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {paymentHistory.map(p => (
                                        <tr key={p.id}>
                                            <td>{new Date(p.created_at).toLocaleDateString()}</td>
                                            <td style={{ textTransform: "capitalize" }}>{p.payment_type}</td>
                                            <td style={{ fontWeight: "600" }}>₹{(p.amount || 0).toFixed(2)}</td>
                                            <td>
                                                <span className="status-badge" style={{ 
                                                    background: p.status === "success" ? "rgba(16, 185, 129, 0.1)" : "rgba(245, 158, 11, 0.1)", 
                                                    color: p.status === "success" ? "#34d399" : "#fbbf24" 
                                                }}>
                                                    {p.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
                
                <div className="dashboard-panel">
                    <div className="panel-header">
                        <FaHistory style={{ color: "var(--primary)" }} /> Subscription Log
                    </div>
                    {subHistory.length === 0 ? <p style={{ color: "var(--text-muted)" }}>No history found.</p> : (
                        <div style={{ overflowX: "auto" }}>
                            <table className="history-table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Event</th>
                                        <th>Amount</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {subHistory.map(h => (
                                        <tr key={h.id}>
                                            <td>{new Date(h.created_at).toLocaleDateString()}</td>
                                            <td style={{ textTransform: "capitalize" }}>{h.change_type}</td>
                                            <td style={{ fontWeight: "600" }}>₹{(h.payment_required || 0).toFixed(2)}</td>
                                            <td>
                                                <span className="status-badge" style={{ 
                                                    background: h.status === "completed" ? "rgba(16, 185, 129, 0.1)" : "rgba(148, 163, 184, 0.1)", 
                                                    color: h.status === "completed" ? "#34d399" : "#94a3b8" 
                                                }}>
                                                    {h.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

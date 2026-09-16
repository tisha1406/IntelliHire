import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { CreditCard, Smartphone, CheckCircle2, XCircle, ShieldCheck, ArrowRight, X, Lock } from "lucide-react";

export default function PaymentGateway({ isOpen, onClose, onSuccess, amount, orderId, currency = "INR", pricing }) {
    const [method, setMethod] = useState("upi");
    const [status, setStatus] = useState("idle");
    const [upiId, setUpiId] = useState("");
    const [cardDetails, setCardDetails] = useState({ number: "", name: "", expiry: "", cvv: "" });
    const [errorMsg, setErrorMsg] = useState("");

    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = "hidden";
        } else {
            document.body.style.overflow = "unset";
        }
        return () => {
            document.body.style.overflow = "unset";
        };
    }, [isOpen]);

    useEffect(() => {
        if (isOpen) {
            setStatus("idle");
            setUpiId("");
            setCardDetails({ number: "", name: "", expiry: "", cvv: "" });
            setErrorMsg("");
        }
    }, [isOpen]);

    if (!isOpen) return null;

    const handlePay = () => {
        if (method === "upi") {
            if (!upiId.includes("@")) {
                setErrorMsg("Please enter a valid UPI ID (e.g. name@upi)");
                return;
            }
        } else {
            if (cardDetails.number.replace(/\s/g, "").length < 15) {
                setErrorMsg("Please enter a valid card number");
                return;
            }
            if (!cardDetails.name || !cardDetails.expiry || cardDetails.cvv.length < 3) {
                setErrorMsg("Please fill all card details correctly");
                return;
            }
        }

        setErrorMsg("");
        setStatus("processing");

        setTimeout(() => {
            setStatus("verifying");
            setTimeout(() => {
                setStatus("success");
                setTimeout(() => {
                    const paymentId = `INTL-PAY-${Math.random().toString(36).substring(2, 10).toUpperCase()}`;
                    onSuccess(paymentId, orderId);
                }, 1500);
            }, 1500);
        }, 2000);
    };

    const handleCancel = () => {
        if (status === "processing" || status === "verifying" || status === "success") return;
        onClose();
    };

    const formatAmount = (val) => {
        return new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: currency,
            maximumFractionDigits: 2,
        }).format(val || 0);
    };

    const formatCardNumber = (value) => {
        const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
        const matches = v.match(/\d{4,16}/g);
        const match = matches && matches[0] || '';
        let parts = [];
        for (let i = 0, len = match.length; i < len; i += 4) {
            parts.push(match.substring(i, i + 4));
        }
        return parts.length ? parts.join(' ') : value;
    };

    return createPortal(
        <>
            <style>{`
                .intellihire-payment-gateway__overlay {
                    position: fixed;
                    inset: 0;
                    background: rgba(15, 23, 42, 0.85);
                    backdrop-filter: blur(4px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 16px;
                    z-index: 99999;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                }
                .intellihire-payment-gateway__modal {
                    background: #ffffff;
                    width: 100%;
                    max-width: 520px;
                    max-height: calc(100vh - 32px);
                    border-radius: 20px;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    position: relative;
                }
                .intellihire-payment-gateway__header {
                    background: #0f172a;
                    padding: 24px;
                    color: #ffffff;
                    flex-shrink: 0;
                    position: relative;
                }
                .intellihire-payment-gateway__close {
                    position: absolute;
                    top: 16px;
                    right: 16px;
                    background: transparent;
                    border: none;
                    color: #94a3b8;
                    cursor: pointer;
                    padding: 8px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s ease;
                }
                .intellihire-payment-gateway__close:hover {
                    color: #ffffff;
                    background: rgba(255, 255, 255, 0.1);
                }
                .intellihire-payment-gateway__header-title {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                .intellihire-payment-gateway__icon-box {
                    width: 40px;
                    height: 40px;
                    background: rgba(99, 102, 241, 0.2);
                    border: 1px solid rgba(99, 102, 241, 0.3);
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #818cf8;
                }
                .intellihire-payment-gateway__h2 {
                    font-size: 20px;
                    font-weight: 700;
                    margin: 0 0 4px 0;
                    letter-spacing: -0.02em;
                }
                .intellihire-payment-gateway__subtitle {
                    font-size: 13px;
                    color: #818cf8;
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    margin: 0;
                    font-weight: 500;
                }
                .intellihire-payment-gateway__body {
                    padding: 24px;
                    background: #f8fafc;
                    flex: 1;
                    overflow-y: auto;
                }
                .intellihire-payment-gateway__summary {
                    background: #ffffff;
                    border-radius: 12px;
                    padding: 16px;
                    border: 1px solid #e2e8f0;
                    margin-bottom: 24px;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                }
                .intellihire-payment-gateway__summary-title {
                    font-size: 11px;
                    font-weight: 700;
                    color: #64748b;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    margin: 0 0 16px 0;
                }
                .intellihire-payment-gateway__summary-row {
                    display: flex;
                    justify-content: space-between;
                    font-size: 14px;
                    color: #475569;
                    margin-bottom: 12px;
                }
                .intellihire-payment-gateway__summary-row--bold {
                    font-weight: 600;
                    color: #0f172a;
                }
                .intellihire-payment-gateway__summary-row--highlight {
                    color: #4f46e5;
                }
                .intellihire-payment-gateway__summary-divider {
                    height: 1px;
                    background: #e2e8f0;
                    margin: 12px 0;
                }
                .intellihire-payment-gateway__total-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-top: 16px;
                    padding-top: 16px;
                    border-top: 1px solid #cbd5e1;
                }
                .intellihire-payment-gateway__total-label {
                    font-size: 15px;
                    font-weight: 700;
                    color: #0f172a;
                }
                .intellihire-payment-gateway__total-amount {
                    font-size: 22px;
                    font-weight: 800;
                    color: #0f172a;
                }
                .intellihire-payment-gateway__tabs {
                    display: flex;
                    background: #e2e8f0;
                    padding: 6px;
                    border-radius: 12px;
                    margin-bottom: 24px;
                    gap: 6px;
                }
                .intellihire-payment-gateway__tab {
                    flex: 1;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    padding: 10px 0;
                    background: transparent;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    color: #64748b;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                .intellihire-payment-gateway__tab--active {
                    background: #ffffff;
                    color: #4f46e5;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .intellihire-payment-gateway__error {
                    background: #fef2f2;
                    border: 1px solid #fecaca;
                    color: #b91c1c;
                    padding: 12px 16px;
                    border-radius: 10px;
                    font-size: 14px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 20px;
                    font-weight: 500;
                }
                .intellihire-payment-gateway__form-group {
                    margin-bottom: 16px;
                }
                .intellihire-payment-gateway__label {
                    display: block;
                    font-size: 13px;
                    font-weight: 700;
                    color: #334155;
                    margin-bottom: 6px;
                }
                .intellihire-payment-gateway__input-wrapper {
                    position: relative;
                }
                .intellihire-payment-gateway__input-icon {
                    position: absolute;
                    left: 16px;
                    top: 50%;
                    transform: translateY(-50%);
                    color: #94a3b8;
                }
                .intellihire-payment-gateway__input {
                    width: 100%;
                    padding: 14px 16px;
                    font-size: 15px;
                    background: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 10px;
                    color: #0f172a;
                    font-weight: 500;
                    outline: none;
                    transition: all 0.2s;
                    box-sizing: border-box;
                }
                .intellihire-payment-gateway__input--with-icon {
                    padding-left: 48px;
                }
                .intellihire-payment-gateway__input:focus {
                    border-color: #6366f1;
                    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
                }
                .intellihire-payment-gateway__grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 16px;
                }
                .intellihire-payment-gateway__footer {
                    background: #ffffff;
                    padding: 24px;
                    border-top: 1px solid #f1f5f9;
                    flex-shrink: 0;
                }
                .intellihire-payment-gateway__pay-btn {
                    width: 100%;
                    background: #4f46e5;
                    color: #ffffff;
                    border: none;
                    padding: 16px;
                    border-radius: 12px;
                    font-size: 16px;
                    font-weight: 700;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
                    transition: all 0.2s ease;
                }
                .intellihire-payment-gateway__pay-btn:hover {
                    background: #4338ca;
                    transform: translateY(-1px);
                    box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35);
                }
                .intellihire-payment-gateway__disclaimer {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                    font-size: 12px;
                    color: #94a3b8;
                    margin-top: 16px;
                    font-weight: 500;
                }
                .intellihire-payment-gateway__status {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: 40px 20px;
                    text-align: center;
                }
                .intellihire-payment-gateway__spinner-box {
                    position: relative;
                    width: 80px;
                    height: 80px;
                    margin-bottom: 24px;
                }
                .intellihire-payment-gateway__spinner-bg {
                    position: absolute;
                    inset: 0;
                    border: 4px solid #e2e8f0;
                    border-radius: 50%;
                }
                .intellihire-payment-gateway__spinner {
                    position: absolute;
                    inset: 0;
                    border: 4px solid #4f46e5;
                    border-top-color: transparent;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                .intellihire-payment-gateway__spinner-icon {
                    position: absolute;
                    inset: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #4f46e5;
                }
                .intellihire-payment-gateway__success-icon {
                    width: 80px;
                    height: 80px;
                    background: #dcfce7;
                    color: #16a34a;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 24px;
                    box-shadow: 0 10px 25px rgba(22, 163, 74, 0.2);
                }
                .intellihire-payment-gateway__status-title {
                    font-size: 20px;
                    font-weight: 800;
                    color: #0f172a;
                    margin: 0 0 8px 0;
                }
                .intellihire-payment-gateway__status-text {
                    font-size: 14px;
                    color: #64748b;
                    margin: 0;
                    font-weight: 500;
                }
                .intellihire-payment-gateway__reference {
                    background: #f1f5f9;
                    border: 1px solid #e2e8f0;
                    padding: 12px 24px;
                    border-radius: 10px;
                    margin-top: 32px;
                }
                .intellihire-payment-gateway__reference span {
                    display: block;
                    font-size: 11px;
                    text-transform: uppercase;
                    color: #64748b;
                    font-weight: 700;
                    margin-bottom: 4px;
                }
                .intellihire-payment-gateway__reference strong {
                    font-family: monospace;
                    font-size: 14px;
                    color: #0f172a;
                }
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}</style>

            <div className="intellihire-payment-gateway__overlay" onClick={handleCancel}>
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 15 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 15 }}
                    className="intellihire-payment-gateway__modal"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="intellihire-payment-gateway__header">
                        {status === "idle" && (
                            <button 
                                onClick={handleCancel}
                                className="intellihire-payment-gateway__close"
                                aria-label="Close"
                            >
                                <X size={20} />
                            </button>
                        )}
                        <div className="intellihire-payment-gateway__header-title">
                            <div className="intellihire-payment-gateway__icon-box">
                                <ShieldCheck size={24} />
                            </div>
                            <div>
                                <h2 className="intellihire-payment-gateway__h2">IntelliHire Checkout</h2>
                                <p className="intellihire-payment-gateway__subtitle">
                                    <Lock size={12} /> Secure Simulated Payment
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Scrollable Body */}
                    <div className="intellihire-payment-gateway__body">
                        <AnimatePresence mode="wait">
                            {status === "idle" && (
                                <motion.div
                                    key="form"
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: 20 }}
                                >
                                    {/* Order Summary */}
                                    {pricing ? (
                                        <div className="intellihire-payment-gateway__summary">
                                            <h4 className="intellihire-payment-gateway__summary-title">Order Summary</h4>
                                            
                                            {pricing.is_upgrade ? (
                                                <>
                                                    <div className="intellihire-payment-gateway__summary-row">
                                                        <span>Current Value</span>
                                                        <span>{formatAmount(pricing.current_price)}/yr</span>
                                                    </div>
                                                    <div className="intellihire-payment-gateway__summary-row intellihire-payment-gateway__summary-row--bold">
                                                        <span>New Configuration</span>
                                                        <span>{formatAmount(pricing.new_price)}/yr</span>
                                                    </div>
                                                    <div className="intellihire-payment-gateway__summary-divider"></div>
                                                    <div className="intellihire-payment-gateway__summary-row intellihire-payment-gateway__summary-row--highlight">
                                                        <span>Prorated Upgrade</span>
                                                        <span>{formatAmount(pricing.difference - pricing.tax)}</span>
                                                    </div>
                                                    <div className="intellihire-payment-gateway__summary-row">
                                                        <span>Taxes (18%)</span>
                                                        <span>{formatAmount(pricing.tax)}</span>
                                                    </div>
                                                </>
                                            ) : pricing.base_price !== undefined ? (
                                                <>
                                                    <div className="intellihire-payment-gateway__summary-row">
                                                        <span>Base Price</span>
                                                        <span>{formatAmount(pricing.base_price)}</span>
                                                    </div>
                                                    {(pricing.feature_cost > 0) && (
                                                        <div className="intellihire-payment-gateway__summary-row">
                                                            <span>Premium Features</span>
                                                            <span>{formatAmount(pricing.feature_cost)}</span>
                                                        </div>
                                                    )}
                                                    {(pricing.limit_cost > 0) && (
                                                        <div className="intellihire-payment-gateway__summary-row">
                                                            <span>Capacity Add-ons</span>
                                                            <span>{formatAmount(pricing.limit_cost)}</span>
                                                        </div>
                                                    )}
                                                    <div className="intellihire-payment-gateway__summary-divider"></div>
                                                    <div className="intellihire-payment-gateway__summary-row">
                                                        <span>Taxes (18%)</span>
                                                        <span>{formatAmount(pricing.tax)}</span>
                                                    </div>
                                                </>
                                            ) : null}

                                            <div className="intellihire-payment-gateway__total-row">
                                                <span className="intellihire-payment-gateway__total-label">Total Due</span>
                                                <span className="intellihire-payment-gateway__total-amount">{formatAmount(amount)}</span>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="intellihire-payment-gateway__summary" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <span className="intellihire-payment-gateway__total-label">Total Due</span>
                                            <span className="intellihire-payment-gateway__total-amount">{formatAmount(amount)}</span>
                                        </div>
                                    )}

                                    {/* Tabs */}
                                    <div className="intellihire-payment-gateway__tabs">
                                        <button
                                            onClick={() => setMethod("upi")}
                                            className={`intellihire-payment-gateway__tab ${method === "upi" ? "intellihire-payment-gateway__tab--active" : ""}`}
                                        >
                                            <Smartphone size={16} /> UPI
                                        </button>
                                        <button
                                            onClick={() => setMethod("card")}
                                            className={`intellihire-payment-gateway__tab ${method === "card" ? "intellihire-payment-gateway__tab--active" : ""}`}
                                        >
                                            <CreditCard size={16} /> Card
                                        </button>
                                    </div>

                                    {/* Error */}
                                    {errorMsg && (
                                        <div className="intellihire-payment-gateway__error">
                                            <XCircle size={18} />
                                            {errorMsg}
                                        </div>
                                    )}

                                    {/* UPI Form */}
                                    {method === "upi" && (
                                        <div className="intellihire-payment-gateway__form-group">
                                            <label className="intellihire-payment-gateway__label">UPI ID</label>
                                            <input
                                                type="text"
                                                value={upiId}
                                                onChange={(e) => setUpiId(e.target.value)}
                                                placeholder="name@upi"
                                                className="intellihire-payment-gateway__input"
                                            />
                                        </div>
                                    )}

                                    {/* Card Form */}
                                    {method === "card" && (
                                        <>
                                            <div className="intellihire-payment-gateway__form-group">
                                                <label className="intellihire-payment-gateway__label">Card Number</label>
                                                <div className="intellihire-payment-gateway__input-wrapper">
                                                    <CreditCard size={18} className="intellihire-payment-gateway__input-icon" />
                                                    <input
                                                        type="text"
                                                        value={cardDetails.number}
                                                        onChange={(e) => setCardDetails({ ...cardDetails, number: formatCardNumber(e.target.value) })}
                                                        placeholder="0000 0000 0000 0000"
                                                        maxLength={19}
                                                        className="intellihire-payment-gateway__input intellihire-payment-gateway__input--with-icon"
                                                        style={{ fontFamily: 'monospace' }}
                                                    />
                                                </div>
                                            </div>
                                            <div className="intellihire-payment-gateway__form-group">
                                                <label className="intellihire-payment-gateway__label">Name on Card</label>
                                                <input
                                                    type="text"
                                                    value={cardDetails.name}
                                                    onChange={(e) => setCardDetails({ ...cardDetails, name: e.target.value })}
                                                    placeholder="John Doe"
                                                    className="intellihire-payment-gateway__input"
                                                />
                                            </div>
                                            <div className="intellihire-payment-gateway__grid">
                                                <div className="intellihire-payment-gateway__form-group">
                                                    <label className="intellihire-payment-gateway__label">Expiry</label>
                                                    <input
                                                        type="text"
                                                        value={cardDetails.expiry}
                                                        onChange={(e) => {
                                                            let val = e.target.value.replace(/\D/g, '');
                                                            if (val.length >= 2) val = val.substring(0,2) + '/' + val.substring(2,4);
                                                            setCardDetails({ ...cardDetails, expiry: val })
                                                        }}
                                                        placeholder="MM/YY"
                                                        maxLength={5}
                                                        className="intellihire-payment-gateway__input"
                                                        style={{ textAlign: 'center' }}
                                                    />
                                                </div>
                                                <div className="intellihire-payment-gateway__form-group">
                                                    <label className="intellihire-payment-gateway__label">CVV</label>
                                                    <input
                                                        type="password"
                                                        value={cardDetails.cvv}
                                                        onChange={(e) => setCardDetails({ ...cardDetails, cvv: e.target.value.replace(/\D/g, '') })}
                                                        placeholder="•••"
                                                        maxLength={4}
                                                        className="intellihire-payment-gateway__input"
                                                        style={{ textAlign: 'center', letterSpacing: '4px', fontFamily: 'monospace' }}
                                                    />
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </motion.div>
                            )}

                            {(status === "processing" || status === "verifying") && (
                                <motion.div
                                    key="processing"
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="intellihire-payment-gateway__status"
                                >
                                    <div className="intellihire-payment-gateway__spinner-box">
                                        <div className="intellihire-payment-gateway__spinner-bg"></div>
                                        <div className="intellihire-payment-gateway__spinner"></div>
                                        <div className="intellihire-payment-gateway__spinner-icon">
                                            <ShieldCheck size={28} />
                                        </div>
                                    </div>
                                    <h3 className="intellihire-payment-gateway__status-title">
                                        {status === "processing" ? "Processing Payment..." : "Verifying Transaction..."}
                                    </h3>
                                    <p className="intellihire-payment-gateway__status-text">
                                        Please do not close this window or press back.
                                    </p>
                                </motion.div>
                            )}

                            {status === "success" && (
                                <motion.div
                                    key="success"
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="intellihire-payment-gateway__status"
                                >
                                    <motion.div 
                                        initial={{ scale: 0 }}
                                        animate={{ scale: 1 }}
                                        transition={{ type: "spring", bounce: 0.5, damping: 15 }}
                                        className="intellihire-payment-gateway__success-icon"
                                    >
                                        <CheckCircle2 size={40} />
                                    </motion.div>
                                    <h3 className="intellihire-payment-gateway__status-title">Payment Successful</h3>
                                    <p className="intellihire-payment-gateway__status-text">Your subscription is being updated...</p>
                                    
                                    {orderId && (
                                        <div className="intellihire-payment-gateway__reference">
                                            <span>Order Reference</span>
                                            <strong>{orderId}</strong>
                                        </div>
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                    {/* Footer */}
                    {status === "idle" && (
                        <div className="intellihire-payment-gateway__footer">
                            <button
                                onClick={handlePay}
                                className="intellihire-payment-gateway__pay-btn"
                            >
                                Pay {formatAmount(amount)}
                            </button>
                            <div className="intellihire-payment-gateway__disclaimer">
                                <ShieldCheck size={14} />
                                This is a simulated payment gateway. No real money will be charged.
                            </div>
                        </div>
                    )}
                </motion.div>
            </div>
        </>
    );
}


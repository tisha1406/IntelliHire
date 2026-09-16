import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { CreditCard, Smartphone, CheckCircle2, XCircle, ShieldCheck, ArrowRight, X, Lock } from "lucide-react";

export default function PaymentGateway({ isOpen, onClose, onSuccess, amount, orderId, currency = "INR", pricing }) {
    const [method, setMethod] = useState("upi"); // "upi" or "card"
    const [status, setStatus] = useState("idle"); // "idle", "processing", "verifying", "success", "error"
    const [upiId, setUpiId] = useState("");
    const [cardDetails, setCardDetails] = useState({ number: "", name: "", expiry: "", cvv: "" });
    const [errorMsg, setErrorMsg] = useState("");

    // Lock body scroll when modal is open
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

    // Reset state when opened
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

        // Simulate payment processing delays
        setTimeout(() => {
            setStatus("verifying");
            setTimeout(() => {
                setStatus("success");
                setTimeout(() => {
                    // Generate a simulated payment ID
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
        if (parts.length) {
            return parts.join(' ');
        } else {
            return value;
        }
    };

    return createPortal(
        <div 
            className="fixed inset-0 flex items-center justify-center p-4 sm:p-6" 
            style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, zIndex: 99999 }}
        >
            {/* Backdrop */}
            <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm"
                onClick={handleCancel}
            />

            {/* Modal */}
            <motion.div
                initial={{ opacity: 0, scale: 0.96, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.96, y: 20 }}
                className="bg-white rounded-2xl shadow-2xl w-full max-w-[500px] overflow-hidden relative flex flex-col max-h-[90vh]"
            >
                {/* Header */}
                <div className="bg-slate-900 p-5 sm:p-6 text-white relative shrink-0">
                    {status === "idle" && (
                        <button 
                            onClick={handleCancel}
                            className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors p-2 rounded-full hover:bg-slate-800"
                            aria-label="Close"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    )}
                    <div className="flex items-center gap-3 mb-1">
                        <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
                            <ShieldCheck className="w-6 h-6 text-indigo-400" />
                        </div>
                        <div>
                            <h2 className="font-bold text-xl tracking-tight leading-none mb-1">IntelliHire Checkout</h2>
                            <p className="text-indigo-300 text-xs font-medium flex items-center gap-1">
                                <Lock className="w-3 h-3" /> Secure Simulated Payment
                            </p>
                        </div>
                    </div>
                </div>

                {/* Scrollable Body */}
                <div className="p-5 sm:p-6 overflow-y-auto flex-1 bg-slate-50">
                    <AnimatePresence mode="wait">
                        {status === "idle" && (
                            <motion.div
                                key="form"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                            >
                                {/* Order Summary */}
                                {pricing && (
                                    <div className="mb-6 bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
                                        <h4 className="text-xs font-bold text-slate-500 mb-3 uppercase tracking-wider">Order Summary</h4>
                                        {pricing.is_upgrade ? (
                                            <div className="space-y-2.5 text-sm">
                                                <div className="flex justify-between text-slate-600">
                                                    <span>Current Value</span>
                                                    <span>{formatAmount(pricing.current_price)}/yr</span>
                                                </div>
                                                <div className="flex justify-between font-medium text-slate-900">
                                                    <span>New Configuration</span>
                                                    <span>{formatAmount(pricing.new_price)}/yr</span>
                                                </div>
                                                <div className="flex justify-between text-indigo-600 mt-3 pt-3 border-t border-slate-100">
                                                    <span>Prorated Upgrade</span>
                                                    <span>{formatAmount(pricing.difference - pricing.tax)}</span>
                                                </div>
                                                <div className="flex justify-between text-slate-500">
                                                    <span>Taxes (18%)</span>
                                                    <span>{formatAmount(pricing.tax)}</span>
                                                </div>
                                            </div>
                                        ) : pricing.base_price !== undefined ? (
                                            <div className="space-y-2.5 text-sm">
                                                <div className="flex justify-between text-slate-600">
                                                    <span>Base Price</span>
                                                    <span>{formatAmount(pricing.base_price)}</span>
                                                </div>
                                                {(pricing.feature_cost > 0) && (
                                                    <div className="flex justify-between text-slate-600">
                                                        <span>Premium Features</span>
                                                        <span>{formatAmount(pricing.feature_cost)}</span>
                                                    </div>
                                                )}
                                                {(pricing.limit_cost > 0) && (
                                                    <div className="flex justify-between text-slate-600">
                                                        <span>Capacity Add-ons</span>
                                                        <span>{formatAmount(pricing.limit_cost)}</span>
                                                    </div>
                                                )}
                                                <div className="flex justify-between text-slate-500 mt-3 pt-3 border-t border-slate-100">
                                                    <span>Taxes (18%)</span>
                                                    <span>{formatAmount(pricing.tax)}</span>
                                                </div>
                                            </div>
                                        ) : null}
                                        
                                        <div className="flex justify-between items-center mt-3 pt-3 border-t border-slate-200">
                                            <span className="font-bold text-slate-800">Total Due</span>
                                            <span className="font-extrabold text-xl text-slate-900">{formatAmount(amount)}</span>
                                        </div>
                                    </div>
                                )}

                                {/* Fallback summary if no pricing object but amount exists */}
                                {!pricing && (
                                    <div className="mb-6 bg-white rounded-xl p-4 border border-slate-200 shadow-sm flex justify-between items-center">
                                        <span className="font-bold text-slate-800">Total Due</span>
                                        <span className="font-extrabold text-xl text-slate-900">{formatAmount(amount)}</span>
                                    </div>
                                )}

                                {/* Method Tabs */}
                                <div className="flex p-1.5 bg-slate-200/80 rounded-xl mb-6">
                                    <button
                                        onClick={() => setMethod("upi")}
                                        className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                                            method === "upi" ? "bg-white text-indigo-700 shadow shadow-slate-200" : "text-slate-600 hover:text-slate-900"
                                        }`}
                                    >
                                        <Smartphone className="w-4 h-4" /> UPI
                                    </button>
                                    <button
                                        onClick={() => setMethod("card")}
                                        className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                                            method === "card" ? "bg-white text-indigo-700 shadow shadow-slate-200" : "text-slate-600 hover:text-slate-900"
                                        }`}
                                    >
                                        <CreditCard className="w-4 h-4" /> Card
                                    </button>
                                </div>

                                {errorMsg && (
                                    <div className="mb-5 p-3.5 bg-red-50 text-red-700 rounded-xl text-sm border border-red-200 flex items-center gap-2.5 font-medium">
                                        <XCircle className="w-5 h-5 shrink-0" />
                                        {errorMsg}
                                    </div>
                                )}

                                {/* UPI Form */}
                                {method === "upi" && (
                                    <div className="space-y-4 mb-2">
                                        <div>
                                            <label className="block text-sm font-bold text-slate-700 mb-1.5">UPI ID</label>
                                            <input
                                                type="text"
                                                value={upiId}
                                                onChange={(e) => setUpiId(e.target.value)}
                                                placeholder="name@upi"
                                                className="w-full px-4 py-3.5 bg-white border border-slate-300 rounded-xl focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-slate-900 font-medium"
                                            />
                                        </div>
                                    </div>
                                )}

                                {/* Card Form */}
                                {method === "card" && (
                                    <div className="space-y-4 mb-2">
                                        <div>
                                            <label className="block text-sm font-bold text-slate-700 mb-1.5">Card Number</label>
                                            <div className="relative">
                                                <CreditCard className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                                <input
                                                    type="text"
                                                    value={cardDetails.number}
                                                    onChange={(e) => setCardDetails({ ...cardDetails, number: formatCardNumber(e.target.value) })}
                                                    placeholder="0000 0000 0000 0000"
                                                    maxLength={19}
                                                    className="w-full pl-12 pr-4 py-3.5 bg-white border border-slate-300 rounded-xl focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-mono text-slate-900 font-medium"
                                                />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-bold text-slate-700 mb-1.5">Name on Card</label>
                                            <input
                                                type="text"
                                                value={cardDetails.name}
                                                onChange={(e) => setCardDetails({ ...cardDetails, name: e.target.value })}
                                                placeholder="John Doe"
                                                className="w-full px-4 py-3.5 bg-white border border-slate-300 rounded-xl focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-slate-900 font-medium"
                                            />
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="block text-sm font-bold text-slate-700 mb-1.5">Expiry</label>
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
                                                    className="w-full px-4 py-3.5 bg-white border border-slate-300 rounded-xl focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-center text-slate-900 font-medium"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-bold text-slate-700 mb-1.5">CVV</label>
                                                <input
                                                    type="password"
                                                    value={cardDetails.cvv}
                                                    onChange={(e) => setCardDetails({ ...cardDetails, cvv: e.target.value.replace(/\D/g, '') })}
                                                    placeholder="•••"
                                                    maxLength={4}
                                                    className="w-full px-4 py-3.5 bg-white border border-slate-300 rounded-xl focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-center font-mono tracking-widest text-slate-900 font-medium"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </motion.div>
                        )}

                        {(status === "processing" || status === "verifying") && (
                            <motion.div
                                key="processing"
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="flex flex-col items-center justify-center py-16"
                            >
                                <div className="relative w-24 h-24 mb-8">
                                    <div className="absolute inset-0 border-4 border-slate-200 rounded-full"></div>
                                    <div className="absolute inset-0 border-4 border-indigo-600 rounded-full border-t-transparent animate-spin"></div>
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <ShieldCheck className="w-8 h-8 text-indigo-600 animate-pulse" />
                                    </div>
                                </div>
                                <h3 className="text-xl font-bold text-slate-900 mb-2">
                                    {status === "processing" ? "Processing Payment..." : "Verifying Transaction..."}
                                </h3>
                                <p className="text-slate-500 text-sm text-center font-medium">
                                    Please do not close this window or press back.
                                </p>
                            </motion.div>
                        )}

                        {status === "success" && (
                            <motion.div
                                key="success"
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="flex flex-col items-center justify-center py-16"
                            >
                                <motion.div 
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    transition={{ type: "spring", bounce: 0.5, damping: 15 }}
                                    className="w-24 h-24 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-6 shadow-lg shadow-green-100"
                                >
                                    <CheckCircle2 className="w-12 h-12" />
                                </motion.div>
                                <h3 className="text-2xl font-extrabold text-slate-900 mb-2">Payment Successful</h3>
                                <p className="text-slate-500 text-sm font-medium">Your subscription is being updated...</p>
                                
                                {orderId && (
                                    <div className="mt-8 bg-slate-100 p-4 rounded-xl w-full text-center border border-slate-200">
                                        <p className="text-xs text-slate-500 uppercase tracking-wide font-bold mb-1">Order Reference</p>
                                        <p className="font-mono text-sm text-slate-700">{orderId}</p>
                                    </div>
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Footer fixed at bottom */}
                {status === "idle" && (
                    <div className="p-5 sm:p-6 bg-white border-t border-slate-100 shrink-0">
                        <button
                            onClick={handlePay}
                            className="w-full bg-indigo-600 text-white font-bold text-lg py-4 rounded-xl hover:bg-indigo-700 active:bg-indigo-800 transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 hover:shadow-indigo-600/40 hover:-translate-y-0.5"
                        >
                            Pay {formatAmount(amount)}
                        </button>
                        
                        <div className="mt-4 flex items-center justify-center gap-1.5 text-xs text-slate-400 font-medium text-center">
                            <ShieldCheck className="w-4 h-4 shrink-0" />
                            <span>This is a simulated payment gateway. No real money will be charged.</span>
                        </div>
                    </div>
                )}
            </motion.div>
        </div>,
        document.body
    );
}


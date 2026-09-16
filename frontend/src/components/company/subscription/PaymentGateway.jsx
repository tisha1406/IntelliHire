import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { CreditCard, Smartphone, CheckCircle2, XCircle, ShieldCheck, ArrowRight, X } from "lucide-react";

export default function PaymentGateway({ isOpen, onClose, onSuccess, amount, orderId, currency = "INR" }) {
    const [method, setMethod] = useState("upi"); // "upi" or "card"
    const [status, setStatus] = useState("idle"); // "idle", "processing", "verifying", "success", "error"
    const [upiId, setUpiId] = useState("");
    const [cardDetails, setCardDetails] = useState({ number: "", name: "", expiry: "", cvv: "" });
    const [errorMsg, setErrorMsg] = useState("");

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
        if (status === "processing" || status === "verifying") return; // Prevent close during process
        onClose();
    };

    const formatAmount = (val) => {
        return new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: currency,
            maximumFractionDigits: 0,
        }).format(val || 0);
    };

    return createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, zIndex: 9999 }}>
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden relative flex flex-col"
            >
                {/* Header */}
                <div className="bg-slate-900 p-6 text-white relative">
                    {status === "idle" && (
                        <button 
                            onClick={handleCancel}
                            className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    )}
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
                            <ShieldCheck className="w-5 h-5 text-white" />
                        </div>
                        <h2 className="font-bold text-lg tracking-tight">IntelliHire Secure Checkout</h2>
                    </div>
                    <p className="text-slate-400 text-sm mb-1">Amount Payable</p>
                    <div className="text-3xl font-bold flex items-baseline gap-1">
                        {formatAmount(amount)}
                    </div>
                    {orderId && (
                        <p className="text-slate-500 text-xs mt-3 font-mono">Order ID: {orderId}</p>
                    )}
                </div>

                {/* Body */}
                <div className="p-6 flex-1 bg-slate-50">
                    <AnimatePresence mode="wait">
                        {status === "idle" && (
                            <motion.div
                                key="form"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                            >
                                {/* Method Tabs */}
                                <div className="flex p-1 bg-slate-200/70 rounded-xl mb-6">
                                    <button
                                        onClick={() => setMethod("upi")}
                                        className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                                            method === "upi" ? "bg-white text-indigo-700 shadow-sm" : "text-slate-600 hover:text-slate-900"
                                        }`}
                                    >
                                        <Smartphone className="w-4 h-4" /> UPI
                                    </button>
                                    <button
                                        onClick={() => setMethod("card")}
                                        className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                                            method === "card" ? "bg-white text-indigo-700 shadow-sm" : "text-slate-600 hover:text-slate-900"
                                        }`}
                                    >
                                        <CreditCard className="w-4 h-4" /> Card
                                    </button>
                                </div>

                                {errorMsg && (
                                    <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm border border-red-100 flex items-center gap-2">
                                        <XCircle className="w-4 h-4 shrink-0" />
                                        {errorMsg}
                                    </div>
                                )}

                                {/* UPI Form */}
                                {method === "upi" && (
                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 mb-1.5">UPI ID</label>
                                            <input
                                                type="text"
                                                value={upiId}
                                                onChange={(e) => setUpiId(e.target.value)}
                                                placeholder="name@upi"
                                                className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-colors"
                                            />
                                        </div>
                                    </div>
                                )}

                                {/* Card Form */}
                                {method === "card" && (
                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 mb-1.5">Card Number</label>
                                            <div className="relative">
                                                <CreditCard className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                                <input
                                                    type="text"
                                                    value={cardDetails.number}
                                                    onChange={(e) => setCardDetails({ ...cardDetails, number: e.target.value })}
                                                    placeholder="0000 0000 0000 0000"
                                                    maxLength={19}
                                                    className="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-colors font-mono"
                                                />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 mb-1.5">Name on Card</label>
                                            <input
                                                type="text"
                                                value={cardDetails.name}
                                                onChange={(e) => setCardDetails({ ...cardDetails, name: e.target.value })}
                                                placeholder="John Doe"
                                                className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-colors"
                                            />
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="block text-sm font-medium text-slate-700 mb-1.5">Expiry</label>
                                                <input
                                                    type="text"
                                                    value={cardDetails.expiry}
                                                    onChange={(e) => setCardDetails({ ...cardDetails, expiry: e.target.value })}
                                                    placeholder="MM/YY"
                                                    maxLength={5}
                                                    className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-colors text-center"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-slate-700 mb-1.5">CVV</label>
                                                <input
                                                    type="password"
                                                    value={cardDetails.cvv}
                                                    onChange={(e) => setCardDetails({ ...cardDetails, cvv: e.target.value })}
                                                    placeholder="•••"
                                                    maxLength={4}
                                                    className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-colors text-center font-mono tracking-widest"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                )}

                                <button
                                    onClick={handlePay}
                                    className="w-full mt-8 bg-indigo-600 text-white font-medium py-3.5 rounded-xl hover:bg-indigo-700 active:bg-indigo-800 transition-colors flex items-center justify-center gap-2 group shadow-sm shadow-indigo-600/20"
                                >
                                    Pay {formatAmount(amount)}
                                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </button>
                                
                                <div className="mt-4 flex items-center justify-center gap-2 text-xs text-slate-500">
                                    <ShieldCheck className="w-4 h-4" />
                                    This is a simulated payment gateway. No real money is charged.
                                </div>
                            </motion.div>
                        )}

                        {(status === "processing" || status === "verifying") && (
                            <motion.div
                                key="processing"
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="flex flex-col items-center justify-center py-12"
                            >
                                <div className="relative w-20 h-20 mb-6">
                                    <div className="absolute inset-0 border-4 border-slate-100 rounded-full"></div>
                                    <div className="absolute inset-0 border-4 border-indigo-600 rounded-full border-t-transparent animate-spin"></div>
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <ShieldCheck className="w-6 h-6 text-indigo-600 animate-pulse" />
                                    </div>
                                </div>
                                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                                    {status === "processing" ? "Processing Payment..." : "Verifying Transaction..."}
                                </h3>
                                <p className="text-slate-500 text-sm text-center">
                                    Please do not close this window or press back.
                                </p>
                            </motion.div>
                        )}

                        {status === "success" && (
                            <motion.div
                                key="success"
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="flex flex-col items-center justify-center py-12"
                            >
                                <motion.div 
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    transition={{ type: "spring", bounce: 0.5 }}
                                    className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-6"
                                >
                                    <CheckCircle2 className="w-10 h-10" />
                                </motion.div>
                                <h3 className="text-xl font-bold text-slate-900 mb-2">Payment Successful!</h3>
                                <p className="text-slate-500 text-sm">Redirecting...</p>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </motion.div>
        </div>,
        document.body
    );
}


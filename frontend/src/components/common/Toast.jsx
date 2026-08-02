import React, { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FaCheckCircle, FaExclamationCircle, FaInfoCircle, FaTimes } from "react-icons/fa";

export default function Toast({
    message,
    type = "success", // success, error, info, warning
    onClose,
    duration = 3000,
    className = "",
    ...props
}) {
    useEffect(() => {
        const timer = setTimeout(() => {
            if (onClose) onClose();
        }, duration);

        return () => clearTimeout(timer);
    }, [duration, onClose]);

    const getIcon = () => {
        switch (type) {
            case "success":
                return <FaCheckCircle className="toast-icon text-success" />;
            case "error":
                return <FaExclamationCircle className="toast-icon text-danger" />;
            case "warning":
                return <FaExclamationCircle className="toast-icon text-warning" />;
            case "info":
            default:
                return <FaInfoCircle className="toast-icon text-info" />;
        }
    };

    return (
        <motion.div
            className={`toast-alert-box type-${type} ${className}`}
            initial={{
                opacity:0,
                x:60,
                scale:.96
            }}

            animate={{
                opacity:1,
                x:0,
                scale:1
            }}

            exit={{
                opacity:0,
                x:80,
                scale:.94
            }}
            transition={{ type: "spring", stiffness: 420, damping: 30 }}
            {...props}
        >
            <div className="toast-body">
                {getIcon()}
                <span className="toast-message">{message}</span>
            </div>
            <button className="toast-dismiss-btn" onClick={onClose}>
                <FaTimes />
            </button>
        </motion.div>
    );
}

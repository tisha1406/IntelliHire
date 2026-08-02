import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FaTimes } from "react-icons/fa";

export default function Modal({
    isOpen,
    onClose,
    title,
    children,
    size = "md", // sm, md, lg
    position = "center", // center, top-right
    className = "",
    ...props
}) {
    const wrapperClass = position === "top-right" ? "modal-wrapper-top-right" : "modal-wrapper-centered";

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="modal-root-overlay">
                    {/* Backdrop */}
                    <motion.div
                        className="modal-backdrop-blur"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                    />

                    {/* Panel wrapper */}
                    <div className={wrapperClass}>
                        <motion.div
                            className={`modal-panel-card size-${size} ${className}`}
                            initial={{ opacity: 0, scale: 0.95, y: 15 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 15 }}
                            transition={{ type: "spring", stiffness: 350, damping: 28 }}
                            {...props}
                        >
                            {title && (
                                <div className="modal-panel-header">
                                    <h4 className="modal-panel-title">{title}</h4>
                                    <button className="modal-close-btn" type="button" onClick={onClose}>
                                        <FaTimes />
                                    </button>
                                </div>
                            )}
                            <div className="modal-panel-body">
                                {children}
                            </div>
                        </motion.div>
                    </div>
                </div>
            )}
        </AnimatePresence>
    );
}

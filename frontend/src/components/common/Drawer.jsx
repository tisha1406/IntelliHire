import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FaTimes } from "react-icons/fa";

export default function Drawer({
    isOpen,
    onClose,
    title,
    children,
    size = "md", // sm, md, lg
    className = "",
    ...props
}) {
    return (
        <AnimatePresence>
            {isOpen && (
                <div className="drawer-root-overlay">
                    {/* Backdrop */}
                    <motion.div
                        className="drawer-backdrop-blur"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                    />

                    {/* Drawer Content */}
                    <motion.div
                        className={`drawer-slide-panel size-${size} ${className}`}
                        initial={{ x: "100%" }}
                        animate={{ x: 0 }}
                        exit={{ x: "100%" }}
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                        {...props}
                    >
                        <div className="drawer-header">
                            <h4 className="drawer-title">{title}</h4>
                            <button className="drawer-close-btn" type="button" onClick={onClose}>
                                <FaTimes />
                            </button>
                        </div>
                        <div className="drawer-body">
                            {children}
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}

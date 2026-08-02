import React, { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FaTimes } from "react-icons/fa";

export default function Drawer({
    isOpen,
    onClose,
    title,
    children,
    footer,
    size = "md", // sm, md, lg
    className = "",
    ...props
}) {

    // Disable body scroll while drawer is open
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

    // Close drawer with Escape key
    useEffect(() => {

        const handleKeyDown = (e) => {

            if (e.key === "Escape" && isOpen) {

                onClose();

            }

        };

        window.addEventListener("keydown", handleKeyDown);

        return () => {

            window.removeEventListener(
                "keydown",
                handleKeyDown
            );

        };

    }, [isOpen, onClose]);

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

                    {/* Drawer */}

                    <motion.div
                        className={`drawer-slide-panel size-${size} ${className}`}
                        initial={{ x: "100%" }}
                        animate={{ x: 0 }}
                        exit={{ x: "100%" }}
                        transition={{
                            type: "spring",
                            stiffness: 300,
                            damping: 30,
                        }}
                        onClick={(e) => e.stopPropagation()}
                        {...props}
                    >

                        <div className="drawer-header">

                            <h4 className="drawer-title">

                                {title}

                            </h4>

                            <button
                                className="drawer-close-btn"
                                type="button"
                                onClick={onClose}
                            >

                                <FaTimes />

                            </button>

                        </div>

                        <div className="drawer-body">

                            {children}

                        </div>

                        {footer && (

                            <div className="drawer-footer">

                                {footer}

                            </div>

                        )}

                    </motion.div>

                </div>

            )}

        </AnimatePresence>

    );

}
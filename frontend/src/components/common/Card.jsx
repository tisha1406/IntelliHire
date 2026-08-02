import React from "react";
import { motion } from "framer-motion";

export default function Card({
    children,
    className = "",
    whileHover = null,
    onClick = null,
    ...props
}) {
    const hoverAnim = whileHover || (onClick ? { y: -3, scale: 1.005 } : {});

    return (
        <motion.div
            className={`custom-card-panel ${className}`}
            whileHover={hoverAnim}
            onClick={onClick}
            transition={{ duration: 0.2 }}
            {...props}
        >
            {children}
        </motion.div>
    );
}

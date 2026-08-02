import React from "react";
import { motion } from "framer-motion";

export default function MetricCard({
    title,
    value,
    subtitle,
    badgeText,
    badgeVariant = "primary",
    className = "",
    ...props
}) {
    return (
        <motion.div
            className={`metric-card ${className}`}
            whileHover={{ y: -4, scale: 1.01 }}
            transition={{ duration: 0.2 }}
            {...props}
        >
            <div className="metric-header">
                <span className="metric-title">{title}</span>
                {badgeText && (
                    <span className={`custom-badge badge-${badgeVariant} metric-badge`}>
                        {badgeText}
                    </span>
                )}
            </div>
            <div className="metric-body">
                <h3 className="metric-value">{value}</h3>
                {subtitle && <p className="metric-subtitle">{subtitle}</p>}
            </div>
        </motion.div>
    );
}

import React from "react";
import { motion } from "framer-motion";

export default function ChartCard({
    title,
    subtitle,
    children,
    className = "",
    action = null,
    ...props
}) {
    return (
        <motion.div
            className={`chart-card-wrapper ${className}`}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            {...props}
        >
            <div className="chart-card-header">
                <div>
                    <h3 className="chart-card-title">{title}</h3>
                    {subtitle && <p className="chart-card-subtitle">{subtitle}</p>}
                </div>
                {action && <div className="chart-card-action">{action}</div>}
            </div>
            <div className="chart-card-content">
                {children}
            </div>
        </motion.div>
    );
}

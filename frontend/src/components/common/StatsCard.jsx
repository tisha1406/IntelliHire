import React from "react";
import { motion } from "framer-motion";
import { FaArrowUp, FaArrowDown } from "react-icons/fa";

export default function StatsCard({
    title,
    value,
    change,
    icon,
    color,
    trendPercent,
    isPositive = true,
    className = "",
    ...props
}) {
    return (
        <motion.div
            className={`stats-card ${className}`}
            whileHover={{ y: -6, scale: 1.02 }}
            transition={{ duration: 0.25 }}
            {...props}
        >
            <div className="stats-icon" style={{ background: color || "var(--primary)" }}>
                {icon}
            </div>
            <div className="stats-content">
                <span>{title}</span>
                <h2>{value}</h2>
                <div className="stats-trend-info">
                    {change && (
                        <span className={`stats-change ${isPositive ? "trend-up" : "trend-down"}`}>
                            {isPositive ? <FaArrowUp className="trend-arrow" /> : <FaArrowDown className="trend-arrow" />}
                            {change}
                        </span>
                    )}
                </div>
            </div>
        </motion.div>
    );
}

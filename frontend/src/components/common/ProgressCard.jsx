import React from "react";
import { motion } from "framer-motion";

export default function ProgressCard({
    title,
    current,
    target,
    progress, // percentage 0-100
    color = "var(--primary)",
    className = "",
    ...props
}) {
    const computedProgress = Math.min(100, Math.max(0, progress !== undefined ? progress : (current / target) * 100));

    return (
        <div className={`progress-card-item ${className}`} {...props}>
            <div className="progress-card-header">
                <span className="progress-card-title">{title}</span>
                <span className="progress-card-stats">
                    <strong>{current}</strong> / {target}
                </span>
            </div>
            <div className="progress-track-bg">
                <motion.div
                    className="progress-fill-bar"
                    style={{ background: color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${computedProgress}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                />
            </div>
            <div className="progress-card-footer">
                <span>Completion</span>
                <span>{Math.round(computedProgress)}%</span>
            </div>
        </div>
    );
}

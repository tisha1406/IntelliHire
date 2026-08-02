import React from "react";
import { motion } from "framer-motion";

export default function Tabs({
    tabs = [],
    activeTab,
    onChange,
    className = "",
    ...props
}) {
    return (
        <div className={`custom-tabs-container ${className}`} {...props}>
            <div className="tabs-header-row">
                {tabs.map((tab) => {
                    const isActive = tab.id === activeTab;
                    return (
                        <button
                            key={tab.id}
                            className={`tab-trigger-btn ${isActive ? "is-active" : ""}`}
                            onClick={() => onChange(tab.id)}
                            type="button"
                        >
                            {tab.icon && <span className="tab-trigger-icon">{tab.icon}</span>}
                            <span className="tab-trigger-label">{tab.label}</span>
                            {isActive && (
                                <motion.div
                                    className="active-tab-indicator-bar"
                                    layoutId="activeTabIndicator"
                                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                                />
                            )}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}

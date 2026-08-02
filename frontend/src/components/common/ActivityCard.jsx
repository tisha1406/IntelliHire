import React from "react";
import { FaUserPlus, FaCheckCircle, FaExclamationTriangle, FaFileInvoice } from "react-icons/fa";

export default function ActivityCard({
    activity,
    className = "",
    ...props
}) {
    const { type, title, description, time } = activity;

    const getActivityIcon = () => {
        switch (type) {
            case "candidate":
                return <FaUserPlus className="activity-icon act-candidate" />;
            case "interview":
                return <FaCheckCircle className="activity-icon act-interview" />;
            case "campaign":
                return <FaFileInvoice className="activity-icon act-campaign" />;
            case "report":
                return <FaCheckCircle className="activity-icon act-report" />;
            default:
                return <FaExclamationTriangle className="activity-icon act-default" />;
        }
    };

    return (
        <div className={`activity-log-card ${className}`} {...props}>
            <div className="activity-icon-wrapper">
                {getActivityIcon()}
            </div>
            <div className="activity-content">
                <span className="activity-time-stamp">{time}</span>
                <h5 className="activity-title">{title}</h5>
                <p className="activity-desc">{description}</p>
            </div>
        </div>
    );
}

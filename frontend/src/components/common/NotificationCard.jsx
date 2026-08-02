import React from "react";
import { FaTrash, FaCheck, FaInfoCircle, FaShieldAlt, FaBriefcase, FaUserCircle } from "react-icons/fa";
import { motion } from "framer-motion";

export default function NotificationCard({
    notification,
    onToggleRead,
    onDelete,
    className = "",
    ...props
}) {
    const { id, type, title, message, time, unread } = notification;

    const getIcon = () => {
        switch (type) {
            case "system":
                return <FaInfoCircle className="notif-type-icon icon-system" />;
            case "security":
                return <FaShieldAlt className="notif-type-icon icon-security" />;
            case "recruitment":
                return <FaBriefcase className="notif-type-icon icon-recruitment" />;
            case "candidate":
                return <FaUserCircle className="notif-type-icon icon-candidate" />;
            default:
                return <FaInfoCircle className="notif-type-icon" />;
        }
    };

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -50 }}
            className={`notification-item-card ${unread ? "is-unread" : ""} ${className}`}
            {...props}
        >
            <div className="notif-icon-col">
                {getIcon()}
                {unread && <span className="unread-pulse-dot" />}
            </div>
            <div className="notif-content-col">
                <div className="notif-header-row">
                    <h5 className="notif-card-title">{title}</h5>
                    <span className="notif-card-time">{time}</span>
                </div>
                <p className="notif-card-msg">{message}</p>
            </div>
            <div className="notif-actions-col">
                <button
                    className="notif-action-btn read-toggle"
                    onClick={() => onToggleRead(id)}
                    title={unread ? "Mark as Read" : "Mark as Unread"}
                >
                    <FaCheck />
                </button>
                <button
                    className="notif-action-btn delete-btn"
                    onClick={() => onDelete(id)}
                    title="Delete Notification"
                >
                    <FaTrash />
                </button>
            </div>
        </motion.div>
    );
}

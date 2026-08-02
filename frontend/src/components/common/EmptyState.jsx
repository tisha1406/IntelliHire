import React from "react";
import { FaInbox } from "react-icons/fa";

export default function EmptyState({
    title = "No data available",
    description = "There are no records matching your query.",
    icon = <FaInbox />,
    action = null,
    className = "",
    ...props
}) {
    return (
        <div className={`custom-empty-state ${className}`} {...props}>
            <div className="empty-state-icon-circle">
                {icon}
            </div>
            <h4 className="empty-state-title">{title}</h4>
            <p className="empty-state-desc">{description}</p>
            {action && <div className="empty-state-action-slot">{action}</div>}
        </div>
    );
}

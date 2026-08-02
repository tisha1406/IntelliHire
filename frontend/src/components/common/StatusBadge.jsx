import React from "react";
import Badge from "./Badge";

export default function StatusBadge({
    status,
    className = "",
    ...props
}) {
    const getVariant = (s) => {
        switch (s?.toLowerCase()) {
            case "active":
            case "completed":
            case "selected":
            case "hired":
            case "shortlisted":
            case "ready":
                return "success";
            case "closed":
            case "rejected":
            case "inactive":
            case "failed":
            case "deactivated":
                return "danger";
            case "draft":
            case "archived":
            case "unread":
                return "neutral";
            case "scheduled":
            case "pending":
            case "assessment pending":
            case "under review":
            case "in progress":
                return "warning";
            default:
                return "neutral";
        }
    };

    return (
        <Badge variant={getVariant(status)} className={`status-badge-wrapper ${className}`} {...props}>
            {status}
        </Badge>
    );
}

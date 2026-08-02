import React from "react";
import { motion } from "framer-motion";
import { FaEye, FaEdit, FaCopy, FaTrashAlt, FaMapMarkerAlt, FaUser } from "react-icons/fa";
import Badge from "./Badge";

export default function CampaignCard({
    campaign,
    onView,
    onEdit,
    onDuplicate,
    onDelete,
    className = "",
    layout = "grid", // grid or list
    ...props
}) {
    const {
        name,
        department,
        location,
        recruiter,
        status,
        applicants,
        aiScreeningProgress,
        createdDate,
        deadline
    } = campaign;

    const getStatusVariant = (s) => {
        switch (s?.toLowerCase()) {
            case "active":
                return "success";
            case "closed":
                return "danger";
            case "draft":
                return "neutral";
            case "scheduled":
                return "warning";
            default:
                return "neutral";
        }
    };

    const isGrid = layout === "grid";

    return (
        <motion.div
            className={`campaign-card-item ${isGrid ? "camp-grid" : "camp-list"} ${className}`}
            whileHover={{ y: -2, scale: 1.005 }}
            transition={{ duration: 0.2 }}
            {...props}
        >
            {/* Clickable area: title + body → navigates to detail */}
            <div className="camp-clickable-area" onClick={onView} style={{ cursor: "pointer" }}>
                <div className="camp-header">
                    <div>
                        <h4 className="camp-title">{name}</h4>
                        <div className="camp-sub-meta">
                            <span className="camp-dept">{department}</span>
                            <span className="camp-divider">•</span>
                            <span className="camp-loc"><FaMapMarkerAlt className="meta-icon" /> {location}</span>
                        </div>
                    </div>
                    <Badge variant={getStatusVariant(status)} className="camp-status">
                        {status}
                    </Badge>
                </div>

                <div className="camp-body">
                    <div className="camp-metrics">
                        <div className="metric-col">
                            <span className="metric-val">{applicants}</span>
                            <span className="metric-lbl">Applicants</span>
                        </div>
                        <div className="metric-col">
                            <span className="metric-val">{recruiter}</span>
                            <span className="metric-lbl"><FaUser className="meta-icon" /> Recruiter</span>
                        </div>
                    </div>

                    <div className="camp-progress-section">
                        <div className="progress-labels">
                            <span>AI Screening Progress</span>
                            <span>{aiScreeningProgress}%</span>
                        </div>
                        <div className="camp-progress-track">
                            <motion.div
                                className="camp-progress-fill"
                                initial={{ width: 0 }}
                                animate={{ width: `${aiScreeningProgress}%` }}
                                transition={{ duration: 0.6 }}
                            />
                        </div>
                    </div>
                </div>
            </div> {/* end camp-clickable-area */}

            <div className="camp-footer">
                <div className="camp-dates">
                    <span>Created {createdDate} &bull; Ends {deadline}</span>
                </div>
                <div className="camp-actions" onClick={(e) => e.stopPropagation()}>
                    <button className="camp-action-btn view-btn" onClick={onView} title="View Details">
                        <FaEye />
                    </button>
                    <button className="camp-action-btn edit-btn" onClick={onEdit} title="Edit Campaign">
                        <FaEdit />
                    </button>
                    <button className="camp-action-btn duplicate-btn" onClick={onDuplicate} title="Duplicate Campaign">
                        <FaCopy />
                    </button>
                    <button className="camp-action-btn delete-btn" onClick={onDelete} title="Delete Campaign">
                        <FaTrashAlt />
                    </button>
                </div>
            </div>
        </motion.div>
    );
}

import React from "react";
import { motion } from "framer-motion";
import { FaCalendarAlt, FaCheck, FaTimes, FaEye } from "react-icons/fa";
import Badge from "./Badge";

export default function CandidateCard({
    candidate,
    onView,
    onSchedule,
    onShortlist,
    onReject,
    className = "",
    ...props
}) {
    const {
        name,
        email,
        experience,
        skills = [],
        aiMatch,
        resumeScore,
        interviewScore,
        currentStage,
        status
    } = candidate;

    // Get color variant for stage
    const getStageVariant = (stage) => {
        switch (stage?.toLowerCase()) {
            case "selected":
            case "offered":
                return "success";
            case "interviewing":
            case "interview scheduled":
                return "primary";
            case "screening":
                return "info";
            case "rejected":
                return "danger";
            default:
                return "neutral";
        }
    };

    // Get initials
    const getInitials = (n) => {
        return n
            ? n
                  .split(" ")
                  .map((x) => x[0])
                  .join("")
                  .toUpperCase()
                  .slice(0, 2)
            : "CN";
    };

    return (
        <motion.div
            className={`candidate-grid-card ${className}`}
            whileHover={{ y: -6, scale: 1.01 }}
            transition={{ duration: 0.2 }}
            {...props}
        >
            <div className="card-top-info">
                <div className="candidate-avatar-circle">
                    {getInitials(name)}
                </div>
                <div className="candidate-meta-details">
                    <h4 className="candidate-name">{name}</h4>
                    <p className="candidate-email">{email}</p>
                </div>
                <Badge variant={getStageVariant(currentStage)} className="candidate-stage-badge">
                    {currentStage}
                </Badge>
            </div>

            <div className="candidate-experience-row">
                <span>{experience}</span>
            </div>

            {/* Match Indicators */}
            <div className="candidate-scores-grid">
                <div className="score-metric">
                    <strong className="ai-score">{aiMatch}%</strong>
                    <span>AI Match</span>
                </div>
                <div className="score-metric">
                    <strong className="resume-score">{resumeScore}</strong>
                    <span>Resume</span>
                </div>
                <div className="score-metric">
                    <strong className="interview-score">{interviewScore || "-"}</strong>
                    <span>Interview</span>
                </div>
            </div>

            {/* Skills Tag List */}
            <div className="candidate-skills-wrap">
                {skills.slice(0, 3).map((skill, idx) => (
                    <Badge key={idx} variant="neutral" className="skill-badge-mini">
                        {skill}
                    </Badge>
                ))}
                {skills.length > 3 && (
                    <span style={{ fontSize: 9, color: "var(--text-secondary)" }}>+{skills.length - 3}</span>
                )}
            </div>

            {/* Action Buttons */}
            <div className="candidate-actions-footer">
                <button className="icon-btn-action view-btn" onClick={onView} title="View Profile">
                    <FaEye />
                </button>
                <button className="icon-btn-action schedule-btn" onClick={onSchedule} title="Schedule AI Interview">
                    <FaCalendarAlt />
                </button>
                {status !== "Shortlisted" && (
                    <button className="icon-btn-action shortlist-btn" onClick={onShortlist} title="Shortlist Candidate">
                        <FaCheck />
                    </button>
                )}
                {status !== "Rejected" && (
                    <button className="icon-btn-action reject-btn" onClick={onReject} title="Reject Candidate">
                        <FaTimes />
                    </button>
                )}
            </div>
        </motion.div>
    );
}

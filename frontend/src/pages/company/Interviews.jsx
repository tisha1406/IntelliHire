import React, { useState, useEffect } from "react";
import { FaCalendarPlus, FaRobot, FaCheckCircle, FaTimesCircle, FaStar } from "react-icons/fa";
import { AnimatePresence } from "framer-motion";

// Services
import interviewService from "../../services/company/interviewService";

// Common components
import PageHeader from "../../components/common/PageHeader";
import StatsCard from "../../components/common/StatsCard";
import DataTable from "../../components/common/DataTable";
import SearchBar from "../../components/common/SearchBar";
import FilterDropdown from "../../components/common/FilterDropdown";
import StatusBadge from "../../components/common/StatusBadge";
import Button from "../../components/common/Button";
import Modal from "../../components/common/Modal";
import Badge from "../../components/common/Badge";
import ConfirmDialog from "../../components/common/ConfirmDialog";
import Toast from "../../components/common/Toast";
import Card from "../../components/common/Card";

// CSS Styles
import "../../styles/company/Interviews.css";

export default function Interviews() {
    const [interviews, setInterviews] = useState([]);
    const [stats, setStats] = useState({ upcoming: 0, completed: 0, cancelled: 0, averageScore: 0 });
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [selectedStatus, setSelectedStatus] = useState("");

    // Details Modal state
    const [selectedInt, setSelectedInt] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Cancel Dialog state
    const [cancelId, setCancelId] = useState(null);
    const [isConfirmOpen, setIsConfirmOpen] = useState(false);

    // Toast feedback
    const [toast, setToast] = useState(null);

    const triggerToast = (msg, type = "success") => {
        setToast({ message: msg, type });
    };

    const fetchInterviews = async () => {
        try {
            setLoading(true);
            const res = await interviewService.getInterviews();
            setStats(res.stats || { upcoming: 0, completed: 0, cancelled: 0, averageScore: 0 });
            setInterviews(res.interviews || []);
        } catch (err) {
            console.error("Failed to fetch interviews:", err);
            triggerToast("Unable to load interviews data from backend.", "error");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchInterviews();
    }, []);

    const statusOptions = [
        { value: "Scheduled", label: "Scheduled" },
        { value: "Completed", label: "Completed" },
        { value: "Cancelled", label: "Cancelled" }
    ];

    // Handlers
    const handleViewEvaluation = (int) => {
        if (int.status === "Completed") {
            setSelectedInt(int);
            setIsModalOpen(true);
        } else {
            triggerToast("Evaluation reports are only available for Completed AI interviews.", "warning");
        }
    };

    const handleJoin = (int) => {
        triggerToast(`Launching video console to join ${int.candidate}'s session.`, "info");
    };

    const handleReschedule = (int) => {
        triggerToast(`Reschedule invitation email triggered for ${int.candidate}.`, "info");
    };

    const handleCancelClick = (id) => {
        setCancelId(id);
        setIsConfirmOpen(true);
    };

    const handleConfirmCancel = async () => {
        try {
            await interviewService.cancelInterview(cancelId);
            setIsConfirmOpen(false);
            setCancelId(null);
            triggerToast("AI Interview session cancelled successfully.", "success");
            await fetchInterviews();
        } catch (err) {
            console.error("Failed to cancel interview:", err);
            triggerToast("Failed to cancel AI Interview session.", "error");
        }
    };

    // Filter logic
    const filteredInterviews = interviews.filter((int) => {
        const candidateMatch = int.candidate ? int.candidate.toLowerCase().includes(search.toLowerCase()) : false;
        const positionMatch = int.position ? int.position.toLowerCase().includes(search.toLowerCase()) : false;
        const interviewerMatch = int.interviewer ? int.interviewer.toLowerCase().includes(search.toLowerCase()) : false;
        
        const matchesSearch = candidateMatch || positionMatch || interviewerMatch;
        const matchesStatus = selectedStatus === "" || int.status === selectedStatus;

        return matchesSearch && matchesStatus;
    });

    // Columns Definition
    const columns = [
        {
            key: "candidate",
            label: "Candidate",
            sortable: true,
            render: (val, row) => (
                <div className="table-candidate-cell" onClick={() => handleViewEvaluation(row)}>
                    <strong>{val}</strong>
                    <span>ID: {row.id.substring(row.id.length - 8)}</span>
                </div>
            )
        },
        { key: "position", label: "Position", sortable: true },
        { key: "interviewer", label: "Hiring Loop Panel" },
        { key: "date", label: "Date", sortable: true },
        { key: "time", label: "Time" },
        {
            key: "status",
            label: "Status",
            sortable: true,
            render: (val) => <StatusBadge status={val} />
        },
        {
            key: "aiScore",
            label: "AI Score",
            sortable: true,
            render: (val) => val ? <strong className="ai-score-value-bold">{val} / 100</strong> : <span className="ai-score-pending">-</span>
        },
        {
            key: "actions",
            label: "Actions",
            render: (_, row) => (
                <div className="table-actions-cell">
                    {row.status === "Scheduled" ? (
                        <>
                            <Button variant="primary" size="sm" onClick={() => handleJoin(row)}>
                                Join
                            </Button>
                            <Button variant="outline" size="sm" onClick={() => handleReschedule(row)}>
                                Reschedule
                            </Button>
                            <Button variant="ghost" size="sm" className="btn-text-danger" onClick={() => handleCancelClick(row.id)}>
                                Cancel
                            </Button>
                        </>
                    ) : row.status === "Completed" ? (
                        <Button variant="ghost" size="sm" onClick={() => handleViewEvaluation(row)}>
                            View Evaluation
                        </Button>
                    ) : (
                        <span className="text-muted-italics">No actions</span>
                    )}
                </div>
            )
        }
    ];

    if (loading) {
        return (
            <div className="interviews-page-wrapper">
                <PageHeader
                    title="AI Interviews Portal"
                    subtitle="Oversee automated voice screening sessions, check evaluations scores, and manage schedules."
                    breadcrumbs={[{ label: "AI Interviews" }]}
                />
                <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "350px", flexDirection: "column", gap: "16px" }}>
                    <div className="loading-spinner-circle" style={{
                        width: "48px",
                        height: "48px",
                        borderRadius: "50%",
                        border: "3px solid var(--border)",
                        borderTopColor: "var(--primary)",
                        animation: "spin 1s linear infinite"
                    }} />
                    <style>{`
                        @keyframes spin {
                            to { transform: rotate(360deg); }
                        }
                    `}</style>
                    <p style={{ color: "var(--text-secondary)", fontSize: "14px" }}>Loading interviews data...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="interviews-page-wrapper">
            <PageHeader
                title="AI Interviews Portal"
                subtitle="Oversee automated voice screening sessions, check evaluations scores, and manage schedules."
                breadcrumbs={[{ label: "AI Interviews" }]}
                actions={
                    <Button variant="primary" iconLeft={<FaCalendarPlus />} onClick={() => triggerToast("New interview scheduling locked. Schedule via candidate list page instead.", "warning")}>
                        Schedule Interview
                    </Button>
                }
            />

            {/* Statistics */}
            <div className="dashboard-stats-grid">
                <StatsCard
                    title="Scheduled (Upcoming)"
                    value={stats.upcoming}
                    icon={<FaCalendarPlus />}
                    color="linear-gradient(135deg, #3B82F6, #60A5FA)"
                />
                <StatsCard
                    title="Interviews Completed"
                    value={stats.completed}
                    icon={<FaCheckCircle />}
                    color="linear-gradient(135deg, #10B981, #34D399)"
                />
                <StatsCard
                    title="Cancelled Sessions"
                    value={stats.cancelled}
                    icon={<FaTimesCircle />}
                    color="linear-gradient(135deg, #EF4444, #F87171)"
                />
                <StatsCard
                    title="Average AI Fit Score"
                    value={`${stats.averageScore} / 100`}
                    icon={<FaRobot />}
                    color="linear-gradient(135deg, #8B5CF6, #C084FC)"
                />
            </div>

            {/* Filters panel */}
            <Card className="candidates-filter-panel">
                <div className="filter-inputs">
                    <SearchBar value={search} onChange={setSearch} placeholder="Search candidate, role..." />
                    <FilterDropdown
                        label="Status"
                        options={statusOptions}
                        selected={selectedStatus}
                        onChange={setSelectedStatus}
                    />
                </div>
            </Card>

            {/* Interviews Table list */}
            <Card className="candidates-table-card">
                <DataTable
                    columns={columns}
                    data={filteredInterviews}
                />
            </Card>

            {/* Evaluation Modal Details */}
            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={selectedInt ? `${selectedInt.candidate} - AI Evaluation` : "Evaluation Feedback"}
                size="lg"
            >
                {selectedInt && selectedInt.evaluation && (
                    <div className="evaluation-modal-details-grid">
                        <div className="eval-summary-card">
                            <div className="score-badge-circle">
                                <h3>{selectedInt.aiScore}</h3>
                                <span>Fit Score</span>
                            </div>
                            <div className="eval-meta-col">
                                <h3>{selectedInt.candidate}</h3>
                                <p>{selectedInt.position}</p>
                                <Badge variant="primary" className="mt-2">
                                    Verdict: {selectedInt.evaluation.recommendation}
                                </Badge>
                            </div>
                        </div>

                        {/* Summary description */}
                        <div className="modal-inner-section">
                            <h5 className="section-title"><FaRobot className="icon-eval" /> AI Screening Summary</h5>
                            <p className="eval-paragraph-desc">{selectedInt.evaluation.summary}</p>
                        </div>

                        {/* Strengths & Weaknesses */}
                        <div className="strengths-weaknesses-split">
                            <div className="eval-box strength-box">
                                <h5>Candidate Strengths</h5>
                                <ul>
                                    {selectedInt.evaluation.strengths.map((str, idx) => (
                                        <li key={idx}>✓ {str}</li>
                                    ))}
                                </ul>
                            </div>
                            <div className="eval-box weakness-box">
                                <h5>Identified Gaps</h5>
                                <ul>
                                    {selectedInt.evaluation.weaknesses.map((weak, idx) => (
                                        <li key={idx}>⚠️ {weak}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>

                        {/* Questions & Transcript list */}
                        <div className="modal-inner-section">
                            <h5 className="section-title">Question Transcript & Sentiment Analysis</h5>
                            <div className="transcripts-list">
                                {selectedInt.evaluation.questions && selectedInt.evaluation.questions.map((qObj, idx) => (
                                    <div key={idx} className="transcript-box-item">
                                        <div className="transcript-question-line">
                                            <strong>Q{idx + 1}: {qObj.q}</strong>
                                            <Badge variant={qObj.score > 90 ? "success" : "primary"}>
                                                Score: {qObj.score}%
                                            </Badge>
                                        </div>
                                        <p className="transcript-answer-line">
                                            <strong>A:</strong> "{qObj.a}"
                                        </p>
                                        <div className="transcript-sentiment-bar">
                                            <span>Sentiment Analysis: <strong>{qObj.sentiment}</strong></span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </Modal>

            {/* Cancel confirm */}
            <ConfirmDialog
                isOpen={isConfirmOpen}
                onClose={() => setIsConfirmOpen(false)}
                onConfirm={handleConfirmCancel}
                title="Cancel Session"
                message="Are you sure you want to cancel this AI voice interview session? The scheduler will notify the applicant."
            />

            <div className="toast-container">
                <AnimatePresence>
                    {toast && (
                        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}

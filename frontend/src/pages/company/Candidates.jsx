import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {  FaList, FaUserPlus, FaCheck, FaTimes, FaUserSlash, FaFilePdf, FaRobot } from "react-icons/fa";

import { useEffect } from "react";
import candidateService from "../../services/company/candidateService";

import PageHeader from "../../components/common/PageHeader";
import SearchBar from "../../components/common/SearchBar";
import FilterDropdown from "../../components/common/FilterDropdown";
import Tabs from "../../components/common/Tabs";
import DataTable from "../../components/common/DataTable";
import Pagination from "../../components/common/Pagination";
import CandidateCard from "../../components/common/CandidateCard";
import EmptyState from "../../components/common/EmptyState";
import Timeline from "../../components/common/Timeline";
import Badge from "../../components/common/Badge";
import StatusBadge from "../../components/common/StatusBadge";
import Button from "../../components/common/Button";
import Toast from "../../components/common/Toast";
import Card from "../../components/common/Card";
import Modal from "../../components/common/Modal";

import "../../styles/company/Candidates.css";

export default function Candidates() {
    const USE_MOCK_DATA = false;

    const [candidates, setCandidates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [selectedStage, setSelectedStage] = useState("");
    const [selectedMatch, setSelectedMatch] = useState("");

    // Detail drawer state
    const [selectedCand, setSelectedCand] = useState(null);
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);

    // Toast feedback
    const [toast, setToast] = useState(null);

    // Pagination
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 8;

    const showToast = (message, type = "success") => {
        setToast({
            message,
            type,
        });
    };

    const closeToast = () => {
        setToast(null);
    };
    const stages = [
        { value: "Screening", label: "Screening" },
        { value: "Interviewing", label: "Interviewing" },
        { value: "Selected", label: "Selected" },
        { value: "Offered", label: "Offered" },
        { value: "Rejected", label: "Rejected" }
    ];

    const matchThresholds = [
        { value: "90", label: "90%+ Fit Match" },
        { value: "80", label: "80%+ Fit Match" },
        { value: "70", label: "70%+ Fit Match" }
    ];

    // Handlers
    const handleViewDetails = (cand) => {
        setSelectedCand(cand);
        setIsDrawerOpen(true);
    };

    const handleShortlist = async (id) => {

            try {

                await candidateService.shortlistCandidate(id);
                setIsDrawerOpen(false);

                setSelectedCand(null);

                await fetchCandidates();

                showToast("Candidate shortlisted","success");

            }

            catch {

                showToast("Failed");

            }

        };

    const handleReject = async (id) => {

        try {

            await candidateService.rejectCandidate(id);

            fetchCandidates();

            showToast("Candidate rejected","error");

        }

        catch {

            showToast("Failed");

        }

    };
    

    const handleSchedule = async (candidate) => {

        try {

            await candidateService.scheduleInterview(candidate.id);

         showToast(`Interview scheduled for ${candidate.name}`, "success");

        }

        catch {

            showToast("Failed");

        }

    };

    // Filter Logic
    const filteredCandidates = candidates.filter((cand) => {
        const matchesSearch = cand.name.toLowerCase().includes(search.toLowerCase()) ||
            cand.email.toLowerCase().includes(search.toLowerCase()) ||
            cand.skills.some((s) => s.toLowerCase().includes(search.toLowerCase()));

        const matchesStage = selectedStage === "" || cand.currentStage === selectedStage;

        const matchesMatch = selectedMatch === "" || cand.aiMatch >= parseInt(selectedMatch);

        return matchesSearch && matchesStage && matchesMatch;
    });

    // Pagination logic
    const totalPages = Math.ceil(filteredCandidates.length / itemsPerPage);
    const paginatedCands = filteredCandidates.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage
    );

    // Table view columns
    const columns = [
        {
            key: "name",
            label: "Candidate",
            sortable: true,
            render: (val, row) => (
                <div className="cand-table-avatar-cell" onClick={() => handleViewDetails(row)}>
                    <div className="cand-avatar-initials">
                        {val.split(" ").map((x) => x[0]).join("")}
                    </div>
                    <div>
                        <strong>{val}</strong>
                        <span>{row.email}</span>
                    </div>
                </div>
            )
        },
        { key: "experience", label: "Experience", render: (val) => val.split("-")[0] },
        {
            key: "aiMatch",
            label: "AI Match",
            sortable: true,
            render: (val) => <strong className="ai-score-cell">{val}%</strong>
        },
        {
            key: "resumeScore",
            label: "Resume",
            sortable: true,
            render: (val) => <span className="resume-score-cell">{val}</span>
        },
        {
            key: "currentStage",
            label: "Pipeline Stage",
            sortable: true,
            render: (val) => <StatusBadge status={val} />
        },
        {
            key: "actions",
            label: "Actions",
            render: (_, row) => (
                <div className="table-actions-cell">
                    <Button variant="ghost" size="sm" onClick={() => handleViewDetails(row)}>
                        View
                    </Button>
                    {row.status !== "Shortlisted" && (
                        <button className="icon-btn-action  shortlist-btn" aria-label="Schedule Interview" onClick={() => handleShortlist(row.id)} title="Shortlist">
                            <FaCheck />
                        </button>
                    )}
                    {row.status !== "Rejected" && (
                        <button className="icon-btn-action reject-btn" aria-label="Schedule Interview" onClick={() => handleReject(row.id)} title="Reject">
                            <FaTimes />
                        </button>
                    )}
                </div>
            )
        }
    ];

    // useEffect(() => {

    //     fetchCandidates();

    // }, []);

    useEffect(() => {
        fetchCandidates();
    }, []);

    const fetchCandidates = async () => {

        try {

            setLoading(true);

            const res = await candidateService.getCandidates();

            setCandidates(res.data);

        }

        catch (err) {

            console.error(err);

            showToast("Unable to load candidates.", "error");

        }

        finally {

            setLoading(false);

        }

    };
    return (
        <div className="candidates-page-wrapper">
            <PageHeader
                title="Candidates (ATS)"
                subtitle="Manage candidate pipelines and AI screening."
                breadcrumbs={[{ label: "Candidates" }]}
            />

            {/* Filters panel */}
            <Card className="candidates-filter-panel">
                <div className="filter-inputs">
                    <SearchBar value={search} onChange={setSearch} placeholder="Search by name, skills..." />
                    <FilterDropdown
                        label="Pipeline Stage"
                        options={stages}
                        selected={selectedStage}
                        onChange={setSelectedStage}
                    />
                    <FilterDropdown
                        label="Min Fit Match"
                        options={matchThresholds}
                        selected={selectedMatch}
                        onChange={setSelectedMatch}
                    />
                </div>
                
            </Card>

            {/* List area */}
            <div className="candidates-content-area">
                {filteredCandidates.length === 0 ? (
                    <div className="empty-state">
                        <h3>No candidates found</h3>
                        <p>Try adjusting your filters.</p>
                    </div>
                ) : (
                    <div>
                        <div className="candidates-grid">
                            {paginatedCands.map((cand) => (
                                <CandidateCard
                                    key={cand.id}
                                    candidate={cand}
                                    onView={() => handleViewDetails(cand)}
                                    onSchedule={() => handleSchedule(cand)}
                                    onShortlist={() => handleShortlist(cand.id)}
                                    onReject={() => handleReject(cand.id)}
                                />
                            ))}
                        </div>
                        <Pagination
                            currentPage={currentPage}
                            totalPages={totalPages}
                            onPageChange={setCurrentPage}
                            className="candidates-pagination"
                        />
                    </div>
                ) }
            </div>

            {/* Detail Drawer */}
            <Modal
                isOpen={isDrawerOpen}
                onClose={() => setIsDrawerOpen(false)}
                title={selectedCand ? `${selectedCand.name}` : "Candidate"}
                size="xl"
            >
                {selectedCand && (
                    <div className="drawer-profile-container">
                        {/* Summary Header */}
                        <div className="drawer-profile-header">
                            <div className="hdr-avatar-circle">
                                {selectedCand.name.split(" ").map(x => x[0]).join("")}
                            </div>
                            <div className="hdr-meta">
                                <h3>{selectedCand.name}</h3>
                                <p>{selectedCand.email} • {selectedCand.phone}</p>
                                <div className="hdr-badges">
                                    <Badge variant="primary" className="match-pill">
                                        AI Match: {selectedCand.aiMatch}%
                                    </Badge>
                                    <StatusBadge status={selectedCand.currentStage} />
                                </div>
                            </div>
                        </div>

                        {/* Split Details columns */}
                        <div className="drawer-profile-body-grid">
                            <div className="details-col-left">
                                {/* Timeline */}
                                <div className="drawer-section">
                                    <h4>Application Timeline</h4>
                                    <Timeline items={selectedCand.timeline} />
                                </div>

                                {/* Mock Resume Frame */}
                                <div className="drawer-section">
                                    <h4>Resume Preview</h4>
                                    <div className="mock-resume-frame">
                                        <FaFilePdf className="pdf-logo" />
                                        <h5>{selectedCand.name.replace(" ", "_")}_CV.pdf</h5>
                                        <span>PDF Document - Mock Preview Frame</span>
                                        <Button variant="outline" size="sm" onClick={() => showToast("Resume download started.", "info")}>
                                            Download Resume
                                        </Button>
                                    </div>
                                </div>
                            </div>

                            <div className="details-col-right">
                                {/* AI Match recommendation */}
                                <div className="drawer-section recommendation-accent-box">
                                    <h4 className="rec-box-title"><FaRobot /> AI Evaluation Recommendation</h4>
                                    <p className="rec-text">{selectedCand.aiRecommendations}</p>
                                </div>

                                {/* Skills */}
                                <div className="drawer-section">
                                    <h4>Skills</h4>
                                    <div className="drawer-skills-list">
                                        {selectedCand.skills.map((skill, i) => (
                                            <Badge key={i} variant="neutral">
                                                {skill}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>

                                {/* Experience */}
                                <div className="drawer-section">
                                    <h4>Professional Experience</h4>
                                    <p className="drawer-details-txt">{selectedCand.experience}</p>
                                </div>

                                {/* Education */}
                                <div className="drawer-section">
                                    <h4>Education</h4>
                                    <p className="drawer-details-txt">{selectedCand.education}</p>
                                </div>

                                {/* Notes */}
                                <div className="drawer-section">
                                    <h4>Interview Notes</h4>
                                    <p className="drawer-details-txt italic-notes">"{selectedCand.notes}"</p>
                                </div>
                            </div>
                        </div>

                        {/* Action footer */}
                        <div className="drawer-footer-actions">

                            <Button
    variant="secondary"
    onClick={() => {
        console.log("Close clicked");
        setSelectedCand(null);
        setIsDrawerOpen(false);
    }}
>
    Close
</Button>

                            <div className="main-actions-group">

                                {selectedCand.status !== "Rejected" && (

                                    <Button
    variant="danger"
    onClick={() => {
        console.log("Reject clicked");
        handleReject(selectedCand.id);
    }}
>
    Reject
</Button>

                                )}

                                {selectedCand.status !== "Shortlisted" && (

                                    <Button
                                        variant="success"
                                        onClick={() => handleShortlist(selectedCand.id)}
                                    >
                                        Shortlist
                                    </Button>

                                )}

                                <Button
    onClick={() => {
        console.log("Schedule clicked");
        handleSchedule(selectedCand);
    }}
>
    Schedule Interview
</Button>

                            </div>

                        </div>
                    </div>
                )}
            </Modal>

            <div className="toast-container">
                <AnimatePresence>
                    {toast && (
                        <Toast
                            message={toast.message}
                            type={toast.type}
                            onClose={closeToast}
                        />
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
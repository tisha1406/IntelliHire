import React, { useState, useEffect, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { FaEye, FaEdit, FaTrashAlt, FaPlus, FaInbox } from "react-icons/fa";
import { AnimatePresence, motion } from "framer-motion";
import { getJobs, deleteJob } from "../../api/jobs";
import ConfirmDialog from "../../components/common/ConfirmDialog";
import "../../styles/company/Jobs.css";

// Custom debounce hook for search
function useDebounce(value, delay) {
    const [debouncedValue, setDebouncedValue] = useState(value);
    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);
        return () => clearTimeout(handler);
    }, [value, delay]);
    return debouncedValue;
}

export default function Jobs() {
    const navigate = useNavigate();
    const location = useLocation();

    // Data State
    const [jobs, setJobs] = useState([]);
    const [totalJobs, setTotalJobs] = useState(0);
    const [loading, setLoading] = useState(true);

    // Filters & Pagination State
    const [search, setSearch] = useState("");
    const debouncedSearch = useDebounce(search, 300);
    
    const [selectedDept, setSelectedDept] = useState("");
    const [selectedType, setSelectedType] = useState("");
    
    const [sortKey, setSortKey] = useState("created_at");
    const [sortDir, setSortDir] = useState("desc");
    
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 10;

    // Actions state
    const [deleteId, setDeleteId] = useState(null);
    const [isConfirmOpen, setIsConfirmOpen] = useState(false);
    const [toastMessage, setToastMessage] = useState(null);
    const [toastType, setToastType] = useState("success");

    const departments = [
        "", "Engineering", "AI & Data Science", "Design", "Product", 
        "Marketing", "Sales", "Human Resources", "Customer Success"
    ];

    const employmentTypes = [
        "", "Full-time", "Part-time", "Contract", "Internship"
    ];

    const showToast = (msg, type = "success") => {
        setToastMessage(msg);
        setToastType(type);
        setTimeout(() => setToastMessage(null), 3000);
    };

    // Handle toast messages coming from navigation (e.g. from JobForm)
    useEffect(() => {
        if (location.state?.toastMessage) {
            showToast(location.state.toastMessage, "success");
            window.history.replaceState({}, document.title);
        }
    }, [location]);

    const fetchJobs = useCallback(async () => {
        setLoading(true);
        try {
            const data = await getJobs({
                q: debouncedSearch || undefined,
                department: selectedDept || undefined,
                employment_type: selectedType || undefined,
                sort: sortKey,
                order: sortDir,
                page: currentPage,
                page_size: itemsPerPage
            });
            if (data) {
                setJobs(data.jobs);
                setTotalJobs(data.total);
            }
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            setLoading(false);
        }
    }, [debouncedSearch, selectedDept, selectedType, sortKey, sortDir, currentPage]);

    useEffect(() => {
        fetchJobs();
    }, [fetchJobs]);

    const handleSort = (key) => {
        if (sortKey === key) {
            setSortDir(sortDir === "asc" ? "desc" : "asc");
        } else {
            setSortKey(key);
            setSortDir("asc");
        }
    };

    const handleDeleteClick = (id) => {
        setDeleteId(id);
        setIsConfirmOpen(true);
    };

    const handleConfirmDelete = async () => {
        setIsConfirmOpen(false);
        try {
            await deleteJob(deleteId);
            showToast("Job opening successfully deleted.");
            if (jobs.length === 1 && currentPage > 1) {
                setCurrentPage(currentPage - 1);
            } else {
                fetchJobs();
            }
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            setDeleteId(null);
        }
    };

    const totalPages = Math.ceil(totalJobs / itemsPerPage);

    return (
        <div className="jobs-layout">
            {/* Header Section */}
            <div className="jobs-header">
                <div className="jobs-header__info">
                    <span className="jobs-header__breadcrumb">Home &gt; Job Openings</span>
                    <h1 className="jobs-header__title">Job Openings</h1>
                    <p className="jobs-header__subtitle">Manage your active corporate careers listings and applicants.</p>
                </div>
                <button 
                    className="jobs-btn jobs-btn--primary" 
                    onClick={() => navigate("/company/jobs/new")}
                >
                    <FaPlus /> Add Opening
                </button>
            </div>

            {/* Filter Card */}
            <div className="jobs-filter-card">
                <input 
                    type="text"
                    className="jobs-filter-card__search"
                    placeholder="Search by job title or location..."
                    value={search}
                    onChange={(e) => {
                        setSearch(e.target.value);
                        setCurrentPage(1); // Reset to page 1 on search
                    }}
                />
                
                <select 
                    className="jobs-filter-card__select"
                    value={selectedDept}
                    onChange={(e) => {
                        setSelectedDept(e.target.value);
                        setCurrentPage(1);
                    }}
                >
                    <option value="">All Departments</option>
                    {departments.filter(d => d).map(d => (
                        <option key={d} value={d}>{d}</option>
                    ))}
                </select>

                <select 
                    className="jobs-filter-card__select"
                    value={selectedType}
                    onChange={(e) => {
                        setSelectedType(e.target.value);
                        setCurrentPage(1);
                    }}
                >
                    <option value="">All Employment Types</option>
                    {employmentTypes.filter(d => d).map(d => (
                        <option key={d} value={d}>{d}</option>
                    ))}
                </select>
            </div>

            {/* Table Card */}
            <div className="jobs-table-card">
                <div className="jobs-table-wrapper">
                    <table className="jobs-table">
                        <thead>
                            <tr>
                                <th className="jobs-table__th jobs-table__th--sortable" onClick={() => handleSort("title")}>Job Title ↕</th>
                                <th className="jobs-table__th jobs-table__th--sortable" onClick={() => handleSort("department")}>Department ↕</th>
                                <th className="jobs-table__th jobs-table__th--sortable" onClick={() => handleSort("location")}>Location ↕</th>
                                <th className="jobs-table__th jobs-table__th--sortable" onClick={() => handleSort("employment_type")}>Employment Type ↕</th>
                                <th className="jobs-table__th jobs-table__th--sortable" onClick={() => handleSort("salary_scale")}>Salary Scale ↕</th>
                                <th className="jobs-table__th jobs-table__th--sortable" onClick={() => handleSort("applicants")}>Applicants ↕</th>
                                <th className="jobs-table__th jobs-table__th--sortable" onClick={() => handleSort("status")}>Status ↕</th>
                                <th className="jobs-table__th jobs-table__th--sortable" onClick={() => handleSort("created_at")}>Created Date ↕</th>
                                <th className="jobs-table__th">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                Array.from({ length: 5 }).map((_, i) => (
                                    <tr key={i} className="jobs-table__tr">
                                        {Array.from({ length: 9 }).map((_, j) => (
                                            <td key={j} className="jobs-table__td">
                                                <div className={`jobs-skeleton ${j === 6 ? 'jobs-skeleton--badge' : 'jobs-skeleton--text'}`} />
                                            </td>
                                        ))}
                                    </tr>
                                ))
                            ) : jobs.length === 0 ? (
                                <tr>
                                    <td colSpan="9">
                                        <div className="jobs-empty">
                                            <FaInbox className="jobs-empty__icon" />
                                            <h3 className="jobs-empty__title">No jobs found</h3>
                                            <p className="jobs-empty__desc">We couldn't find any job openings matching your current criteria.</p>
                                            <button className="jobs-btn jobs-btn--primary" onClick={() => navigate("/company/jobs/new")}>
                                                Create first opening
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                jobs.map((job) => (
                                    <tr key={job.id} className="jobs-table__tr">
                                        <td className="jobs-table__td">
                                            <div className="jobs-cell-title">
                                                <span className="jobs-cell-title__main">{job.title}</span>
                                                <span className="jobs-cell-title__sub">{job.id.substring(0, 8).toUpperCase()}</span>
                                            </div>
                                        </td>
                                        <td className="jobs-table__td">{job.department}</td>
                                        <td className="jobs-table__td">{job.location}</td>
                                        <td className="jobs-table__td">{job.employment_type}</td>
                                        <td className="jobs-table__td" style={{ color: "var(--text-tertiary)" }}>{job.salary_scale || "Not specified"}</td>
                                        <td className="jobs-table__td">
                                            <span style={{ fontWeight: 600 }}>{job.applicants}</span>
                                        </td>
                                        <td className="jobs-table__td">
                                            <span className={`jobs-status jobs-status--${job.status.toLowerCase()}`}>
                                                {job.status}
                                            </span>
                                        </td>
                                        <td className="jobs-table__td" style={{ color: "var(--text-tertiary)" }}>
                                            {job.created_date.split("T")[0]}
                                        </td>
                                        <td className="jobs-table__td">
                                            <div className="jobs-action-group">
                                                <button 
                                                    className="jobs-action-btn jobs-action-btn--view" 
                                                    onClick={() => navigate(`/company/jobs/${job.id}`)} 
                                                    title="View"
                                                >
                                                    <FaEye />
                                                </button>
                                                <button 
                                                    className="jobs-action-btn jobs-action-btn--edit" 
                                                    onClick={() => navigate(`/company/jobs/${job.id}/edit`)} 
                                                    title="Edit"
                                                >
                                                    <FaEdit />
                                                </button>
                                                <button 
                                                    className="jobs-action-btn jobs-action-btn--delete" 
                                                    onClick={() => handleDeleteClick(job.id)} 
                                                    title="Delete"
                                                >
                                                    <FaTrashAlt />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {!loading && jobs.length > 0 && (
                    <div className="jobs-pagination">
                        <div className="jobs-pagination__info">
                            Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, totalJobs)} of {totalJobs} results
                        </div>
                        <div className="jobs-pagination__controls">
                            <button 
                                className="jobs-pagination__btn" 
                                disabled={currentPage === 1}
                                onClick={() => setCurrentPage(p => p - 1)}
                            >
                                Previous
                            </button>
                            <span style={{ padding: '0 8px', display: 'flex', alignItems: 'center', fontSize: '13px', fontWeight: 500, color: 'var(--text-secondary)' }}>
                                Page {currentPage} of {totalPages}
                            </span>
                            <button 
                                className="jobs-pagination__btn" 
                                disabled={currentPage === totalPages || totalPages === 0}
                                onClick={() => setCurrentPage(p => p + 1)}
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </div>

            <ConfirmDialog
                isOpen={isConfirmOpen}
                onClose={() => setIsConfirmOpen(false)}
                onConfirm={handleConfirmDelete}
                title="Delete Job Opening"
                message="Are you sure you want to delete this job listing? This action cannot be undone."
            />

            {/* Top-Right Toast Notifications */}
            <div className="jobs-toast-container">
                <AnimatePresence>
                    {toastMessage && (
                        <motion.div
                            className={`jobs-toast jobs-toast--${toastType}`}
                            initial={{ x: 50, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
                        >
                            <div className="jobs-toast__message">{toastMessage}</div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}

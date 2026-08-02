import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { FaArrowLeft, FaCheck } from "react-icons/fa";
import { getJob, createJob, updateJob } from "../../api/jobs";
import "../../styles/company/Jobs.css";

export default function JobForm() {
    const navigate = useNavigate();
    const { id } = useParams();
    const isEditMode = Boolean(id);

    const [loading, setLoading] = useState(isEditMode);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    const [formData, setFormData] = useState({
        title: "",
        department: "Engineering",
        location: "",
        employment_type: "Full-time",
        salary_scale: "",
        status: "Active"
    });

    useEffect(() => {
        if (isEditMode) {
            const fetchJob = async () => {
                try {
                    const data = await getJob(id);
                    setFormData({
                        title: data.title,
                        department: data.department,
                        location: data.location,
                        employment_type: data.employment_type,
                        salary_scale: data.salary_scale || "",
                        status: data.status
                    });
                } catch (err) {
                    setError(err.message);
                } finally {
                    setLoading(false);
                }
            };
            fetchJob();
        }
    }, [id, isEditMode]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setError(null);
        try {
            if (isEditMode) {
                await updateJob(id, formData);
            } else {
                await createJob(formData);
            }
            navigate("/company/jobs", { state: { toastMessage: `Job opening successfully ${isEditMode ? 'updated' : 'added'}.` } });
        } catch (err) {
            setError(err.message);
            setSubmitting(false);
        }
    };

    return (
        <div className="jobs-layout">
            <div className="jobs-header">
                <div className="jobs-header__info">
                    <button className="jobs-btn jobs-btn--secondary" onClick={() => navigate("/company/jobs")} style={{ padding: 0, border: 'none', color: "var(--text-tertiary)", marginBottom: "8px" }}>
                        <FaArrowLeft /> Back to Jobs
                    </button>
                    <h1 className="jobs-header__title">{isEditMode ? "Edit Job Opening" : "Add New Opening"}</h1>
                    <p className="jobs-header__subtitle">Fill in the details to {isEditMode ? "update this" : "create a new"} job opening.</p>
                </div>
            </div>

            {/* Stepper Placeholder (Matching Design) */}
            <div style={{ display: "flex", gap: "24px", alignItems: "center", marginBottom: "24px", padding: "16px", backgroundColor: "var(--card)", borderRadius: "var(--radius-lg)", border: "1px solid var(--border)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--primary)", fontSize: "13px", fontWeight: "600" }}>
                    <div style={{ width: "24px", height: "24px", borderRadius: "50%", backgroundColor: "var(--primary)", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px" }}>1</div>
                    Basic Information
                </div>
                <div style={{ height: "1px", flex: 1, backgroundColor: "var(--border)" }}></div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-tertiary)", fontSize: "13px", fontWeight: "500" }}>
                    <div style={{ width: "24px", height: "24px", borderRadius: "50%", backgroundColor: "var(--border)", color: "var(--text-secondary)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px" }}>2</div>
                    Job Description
                </div>
                <div style={{ height: "1px", flex: 1, backgroundColor: "var(--border)" }}></div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-tertiary)", fontSize: "13px", fontWeight: "500" }}>
                    <div style={{ width: "24px", height: "24px", borderRadius: "50%", backgroundColor: "var(--border)", color: "var(--text-secondary)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px" }}>3</div>
                    Requirements
                </div>
            </div>

            <div className="jobs-table-card" style={{ padding: "24px", maxWidth: "800px" }}>
                <h3 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px" }}>Basic Information</h3>
                
                {error && <div style={{ color: "var(--danger)", marginBottom: "16px", padding: "12px", backgroundColor: "var(--danger-muted)", borderRadius: "var(--radius-sm)", border: "1px solid var(--danger)" }}>{error}</div>}
                
                {loading ? (
                    <div className="jobs-skeleton jobs-skeleton--text" style={{ height: "200px", width: "100%" }}></div>
                ) : (
                    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                        
                        <div style={{ display: "flex", gap: "20px" }}>
                            <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
                                <label style={{ fontSize: "13px", fontWeight: "500", color: "var(--text-secondary)" }}>Job Title <span style={{ color: "var(--danger)" }}>*</span></label>
                                <input 
                                    required
                                    name="title"
                                    className="jobs-filter-card__search" 
                                    value={formData.title} 
                                    onChange={handleChange} 
                                    placeholder="e.g. Senior Frontend Developer" 
                                />
                            </div>

                            <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
                                <label style={{ fontSize: "13px", fontWeight: "500", color: "var(--text-secondary)" }}>Department <span style={{ color: "var(--danger)" }}>*</span></label>
                                <select 
                                    name="department"
                                    className="jobs-filter-card__select" 
                                    value={formData.department} 
                                    onChange={handleChange}
                                >
                                    <option value="Engineering">Engineering</option>
                                    <option value="AI & Data Science">AI & Data Science</option>
                                    <option value="Design">Design</option>
                                    <option value="Product">Product</option>
                                    <option value="Marketing">Marketing</option>
                                    <option value="Sales">Sales</option>
                                    <option value="Human Resources">Human Resources</option>
                                    <option value="Customer Success">Customer Success</option>
                                </select>
                            </div>
                        </div>

                        <div style={{ display: "flex", gap: "20px" }}>
                            <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
                                <label style={{ fontSize: "13px", fontWeight: "500", color: "var(--text-secondary)" }}>Location <span style={{ color: "var(--danger)" }}>*</span></label>
                                <input 
                                    required
                                    name="location"
                                    className="jobs-filter-card__search" 
                                    value={formData.location} 
                                    onChange={handleChange} 
                                    placeholder="e.g. Remote / New York" 
                                />
                            </div>
                            
                            <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
                                <label style={{ fontSize: "13px", fontWeight: "500", color: "var(--text-secondary)" }}>Employment Type <span style={{ color: "var(--danger)" }}>*</span></label>
                                <select 
                                    name="employment_type"
                                    className="jobs-filter-card__select" 
                                    value={formData.employment_type} 
                                    onChange={handleChange}
                                >
                                    <option value="Full-time">Full-time</option>
                                    <option value="Part-time">Part-time</option>
                                    <option value="Contract">Contract</option>
                                    <option value="Internship">Internship</option>
                                </select>
                            </div>
                        </div>

                        <div style={{ display: "flex", gap: "20px" }}>
                            <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
                                <label style={{ fontSize: "13px", fontWeight: "500", color: "var(--text-secondary)" }}>Salary Range</label>
                                <input 
                                    name="salary_scale"
                                    className="jobs-filter-card__search" 
                                    value={formData.salary_scale} 
                                    onChange={handleChange} 
                                    placeholder="e.g. $100,000 - $150,000" 
                                />
                            </div>
                            
                            <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
                                <label style={{ fontSize: "13px", fontWeight: "500", color: "var(--text-secondary)" }}>Status</label>
                                <select 
                                    name="status"
                                    className="jobs-filter-card__select" 
                                    value={formData.status} 
                                    onChange={handleChange}
                                >
                                    <option value="Active">Active</option>
                                    <option value="Closed">Closed</option>
                                    <option value="Draft">Draft</option>
                                </select>
                            </div>
                        </div>

                        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "24px", paddingTop: "24px", borderTop: "1px solid var(--border)" }}>
                            <button type="button" className="jobs-btn jobs-btn--secondary" onClick={() => navigate("/company/jobs")}>
                                Cancel
                            </button>
                            <button type="submit" disabled={submitting} className="jobs-btn jobs-btn--primary">
                                {submitting ? "Saving..." : (isEditMode ? "Save Changes" : "Save Opening")}
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}

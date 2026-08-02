import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { FaArrowLeft, FaArrowRight, FaCheckCircle, FaTrash, FaPlus } from "react-icons/fa";

import { useAuthContext } from "../../context/AuthContext";

import campaignService from "../../services/company/campaignService";
// Common components

import PageHeader from "../../components/common/PageHeader";
import Stepper from "../../components/common/Stepper";
import Button from "../../components/common/Button";
import Input from "../../components/common/Input";
import Select from "../../components/common/Select";
import Card from "../../components/common/Card";
import Toast from "../../components/common/Toast";


import "../../styles/company/Campaign.css";

const DEPARTMENTS = [
    { value: "Engineering", label: "Engineering" },
    { value: "AI & Data Science", label: "AI & Data Science" },
    { value: "Design", label: "Design" },
    { value: "Product", label: "Product" },
    { value: "Marketing", label: "Marketing" },
    { value: "Sales", label: "Sales" },
    { value: "Human Resources", label: "Human Resources" }
];

const EMPLOYMENT_TYPES = [
    { value: "Full-time", label: "Full-time" },
    { value: "Part-time", label: "Part-time" },
    { value: "Contract", label: "Contract" },
    { value: "Remote", label: "Remote" }
];

const STRICTNESS_LEVELS = [
    { value: "Low", label: "Low (Friendly guidance)" },
    { value: "Medium", label: "Medium (Standard guidelines)" },
    { value: "High", label: "High (Technical correctness prioritised)" },
    { value: "Very High", label: "Very High (Strict code validation)" }
];

export default function NewCampaign() {
    const navigate = useNavigate();
    const { user, loading } = useAuthContext();
    const [currentStep, setCurrentStep] = useState(0);

    // Form inputs state
    const [formData, setFormData] = useState({
        name: "",
        department: "",
        location: "",
        deadline: "",
        salary: "",
        description: "",
        employmentType: "",
        requirements: ["React experience", "TypeScript fluency"],
        interviewDuration: 45,
        strictness: "High",
        interviewType: "Technical"
    });

    const [reqInput, setReqInput] = useState("");
    const [errors, setErrors] = useState({});
    const [toastMessage, setToastMessage] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    const steps = [
        "Basic Information",
        "Job Description",
        "Requirements",
        "Interview Settings",
        "Review & Publish"
    ];

    const validateStep = () => {
        const errs = {};
        if (currentStep === 0) {
            if (!formData.name) errs.name = "Campaign name is required.";
            if (!formData.department) errs.department = "Department is required.";
            if (!formData.location) errs.location = "Location is required.";
            if (!formData.deadline) errs.deadline = "Deadline is required.";
        } else if (currentStep === 1) {
            if (!formData.description) errs.description = "Job description is required.";
            if (!formData.employmentType) errs.employmentType = "Employment type is required.";
        } else if (currentStep === 2) {
            if (formData.requirements.length === 0) {
                errs.requirements = "Please add at least one job requirement.";
            }
        }
        setErrors(errs);
        return Object.keys(errs).length === 0;
    };

    const handleNext = () => {
        if (validateStep()) {
            setCurrentStep((prev) => Math.min(steps.length - 1, prev + 1));
        }
    };

    const handleBack = () => {
        setCurrentStep((prev) => Math.max(0, prev - 1));
    };

    const handleAddRequirement = () => {
        const value = reqInput.trim();

        if (value && !formData.requirements.includes(value)) {
            setFormData({
                ...formData,
                requirements: [...formData.requirements, value]
            });
            setReqInput("");
        }
    };

    const handleRemoveRequirement = (index) => {
        setFormData({
            ...formData,
            requirements: formData.requirements.filter((_, idx) => idx !== index)
        });
    };

    const handleSubmit = async () => {

    if (loading) return;

    if (!user?.companyId) {
        setToastMessage("Company information not found.");
        return;
    }

    if (!validateStep()) return;

    try {

        setSubmitting(true);

        await campaignService.createCampaign({
            company_id: user.companyId,

            name: formData.name.trim(),

            department: formData.department.trim(),

            location: formData.location.trim(),

            deadline: formData.deadline,

            salary: formData.salary.trim(),

            description: formData.description.trim(),

            employment_type: formData.employmentType.trim(),

            requirements: formData.requirements,

            interview_settings: {
                duration: formData.interviewDuration,
                strictness: formData.strictness,
                type: formData.interviewType
            }
        });

        setToastMessage("Campaign Created Successfully.");

        setTimeout(() => {
            navigate("/company/campaigns");
        }, 1500);

    } catch (err) {

        console.log(err);

        setToastMessage("Failed to create campaign.");

    } finally {

        setSubmitting(false);

    }
};

    const slideVariants = {
        enter: { opacity: 0, x: 20 },
        center: { opacity: 1, x: 0 },
        exit: { opacity: 0, x: -20 }
    };

    return (
        <div className="new-campaign-page">
            <PageHeader
                title="Create Campaign"
                subtitle="Configure details, requirements, and AI screening strictness parameters for a new role."
                breadcrumbs={[
                    { label: "Campaigns", path: "/company/campaigns" },
                    { label: "New Campaign" }
                ]}
                actions={
                    <Button variant="ghost" iconLeft={<FaArrowLeft />} onClick={() => navigate("/company/campaigns")}>
                        Back to List
                    </Button>
                }
            />

            <Card className="wizard-card-container">
                <Stepper steps={steps} currentStep={currentStep} className="new-camp-stepper" />

                <div className="wizard-form-body">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={currentStep}
                            variants={slideVariants}
                            initial="enter"
                            animate="center"
                            exit="exit"
                            transition={{ duration: 0.25 }}
                            className="step-animation-wrapper"
                        >
                            {/* STEP 1: BASIC INFO */}
                            {currentStep === 0 && (
                                <div className="step-fields-layout">
                                    <h3>Basic Campaign Details</h3>
                                    <div className="form-grid-2x">
                                        <Input
                                            label="Campaign / Job Title"
                                            placeholder="e.g. Lead Frontend Architect"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            error={errors.name}
                                        />
                                        <Select
                                            label="Department"
                                            options={DEPARTMENTS}
                                            value={formData.department}
                                            onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                                            error={errors.department}
                                            placeholder="Choose department..."
                                        />
                                    </div>
                                    <div className="form-grid-3x">
                                        <Input
                                            label="Location"
                                            placeholder="e.g. Remote / New York"
                                            value={formData.location}
                                            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                                            error={errors.location}
                                        />
                                        <Input
                                            label="Salary Range"
                                            placeholder="e.g. $140,000 - $160,000"
                                            value={formData.salary}
                                            onChange={(e) => setFormData({ ...formData, salary: e.target.value })}
                                        />
                                        <Input
                                            label="Deadline Date"
                                            type="date"
                                            value={formData.deadline}
                                            onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                                            error={errors.deadline}
                                        />
                                    </div>
                                </div>
                            )}

                            {/* STEP 2: JOB DESCRIPTION */}
                            {currentStep === 1 && (
                                <div className="step-fields-layout">
                                    <h3>Job Overview & Work Type</h3>
                                    <Select
                                        label="Employment Type"
                                        options={EMPLOYMENT_TYPES}
                                        value={formData.employmentType}
                                        onChange={(e) => setFormData({ ...formData, employmentType: e.target.value })}
                                        error={errors.employmentType}
                                        placeholder="Choose type..."
                                    />
                                    <div className="custom-input-group">
                                        <label className="input-label">Detailed Job Description</label>
                                        <textarea
                                            value={formData.description}
                                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                            className={`custom-textarea ${errors.description ? "textarea-error" : ""}`}
                                            placeholder="Introduce the candidate to your company, key deliverables, and day-to-day objectives..."
                                            rows={6}
                                        />
                                        {errors.description && <span className="input-error-msg">{errors.description}</span>}
                                    </div>
                                </div>
                            )}

                            {/* STEP 3: REQUIREMENTS */}
                            {currentStep === 2 && (
                                <div className="step-fields-layout">
                                    <h3>Competencies & Requirements</h3>
                                    <p className="step-instruction-text">
                                        List critical qualifications. Our AI agents will match candidates' resumes against these items.
                                    </p>
                                    <div className="requirement-adder-row">
                                        <Input
                                            placeholder="e.g. 5+ years Go development"
                                            value={reqInput}
                                            onChange={(e) => setReqInput(e.target.value)}
                                        />
                                        <Button variant="outline" iconLeft={<FaPlus />} onClick={handleAddRequirement}>
                                            Add
                                        </Button>
                                    </div>
                                    {errors.requirements && <p className="input-error-msg">{errors.requirements}</p>}

                                    <div className="requirements-dynamic-list">
                                        {formData.requirements.map((req, idx) => (
                                            <div key={idx} className="req-pill-item compact-chip">
                                                <span>{req}</span>
                                                <button className="delete-pill-btn" onClick={() => handleRemoveRequirement(idx)}>
                                                    &times;
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* STEP 4: INTERVIEW SETTINGS */}
                            {currentStep === 3 && (
                                <div className="step-fields-layout">
                                    <h3>Configure AI Agent Parameters</h3>
                                    <div className="form-grid-2x">
                                        <Select
                                            label="AI Strictness Policy"
                                            options={STRICTNESS_LEVELS}
                                            value={formData.strictness}
                                            onChange={(e) => setFormData({ ...formData, strictness: e.target.value })}
                                        />
                                        <Input
                                            label="Primary Interview Target"
                                            placeholder="e.g. Technical / System / Marketing Pitch"
                                            value={formData.interviewType}
                                            onChange={(e) => setFormData({ ...formData, interviewType: e.target.value })}
                                        />
                                    </div>
                                    <div className="duration-slider-section">
                                        <div className="slider-labels">
                                            <label className="input-label">Interview Duration Limit</label>
                                            <strong>{formData.interviewDuration} minutes</strong>
                                        </div>
                                        <input
                                            type="range"
                                            min="15"
                                            max="90"
                                            step="5"
                                            value={formData.interviewDuration}
                                            onChange={(e) => setFormData({ ...formData, interviewDuration: parseInt(e.target.value) })}
                                            className="custom-range-slider"
                                        />
                                        <div className="slider-endpoints">
                                            <span>15 mins</span>
                                            <span>90 mins</span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* STEP 5: REVIEW */}
                            {currentStep === 5 - 1 && (
                                <div className="step-fields-layout review-step-layout">
                                    <div className="review-alert-tag">
                                        <FaCheckCircle className="review-check" />
                                        <div>
                                            <h4>Ready to Publish</h4>
                                            <p>Verify details below. Once published, candidate portals will activate.</p>
                                        </div>
                                    </div>

                                    <div className="review-summary-cards">
                                        <div className="review-card">
                                            <span>Campaign</span>
                                            <h4>{formData.name}</h4>
                                        </div>
                                        <div className="review-card">
                                            <span>Department</span>
                                            <h4>{formData.department}</h4>
                                        </div>
                                        <div className="review-card">
                                            <span>Salary</span>
                                            <h4>{formData.salary || "Not Specified"}</h4>
                                        </div>
                                        <div className="review-card">
                                            <span>Location</span>
                                            <h4>{formData.location}</h4>
                                        </div>
                                        <div className="review-card">
                                            <span>Deadline</span>
                                            <h4>{formData.deadline}</h4>
                                        </div>
                                        <div className="review-card">
                                            <span>Interview Type</span>
                                            <h4>{formData.interviewType}</h4>
                                        </div>
                                        <div className="review-card">
                                            <span>AI Strictness</span>
                                            <h4>{formData.strictness}</h4>
                                        </div>
                                    </div>

                                    <div className="review-block-full">
                                        <span>Expected Candidate Requirements</span>
                                        <div className="review-reqs-wrap">
                                            {formData.requirements.map((req, idx) => (
                                                <span key={idx} className="compact-chip read-only">
                                                    {req}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    </AnimatePresence>
                </div>

                <div className="wizard-form-footer">
                    <Button variant="ghost" onClick={handleBack} disabled={currentStep === 0}>
                        Back
                    </Button>

                    {currentStep === steps.length - 1 ? (
                        <Button variant="success" onClick={handleSubmit} disabled={submitting}>
                            Publish Campaign
                        </Button>
                    ) : (
                        <Button variant="primary" onClick={handleNext} iconRight={<FaArrowRight />}>
                            Next Step
                        </Button>
                    )}
                </div>
            </Card>

            {/* Toast Alerts — fixed top-right */}
            <div className="toast-portal">
                <AnimatePresence>
                    {toastMessage && (
                        <>
                            <motion.div
                                className="toast-backdrop"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                            />
                            <Toast message={toastMessage} type="success" onClose={() => setToastMessage(null)} />
                        </>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}

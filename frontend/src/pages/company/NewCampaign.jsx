import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { FaArrowLeft, FaArrowRight, FaCheckCircle, FaTrash, FaPlus } from "react-icons/fa";

import { useAuthContext } from "../../context/AuthContext";

import campaignService from "../../services/company/campaignService";
import recruiterManagementService from "../../services/company/recruiterManagementService";
// Common components

import PageHeader from "../../components/common/PageHeader";
import Stepper from "../../components/common/Stepper";
import Button from "../../components/common/Button";
import Input from "../../components/common/Input";
import Select from "../../components/common/Select";
import Card from "../../components/common/Card";
import Toast from "../../components/common/Toast";
import { VALID_VOICES } from "../../utils/voiceConstants";
import { DIFFICULTY_LEVELS } from "../../utils/difficultyConstants";
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

import { SettingsAPI } from "../../api/settings";

const INTERVIEW_TYPES = [
    { value: "technical", label: "Technical" },
    { value: "resume_experience", label: "Resume / Experience" },
    { value: "hr_behavioral", label: "HR / Behavioral" },
    { value: "situational_case", label: "Situational / Case" },
    { value: "mixed", label: "Mixed" }
];

const CRITICALITY_OPTIONS = [
    { value: "critical", label: "Critical" },
    { value: "required", label: "Required" },
    { value: "preferred", label: "Preferred" }
];

import { usePermissions } from "../../context/PermissionsContext";

export default function NewCampaign() {
    const navigate = useNavigate();
    const { user, loading } = useAuthContext();
    const { platform } = usePermissions();
    const [currentStep, setCurrentStep] = useState(0);

    const [strategies, setStrategies] = useState([]);
    
    React.useEffect(() => {
        SettingsAPI.getStrategies().then(res => {
            const allStrategies = Array.isArray(res) 
                ? res 
                : (Array.isArray(res?.data) ? res.data : []);
            if (platform?.allowed_strategies) {
                setStrategies(allStrategies.filter(s => s.is_active && platform.allowed_strategies.includes(s.name)));
            }
        }).catch(err => console.error(err));
    }, [platform]);

    // Form inputs state
    const [formData, setFormData] = useState({
        name: "",
        department: "",
        location: "",
        deadline: "",
        salary: "",
        description: "",
        employmentType: "",
        requirements: [
            { skill: "React experience", criticality: "required" },
            { skill: "TypeScript fluency", criticality: "preferred" }
        ],
        interviewDuration: 45,
        strictness: "medium", // Default fallback if needed
        interviewType: "technical",
        strategy_id: "",
        mixed_composition: {
            technical: 0,
            resume_experience: 0,
            hr_behavioral: 0,
            situational_case: 0
        },
        budget_override_target: "",
        difficulty_band: "",
        language: "",
        voice_id: "",
        assigned_recruiter_ids: []
    });

    const [reqInput, setReqInput] = useState("");
    const [reqCriticality, setReqCriticality] = useState("required");
    const [recruiters, setRecruiters] = useState([]);
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
        } else if (currentStep === 3) {
            if (!formData.strategy_id) errs.strategy_id = "Strategy is required.";
            if (formData.interviewType === "mixed") {
                const sum = (formData.mixed_composition.technical || 0) +
                            (formData.mixed_composition.resume_experience || 0) +
                            (formData.mixed_composition.hr_behavioral || 0) +
                            (formData.mixed_composition.situational_case || 0);
                if (Math.abs(sum - 1.0) > 0.01) {
                    errs.mixed_composition = "Mixed composition must total exactly 1.0 (100%)";
                }
            }
        }
        setErrors(errs);
        return Object.keys(errs).length === 0;
    };

    const selectedStrategy = strategies.find(s => s.strategy_id === formData.strategy_id);

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

        if (value && !formData.requirements.find(r => r.skill === value)) {
            setFormData({
                ...formData,
                requirements: [...formData.requirements, { skill: value, criticality: reqCriticality }]
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

        const payload = {
            name: formData.name.trim(),
            department: formData.department.trim(),
            location: formData.location.trim(),
            deadline: formData.deadline,
            salary: formData.salary.trim(),
            description: formData.description.trim(),
            employment_type: formData.employmentType.trim(),
            assigned_recruiter_ids: formData.assigned_recruiter_ids,
            requirements: formData.requirements,
            interview_type: formData.interviewType,
            strategy_id: formData.strategy_id,
            interview_settings: {
                duration: formData.interviewDuration,
                strictness: formData.strictness,
                type: formData.interviewType
            }
        };

        if (formData.interviewType === "mixed") {
            payload.mixed_composition = formData.mixed_composition;
        }

        if (formData.budget_override_target !== "") {
            payload.budget_override = { target_questions: parseInt(formData.budget_override_target) };
        }

        if (formData.difficulty_band) {
            payload.difficulty_band = formData.difficulty_band;
        }

        if (formData.language) {
            payload.language = formData.language;
        }

        if (formData.voice_id) {
            payload.voice_id = formData.voice_id;
        }

        await campaignService.createCampaign(payload);

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
                                    <div className="requirement-adder-row" style={{ display: 'flex', gap: '10px' }}>
                                        <div style={{ flex: 2 }}>
                                            <Input
                                                placeholder="e.g. 5+ years Go development"
                                                value={reqInput}
                                                onChange={(e) => setReqInput(e.target.value)}
                                            />
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <Select
                                                options={CRITICALITY_OPTIONS}
                                                value={reqCriticality}
                                                onChange={(e) => setReqCriticality(e.target.value)}
                                            />
                                        </div>
                                        <Button variant="outline" iconLeft={<FaPlus />} onClick={handleAddRequirement}>
                                            Add
                                        </Button>
                                    </div>
                                    {errors.requirements && <p className="input-error-msg">{errors.requirements}</p>}

                                    <div className="requirements-dynamic-list">
                                        {formData.requirements.map((req, idx) => (
                                            <div key={idx} className="req-pill-item compact-chip">
                                                <span>{req.skill} <small>({req.criticality})</small></span>
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
                                            label="Interview Strategy"
                                            placeholder="Select strategy..."
                                            options={[
                                                ...strategies.filter(s => !formData.interviewType || s.applicable_interview_types.includes(formData.interviewType)).map(s => ({ value: s.strategy_id, label: s.name }))
                                            ]}
                                            value={formData.strategy_id}
                                            onChange={(e) => setFormData({ ...formData, strategy_id: e.target.value })}
                                            error={errors.strategy_id}
                                        />
                                        <Select
                                            label="Interview Type"
                                            placeholder="Select type..."
                                            options={[
                                                ...INTERVIEW_TYPES
                                            ]}
                                            value={formData.interviewType}
                                            onChange={(e) => setFormData({ ...formData, interviewType: e.target.value })}
                                        />
                                    </div>

                                    {selectedStrategy && selectedStrategy.description && (
                                        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '5px', marginBottom: '20px' }}>
                                            {selectedStrategy.description}
                                        </p>
                                    )}

                                    {formData.interviewType === "mixed" && (
                                        <div className="mixed-composition-section" style={{ marginTop: '20px' }}>
                                            <h4>Mixed Composition (Target interview emphasis)</h4>
                                            {errors.mixed_composition && <p className="input-error-msg">{errors.mixed_composition}</p>}
                                            <div className="form-grid-2x">
                                                <Input label="Technical" type="number" step="0.1" min="0" max="1"
                                                    value={formData.mixed_composition.technical}
                                                    onChange={e => setFormData({ ...formData, mixed_composition: { ...formData.mixed_composition, technical: parseFloat(e.target.value) || 0 } })} />
                                                <Input label="Resume / Experience" type="number" step="0.1" min="0" max="1"
                                                    value={formData.mixed_composition.resume_experience}
                                                    onChange={e => setFormData({ ...formData, mixed_composition: { ...formData.mixed_composition, resume_experience: parseFloat(e.target.value) || 0 } })} />
                                                <Input label="HR / Behavioral" type="number" step="0.1" min="0" max="1"
                                                    value={formData.mixed_composition.hr_behavioral}
                                                    onChange={e => setFormData({ ...formData, mixed_composition: { ...formData.mixed_composition, hr_behavioral: parseFloat(e.target.value) || 0 } })} />
                                                <Input label="Situational / Case" type="number" step="0.1" min="0" max="1"
                                                    value={formData.mixed_composition.situational_case}
                                                    onChange={e => setFormData({ ...formData, mixed_composition: { ...formData.mixed_composition, situational_case: parseFloat(e.target.value) || 0 } })} />
                                            </div>
                                        </div>
                                    )}

                                    {selectedStrategy && (
                                        <div className="budget-override-section" style={{ marginTop: '20px', padding: '15px', background: 'var(--bg-card-hover)', borderRadius: '8px' }}>
                                            <h4>Question Budget</h4>
                                            {selectedStrategy.budget_mode === "distinct_topics" ? (
                                                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                                                    Based on distinct topics
                                                </p>
                                            ) : (
                                                <>
                                                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                                                        Target: {selectedStrategy.target_questions} questions | Adjustable: {selectedStrategy.min_questions + (selectedStrategy.company_override_bounds?.target_questions_min_delta || 0)}–{selectedStrategy.max_questions + (selectedStrategy.company_override_bounds?.target_questions_max_delta || 0)}
                                                    </p>
                                                    <div className="form-grid-2x">
                                                        {selectedStrategy.min_questions !== selectedStrategy.max_questions && (
                                                            <Input
                                                                label="Target Questions Override (Optional)"
                                                                type="number"
                                                                min={selectedStrategy.min_questions + (selectedStrategy.company_override_bounds?.target_questions_min_delta || 0)}
                                                                max={selectedStrategy.max_questions + (selectedStrategy.company_override_bounds?.target_questions_max_delta || 0)}
                                                                placeholder={`Default: ${selectedStrategy.target_questions}`}
                                                                value={formData.budget_override_target}
                                                                onChange={(e) => setFormData({ ...formData, budget_override_target: e.target.value })}
                                                            />
                                                        )}
                                                    </div>
                                                </>
                                            )}
                                            {selectedStrategy.difficulty_policy?.band_constrainable !== false && (
                                                <div className="form-grid-2x" style={{ marginTop: '15px' }}>
                                                    <Select
                                                        label="Difficulty"
                                                        placeholder="Select difficulty..."
                                                        options={DIFFICULTY_LEVELS}
                                                        value={formData.difficulty_band}
                                                        onChange={(e) => setFormData({ ...formData, difficulty_band: e.target.value })}
                                                    />
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    <div className="form-grid-2x" style={{ marginTop: '20px' }}>
                                        <Select
                                            label="Language"
                                            placeholder="Platform Default"
                                            options={[
                                                ...(platform?.allowed_languages || ["English"]).map(l => ({ value: l, label: l }))
                                            ]}
                                            value={formData.language}
                                            onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                                        />
                                        <Select
                                            label="Voice"
                                            placeholder="Platform Default"
                                            options={VALID_VOICES}
                                            value={formData.voice_id}
                                            onChange={(e) => setFormData({ ...formData, voice_id: e.target.value })}
                                        />
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
                                            <span>Interview Strategy</span>
                                            <h4>{selectedStrategy ? selectedStrategy.name : formData.strategy_id}</h4>
                                        </div>
                                        <div className="review-card">
                                            <span>Language</span>
                                            <h4>{formData.language || "Platform Default"}</h4>
                                        </div>
                                        <div className="review-card">
                                            <span>Voice</span>
                                            <h4>{formData.voice_id ? formData.voice_id.charAt(0).toUpperCase() + formData.voice_id.slice(1) : "Platform Default"}</h4>
                                        </div>
                                        <div className="review-card">
                                            <span>Question Target</span>
                                            <h4>{formData.budget_override_target || (selectedStrategy ? (selectedStrategy.budget_mode === "distinct_topics" ? "Based on distinct topics" : selectedStrategy.target_questions) : "Default")}</h4>
                                        </div>
                                    </div>

                                    <div className="review-block-full">
                                        <span>Expected Candidate Requirements</span>
                                        <div className="review-reqs-wrap">
                                            {formData.requirements.map((req, idx) => (
                                                <span key={idx} className="compact-chip read-only">
                                                    {req.skill} <small>({req.criticality})</small>
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

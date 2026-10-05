import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import toast, { Toaster } from "react-hot-toast";
import { ArrowLeft, Info } from "lucide-react";

import DashboardGrid from "../../../layouts/DashboardGrid";
import PageHeader from "../../../components/layout/PageHeader";
import SectionCard from "../../../components/layout/SectionCard";
import Button from "../../../components/common/Button";
import { StrategiesAPI } from "../../../api/strategies";
import "../../../styles/admin/form.css";

import { strategySchema, defaultValues } from "./schema";
import {
    INTERVIEW_TYPES,
    QUESTION_CATEGORIES,
    DIFFICULTY_LEVELS,
    TOPIC_SELECTION_POLICY_TYPES,
    DIFFICULTY_SCOPES,
    BUDGET_MODES,
} from "./constants";

function FieldError({ error }) {
    if (!error) return null;
    return <span style={{ color: "var(--danger)", fontSize: "12px" }}>{error.message}</span>;
}

function CheckboxGroup({ label, options, selected, onChange, error }) {
    const toggle = (value) => {
        if (selected.includes(value)) {
            onChange(selected.filter((v) => v !== value));
        } else {
            onChange([...selected, value]);
        }
    };

    return (
        <div className="ih-form-group">
            <label>{label}</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
                {options.map((opt) => (
                    <label
                        key={opt.value}
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "6px",
                            padding: "6px 12px",
                            borderRadius: "6px",
                            border: `1px solid ${selected.includes(opt.value) ? "var(--primary)" : "var(--border)"}`,
                            background: selected.includes(opt.value) ? "rgba(79, 70, 229, 0.1)" : "var(--bg-secondary)",
                            cursor: "pointer",
                            fontSize: "13px",
                            color: "var(--text)",
                        }}
                    >
                        <input
                            type="checkbox"
                            checked={selected.includes(opt.value)}
                            onChange={() => toggle(opt.value)}
                            style={{ accentColor: "var(--primary)" }}
                        />
                        {opt.label}
                    </label>
                ))}
            </div>
            <FieldError error={error} />
        </div>
    );
}

// Authoring form for backend/app/ai_interview/schemas/strategy.py's
// StrategyDefinition. This component only edits and submits configuration —
// it contains no interview decision logic (no priority/difficulty/follow-up/
// completion calculation; that all lives in the backend's deterministic engine).
export default function StrategyForm({ strategyId }) {
    const navigate = useNavigate();
    const isEditMode = !!strategyId;

    const [initialLoading, setInitialLoading] = useState(isEditMode);
    const [loadError, setLoadError] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [apiError, setApiError] = useState(null);

    const {
        register,
        handleSubmit,
        watch,
        setValue,
        reset,
        formState: { errors },
    } = useForm({
        resolver: zodResolver(strategySchema),
        defaultValues,
        mode: "onChange",
    });

    useEffect(() => {
        if (!isEditMode) return;

        const fetchStrategy = async () => {
            setInitialLoading(true);
            setLoadError(null);
            try {
                const data = await StrategiesAPI.getStrategy(strategyId);
                reset({
                    ...defaultValues,
                    ...data,
                    critical_topic_max_followups: data.critical_topic_max_followups ?? "",
                });
            } catch (err) {
                console.error("Failed to load strategy for editing:", err);
                setLoadError("Unable to load this strategy's configuration.");
            } finally {
                setInitialLoading(false);
            }
        };
        fetchStrategy();
    }, [isEditMode, strategyId, reset]);

    const onSubmit = async (data) => {
        setApiError(null);
        setSubmitting(true);
        try {
            const payload = {
                ...data,
                critical_topic_max_followups:
                    data.critical_topic_max_followups === "" ? null : data.critical_topic_max_followups,
            };

            // Editing an existing strategy NEVER mutates a prior version in
            // place — it creates a brand-new version via the versions
            // endpoint. strategy_id stays locked to the one being edited
            // (the field is disabled in edit mode) so this can never create
            // a second, unrelated strategy.
            const response = isEditMode
                ? await StrategiesAPI.createStrategyVersion(strategyId, { ...payload, strategy_id: strategyId })
                : await StrategiesAPI.createStrategy(payload);

            toast.success(isEditMode ? "New version created successfully." : "Strategy created successfully.");
            navigate(`/admin/strategies/${response.strategy_id || strategyId || payload.strategy_id}`);
        } catch (err) {
            console.error(isEditMode ? "Failed to create new strategy version:" : "Failed to create strategy:", err);
            const message = err?.message || (isEditMode ? "Failed to create new version." : "Failed to create strategy.");
            setApiError(message);
            toast.error(message);
        } finally {
            setSubmitting(false);
        }
    };

    if (initialLoading) {
        return (
            <DashboardGrid>
                <PageHeader title="Loading..." />
                <div style={{ padding: "20px", color: "var(--text-secondary)" }}>Loading strategy configuration...</div>
            </DashboardGrid>
        );
    }

    if (loadError) {
        return (
            <DashboardGrid>
                <PageHeader title="Error" />
                <div style={{ padding: "20px", color: "var(--danger)" }}>{loadError}</div>
            </DashboardGrid>
        );
    }

    const applicableTypes = watch("applicable_interview_types") || [];
    const allowedCategories = watch("followup_policy.allowed_categories") || [];
    const allowedBands = watch("company_override_bounds.allowed_difficulty_bands") || [];

    const rightContent = (
        <Button
            variant="outline"
            onClick={() => navigate(isEditMode ? `/admin/strategies/${strategyId}` : "/admin/strategies")}
        >
            <ArrowLeft size={16} /> Cancel
        </Button>
    );

    return (
        <DashboardGrid>
            <Toaster position="top-right" toastOptions={{ style: { background: "var(--card-bg)", color: "var(--text)", border: "1px solid var(--border)" } }} />

            <PageHeader
                title={isEditMode ? `Edit Strategy: ${strategyId}` : "New Interview Strategy"}
                description="Author the deterministic policy that governs topic selection, difficulty, follow-ups, and completion for the Official Interview Engine. This form only edits configuration — it does not calculate interview decisions."
                rightContent={rightContent}
            />

            {isEditMode && (
                <SectionCard>
                    <div style={{ display: "flex", gap: "10px", alignItems: "flex-start", color: "var(--text-secondary)", fontSize: "13px" }}>
                        <Info size={18} style={{ flexShrink: 0, marginTop: "1px" }} />
                        <span>
                            This backend has no endpoint to update an existing strategy version's fields in place.
                            Saving here creates a brand-new version with these values — the version you loaded (and
                            every version before it) remains unchanged and still retrievable from the version history.
                            Activating the new version is a separate step on the strategy detail page.
                        </span>
                    </div>
                </SectionCard>
            )}

            <form onSubmit={handleSubmit(onSubmit)} autoComplete="off">
                <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                    <SectionCard>
                        <h3 style={{ marginTop: 0 }}>Basic Information</h3>
                        <div className="ih-form-row">
                            <div className="ih-form-group">
                                <label>
                                    Strategy ID <span className="required">*</span>
                                </label>
                                <input
                                    type="text"
                                    {...register("strategy_id")}
                                    placeholder="e.g. my_custom_strategy"
                                    disabled={isEditMode}
                                    autoComplete="off"
                                    style={{ borderColor: errors.strategy_id ? "var(--danger)" : "" }}
                                />
                                <FieldError error={errors.strategy_id} />
                            </div>
                            <div className="ih-form-group">
                                <label>
                                    Name <span className="required">*</span>
                                </label>
                                <input
                                    type="text"
                                    {...register("name")}
                                    placeholder="e.g. My Custom Strategy"
                                    autoComplete="off"
                                    style={{ borderColor: errors.name ? "var(--danger)" : "" }}
                                />
                                <FieldError error={errors.name} />
                            </div>
                        </div>
                        <div className="ih-form-row">
                            <div className="ih-form-group">
                                <label>
                                    Description <span className="required">*</span>
                                </label>
                                <textarea
                                    {...register("description")}
                                    placeholder="Describe how this strategy should select topics, adapt difficulty, and decide follow-ups."
                                    autoComplete="off"
                                    style={{ height: "80px", resize: "none", borderColor: errors.description ? "var(--danger)" : "" }}
                                />
                                <FieldError error={errors.description} />
                            </div>
                        </div>
                        <div className="ih-form-row">
                            <label style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text)", fontSize: "14px", cursor: "pointer" }}>
                                <input type="checkbox" {...register("is_active")} style={{ width: "16px", height: "16px", accentColor: "var(--primary)" }} />
                                Active
                            </label>
                        </div>
                    </SectionCard>

                    <SectionCard>
                        <h3 style={{ marginTop: 0 }}>Applicability</h3>
                        <CheckboxGroup
                            label="Applicable Interview Types *"
                            options={INTERVIEW_TYPES}
                            selected={applicableTypes}
                            onChange={(val) => setValue("applicable_interview_types", val, { shouldValidate: true })}
                            error={errors.applicable_interview_types}
                        />
                        <div className="ih-form-row">
                            <div className="ih-form-group">
                                <label>Budget Mode</label>
                                <select {...register("budget_mode")}>
                                    {BUDGET_MODES.map((o) => (
                                        <option key={o.value} value={o.value}>{o.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </SectionCard>

                    <SectionCard>
                        <h3 style={{ marginTop: 0 }}>Question Budget</h3>
                        <div className="ih-form-row">
                            <div className="ih-form-group">
                                <label>Min Questions <span className="required">*</span></label>
                                <input type="number" {...register("min_questions")} style={{ borderColor: errors.min_questions ? "var(--danger)" : "" }} />
                                <FieldError error={errors.min_questions} />
                            </div>
                            <div className="ih-form-group">
                                <label>Target Questions <span className="required">*</span></label>
                                <input type="number" {...register("target_questions")} style={{ borderColor: errors.target_questions ? "var(--danger)" : "" }} />
                                <FieldError error={errors.target_questions} />
                            </div>
                            <div className="ih-form-group">
                                <label>Max Questions <span className="required">*</span></label>
                                <input type="number" {...register("max_questions")} style={{ borderColor: errors.max_questions ? "var(--danger)" : "" }} />
                                <FieldError error={errors.max_questions} />
                            </div>
                        </div>
                        <div className="ih-form-row">
                            <div className="ih-form-group">
                                <label>Max Questions / Topic</label>
                                <input type="number" {...register("max_questions_per_topic")} style={{ borderColor: errors.max_questions_per_topic ? "var(--danger)" : "" }} />
                                <FieldError error={errors.max_questions_per_topic} />
                            </div>
                            <div className="ih-form-group">
                                <label>Max Follow-ups / Topic</label>
                                <input type="number" {...register("max_followups_per_topic")} style={{ borderColor: errors.max_followups_per_topic ? "var(--danger)" : "" }} />
                                <FieldError error={errors.max_followups_per_topic} />
                            </div>
                            <div className="ih-form-group">
                                <label>Critical Topic Max Follow-ups</label>
                                <input type="number" {...register("critical_topic_max_followups")} placeholder="Optional" />
                            </div>
                        </div>
                    </SectionCard>

                    <SectionCard>
                        <h3 style={{ marginTop: 0 }}>Score Thresholds</h3>
                        <div className="ih-form-row">
                            <div className="ih-form-group">
                                <label>Weak Threshold <span className="required">*</span></label>
                                <input type="number" step="0.01" {...register("weak_threshold")} style={{ borderColor: errors.weak_threshold ? "var(--danger)" : "" }} />
                                <FieldError error={errors.weak_threshold} />
                            </div>
                            <div className="ih-form-group">
                                <label>Acceptable Threshold <span className="required">*</span></label>
                                <input type="number" step="0.01" {...register("acceptable_threshold")} style={{ borderColor: errors.acceptable_threshold ? "var(--danger)" : "" }} />
                                <FieldError error={errors.acceptable_threshold} />
                            </div>
                            <div className="ih-form-group">
                                <label>Strong Threshold <span className="required">*</span></label>
                                <input type="number" step="0.01" {...register("strong_threshold")} style={{ borderColor: errors.strong_threshold ? "var(--danger)" : "" }} />
                                <FieldError error={errors.strong_threshold} />
                            </div>
                        </div>
                    </SectionCard>

                    <SectionCard>
                        <h3 style={{ marginTop: 0 }}>Topic Selection Policy</h3>
                        <div className="ih-form-row">
                            <div className="ih-form-group">
                                <label>Policy Type</label>
                                <select {...register("topic_selection_policy.policy_type")}>
                                    {TOPIC_SELECTION_POLICY_TYPES.map((o) => (
                                        <option key={o.value} value={o.value}>{o.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </SectionCard>

                    <SectionCard>
                        <h3 style={{ marginTop: 0 }}>Difficulty Policy</h3>
                        <div className="ih-form-row">
                            <div className="ih-form-group">
                                <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                    <input type="checkbox" {...register("difficulty_policy.adapts")} style={{ width: "16px", height: "16px", accentColor: "var(--primary)" }} />
                                    Adapts per answer
                                </label>
                            </div>
                            <div className="ih-form-group">
                                <label>Scope</label>
                                <select {...register("difficulty_policy.scope")}>
                                    {DIFFICULTY_SCOPES.map((o) => (
                                        <option key={o.value} value={o.value}>{o.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className="ih-form-row">
                            <div className="ih-form-group">
                                <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                    <input type="checkbox" {...register("difficulty_policy.reset_on_switch")} style={{ width: "16px", height: "16px", accentColor: "var(--primary)" }} />
                                    Reset on topic switch
                                </label>
                            </div>
                            <div className="ih-form-group">
                                <label>Step Size</label>
                                <input type="number" {...register("difficulty_policy.step_size")} style={{ borderColor: errors.difficulty_policy?.step_size ? "var(--danger)" : "" }} />
                                <FieldError error={errors.difficulty_policy?.step_size} />
                            </div>
                            <div className="ih-form-group">
                                <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                    <input type="checkbox" {...register("difficulty_policy.band_constrainable")} style={{ width: "16px", height: "16px", accentColor: "var(--primary)" }} />
                                    Band constrainable by campaign
                                </label>
                            </div>
                        </div>
                    </SectionCard>

                    <SectionCard>
                        <h3 style={{ marginTop: 0 }}>Follow-up Policy</h3>
                        <CheckboxGroup
                            label="Allowed Categories"
                            options={QUESTION_CATEGORIES}
                            selected={allowedCategories}
                            onChange={(val) => setValue("followup_policy.allowed_categories", val, { shouldValidate: true })}
                        />
                        <div className="ih-form-row">
                            <div className="ih-form-group">
                                <label>Max Per Topic</label>
                                <input type="number" {...register("followup_policy.max_per_topic")} style={{ borderColor: errors.followup_policy?.max_per_topic ? "var(--danger)" : "" }} />
                                <FieldError error={errors.followup_policy?.max_per_topic} />
                            </div>
                        </div>
                    </SectionCard>

                    <SectionCard>
                        <h3 style={{ marginTop: 0 }}>Gap Policy</h3>
                        <div className="ih-form-row">
                            <div className="ih-form-group">
                                <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                    <input type="checkbox" {...register("gap_policy.enabled")} style={{ width: "16px", height: "16px", accentColor: "var(--primary)" }} />
                                    Enabled
                                </label>
                            </div>
                            <div className="ih-form-group">
                                <label>Max Share of Budget</label>
                                <input type="number" step="0.01" {...register("gap_policy.max_share_of_budget")} style={{ borderColor: errors.gap_policy?.max_share_of_budget ? "var(--danger)" : "" }} />
                                <FieldError error={errors.gap_policy?.max_share_of_budget} />
                            </div>
                        </div>
                    </SectionCard>

                    <SectionCard>
                        <h3 style={{ marginTop: 0 }}>Completion Policy</h3>
                        <div className="ih-form-row">
                            <div className="ih-form-group">
                                <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                    <input type="checkbox" {...register("completion_policy.allow_early_exit")} style={{ width: "16px", height: "16px", accentColor: "var(--primary)" }} />
                                    Allow early exit
                                </label>
                            </div>
                            <div className="ih-form-group">
                                <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                    <input type="checkbox" {...register("completion_policy.require_all_critical_covered")} style={{ width: "16px", height: "16px", accentColor: "var(--primary)" }} />
                                    Require all critical topics covered
                                </label>
                            </div>
                        </div>
                    </SectionCard>

                    <SectionCard>
                        <h3 style={{ marginTop: 0 }}>Company Override Bounds</h3>
                        <p style={{ marginTop: 0, color: "var(--text-secondary)", fontSize: "13px" }}>
                            Defines how far a company may narrow this strategy's budget/difficulty when configuring a campaign.
                        </p>
                        <div className="ih-form-row">
                            <div className="ih-form-group">
                                <label>Target Questions Min Delta</label>
                                <input type="number" {...register("company_override_bounds.target_questions_min_delta")} />
                            </div>
                            <div className="ih-form-group">
                                <label>Target Questions Max Delta</label>
                                <input type="number" {...register("company_override_bounds.target_questions_max_delta")} />
                            </div>
                        </div>
                        <CheckboxGroup
                            label="Allowed Difficulty Bands"
                            options={DIFFICULTY_LEVELS}
                            selected={allowedBands}
                            onChange={(val) => setValue("company_override_bounds.allowed_difficulty_bands", val, { shouldValidate: true })}
                        />
                    </SectionCard>

                    {errors.max_questions?.type === "custom" && (
                        <div style={{ color: "var(--danger)", fontSize: "13px" }}>{errors.max_questions.message}</div>
                    )}
                    {errors.strong_threshold?.type === "custom" && (
                        <div style={{ color: "var(--danger)", fontSize: "13px" }}>{errors.strong_threshold.message}</div>
                    )}

                    {apiError && (
                        <SectionCard>
                            <div style={{ color: "var(--danger)", fontSize: "14px" }}>{apiError}</div>
                        </SectionCard>
                    )}

                    <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end" }}>
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => navigate(isEditMode ? `/admin/strategies/${strategyId}` : "/admin/strategies")}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            variant="primary"
                            isLoading={submitting}
                        >
                            {isEditMode ? "Save as New Version" : "Create Strategy"}
                        </Button>
                    </div>
                </div>
            </form>
        </DashboardGrid>
    );
}

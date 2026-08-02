import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import toast, { Toaster } from "react-hot-toast";
import { 
    ArrowLeft, Check, Info, Settings, Shield, 
    CreditCard, LayoutGrid, Globe, Mic, Cpu, MessageSquare, 
    CheckCircle2, FileText, Copy
} from "lucide-react";

import DashboardGrid from "../../../layouts/DashboardGrid";
import PageHeader from "../../../components/layout/PageHeader";
import SectionCard from "../../../components/layout/SectionCard";
import Button from "../../../components/common/Button";
import { CompaniesAPI } from "../../../api/companies";
import { SettingsAPI } from "../../../api/settings";
import "../../../styles/admin/form.css";

import { companySchema, defaultValues } from "./schema";

import GeneralTab from "./tabs/GeneralTab";
import SubscriptionTab from "./tabs/SubscriptionTab";
import LimitsTab from "./tabs/LimitsTab";
import AIModelsTab from "./tabs/AIModelsTab";
import LanguagesTab from "./tabs/LanguagesTab";
import VoicesTab from "./tabs/VoicesTab";
import InterviewModesTab from "./tabs/InterviewModesTab";
import StrategiesTab from "./tabs/StrategiesTab";
import FeaturesTab from "./tabs/FeaturesTab";
import SecurityTab from "./tabs/SecurityTab";
import ReviewTab from "./tabs/ReviewTab";

const TABS = [
    { id: 'general', label: 'General', icon: <Info size={18} /> },
    { id: 'subscription', label: 'Subscription', icon: <CreditCard size={18} /> },
    { id: 'limits', label: 'Limits', icon: <LayoutGrid size={18} /> },
    { id: 'ai_models', label: 'AI Models', icon: <Cpu size={18} /> },
    { id: 'languages', label: 'Languages', icon: <Globe size={18} /> },
    { id: 'voices', label: 'Voices', icon: <Mic size={18} /> },
    { id: 'interview_modes', label: 'Interview Modes', icon: <MessageSquare size={18} /> },
    { id: 'strategies', label: 'Strategies', icon: <Settings size={18} /> },
    { id: 'features', label: 'Features', icon: <CheckCircle2 size={18} /> },
    { id: 'security', label: 'Security', icon: <Shield size={18} /> },
    { id: 'review', label: 'Review & Save', icon: <FileText size={18} /> }
];

export default function CompanyWizard({ companyId }) {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const isEditMode = !!companyId;
    
    const [loading, setLoading] = useState(false);
    const [initialFetchLoading, setInitialFetchLoading] = useState(isEditMode);
    const [masterConfig, setMasterConfig] = useState(null);
    const [credentials, setCredentials] = useState(null);
    const [activeTab, setActiveTab] = useState('general');
    
    const { register, handleSubmit, watch, setValue, formState: { errors }, reset, trigger } = useForm({
        resolver: zodResolver(companySchema),
        defaultValues: defaultValues,
        mode: "onChange"
    });

    useEffect(() => {
        const fetchInitialData = async () => {
            try {
                const config = await SettingsAPI.getMasterSettings();
                setMasterConfig(config);
                
                if (isEditMode) {
                    const company = await CompaniesAPI.getCompany(companyId);
                    reset(company);
                } else {
                    // Pre-fill features from master config
                    const initFeatures = {};
                    config.features.forEach(f => {
                        initFeatures[f.id] = f.enabled;
                    });
                    
                    reset({
                        ...defaultValues,
                        features: initFeatures,
                        allowed_llm_tiers: config.ai_models.map(m => m.id),
                        allowed_languages: config.languages.map(l => l.name),
                        allowed_voices: config.voices.map(v => v.name),
                        allowed_strategies: config.strategies.map(s => s.name),
                        allowed_interview_modes: config.interview_modes.map(m => m.name),
                    });
                }
            } catch (err) {
                toast.error("Failed to load configuration data.");
                console.error("Fetch error", err);
            } finally {
                setInitialFetchLoading(false);
            }
        };
        fetchInitialData();
    }, [isEditMode, companyId, reset]);

    const handleTabChange = async (tabId) => {
        // Trigger validation on current tab before switching
        let valid = true;
        if (activeTab === 'general') {
            valid = await trigger(["general.name", "general.contact_email", "general.website"]);
        } else if (activeTab === 'subscription') {
            valid = await trigger(["subscription.plan", "subscription.status"]);
        } else if (activeTab === 'limits') {
            valid = await trigger("limits");
        }
        
        if (valid) {
            setActiveTab(tabId);
        } else {
            toast.error("Please fix errors before proceeding.");
        }
    };

    const onSubmit = async (data) => {
        try {
            setLoading(true);
            const promise = isEditMode 
                ? CompaniesAPI.updateCompany(companyId, data)
                : CompaniesAPI.createCompany(data);
                
            toast.promise(promise, {
                loading: isEditMode ? 'Updating Enterprise Configuration...' : 'Provisioning Enterprise...',
                success: 'Success!',
                error: 'Failed to process request.'
            });

            const response = await promise;
            
            if (isEditMode) {
                queryClient.invalidateQueries({ queryKey: ['company-details'] });
                queryClient.invalidateQueries({ queryKey: ['companies'] });
                navigate(`/admin/companies/${companyId}`);
            } else {
                setCredentials({
                    company_id: response.company_id,
                    username: response.username,
                    temporary_password: response.temporary_password
                });
                queryClient.invalidateQueries({ queryKey: ['companies'] });
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleCopy = () => {
        const text = `Username: ${credentials.username}\nTemporary Password: ${credentials.temporary_password}`;
        navigator.clipboard.writeText(text);
        toast.success("Credentials copied to clipboard");
    };

    if (initialFetchLoading || !masterConfig) {
        return (
            <DashboardGrid>
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    <div className="ih-skeleton" style={{ width: '100%', height: '400px', borderRadius: '12px' }}></div>
                </div>
            </DashboardGrid>
        );
    }

    if (credentials) {
        return (
            <DashboardGrid>
                <div style={{ maxWidth: '600px', margin: '40px auto', textAlign: 'center' }}>
                    <div style={{ width: '64px', height: '64px', background: 'var(--success)', color: 'white', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
                        <Check size={32} />
                    </div>
                    <h2 style={{ marginBottom: '12px', color: 'var(--text)' }}>Enterprise Provisioned</h2>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>
                        The company admin account has been provisioned. Please securely share these credentials.
                    </p>
                    
                    <SectionCard>
                        <div style={{ textAlign: 'left', background: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px', marginBottom: '24px' }}>
                            <div style={{ marginBottom: '12px' }}>
                                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Company ID</label>
                                <div style={{ fontFamily: 'monospace', fontSize: '16px', color: 'var(--text)' }}>{credentials.company_id}</div>
                            </div>
                            <div style={{ marginBottom: '12px' }}>
                                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Admin Username</label>
                                <div style={{ fontFamily: 'monospace', fontSize: '16px', color: 'var(--text)' }}>{credentials.username}</div>
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Temporary Password</label>
                                <div style={{ fontFamily: 'monospace', fontSize: '16px', color: 'var(--text)' }}>{credentials.temporary_password}</div>
                            </div>
                        </div>
                        
                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                            <Button variant="outline" onClick={handleCopy}>
                                <Copy size={16} /> Copy Credentials
                            </Button>
                            <Button variant="primary" onClick={() => navigate(`/admin/companies/${credentials.company_id}`)}>
                                Go to Company Dashboard
                            </Button>
                        </div>
                    </SectionCard>
                </div>
            </DashboardGrid>
        );
    }

    return (
        <DashboardGrid>
            <Toaster position="top-right" toastOptions={{ style: { background: 'var(--card-bg)', color: 'var(--text)', border: '1px solid var(--border)' } }} />
            
            <PageHeader 
                title={(
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <button 
                            onClick={() => navigate(isEditMode ? `/admin/companies/${companyId}` : "/admin/companies")}
                            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                        >
                            <ArrowLeft size={20} />
                        </button>
                        {isEditMode ? `Edit Configuration: ${watch("general.name") || companyId}` : "Provision Enterprise Workspace"}
                    </div>
                )}
                description={isEditMode ? "Modify limits, permissions, and AI resources for this company." : "Configure limits, permissions, and AI resources for a new company based on the global Master Config."}
            />

            <form onSubmit={handleSubmit(onSubmit)} style={{ display: 'flex', gap: '24px', alignItems: 'flex-start', minHeight: '600px' }}>
                
                {/* Left Navigation Panel */}
                <div style={{ width: '250px', background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px', position: 'sticky', top: '24px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {TABS.map(tab => {
                            const hasError = tab.id === 'general' && errors.general 
                                || tab.id === 'subscription' && errors.subscription 
                                || tab.id === 'limits' && errors.limits 
                                || tab.id === 'security' && errors.security;

                            return (
                                <button
                                    key={tab.id}
                                    type="button"
                                    onClick={() => handleTabChange(tab.id)}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between',
                                        padding: '12px 16px',
                                        background: activeTab === tab.id ? 'var(--bg-secondary)' : 'transparent',
                                        border: 'none',
                                        borderRadius: '8px',
                                        color: activeTab === tab.id ? 'var(--text)' : 'var(--text-secondary)',
                                        fontWeight: activeTab === tab.id ? '600' : '400',
                                        cursor: 'pointer',
                                        textAlign: 'left',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <span style={{ color: activeTab === tab.id ? 'var(--primary)' : 'inherit' }}>
                                            {tab.icon}
                                        </span>
                                        {tab.label}
                                    </div>
                                    {hasError && <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--danger)' }} />}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Right Content Panel */}
                <div style={{ flex: 1, minWidth: 0, paddingBottom: '60px' }}>
                    <div style={{ display: activeTab === 'general' ? 'block' : 'none' }}>
                        <GeneralTab register={register} errors={errors} />
                    </div>
                    <div style={{ display: activeTab === 'subscription' ? 'block' : 'none' }}>
                        <SubscriptionTab register={register} errors={errors} />
                    </div>
                    <div style={{ display: activeTab === 'limits' ? 'block' : 'none' }}>
                        <LimitsTab register={register} errors={errors} />
                    </div>
                    <div style={{ display: activeTab === 'ai_models' ? 'block' : 'none' }}>
                        <AIModelsTab masterConfig={masterConfig} watch={watch} setValue={setValue} />
                    </div>
                    <div style={{ display: activeTab === 'languages' ? 'block' : 'none' }}>
                        <LanguagesTab masterConfig={masterConfig} watch={watch} setValue={setValue} />
                    </div>
                    <div style={{ display: activeTab === 'voices' ? 'block' : 'none' }}>
                        <VoicesTab masterConfig={masterConfig} watch={watch} setValue={setValue} />
                    </div>
                    <div style={{ display: activeTab === 'interview_modes' ? 'block' : 'none' }}>
                        <InterviewModesTab masterConfig={masterConfig} watch={watch} setValue={setValue} />
                    </div>
                    <div style={{ display: activeTab === 'strategies' ? 'block' : 'none' }}>
                        <StrategiesTab masterConfig={masterConfig} watch={watch} setValue={setValue} />
                    </div>
                    <div style={{ display: activeTab === 'features' ? 'block' : 'none' }}>
                        <FeaturesTab masterConfig={masterConfig} watch={watch} setValue={setValue} />
                    </div>
                    <div style={{ display: activeTab === 'security' ? 'block' : 'none' }}>
                        <SecurityTab register={register} watch={watch} setValue={setValue} />
                    </div>
                    <div style={{ display: activeTab === 'review' ? 'block' : 'none' }}>
                        <ReviewTab 
                            watch={watch} 
                            masterConfig={masterConfig} 
                            isEditMode={isEditMode} 
                            loading={loading} 
                            onSubmit={handleSubmit(onSubmit)} 
                            navigate={navigate} 
                            companyId={companyId} 
                        />
                    </div>
                </div>
            </form>
        </DashboardGrid>
    );
}

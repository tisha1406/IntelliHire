import React from 'react';
import SectionCard from "../../../layout/SectionCard";
import Button from "../../../common/Button";
import { Save } from "lucide-react";

export default function ReviewTab({ watch, masterConfig, isEditMode, loading, onSubmit, navigate, companyId }) {
    const formData = watch();
    
    return (
        <SectionCard title={isEditMode ? "Review & Save Changes" : "Review & Provision"}>
            <div style={{ background: 'var(--bg-secondary)', padding: '24px', borderRadius: '8px', marginBottom: '24px' }}>
                <h3 style={{ margin: '0 0 24px', color: 'var(--text)' }}>{formData.general?.name || "Unnamed Company"} Configuration Summary</h3>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '32px', color: 'var(--text-secondary)', fontSize: '14px' }}>
                    
                    {/* General & Limits */}
                    <div>
                        <h4 style={{ color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: '8px', marginBottom: '12px' }}>General Information</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <div><strong>Email:</strong> {formData.general?.contact_email || "N/A"}</div>
                            <div><strong>Plan:</strong> {formData.subscription?.plan}</div>
                            <div><strong>Industry:</strong> {formData.general?.industry || "N/A"}</div>
                            <div><strong>Status:</strong> {formData.subscription?.status}</div>
                        </div>

                        <h4 style={{ color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: '8px', marginBottom: '12px', marginTop: '24px' }}>Limits & Quotas</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <div><strong>Recruiters Limit:</strong> {formData.limits?.max_recruiters}</div>
                            <div><strong>Interviews Limit:</strong> {formData.limits?.max_interviews}</div>
                            <div><strong>Storage Limit:</strong> {formData.limits?.storage_limit_gb} GB</div>
                        </div>
                    </div>

                    {/* Platform & Security */}
                    <div>
                        <h4 style={{ color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: '8px', marginBottom: '12px' }}>Security Policies</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <div>
                                {formData.security?.login_enabled ? <span style={{ color: 'var(--success)' }}>✓ Login Enabled</span> : <span style={{ color: 'var(--text-muted)' }}>✗ Login Disabled</span>}
                            </div>
                            <div>
                                {formData.security?.mfa_required ? <span style={{ color: 'var(--success)' }}>✓ MFA Enforced</span> : <span style={{ color: 'var(--text-muted)' }}>✗ MFA Optional</span>}
                            </div>
                            <div><strong>Session Timeout:</strong> {formData.security?.session_timeout_minutes} min</div>
                            <div><strong>Login Policy:</strong> {formData.security?.password_policy}</div>
                        </div>

                        <h4 style={{ color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: '8px', marginBottom: '12px', marginTop: '24px' }}>Platform Features</h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {masterConfig.features.filter(f => f.enabled).map(feat => (
                                <div key={feat.id} style={{ display: 'flex', alignItems: 'center', gap: '4px', color: formData.features?.[feat.id] ? 'var(--text)' : 'var(--text-muted)' }}>
                                    {formData.features?.[feat.id] ? '✓' : '□'} {feat.name}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* AI Resources */}
                    <div>
                        <h4 style={{ color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: '8px', marginBottom: '12px' }}>AI Models Allocation</h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {masterConfig.ai_models.map(model => (
                                <div key={model.id} style={{ display: 'flex', alignItems: 'center', gap: '4px', color: formData.allowed_llm_tiers?.includes(model.id) ? 'var(--text)' : 'var(--text-muted)' }}>
                                    {formData.allowed_llm_tiers?.includes(model.id) ? '✓' : '□'} {model.name}
                                </div>
                            ))}
                        </div>

                        <h4 style={{ color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: '8px', marginBottom: '12px', marginTop: '24px' }}>Languages</h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {masterConfig.languages.map(lang => (
                                <div key={lang.id} style={{ display: 'flex', alignItems: 'center', gap: '4px', color: formData.allowed_languages?.includes(lang.name) ? 'var(--text)' : 'var(--text-muted)' }}>
                                    {formData.allowed_languages?.includes(lang.name) ? '✓' : '□'} {lang.name}
                                </div>
                            ))}
                        </div>
                        
                        <h4 style={{ color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: '8px', marginBottom: '12px', marginTop: '24px' }}>Interview Strategies</h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {masterConfig.strategies.map(strat => (
                                <div key={strat.id} style={{ display: 'flex', alignItems: 'center', gap: '4px', color: formData.allowed_strategies?.includes(strat.name) ? 'var(--text)' : 'var(--text-muted)' }}>
                                    {formData.allowed_strategies?.includes(strat.name) ? '✓' : '□'} {strat.name}
                                </div>
                            ))}
                        </div>
                    </div>
                    
                </div>
            </div>
            
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', position: 'sticky', bottom: '0', background: 'var(--card-bg)', padding: '16px 0', borderTop: '1px solid var(--border)' }}>
                <Button type="button" variant="outline" onClick={() => navigate(isEditMode ? `/admin/companies/${companyId}` : "/admin/companies")} disabled={loading}>
                    Cancel
                </Button>
                <Button type="button" variant="primary" onClick={onSubmit} disabled={loading}>
                    <Save size={16} />
                    {loading ? "Saving..." : (isEditMode ? "Save Configuration" : "Provision Enterprise")}
                </Button>
            </div>
        </SectionCard>
    );
}

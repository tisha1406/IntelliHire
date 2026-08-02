import React from 'react';
import SectionCard from "../../../layout/SectionCard";
import ToggleCard from "../components/ToggleCard";
import { ShieldAlert, ShieldCheck } from "lucide-react";

export default function SecurityTab({ register, watch, setValue }) {
    
    // We use watch/setValue to handle the visual ToggleCards manually since they aren't native inputs
    const loginEnabled = watch("security.login_enabled");
    const mfaRequired = watch("security.mfa_required");
    const ssoEnabled = watch("security.sso_enabled");
    const rememberMe = watch("security.remember_me_allowed");

    return (
        <SectionCard title="Security & Compliance" description="Configure authentication policies and access restrictions.">
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                <ToggleCard 
                    label="Allow Company Login"
                    description="If disabled, recruiters and admins from this company cannot log in."
                    checked={loginEnabled}
                    onChange={() => setValue("security.login_enabled", !loginEnabled)}
                    icon={loginEnabled ? <ShieldCheck size={24} /> : <ShieldAlert size={24} />}
                />
                <ToggleCard 
                    label="Require MFA"
                    description="Force Multi-Factor Authentication for all users in this company."
                    checked={mfaRequired}
                    onChange={() => setValue("security.mfa_required", !mfaRequired)}
                />
                <ToggleCard 
                    label="Enable SSO"
                    description="Allow Single Sign-On via SAML/OAuth."
                    checked={ssoEnabled}
                    onChange={() => setValue("security.sso_enabled", !ssoEnabled)}
                />
                <ToggleCard 
                    label="Allow 'Remember Me'"
                    description="Allow users to persist sessions across browser restarts."
                    checked={rememberMe}
                    onChange={() => setValue("security.remember_me_allowed", !rememberMe)}
                />
            </div>

            <div className="ih-form-row">
                <div className="ih-form-group">
                    <label>Password Policy</label>
                    <select {...register("security.password_policy")}>
                        <option value="standard">Standard (8 chars, 1 number)</option>
                        <option value="strict">Strict (12 chars, 1 number, 1 special)</option>
                        <option value="enterprise">Enterprise (16 chars, complex)</option>
                    </select>
                </div>
                <div className="ih-form-group">
                    <label>Session Timeout (Minutes)</label>
                    <input type="number" {...register("security.session_timeout_minutes")} />
                </div>
            </div>

            <div className="ih-form-row">
                <div className="ih-form-group">
                    <label>JWT Lifetime (Hours)</label>
                    <input type="number" {...register("security.jwt_lifetime_hours")} />
                </div>
                <div className="ih-form-group">
                    <label>Refresh Token Lifetime (Days)</label>
                    <input type="number" {...register("security.refresh_token_lifetime_days")} />
                </div>
            </div>

            <div className="ih-form-row">
                <div className="ih-form-group">
                    <label>Concurrent Sessions Allowed</label>
                    <input type="number" {...register("security.concurrent_sessions_allowed")} />
                </div>
                <div className="ih-form-group">
                    <label>Failed Logins Before Lockout</label>
                    <input type="number" {...register("security.login_attempts_before_lockout")} />
                </div>
            </div>
            
        </SectionCard>
    );
}

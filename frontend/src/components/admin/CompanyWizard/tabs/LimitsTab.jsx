import React from 'react';
import SectionCard from "../../../layout/SectionCard";

export default function LimitsTab({ register, errors }) {
    return (
        <SectionCard title="Usage Limits & Quotas" description="Set maximum resource allocations for this company.">
            <div className="ih-form-row">
                <div className="ih-form-group">
                    <label>Maximum Recruiters</label>
                    <input type="number" {...register("limits.max_recruiters")} />
                </div>
                <div className="ih-form-group">
                    <label>Maximum Candidates</label>
                    <input type="number" {...register("limits.max_candidates")} />
                </div>
            </div>
            <div className="ih-form-row">
                <div className="ih-form-group">
                    <label>Maximum Campaigns</label>
                    <input type="number" {...register("limits.max_campaigns")} />
                </div>
                <div className="ih-form-group">
                    <label>Total Allowed Interviews</label>
                    <input type="number" {...register("limits.max_interviews")} />
                </div>
            </div>
            <div className="ih-form-row">
                <div className="ih-form-group">
                    <label>Monthly Interviews Limit</label>
                    <input type="number" {...register("limits.monthly_interviews")} />
                </div>
                <div className="ih-form-group">
                    <label>Concurrent Interviews Limit</label>
                    <input type="number" {...register("limits.concurrent_interviews")} />
                </div>
            </div>
            <div className="ih-form-row">
                <div className="ih-form-group">
                    <label>Storage Limit (GB)</label>
                    <input type="number" step="0.1" {...register("limits.storage_limit_gb")} />
                </div>
                <div className="ih-form-group">
                    <label>Monthly API Requests</label>
                    <input type="number" {...register("limits.api_requests_per_month")} />
                </div>
            </div>
            <div className="ih-form-row">
                <div className="ih-form-group">
                    <label>AI Credits Allocation</label>
                    <input type="number" {...register("limits.ai_credits")} />
                </div>
                <div className="ih-form-group">
                    <label>Total Resume Uploads</label>
                    <input type="number" {...register("limits.resume_uploads")} />
                </div>
            </div>
        </SectionCard>
    );
}

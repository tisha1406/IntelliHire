import React from 'react';
import SectionCard from "../../../layout/SectionCard";

export default function SubscriptionTab({ register, errors }) {
    return (
        <SectionCard title="Subscription Configuration" description="Manage billing, plan tiers, and active status.">
            <div className="ih-form-row">
                <div className="ih-form-group">
                    <label>Plan Tier <span className="required">*</span></label>
                    <select {...register("subscription.plan")}>
                        <option value="Trial">Trial</option>
                        <option value="Basic">Basic</option>
                        <option value="Professional">Professional</option>
                        <option value="Enterprise">Enterprise</option>
                    </select>
                </div>
                <div className="ih-form-group">
                    <label>Status <span className="required">*</span></label>
                    <select {...register("subscription.status")}>
                        <option value="active">Active</option>
                        <option value="trial">Trialing</option>
                        <option value="suspended">Suspended</option>
                        <option value="cancelled">Cancelled</option>
                    </select>
                </div>
            </div>
            <div className="ih-form-row">
                <div className="ih-form-group">
                    <label>Billing Cycle</label>
                    <select {...register("subscription.billing_cycle")}>
                        <option value="monthly">Monthly</option>
                        <option value="annual">Annual</option>
                    </select>
                </div>
                <div className="ih-form-group">
                    <label>Expiry Date</label>
                    <input type="date" {...register("subscription.expiry_date")} />
                </div>
            </div>
            <div className="ih-form-row">
                <div className="ih-form-group">
                    <label>Seat Count (Recruiters & Hiring Managers)</label>
                    <input 
                        type="number" 
                        {...register("subscription.seat_count")} 
                        style={{ borderColor: errors.subscription?.seat_count ? 'var(--danger)' : '' }}
                    />
                    {errors.subscription?.seat_count && <span style={{ color: 'var(--danger)', fontSize: '12px' }}>{errors.subscription.seat_count.message}</span>}
                </div>
            </div>
        </SectionCard>
    );
}

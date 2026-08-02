import React from 'react';
import SectionCard from "../../../layout/SectionCard";

export default function GeneralTab({ register, errors }) {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <SectionCard title="Basic Information" description="Primary company details.">
                <div className="ih-form-row">
                    <div className="ih-form-group">
                        <label>Company Name <span className="required">*</span></label>
                        <input 
                            type="text" 
                            {...register("general.name")} 
                            placeholder="Acme Corp" 
                            style={{ borderColor: errors.general?.name ? 'var(--danger)' : '' }}
                        />
                        {errors.general?.name && <span style={{ color: 'var(--danger)', fontSize: '12px' }}>{errors.general.name.message}</span>}
                    </div>
                    <div className="ih-form-group">
                        <label>Admin Email <span className="required">*</span></label>
                        <input 
                            type="email" 
                            {...register("general.contact_email")} 
                            placeholder="admin@acme.com" 
                            style={{ borderColor: errors.general?.contact_email ? 'var(--danger)' : '' }}
                        />
                        {errors.general?.contact_email && <span style={{ color: 'var(--danger)', fontSize: '12px' }}>{errors.general.contact_email.message}</span>}
                    </div>
                </div>
                <div className="ih-form-row">
                    <div className="ih-form-group">
                        <label>Industry</label>
                        <input type="text" {...register("general.industry")} placeholder="Technology" />
                    </div>
                    <div className="ih-form-group">
                        <label>Company Size</label>
                        <select {...register("general.size")}>
                            <option value="">Select Size</option>
                            <option value="1-10">1-10 employees</option>
                            <option value="11-50">11-50 employees</option>
                            <option value="51-200">51-200 employees</option>
                            <option value="201-500">201-500 employees</option>
                            <option value="500+">500+ employees</option>
                        </select>
                    </div>
                </div>
                <div className="ih-form-row">
                    <div className="ih-form-group">
                        <label>Website URL</label>
                        <input 
                            type="url" 
                            {...register("general.website")} 
                            placeholder="https://acme.com" 
                            style={{ borderColor: errors.general?.website ? 'var(--danger)' : '' }}
                        />
                        {errors.general?.website && <span style={{ color: 'var(--danger)', fontSize: '12px' }}>{errors.general.website.message}</span>}
                    </div>
                    <div className="ih-form-group">
                        <label>Phone Number</label>
                        <input type="tel" {...register("general.phone")} placeholder="+1 555-0198" />
                    </div>
                </div>
            </SectionCard>

            <SectionCard title="Location & Branding">
                <div className="ih-form-row">
                    <div className="ih-form-group">
                        <label>Country</label>
                        <input type="text" {...register("general.country")} placeholder="United States" />
                    </div>
                    <div className="ih-form-group">
                        <label>Timezone</label>
                        <input type="text" {...register("general.timezone")} placeholder="UTC-8" />
                    </div>
                </div>
                <div className="ih-form-row">
                    <div className="ih-form-group">
                        <label>Currency</label>
                        <input type="text" {...register("general.currency")} placeholder="USD" />
                    </div>
                    <div className="ih-form-group">
                        <label>Tax ID / GST</label>
                        <input type="text" {...register("general.tax_id")} placeholder="Optional" />
                    </div>
                </div>
                <div className="ih-form-row">
                    <div className="ih-form-group">
                        <label>Company Address</label>
                        <textarea {...register("general.address")} placeholder="Full address" style={{ height: '80px', resize: 'none' }} />
                    </div>
                </div>
                <div className="ih-form-row">
                    <div className="ih-form-group">
                        <label>Logo URL</label>
                        <input type="text" {...register("general.logo_url")} placeholder="https://cdn.acme.com/logo.png" />
                    </div>
                </div>
            </SectionCard>
        </div>
    );
}

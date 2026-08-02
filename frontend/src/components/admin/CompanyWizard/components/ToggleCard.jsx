import React from 'react';
import { CheckCircle2 } from "lucide-react";

export default function ToggleCard({ label, description, checked, onChange, icon, badges }) {
    return (
        <div 
            onClick={onChange}
            style={{ 
                padding: '16px', 
                borderRadius: '8px', 
                border: `1px solid ${checked ? 'var(--primary)' : 'var(--border)'}`,
                background: checked ? 'rgba(79, 70, 229, 0.1)' : 'var(--bg-secondary)',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                transition: 'all 0.2s',
                height: '100%'
            }}
        >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <div style={{ color: checked ? 'var(--primary)' : 'var(--text-secondary)' }}>
                    {icon || <CheckCircle2 size={24} />}
                </div>
                <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 500, color: 'var(--text)', marginBottom: '4px' }}>{label}</div>
                    {description && <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{description}</div>}
                </div>
                <div>
                    <input 
                        type="checkbox" 
                        checked={checked} 
                        onChange={(e) => { e.stopPropagation(); onChange(); }} 
                        style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }}
                    />
                </div>
            </div>
            
            {/* Optional bottom section for enterprise tags (like Latency, Cost, etc.) */}
            {badges && badges.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: 'auto', paddingTop: '8px', borderTop: `1px solid ${checked ? 'rgba(79,70,229,0.2)' : 'var(--border)'}` }}>
                    {badges.map((badge, idx) => (
                        <span key={idx} style={{ 
                            fontSize: '11px', 
                            padding: '2px 8px', 
                            borderRadius: '12px', 
                            background: badge.color ? badge.color : 'var(--bg)', 
                            color: badge.textColor ? badge.textColor : 'var(--text-secondary)',
                            border: '1px solid var(--border)'
                        }}>
                            {badge.text}
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}

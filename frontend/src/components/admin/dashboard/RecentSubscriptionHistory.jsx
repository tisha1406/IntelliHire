import React from "react";
import { RefreshCcw, ArrowUpCircle, ArrowDownCircle, CheckCircle2 } from "lucide-react";

export default function RecentSubscriptionHistory({ data, loading }) {
    if (loading) {
        return (
            <div className="section-card skeleton" style={{ height: "300px" }}>
                <div className="skeleton-line w-1/3 mb-4"></div>
                <div className="skeleton-line"></div>
                <div className="skeleton-line"></div>
                <div className="skeleton-line"></div>
            </div>
        );
    }

    const getIcon = (type) => {
        switch (type) {
            case "upgrade": return <ArrowUpCircle size={16} />;
            case "downgrade": return <ArrowDownCircle size={16} />;
            case "renewal": return <RefreshCcw size={16} />;
            default: return <CheckCircle2 size={16} />;
        }
    };

    const getIconStyle = (type) => {
        switch (type) {
            case "upgrade": return { backgroundColor: 'var(--success-light)', color: 'var(--success)' };
            case "downgrade": return { backgroundColor: 'var(--warning-light)', color: 'var(--warning)' };
            case "renewal": return { backgroundColor: 'var(--primary-light)', color: 'var(--primary)' };
            default: return { backgroundColor: 'var(--text-light)', color: 'var(--text)' };
        }
    };

    return (
        <div className="section-card h-full flex flex-col">
            <div className="section-header">
                <h3>Recent Subscriptions</h3>
                <span className="badge badge-primary">{data?.length || 0} Recent</span>
            </div>
            
            <div className="activity-list flex-1 overflow-y-auto mt-4" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {(!data || data.length === 0) ? (
                    <div className="empty-state py-8 text-center" style={{ color: "var(--text-secondary)" }}>
                        No recent subscription history.
                    </div>
                ) : (
                    data.map((history) => (
                        <div key={history.id} className="activity-item" style={{ paddingBottom: '12px', borderBottom: '1px solid var(--border)', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                            <div className="activity-icon" style={{ padding: '8px', borderRadius: '50%', ...getIconStyle(history.change_type) }}>
                                {getIcon(history.change_type)}
                            </div>
                            <div className="activity-content" style={{ flex: 1 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                    <h4 style={{ margin: 0, fontSize: '14px', textTransform: 'capitalize' }}>{history.change_type}</h4>
                                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                        {new Date(history.created_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false })}
                                    </span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>
                                        Amount: ₹{(history.payment_required || 0).toLocaleString()}
                                    </p>
                                </div>
                                <div style={{ marginTop: '6px' }}>
                                    <span className={`status-badge status-${history.status === 'completed' ? 'active' : 'pending'}`}>
                                        {history.status}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

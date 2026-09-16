import React from "react";
import { IndianRupee } from "lucide-react";

export default function RecentPayments({ data, loading }) {
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

    return (
        <div className="section-card h-full flex flex-col">
            <div className="section-header">
                <h3>Recent Payments</h3>
                <span className="badge badge-primary">{data?.length || 0} Recent</span>
            </div>
            
            <div className="activity-list flex-1 overflow-y-auto mt-4" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {(!data || data.length === 0) ? (
                    <div className="empty-state py-8 text-center" style={{ color: "var(--text-secondary)" }}>
                        No recent payments found.
                    </div>
                ) : (
                    data.map((payment) => (
                        <div key={payment.id} className="activity-item" style={{ paddingBottom: '12px', borderBottom: '1px solid var(--border)', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                            <div className="activity-icon" style={{ backgroundColor: 'var(--success-light)', color: 'var(--success)', padding: '8px', borderRadius: '50%' }}>
                                <IndianRupee size={16} />
                            </div>
                            <div className="activity-content" style={{ flex: 1 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                    <h4 style={{ margin: 0, fontSize: '14px', textTransform: 'capitalize' }}>{payment.payment_type} Payment</h4>
                                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                        {new Date(payment.created_at).toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit", hour12: false })}
                                    </span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>Order: {payment.order_id}</p>
                                    <span style={{ fontWeight: 'bold', fontSize: '14px' }}>₹{(payment.amount || 0).toLocaleString()}</span>
                                </div>
                                <div style={{ marginTop: '6px' }}>
                                    <span className={`status-badge status-${payment.status === 'success' ? 'active' : payment.status === 'pending' ? 'pending' : 'expired'}`}>
                                        {payment.status}
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

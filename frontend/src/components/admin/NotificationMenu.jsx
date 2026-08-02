import { Bell, Check, CheckCheck, Trash2 } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useAdminNotifications } from "../../hooks/useAdminDashboard";

import "../../styles/admin/topbar.css";

export default function NotificationMenu() {
    const { data: notifications = [], isLoading } = useAdminNotifications();
    const [localRead, setLocalRead] = useState(new Set());
    const [localDeleted, setLocalDeleted] = useState(new Set());
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef(null);

    const activeNotifications = notifications.filter(n => !n.is_read && !localRead.has(n.id) && !localDeleted.has(n.id));
    const allVisible = notifications.filter(n => !localDeleted.has(n.id));
    const count = activeNotifications.length;

    useEffect(() => {
        function handleClickOutside(event) {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const markAllRead = () => {
        const unreadIds = activeNotifications.map(n => n.id);
        setLocalRead(prev => new Set([...prev, ...unreadIds]));
    };

    const markRead = (id) => {
        setLocalRead(prev => new Set([...prev, id]));
    };

    const deleteNotification = (id) => {
        setLocalDeleted(prev => new Set([...prev, id]));
    };
    return (
        <div className="notification-menu-container" ref={menuRef} style={{ position: 'relative' }}>
            <button
                className={`topbar-icon-btn notification-btn ${isOpen ? "active" : ""}`}
                aria-label="Notifications"
                onClick={() => setIsOpen(!isOpen)}
            >
                <Bell size={20} strokeWidth={2} />
                {count > 0 && (
                    <span className="notification-badge">
                        {count}
                    </span>
                )}
            </button>

            {isOpen && (
                <div className="dropdown-menu" style={{ width: '300px' }}>
                    <div className="dropdown-header" style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                        <strong>Notifications</strong>
                        {count > 0 && (
                            <button 
                                onClick={markAllRead}
                                style={{ fontSize: '11px', color: 'var(--primary)', fontWeight: '500' }}
                            >
                                Mark all read
                            </button>
                        )}
                    </div>
                    <div className="dropdown-divider"></div>
                    
                    {allVisible.length > 0 ? (
                        <>
                            {allVisible.map(notification => (
                                <div key={notification.id} className="dropdown-item" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <button 
                                        style={{ display: 'flex', flexDirection: 'column', gap: '4px', textAlign: 'left', flex: 1, background: 'none', border: 'none', cursor: 'pointer', opacity: localRead.has(notification.id) || notification.is_read ? 0.6 : 1 }}
                                        onClick={() => markRead(notification.id)}
                                    >
                                        <span style={{ fontWeight: '500' }}>{notification.title}</span>
                                        <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{notification.message}</span>
                                    </button>
                                    <button 
                                        className="topbar-icon-btn" 
                                        style={{ padding: '4px' }} 
                                        onClick={() => deleteNotification(notification.id)}
                                        title="Delete"
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            ))}
                        </>
                    ) : (
                        <div style={{ padding: '24px 16px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                            <CheckCheck size={24} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                            <p style={{ fontSize: '13px' }}>You're all caught up!</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
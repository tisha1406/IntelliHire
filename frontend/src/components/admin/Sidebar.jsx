import {
    LayoutDashboard,
    Building2,
    Users,
    UserCog,
    CalendarDays,
    ClipboardCheck,
    Sparkles,
    FileSearch,
    BrainCircuit,
    FileBarChart2,
    BarChart3,
    TrendingUp,
    Activity,
    Shield,
    Settings,
    HeartPulse,
    ChevronLeft,
    ChevronRight,
    ChevronDown,
    ChevronUp,
    LogOut
} from "lucide-react";
import { useState, useEffect } from "react";

import SidebarItem from "./SidebarItem";
import useSidebar from "../../hooks/useSidebar";
import { useAuthContext } from "../../context/AuthContext";
import { MonitoringAPI } from "../../api/monitoring";

import "../../styles/admin/sidebar.css";

export default function Sidebar() {
    const { logout } = useAuthContext();
    const {
        collapsed,
        toggleSidebar
    } = useSidebar();
    
    const [storageData, setStorageData] = useState(null);

    useEffect(() => {
        const fetchStorage = async () => {
            try {
                const res = await MonitoringAPI.getStorageUsage();
                if (res && res.platform_storage) {
                    setStorageData(res.platform_storage);
                }
            } catch (err) {
                console.error("Failed to fetch storage stats", err);
            }
        };
        fetchStorage();
    }, []);

    const sections = [
        {
            title: "PLATFORM MANAGEMENT",
            id: "platform-mgmt",
            items: [
                { to: "/admin/dashboard", icon: LayoutDashboard, label: "Dashboard" },
                { to: "/admin/users", icon: Users, label: "Users" }
            ]
        },
        {
            title: "RECRUITMENT",
            id: "recruitment",
            items: [
                { to: "/admin/companies", icon: Building2, label: "Companies" },
                { to: "/admin/recruiters", icon: UserCog, label: "Recruiters" },
                { to: "/admin/candidates", icon: Users, label: "Candidates" },
                { to: "/admin/interviews", icon: ClipboardCheck, label: "Interviews" },
                { to: "/admin/interview-calendar", icon: CalendarDays, label: "Interview Calendar" }
            ]
        },
        {
            title: "AI CENTER",
            id: "ai-center",
            items: [
                { to: "/admin/ai-insights", icon: Sparkles, label: "AI Insights" },
                { to: "/admin/resume-screening", icon: FileSearch, label: "Resume Screening" },
                { to: "/admin/interview-analysis", icon: BrainCircuit, label: "Interview Analysis" },
                { to: "/admin/ai-reports", icon: FileBarChart2, label: "AI Reports" }
            ]
        },
        {
            title: "ANALYTICS",
            id: "analytics",
            items: [
                { to: "/admin/reports", icon: BarChart3, label: "Reports" },
                { to: "/admin/hiring-analytics", icon: TrendingUp, label: "Hiring Analytics" },
                { to: "/admin/performance", icon: Activity, label: "Performance" }
            ]
        },
        {
            title: "SECURITY",
            id: "security",
            items: [
                { to: "/admin/security-logs", icon: Shield, label: "Security Logs" },
                { to: "/admin/system-health", icon: HeartPulse, label: "System Health" }
            ]
        },
        {
            title: "SETTINGS",
            id: "settings",
            items: [
                { to: "/admin/platform-settings", icon: Settings, label: "Platform Settings" }
            ]
        }
    ];

    const [expandedGroups, setExpandedGroups] = useState(
        sections.reduce((acc, section) => ({ ...acc, [section.id]: true }), {})
    );

    const toggleGroup = (id) => {
        if (collapsed) return; // Cannot toggle groups while sidebar is fully collapsed
        setExpandedGroups(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const renderStorage = () => {
        if (collapsed || !storageData) return null;
        
        const { total_used_gb, total_capacity_gb } = storageData;
        const percentage = total_capacity_gb > 0 ? Math.min((total_used_gb / total_capacity_gb) * 100, 100) : 0;
        
        return (
            <div className="sidebar-storage">
                <div className="storage-header">
                    <span>Storage</span>
                    <strong>{Math.round(percentage)}%</strong>
                </div>
                <div className="storage-bar">
                    <div className="storage-progress" style={{ width: `${percentage}%` }}/>
                </div>
                <small>{total_used_gb} GB of {total_capacity_gb} GB Used</small>
            </div>
        );
    };

    return (
        <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
            <div className="sidebar-header">
                <div className="brand">
                    <div className="brand-logo">🤖</div>
                    {!collapsed && (
                        <div className="brand-text">
                            <h2>IntelliHire</h2>
                            <span>AI Recruitment Platform</span>
                        </div>
                    )}
                </div>
                <button
                    className="collapse-btn"
                    onClick={toggleSidebar}
                >
                    {collapsed ? <ChevronRight size={18}/> : <ChevronLeft size={18}/>}
                </button>
            </div>

            <div className="sidebar-scroll">
                {sections.map(section => {
                    const isExpanded = expandedGroups[section.id];
                    return (
                        <div className="sidebar-group" key={section.id}>
                            {!collapsed ? (
                                <div className="sidebar-group-header" onClick={() => toggleGroup(section.id)}>
                                    <span className="sidebar-group-title">{section.title}</span>
                                    {isExpanded ? <ChevronUp size={14}/> : <ChevronDown size={14}/>}
                                </div>
                            ) : null}
                            
                            {(isExpanded || collapsed) && (
                                <div className="sidebar-group-items">
                                    {section.items.map(item => (
                                        <SidebarItem
                                            key={item.label}
                                            to={item.to}
                                            icon={item.icon}
                                            label={item.label}
                                            collapsed={collapsed}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {renderStorage()}

            <div className="sidebar-footer">
                <div className="user-card">
                    <div className="user-avatar">A</div>
                    {!collapsed && (
                        <div className="user-details">
                            <strong>Administrator</strong>
                            <span>● Online</span>
                        </div>
                    )}
                </div>
                <button className="logout-btn" onClick={logout}>
                    <LogOut size={18}/>
                    {!collapsed && <span>Logout</span>}
                </button>
            </div>
        </aside>
    );
}
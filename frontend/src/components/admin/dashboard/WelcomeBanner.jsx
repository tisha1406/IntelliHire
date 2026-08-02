import {
    CalendarDays,
    Building2,
    Users,
    BriefcaseBusiness,
    BrainCircuit
} from "lucide-react";

import "../../../styles/admin/dashboard.css";

import PageHeader from "../../layout/PageHeader";

export default function WelcomeBanner({ welcome = {}, statistics = {}, loading }) {

    const hour = new Date().getHours();

    const greeting =
        hour < 12
            ? "Good Morning"
            : hour < 17
            ? "Good Afternoon"
            : "Good Evening";

    const today = new Date().toLocaleDateString(
        "en-US",
        {
            weekday: "long",
            month: "long",
            day: "numeric"
        }
    );

    const titleContent = loading ? (
        <div className="skeleton" style={{ width: 250, height: 40, marginBottom: 8 }} />
    ) : (
        <>
            {greeting},
            <br />
            {welcome.name || "Administrator"} 👋
            <div style={{ fontSize: '14px', fontWeight: 'normal', color: 'var(--text-secondary)', marginTop: '8px' }}>
                {welcome.role || "SUPER_ADMIN"} • Last Login: {welcome.last_login ? new Date(welcome.last_login).toLocaleString() : "Recently"}
            </div>
        </>
    );

    const rightContent = (
        <>
            <div className="today-card">
                <CalendarDays size={18}/>
                <span>{today}</span>
            </div>
            <div className="hero-stats">
                <div className="hero-stat">
                    <Building2 size={18}/>
                    <div>
                        <strong>{loading ? "..." : (statistics.totalCompanies || 0).toLocaleString()}</strong>
                        <span>Companies</span>
                    </div>
                </div>
                <div className="hero-stat">
                    <Users size={18}/>
                    <div>
                        <strong>{loading ? "..." : (statistics.totalCandidates || 0).toLocaleString()}</strong>
                        <span>Candidates</span>
                    </div>
                </div>
                <div className="hero-stat">
                    <BriefcaseBusiness size={18}/>
                    <div>
                        <strong>{loading ? "..." : (statistics.totalInterviews || 0).toLocaleString()}</strong>
                        <span>Interviews</span>
                    </div>
                </div>
                <div className="hero-stat">
                    <BrainCircuit size={18}/>
                    <div>
                        <strong>{loading ? "..." : statistics.aiAccuracy || "0%"}</strong>
                        <span>AI Accuracy</span>
                    </div>
                </div>
            </div>
        </>
    );

    return (
        <PageHeader 
            title={titleContent}
            description="Manage candidates, companies, interviews and AI-powered hiring decisions from one intelligent platform."
            rightContent={rightContent}
        />
    );
}
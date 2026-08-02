import {
    Building2,
    FileText,
    Settings,
    Sparkles,
    ArrowRight
} from "lucide-react";

import "../../../styles/admin/dashboard.css";
import { useNavigate } from "react-router-dom";

const actions = [
    {
        title: "Add Company",
        description: "Register a new hiring organization",
        icon: <Building2 size={22}/>,
        linkTo: "/admin/companies/new"
    },
    {
        title: "Generate Report",
        description: "Create AI-powered hiring analytics",
        icon: <FileText size={22}/>,
        linkTo: "/admin/reports"
    },
    {
        title: "Platform Settings",
        description: "Manage system configuration",
        icon: <Settings size={22}/>,
        linkTo: "/admin/platform-settings"
    }
];

export default function QuickActions(){
    const navigate = useNavigate();
    return(

        <section className="quick-actions-section">

            <div className="quick-actions-header">

                <div>

                    <h2>

                        Quick Actions

                    </h2>

                    <p>

                        Frequently used administrative tasks

                    </p>

                </div>

                <div className="quick-ai-badge">

                    <Sparkles size={15}/>

                    AI Assisted

                </div>

            </div>

            <div className="quick-actions-grid">

                {

                    actions.map(action=>(

                        <button
                            key={action.title}
                            className={`action-card ${action.primary ? "primary" : ""}`}
                            onClick={() => navigate(action.linkTo)}
                        >

                            <div className="action-icon">

                                {action.icon}

                            </div>

                            <div className="action-content">

                                <h3>

                                    {action.title}

                                </h3>

                                <p>

                                    {action.description}

                                </p>

                            </div>

                            <ArrowRight
                                size={18}
                                className="action-arrow"
                            />

                        </button>

                    ))

                }

            </div>

        </section>

    );

}
import {
    UserPlus,
    FileSearch,
    CalendarClock,
    BadgeCheck,
    ClipboardCheck,
    CalendarDays,
    ThumbsUp,
    ThumbsDown
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import Card from "../../common/Card";

import "../../../styles/admin/dashboard.css";

export default function OverviewChart({ pipeline = {}, loading }) {
    const navigate = useNavigate();

    const pipelineStages = [
        {
            icon: <UserPlus size={18}/>,
            title: "Applications",
            value: pipeline.applications ?? 0,
            color: "blue"
        },
        {
            icon: <FileSearch size={18}/>,
            title: "Resume Screening",
            value: pipeline.resume_screening ?? 0,
            color: "purple"
        },
        {
            icon: <ClipboardCheck size={18}/>,
            title: "Shortlisted",
            value: pipeline.shortlisted ?? 0,
            color: "purple"
        },
        {
            icon: <CalendarDays size={18}/>,
            title: "Interview Scheduled",
            value: pipeline.interview_scheduled ?? 0,
            color: "orange"
        },
        {
            icon: <CalendarClock size={18}/>,
            title: "Interview Completed",
            value: pipeline.interview_completed ?? 0,
            color: "orange"
        },
        {
            icon: <ThumbsUp size={18}/>,
            title: "Selected",
            value: pipeline.selected ?? 0,
            color: "green"
        },
        {
            icon: <ThumbsDown size={18}/>,
            title: "Rejected",
            value: pipeline.rejected ?? 0,
            color: "red"
        },
        {
            icon: <BadgeCheck size={18}/>,
            title: "Hired",
            value: pipeline.hired ?? 0,
            color: "green"
        }
    ];

    return (
        <Card className="pipeline-card">
            <div className="pipeline-header">
                <div>
                    <h3>Recruitment Pipeline</h3>
                    <p>Current hiring funnel across all companies</p>
                </div>
                <button className="pipeline-button" onClick={() => navigate("/admin/hiring-analytics") }>
                    View Analytics
                </button>
            </div>

            <div className="pipeline-grid">
                {pipelineStages.map((stage) => (
                    <div key={stage.title} className={`pipeline-stage ${stage.color}`} title={`${stage.title}: ${stage.value}`}>
                        <div className="pipeline-icon">{stage.icon}</div>
                        <span>{stage.title}</span>
                        <h2>{loading ? "..." : stage.value.toLocaleString()}</h2>
                    </div>
                ))}
            </div>

            <div className="pipeline-progress">
                <div className="progress-step active" />
                <div className="progress-line" />
                <div className="progress-step active" />
                <div className="progress-line" />
                <div className="progress-step active" />
                <div className="progress-line" />
                <div className="progress-step" />
            </div>
        </Card>
    );
}

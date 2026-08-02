import { Building2, Clock3 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Card from "../../common/Card";
import "../../../styles/admin/dashboard.css";

export default function RecentActivity({ data, loading }) {
    const navigate = useNavigate();
    if (loading) {
        return (
            <Card className="activity-card">
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                    Loading activities...
                </div>
            </Card>
        );
    }

    const activities = (data || []).map(item => ({
        id: item.id,
        icon: <Building2 size={18}/>,
        title: item.title || item.type || "Activity",
        description: item.description || "",
        time: item.timestamp ? new Date(item.timestamp).toLocaleString() : "Recently",
        color: "blue"
    }));

    return (
        <Card className="activity-card">
            <div className="activity-header">
                <div>
                    <h3>Recent Activity</h3>
                    <p>Latest platform events and actions</p>
                </div>
            </div>
            <div className="activity-timeline">
                {activities.length > 0 ? activities.map((item, index) => (
                    <div 
                        key={index} 
                        className="activity-item" 
                        style={{ cursor: item.id ? 'pointer' : 'default' }}
                        onClick={() => {
                            if(item.id) navigate(`/admin/companies/${item.id}`);
                        }}
                    >
                        <div className={`activity-icon ${item.color}`}>
                            {item.icon}
                        </div>
                        <div className="activity-content">
                            <h4>{item.title}</h4>
                            <p>{item.description}</p>
                        </div>
                        <div className="activity-time">
                            <Clock3 size={14}/>
                            <span>{item.time}</span>
                        </div>
                    </div>
                )) : (
                    <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                        No recent activities.
                    </div>
                )}
            </div>
        </Card>
    );
}
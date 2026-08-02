export default function ActivityTimeline({ activities }) {
    return (
        <div className="activity-timeline">
            {activities.map((activity, index) => (
                <div key={activity.id || index} className="activity-item">
                    <div className={`activity-icon ${activity.color || 'blue'}`}>
                        {activity.icon}
                    </div>
                    <div className="activity-content">
                        <h4>{activity.title}</h4>
                        <p>{activity.description}</p>
                    </div>
                    <div className="activity-time">
                        {activity.time}
                    </div>
                </div>
            ))}
        </div>
    );
}

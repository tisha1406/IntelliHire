import React from "react";

export default function Timeline({
    items = [],
    className = "",
    ...props
}) {
    return (
        <div className={`vertical-timeline ${className}`} {...props}>
            {items.map((item, idx) => (
                <div key={idx} className="timeline-node-item">
                    <div className="timeline-badge-column">
                        <div className="timeline-bullet-point" />
                        {idx !== items.length - 1 && <div className="timeline-connector-line" />}
                    </div>
                    <div className="timeline-content-card">
                        <div className="timeline-header-row">
                            <h5 className="timeline-node-title">{item.title || item.stage}</h5>
                            <span className="timeline-node-date">{item.date}</span>
                        </div>
                        {item.description && <p className="timeline-node-desc">{item.description}</p>}
                    </div>
                </div>
            ))}
        </div>
    );
}

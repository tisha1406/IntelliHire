import React from "react";
import { FaInbox } from "react-icons/fa";
import Button from "./Button";

export default function EmptyState({
    title = "No data available",
    description = "There are no records matching your query.",
    icon = <FaInbox />,

    // Existing prop (kept for backward compatibility)
    action = null,

    // New props
    primaryAction,
    secondaryAction,

    className = "",
    ...props
}) {

    return (

        <div
            className={`custom-empty-state ${className}`}
            {...props}
        >

            <div className="empty-state-icon-circle">

                {icon}

            </div>

            <h4 className="empty-state-title">

                {title}

            </h4>

            <p className="empty-state-desc">

                {description}

            </p>

            {action && (

                <div className="empty-state-action-slot">

                    {action}

                </div>

            )}

            {(primaryAction || secondaryAction) && (

                <div className="empty-state-actions">

                    {secondaryAction && (

                        <Button
                            variant="outline"
                            onClick={secondaryAction.onClick}
                        >

                            {secondaryAction.label}

                        </Button>

                    )}

                    {primaryAction && (

                        <Button
                            variant="primary"
                            onClick={primaryAction.onClick}
                        >

                            {primaryAction.label}

                        </Button>

                    )}

                </div>

            )}

        </div>

    );

}
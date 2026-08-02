import React from "react";

export default function LoadingSkeleton({
    height = "20px",
    width = "100%",
    borderRadius = "8px",
    className = "",
    ...props
}) {
    return (
        <div
            className={`loading-skeleton-pulse ${className}`}
            style={{
                height,
                width,
                borderRadius,
            }}
            {...props}
        />
    );
}

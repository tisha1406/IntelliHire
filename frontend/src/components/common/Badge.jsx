import "./../../styles/admin/badge.css";

export default function Badge({
    children,
    variant = "primary",
    className = "",
    ...props
}) {
    return (
        <span
            className={`ih-badge ih-badge-${variant} ${className}`}
            {...props}
        >
            {children}
        </span>
    );
}
import "./../../styles/admin/badge.css";

export default function Badge({
<<<<<<< HEAD

    children,

    variant = "primary"

}) {

    return (

        <span className={`ih-badge ${variant}`}>

            {children}

        </span>

    );

=======
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
>>>>>>> origin/main
}
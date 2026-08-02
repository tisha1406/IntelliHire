import "./../../styles/admin/toggle.css";

export default function Toggle({
    checked = false,
    onChange,
    disabled = false,
    label,
    description,
    className = "",
    id,
    ...props
}) {
    const toggleId =
        id ||
        `toggle-${Math.random().toString(36).slice(2, 10)}`;

    return (
        <label
            htmlFor={toggleId}
            className={`ih-toggle-wrapper ${disabled ? "disabled" : ""} ${className}`}
        >
            <div className="ih-toggle-text">
                {label && (
                    <span className="ih-toggle-label">
                        {label}
                    </span>
                )}

                {description && (
                    <span className="ih-toggle-description">
                        {description}
                    </span>
                )}
            </div>

            <div className="ih-toggle-control">
                <input
                    id={toggleId}
                    type="checkbox"
                    className="ih-toggle-input"
                    checked={checked}
                    disabled={disabled}
                    onChange={(e) =>
                        !disabled &&
                        onChange?.(e.target.checked)
                    }
                    {...props}
                />

                <div className="ih-toggle-slider"></div>
            </div>
        </label>
    );
}
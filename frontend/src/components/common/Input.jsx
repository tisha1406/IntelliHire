import React from "react";

export default function Input({
    label,
    error,
    type = "text",
    placeholder = "",
    value,
    onChange,
    icon = null,
    className = "",
    id,
    ...props
}) {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

    return (
        <div className={`custom-input-group ${error ? "has-error" : ""} ${className}`}>
            {label && <label htmlFor={inputId} className="input-label">{label}</label>}
            <div className="input-wrapper">
                {icon && <span className="input-icon">{icon}</span>}
                <input
                    id={inputId}
                    type={type}
                    placeholder={placeholder}
                    value={value}
                    onChange={onChange}
                    className={`custom-input ${icon ? "has-icon" : ""}`}
                    {...props}
                />
            </div>
            {error && <span className="input-error-msg">{error}</span>}
        </div>
    );
}

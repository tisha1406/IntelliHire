import React from "react";

export default function Select({
    label,
    error,
    options = [],
    value,
    onChange,
    className = "",
    id,
    placeholder = "Select option...",
    ...props
}) {
    const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;

    return (
        <div className={`custom-select-group ${error ? "has-error" : ""} ${className}`}>
            {label && <label htmlFor={selectId} className="select-label">{label}</label>}
            <div className="select-wrapper">
                <select
                    id={selectId}
                    value={value}
                    onChange={onChange}
                    className="custom-select"
                    {...props}
                >
                    {placeholder && <option value="" disabled>{placeholder}</option>}
                    {options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                            {opt.label}
                        </option>
                    ))}
                </select>
            </div>
            {error && <span className="select-error-msg">{error}</span>}
        </div>
    );
}

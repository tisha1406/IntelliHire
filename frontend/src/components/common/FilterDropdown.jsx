import React from "react";
import { FaFilter } from "react-icons/fa";

export default function FilterDropdown({
    label,
    options = [],
    selected,
    onChange,
    className = "",
    ...props
}) {
    return (
        <div className={`filter-dropdown-container ${className}`} {...props}>
            {label && <span className="filter-label"><FaFilter className="filter-icon" /> {label}:</span>}
            <select
                value={selected}
                onChange={(e) => onChange(e.target.value)}
                className="filter-select-element"
            >
                <option value="">All</option>
                {options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                        {opt.label}
                    </option>
                ))}
            </select>
        </div>
    );
}

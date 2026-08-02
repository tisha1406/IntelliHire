import { Search, X } from "lucide-react";
import "./../../styles/admin/searchbar.css";

export default function SearchBar({
    value = "",
    onChange,
    placeholder = "Search...",
    onClear,
    className = "",
    ...props
}) {
    return (
        <div
            className={`search-bar-wrapper ${className}`}
            {...props}
        >
            <Search
                className="search-bar-icon"
                size={16}
            />

            <input
                type="text"
                className="search-bar-input"
                placeholder={placeholder}
                value={value}
                onChange={(e) => onChange(e.target.value)}
            />

            {value && onClear && (
                <button
                    type="button"
                    className="search-bar-clear"
                    onClick={onClear}
                    aria-label="Clear search"
                >
                    <X size={14} />
                </button>
            )}
        </div>
    );
}
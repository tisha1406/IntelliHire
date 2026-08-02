import React from "react";
import { FaChevronLeft, FaChevronRight } from "react-icons/fa";

export default function Pagination({
    currentPage,
    totalPages,
    onPageChange,
    className = "",
    ...props
}) {
    if (totalPages <= 1) return null;

    const pages = Array.from({ length: totalPages }).map((_, i) => i + 1);

    return (
        <div className={`custom-pagination ${className}`} {...props}>
            <button
                className="pagination-arrow-btn"
                onClick={() => onPageChange(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
            >
                <FaChevronLeft />
            </button>
            <div className="pagination-numbers">
                {pages.map((p) => (
                    <button
                        key={p}
                        className={`pagination-num-btn ${currentPage === p ? "is-active" : ""}`}
                        onClick={() => onPageChange(p)}
                    >
                        {p}
                    </button>
                ))}
            </div>
            <button
                className="pagination-arrow-btn"
                onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
            >
                <FaChevronRight />
            </button>
        </div>
    );
}

import React from "react";
import { Link } from "react-router-dom";
import { FaChevronRight, FaHome } from "react-icons/fa";

export default function PageHeader({
    title,
    subtitle,
    breadcrumbs = [],
    actions = null,
    className = "",
    ...props
}) {
    return (
        <div className={`page-header-container ${className}`} {...props}>
            <div className="page-header-left-col">
                {/* Breadcrumbs */}
                {breadcrumbs.length > 0 && (
                    <nav className="header-breadcrumbs">
                        <Link to="/company/dashboard" className="breadcrumb-home">
                            <FaHome />
                        </Link>
                        {breadcrumbs.map((crumb, idx) => (
                            <React.Fragment key={idx}>
                                <FaChevronRight className="breadcrumb-separator" />
                                {crumb.path ? (
                                    <Link to={crumb.path} className="breadcrumb-link">
                                        {crumb.label}
                                    </Link>
                                ) : (
                                    <span className="breadcrumb-current">{crumb.label}</span>
                                )}
                            </React.Fragment>
                        ))}
                    </nav>
                )}

                <div className="header-headings">
                    <h1 className="header-title">{title}</h1>
                    {subtitle && <p className="header-subtitle">{subtitle}</p>}
                </div>
            </div>

            {actions && <div className="page-header-actions-col">{actions}</div>}
        </div>
    );
}

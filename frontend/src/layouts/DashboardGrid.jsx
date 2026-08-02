import "./DashboardGrid.css";

export default function DashboardGrid({ children, className = "" }) {
    return (
        <div className={`dashboard-layout-grid ${className}`}>
            {children}
        </div>
    );
}

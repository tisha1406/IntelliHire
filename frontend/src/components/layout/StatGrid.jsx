import "./StatGrid.css";

export default function StatGrid({ children, columns = 4, className = "" }) {
    return (
        <div 
            className={`layout-stat-grid col-${columns} ${className}`}
        >
            {children}
        </div>
    );
}

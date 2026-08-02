import "./ContentGrid.css";

export default function ContentGrid({ left, right, children, className = "" }) {
    // If left/right props are used, render the explicit two-column layout.
    // Otherwise, render children directly in a grid — expecting 2 child divs.
    if (left !== undefined || right !== undefined) {
        return (
            <div className={`layout-content-grid ${className}`}>
                <div className="layout-content-left">{left}</div>
                {right && <div className="layout-content-right">{right}</div>}
            </div>
        );
    }
    // Children pattern — children render directly inside the grid container.
    return (
        <div className={`layout-content-grid ${className}`}>
            {children}
        </div>
    );
}

import "./PageHeader.css";

export default function PageHeader({ 
    title, 
    description, 
    rightContent = null,
    className = "" 
}) {
    return (
        <header className={`page-header-wrapper ${className}`}>
            <div className="page-header-left">
                {title && <h1>{title}</h1>}
                {description && <p>{description}</p>}
            </div>
            {rightContent && (
                <div className="page-header-right">
                    {rightContent}
                </div>
            )}
        </header>
    );
}

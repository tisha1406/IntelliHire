import "./SectionCard.css";

export default function SectionCard({ children, className = "" }) {
    return (
        <section className={`layout-section-card ${className}`}>
            {children}
        </section>
    );
}

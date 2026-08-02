import React from "react";
import { FaCheck } from "react-icons/fa";

export default function Stepper({
    steps = [],
    currentStep, // 0-indexed
    className = "",
    ...props
}) {
    return (
        <div className={`custom-stepper-container ${className}`} {...props}>
            {steps.map((step, idx) => {
                const isCompleted = idx < currentStep;
                const isActive = idx === currentStep;

                return (
                    <div key={idx} className="stepper-step-item">
                        <div className={`stepper-index-circle ${isCompleted ? "is-completed" : ""} ${isActive ? "is-active" : ""}`}>
                            {isCompleted ? <FaCheck className="step-check-icon" /> : <span>{idx + 1}</span>}
                        </div>
                        <div className="stepper-step-content">
                            <span className={`stepper-step-title ${isActive ? "is-active" : ""}`}>{step}</span>
                        </div>
                        {idx !== steps.length - 1 && (
                            <div className={`stepper-join-line ${idx < currentStep ? "line-completed" : ""}`} />
                        )}
                    </div>
                );
            })}
        </div>
    );
}

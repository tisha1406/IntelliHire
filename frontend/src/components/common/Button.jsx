import { motion } from "framer-motion";
import { FaSpinner } from "react-icons/fa";

import "./../../styles/admin/button.css";

export default function Button({
    children,
    type = "button",
    variant = "primary",
    size = "md",
    disabled = false,

    // Existing API (used throughout your project)
    isLoading = false,

    // Backward compatibility with Selin's code
    loading = false,

    onClick,

    iconLeft = null,
    iconRight = null,

    className = "",

    ...props
}) {

    const buttonLoading = isLoading || loading;

    return (
        <motion.button
            type={type}
            disabled={disabled || buttonLoading}
            onClick={disabled || buttonLoading ? undefined : onClick}
            whileHover={
                disabled || buttonLoading
                    ? {}
                    : { scale: 1.02, y: -2 }
            }
            whileTap={
                disabled || buttonLoading
                    ? {}
                    : { scale: 0.98 }
            }
            className={`
                ih-btn
                ih-btn-${variant}
                ih-btn-${size}
                ${buttonLoading ? "is-loading" : ""}
                ${className}
            `}
            {...props}
        >
            {buttonLoading ? (
                <FaSpinner className="btn-spinner animate-spin" />
            ) : (
                <>
                    {iconLeft && (
                        <span className="btn-icon-left">
                            {iconLeft}
                        </span>
                    )}

                    <span className="btn-text">
                        {children}
                    </span>

                    {iconRight && (
                        <span className="btn-icon-right">
                            {iconRight}
                        </span>
                    )}
                </>
            )}
        </motion.button>
    );
}
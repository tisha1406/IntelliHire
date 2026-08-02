import { motion } from "framer-motion";

import "../../styles/company/components.css";

function CompanyStatsCard({
    title,
    value,
    change,
    icon,
    color,
}) {

    return (

        <motion.div
            className="stats-card"
            whileHover={{
                y: -6,
                scale: 1.02,
            }}
            transition={{
                duration: .25,
            }}
        >

            <div
                className="stats-icon"
                style={{
                    background: color,
                }}
            >

                {icon}

            </div>

            <div className="stats-content">

                <span>

                    {title}

                </span>

                <h2>

                    {value}

                </h2>

                <p>

                    {change}

                </p>

            </div>

        </motion.div>

    );

}

export default CompanyStatsCard;
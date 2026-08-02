import {
    TrendingUp,
    TrendingDown
} from "lucide-react";

import Card from "../../common/Card";
import { useNavigate } from "react-router-dom";

import "../../../styles/admin/dashboard.css";

export default function KpiCard({

    title,

    value,

    change,

    icon,

    positive = true,
    progress = 75,
    linkTo,
    loading
}) {
    const navigate = useNavigate();

    const handleClick = () => {
        if (linkTo && !loading) {
            navigate(linkTo);
        }
    };

    return (
        <Card className={`kpi-card ${linkTo ? "clickable" : ""}`} onClick={handleClick}>

            <div className="kpi-header">

                <div className="kpi-icon-wrapper">

                    {icon}

                </div>

                <div
                    className={`kpi-trend ${
                        positive
                            ? "positive"
                            : "negative"
                    }`}
                >

                    {

                        positive

                        ? <TrendingUp size={14}/>

                        : <TrendingDown size={14}/>

                    }

                    {change}

                </div>

            </div>

            <div className="kpi-body">
                <span className="kpi-title">{title}</span>
                <h2 className="kpi-value">
                    {loading ? <div className="skeleton" style={{ width: 60, height: 32 }} /> : value}
                </h2>
            </div>

            <div className="kpi-progress">

                <div
                    className="kpi-progress-fill"
                    style={{
                        width: `${progress}%`
                    }}
                />
            </div>

        </Card>

    );

}
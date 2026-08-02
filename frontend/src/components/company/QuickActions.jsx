import {
    FaPlus,
    FaUserPlus,
    FaFileExport,
} from "react-icons/fa";

import { useNavigate } from "react-router-dom";

import "../../styles/company/QuickActions.css";

function QuickActions(){

    const navigate = useNavigate();

    return(

        <section className="quick-actions">

            <h2>Quick Actions</h2>

            <div className="actions-grid">

                <div
                    className="action-card"
                    onClick={() => navigate("/company/campaigns/new")}
                >

                    <div
                        className="action-icon"
                        style={{
                            background:
                                "linear-gradient(135deg,#2563EB,#3B82F6)"
                        }}
                    >
                        <FaPlus />
                    </div>

                    <h3>New Campaign</h3>

                    <p>Create a new hiring campaign</p>

                </div>

                <div
                    className="action-card"
                    onClick={() => navigate("/company/candidates")}
                >

                    <div
                        className="action-icon"
                        style={{
                            background:
                                "linear-gradient(135deg,#10B981,#22C55E)"
                        }}
                    >
                        <FaUserPlus />
                    </div>

                    <h3>Invite Candidate</h3>

                    <p>Invite applicants by email</p>

                </div>

                <div
                    className="action-card"
                    onClick={() => navigate("/company/exports")}
                >

                    <div
                        className="action-icon"
                        style={{
                            background:
                                "linear-gradient(135deg,#F59E0B,#FBBF24)"
                        }}
                    >
                        <FaFileExport />
                    </div>

                    <h3>Export Reports</h3>

                    <p>Download hiring reports</p>

                </div>

            </div>

        </section>

    );

}

export default QuickActions;
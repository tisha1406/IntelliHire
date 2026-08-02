import {
    FaArrowRight,
    FaBriefcase,
    FaRobot,
    FaUserCheck,
    FaEnvelope,
    FaFileExport,
} from "react-icons/fa";

import { Link } from "react-router-dom";

import {
    activityTimeline,
} from "../../data/company/dashboardMockData";

import "../../styles/company/ActivityTimeline.css";

function ActivityTimeline() {

    const iconMap = {

        campaign: <FaBriefcase />,

        interview: <FaRobot />,

        candidate: <FaUserCheck />,

        invite: <FaEnvelope />,

        report: <FaFileExport />,

    };

    return (

        <section className="activity-section">

            <div className="activity-header">

                <h2>

                    Activity Timeline

                </h2>

                <Link
                    to="/company/activity"
                    className="activity-view-all"
                >

                    View All

                    <FaArrowRight />

                </Link>

            </div>

            <div className="timeline">

                {

                    activityTimeline.map((item) => (

                        <div
                            key={item.id}
                            className="timeline-item"
                        >

                            <div className="timeline-icon">

                                {

                                    iconMap[item.type]

                                }

                            </div>

                            <div className="timeline-content">

                                <h3>

                                    {item.title}

                                </h3>

                                <p>

                                    {item.description}

                                </p>

                                <span>

                                    {item.time}

                                </span>

                            </div>

                        </div>

                    ))

                }

            </div>

        </section>

    );

}

export default ActivityTimeline;
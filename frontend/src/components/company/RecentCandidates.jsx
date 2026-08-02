import { FaArrowRight, FaEye } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";

import {
    recentCandidates,
} from "../../data/company/dashboardMockData";

import "../../styles/company/RecentCandidates.css";

function RecentCandidates(){

    const navigate = useNavigate();

    return(

        <section className="recent-candidates">

            <div className="candidate-section-header">

                <h2 className="candidate-section-title">

                    Recent Candidates

                </h2>

            </div>

            <div className="candidate-list">

                {

                    recentCandidates

                    .slice(0,3)

                    .map(candidate=>(

                        <div

                            key={candidate.id}

                            className="candidate-card"

                        >

                    <div className="candidate-info">

                        <div className="candidate-avatar">

                            {
                                candidate.name
                                    .split(" ")
                                    .map(word => word[0])
                                    .join("")
                            }

                        </div>

                        <div>

                            <h3>

                                {candidate.name}

                            </h3>

                            <p>

                                {candidate.position}

                            </p>

                        </div>

                    </div>

                    <div className="candidate-score">

                        ⭐ {candidate.score}

                    </div>

                    <div

                        className={`candidate-status ${candidate.status
                            .toLowerCase()
                            .replaceAll(" ","-")}`}

                    >

                        {candidate.status}

                    </div>

                            <button

                                className="candidate-view"

                                onClick={()=>navigate(`/company/candidates/${candidate.id}`)}

                            >

                                <FaEye/>

                            </button>

                        </div>

                    ))

                }

            </div>

            <div className="candidate-footer">

                <Link

                    to="/company/candidates"

                    className="candidate-view-all-btn"

                >

                    View All

                    <FaArrowRight/>

                </Link>

            </div>

        </section>
    );

}

export default RecentCandidates;
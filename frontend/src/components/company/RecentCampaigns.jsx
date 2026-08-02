import { FaArrowRight } from "react-icons/fa";
import { Link } from "react-router-dom";

import {
    recentCampaigns,
} from "../../data/company/dashboardMockData";

import "../../styles/company/RecentCampaigns.css";

function RecentCampaigns(){

    return(

        <section className="recent-campaigns">

            <div className="section-header">

                <h2>

                    Recent Campaigns

                </h2>

            </div>

            <div className="campaign-table">

                <div className="table-head">

                    <span>Job Title</span>

                    <span>Department</span>

                    <span>Status</span>

                </div>

                {

                    recentCampaigns

                    .slice(0,4)

                    .map(campaign=>(

                        <div

                            key={campaign.id}

                            className="table-row"

                        >

                            <span>

                                {campaign.title}

                            </span>

                            <span>

                                {campaign.department}

                            </span>

                            <span

                                className={`status ${campaign.status.toLowerCase()}`}

                            >

                                {campaign.status}

                            </span>

                        </div>

                    ))

                }

            </div>

            <div className="card-footer">

                <Link

                    to="/company/campaigns"

                    className="view-all-btn"

                >

                    View All

                    <FaArrowRight/>

                </Link>

            </div>

        </section>
    );

}

export default RecentCampaigns;
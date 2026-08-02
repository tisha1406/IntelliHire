import {

    FaClock,
    FaVideo,

} from "react-icons/fa";

import {

    upcomingInterviews,

} from "../../data/company/dashboardMockData";

import "../../styles/company/UpcomingInterviews.css";

function UpcomingInterviews(){

    return(

        <section className="upcoming-card">

            <div className="upcoming-header">

                <h2>

                    Upcoming Interviews

                </h2>

            </div>

            <div className="upcoming-list">

                {

                    upcomingInterviews.map(interview=>(

                        <div

                            key={interview.id}

                            className="upcoming-item"

                        >

                            <div className="avatar">

                                {

                                    interview.candidate

                                    .split(" ")

                                    .map(word=>word[0])

                                    .join("")

                                }

                            </div>

                            <div className="upcoming-content">

                                <h3>

                                    {interview.candidate}

                                </h3>

                                <p>

                                    {interview.role}

                                </p>

                                <span>

                                    <FaVideo />

                                    {interview.type}

                                </span>

                            </div>

                            <div className="time-box">

                                <FaClock />

                                {interview.time}

                            </div>

                        </div>

                    ))

                }

            </div>

        </section>

    );

}

export default UpcomingInterviews;
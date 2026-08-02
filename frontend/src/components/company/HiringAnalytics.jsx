import {

    Chart as ChartJS,

    CategoryScale,

    LinearScale,

    PointElement,

    LineElement,

    ArcElement,

    Tooltip,

    Legend,

    Filler,

} from "chart.js";

import {

    Line,

    Doughnut,

} from "react-chartjs-2";

import {

    applicationTrend,

    candidateStatus,

} from "../../data/company/dashboardMockData";

import "../../styles/company/HiringAnalytics.css";

ChartJS.register(

    CategoryScale,

    LinearScale,

    PointElement,

    LineElement,

    ArcElement,

    Tooltip,

    Legend,

    Filler,

);

function HiringAnalytics(){

    const lineData={

        labels:applicationTrend.labels,

        datasets:[{

            label:"Applications",

            data:applicationTrend.values,

            borderColor:"#3B82F6",

            backgroundColor:"rgba(59,130,246,.18)",

            fill:true,

            tension:.4,

            pointRadius:4,

        }]

    };

    const doughnutData={

        labels:candidateStatus.map(item=>item.label),

        datasets:[{

            data:candidateStatus.map(item=>item.value),

            backgroundColor:

                candidateStatus.map(item=>item.color),

            borderWidth:0,

        }]

    };

    return(

        <section className="analytics-section">

            <h2>

                Hiring Analytics

            </h2>

            <div className="analytics-grid">

                <div className="chart-card">

                    <h3>

                        Applications Trend

                    </h3>

                <div className="chart-wrapper">

                    <Line

                        data={lineData}

                        options={{

                            responsive:true,

                            maintainAspectRatio:false,

                            plugins:{

                                legend:{

                                    display:false,

                                },

                            },

                        }}

                    />

                </div>

                </div>

                <div className="chart-card">

                    <h3>

                        Candidate Status

                    </h3>

                    <div className="chart-wrapper">

                        <Doughnut

                            data={doughnutData}

                            options={{

                                responsive:true,

                                maintainAspectRatio:false,

                                cutout:"70%",

                                plugins:{

                                    legend:{

                                        position:"bottom",

                                    },

                                },

                            }}

                        />

                    </div>

                </div>

            </div>

        </section>

    );

}

export default HiringAnalytics;
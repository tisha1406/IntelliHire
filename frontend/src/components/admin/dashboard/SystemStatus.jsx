import {
    Server,
    Database,
    BrainCircuit,
    Workflow,
    Activity
} from "lucide-react";

import Card from "../../common/Card";

import "../../../styles/admin/dashboard.css";

export default function SystemStatus({ health = {}, loading }) {
    const systems = [
        {
            icon: <Server size={18}/>,
            name: "FastAPI",
            status: health.fastapi || "Unknown",
            uptime: health.cpu ? `CPU: ${health.cpu}` : "",
            color: health.fastapi === "Healthy" ? "green" : "orange"
        },
        {
            icon: <Database size={18}/>,
            name: "MongoDB",
            status: health.mongodb || "Unknown",
            uptime: health.memory ? `Mem: ${health.memory}` : "",
            color: health.mongodb === "Healthy" ? "blue" : "orange"
        },
        {
            icon: <BrainCircuit size={18}/>,
            name: "LLM Services",
            status: health.llm_service || "Unknown",
            uptime: "Gemini, Groq",
            color: health.llm_service === "Healthy" ? "purple" : "orange"
        },
        {
            icon: <Workflow size={18}/>,
            name: "Speech Services",
            status: health.speech_services || "Unknown",
            uptime: "Sarvam AI",
            color: health.speech_services === "Healthy" ? "orange" : "red"
        }
    ];

    return(

        <Card className="system-card">

            <div className="system-header">

                <div>

                    <h3>

                        System Health

                    </h3>

                    <p>

                        Live infrastructure status

                    </p>

                </div>

                <div className="health-score">

                    <Activity size={16}/>

                    99.8%

                </div>

            </div>

            <div className="system-list">

                {

                    systems.map(system=>(

                        <div
                            key={system.name}
                            className="system-item"
                        >

                            <div className={`system-icon ${system.color}`}>

                                {system.icon}

                            </div>

                            <div className="system-info">

                                <h4>

                                    {system.name}

                                </h4>

                                <span>
                                    {loading ? <div className="skeleton" style={{width: 40, height: 16}} /> : system.uptime}
                                </span>
                            </div>
                            <div className={`system-pill ${system.color}`}>
                                {loading ? "..." : system.status}
                            </div>

                        </div>

                    ))

                }

            </div>

        </Card>

    );

}
import React from 'react';
import SectionCard from "../../../layout/SectionCard";
import ToggleCard from "../components/ToggleCard";
import { MessageSquare } from "lucide-react";

export default function InterviewModesTab({ masterConfig, watch, setValue }) {
    const selectedModes = watch("allowed_interview_modes") || [];

    const toggleMode = (name) => {
        if (selectedModes.includes(name)) {
            setValue("allowed_interview_modes", selectedModes.filter(m => m !== name), { shouldDirty: true });
        } else {
            setValue("allowed_interview_modes", [...selectedModes, name], { shouldDirty: true });
        }
    };

    return (
        <SectionCard title="Interview Modes" description="Select which standard interview workflows the company can launch.">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
                {masterConfig.interview_modes.map(mode => (
                    <ToggleCard 
                        key={mode.id}
                        label={mode.name}
                        description={mode.description}
                        icon={<MessageSquare size={24} />}
                        checked={selectedModes.includes(mode.name)}
                        onChange={() => toggleMode(mode.name)}
                        badges={[
                            { text: `Duration: ${mode.duration}` },
                            { text: `Strategy: ${mode.question_strategy}` },
                            { text: mode.is_default ? 'Default' : '' }
                        ].filter(b => b.text)}
                    />
                ))}
            </div>
        </SectionCard>
    );
}

import React from 'react';
import SectionCard from "../../../layout/SectionCard";
import ToggleCard from "../components/ToggleCard";
import { Settings } from "lucide-react";

export default function StrategiesTab({ masterConfig, watch, setValue }) {
    const selectedStrategies = watch("allowed_strategies") || [];

    const toggleStrategy = (name) => {
        if (selectedStrategies.includes(name)) {
            setValue("allowed_strategies", selectedStrategies.filter(s => s !== name), { shouldDirty: true });
        } else {
            setValue("allowed_strategies", [...selectedStrategies, name], { shouldDirty: true });
        }
    };

    return (
        <SectionCard title="Interview Strategies" description="Select which internal conversational strategies the company can use.">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
                {masterConfig.strategies.map(strat => (
                    <ToggleCard 
                        key={strat.id}
                        label={strat.name}
                        description={strat.description}
                        icon={<Settings size={24} />}
                        checked={selectedStrategies.includes(strat.name)}
                        onChange={() => toggleStrategy(strat.name)}
                        badges={[
                            { text: `Difficulty: ${strat.difficulty}` },
                            { text: `Logic: ${strat.follow_up_logic}` },
                            { text: strat.is_default ? 'Default' : '' }
                        ].filter(b => b.text)}
                    />
                ))}
            </div>
        </SectionCard>
    );
}

import React from 'react';
import SectionCard from "../../../layout/SectionCard";
import ToggleCard from "../components/ToggleCard";
import { Cpu } from "lucide-react";

export default function AIModelsTab({ masterConfig, watch, setValue }) {
    const selectedModels = watch("allowed_llm_tiers") || [];

    const toggleModel = (id) => {
        if (selectedModels.includes(id)) {
            setValue("allowed_llm_tiers", selectedModels.filter(m => m !== id), { shouldDirty: true });
        } else {
            setValue("allowed_llm_tiers", [...selectedModels, id], { shouldDirty: true });
        }
    };

    return (
        <SectionCard title="AI Models Allocation" description="Select which globally enabled AI models this company can access for question generation and evaluation.">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
                {masterConfig.ai_models.map(model => (
                    <ToggleCard 
                        key={model.id}
                        label={model.name}
                        description={`Provider: ${model.provider}`}
                        icon={<Cpu size={24} />}
                        checked={selectedModels.includes(model.id)}
                        onChange={() => toggleModel(model.id)}
                        badges={[
                            { text: `Latency: ${model.latency}` },
                            { text: `Cost: ${model.cost}` },
                            { text: `Context: ${model.context_window}` },
                            ...(model.is_default ? [{ text: 'Default Model', color: 'rgba(79, 70, 229, 0.1)', textColor: 'var(--primary)' }] : [])
                        ]}
                    />
                ))}
                {masterConfig.ai_models.length === 0 && (
                    <div style={{ gridColumn: '1 / -1', color: 'var(--text-secondary)' }}>No AI models currently enabled globally. Check Platform Settings.</div>
                )}
            </div>
        </SectionCard>
    );
}

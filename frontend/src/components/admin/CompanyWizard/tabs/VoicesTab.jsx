import React from 'react';
import SectionCard from "../../../layout/SectionCard";
import ToggleCard from "../components/ToggleCard";
import { Mic, Play } from "lucide-react";

export default function VoicesTab({ masterConfig, watch, setValue }) {
    const selectedVoices = watch("allowed_voices") || [];

    const toggleVoice = (name) => {
        if (selectedVoices.includes(name)) {
            setValue("allowed_voices", selectedVoices.filter(v => v !== name), { shouldDirty: true });
        } else {
            setValue("allowed_voices", [...selectedVoices, name], { shouldDirty: true });
        }
    };

    return (
        <SectionCard title="Voice Catalog" description="Select TTS voices available for this company's interviews.">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
                {masterConfig.voices.map(voice => (
                    <ToggleCard 
                        key={voice.id}
                        label={voice.name}
                        description={`Provider: ${voice.provider} | Lang: ${voice.language}`}
                        icon={<Mic size={24} />}
                        checked={selectedVoices.includes(voice.name)}
                        onChange={() => toggleVoice(voice.name)}
                        badges={[
                            { text: voice.gender },
                            { text: voice.emotion },
                            { text: voice.is_default ? 'Default Selection' : '' }
                        ].filter(b => b.text)}
                    />
                ))}
            </div>
        </SectionCard>
    );
}

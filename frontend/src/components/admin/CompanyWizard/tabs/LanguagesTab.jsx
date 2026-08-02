import React from 'react';
import SectionCard from "../../../layout/SectionCard";
import ToggleCard from "../components/ToggleCard";
import { Globe } from "lucide-react";

export default function LanguagesTab({ masterConfig, watch, setValue }) {
    const selectedLanguages = watch("allowed_languages") || [];

    const toggleLang = (name) => {
        if (selectedLanguages.includes(name)) {
            setValue("allowed_languages", selectedLanguages.filter(l => l !== name), { shouldDirty: true });
        } else {
            setValue("allowed_languages", [...selectedLanguages, name], { shouldDirty: true });
        }
    };

    return (
        <SectionCard title="Language Capabilities" description="Select which languages the AI interviewer can use for candidates from this company.">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                {masterConfig.languages.map(lang => (
                    <ToggleCard 
                        key={lang.id}
                        label={lang.name}
                        description={`ISO Code: ${lang.code}`}
                        icon={<Globe size={24} />}
                        checked={selectedLanguages.includes(lang.name)}
                        onChange={() => toggleLang(lang.name)}
                        badges={[
                            { text: lang.stt_supported ? 'STT Ready' : 'No STT', color: lang.stt_supported ? 'rgba(34, 197, 94, 0.1)' : '', textColor: lang.stt_supported ? 'var(--success)' : '' },
                            { text: lang.tts_supported ? 'TTS Ready' : 'No TTS', color: lang.tts_supported ? 'rgba(34, 197, 94, 0.1)' : '', textColor: lang.tts_supported ? 'var(--success)' : '' },
                            { text: lang.translation_supported ? 'Live Translation' : '' }
                        ].filter(b => b.text)}
                    />
                ))}
            </div>
        </SectionCard>
    );
}

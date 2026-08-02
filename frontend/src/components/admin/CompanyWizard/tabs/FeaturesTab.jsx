import React from 'react';
import SectionCard from "../../../layout/SectionCard";
import ToggleCard from "../components/ToggleCard";
import { CheckCircle2 } from "lucide-react";

export default function FeaturesTab({ masterConfig, watch, setValue }) {
    const features = watch("features") || {};

    const toggleFeature = (id) => {
        setValue(`features.${id}`, !features[id], { shouldDirty: true });
    };

    // Group features by category
    const grouped = masterConfig.features.reduce((acc, feat) => {
        const cat = feat.category || 'Other';
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(feat);
        return acc;
    }, {});

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {Object.keys(grouped).map(category => (
                <SectionCard key={category} title={category}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                        {grouped[category].map(feat => (
                            <ToggleCard 
                                key={feat.id}
                                label={feat.name}
                                description={`Requires ${feat.plan_requirement} plan.`}
                                icon={<CheckCircle2 size={24} />}
                                checked={!!features[feat.id]}
                                onChange={() => toggleFeature(feat.id)}
                            />
                        ))}
                    </div>
                </SectionCard>
            ))}
        </div>
    );
}

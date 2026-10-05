export const VALID_VOICES = [
    { value: "shubh", label: "Shubh" },
    { value: "simran", label: "Simran" },
    { value: "rohan", label: "Rohan" },
    { value: "ishita", label: "Ishita" },
    { value: "sunny", label: "Sunny" }
];

export const isLegacyVoice = (voiceId) => {
    return !VALID_VOICES.some(v => v.value === voiceId);
};

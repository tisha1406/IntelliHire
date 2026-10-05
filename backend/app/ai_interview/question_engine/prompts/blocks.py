# backend/app/ai_interview/question_engine/prompts/blocks.py

from app.ai_interview.question_engine.prompts import prompt_library as lib

COMMON_BLOCK = lib.M0_COMMON
OUTPUT_CONTRACT = lib.OUTPUT_CONTRACT

STRATEGY_BLOCKS = {
    "adaptive_depth": lib.S_ADAPTIVE_DEPTH,
    "fixed_coverage": lib.S_FIXED_COVERAGE,
    "critical_skills": lib.S_CRITICAL_SKILLS,
    "breadth": lib.S_BREADTH,
    "gap_verification": lib.S_GAP_VERIFICATION,
    "behavioral_adaptive": lib.S_BEHAVIORAL_ADAPTIVE
}

DIMENSION_BLOCKS = {
    "technical": lib.D_TECHNICAL,
    "resume": lib.D_RESUME,
    "behavioral": lib.D_BEHAVIORAL,
    "situational": lib.D_SITUATIONAL
}

ENVELOPE_BLOCKS = {
    "technical": lib.ENV_TECHNICAL,
    "resume": lib.ENV_RESUME,
    "behavioral": lib.ENV_BEHAVIORAL,
    "situational": lib.ENV_SITUATIONAL
}

CATEGORY_BLOCKS = {
    "new": {
        "technical": lib.C_NEW_TECHNICAL,
        "resume": lib.C_NEW_RESUME,
        "behavioral": lib.C_NEW_BEHAVIORAL,
        "situational": lib.C_NEW_SITUATIONAL
    },
    "followup_clarification": {
        "technical": lib.C_CLARIFICATION_TECHNICAL,
        "resume": lib.C_CLARIFICATION_RESUME,
        "behavioral": lib.C_CLARIFICATION_BEHAVIORAL,
        "situational": lib.C_CLARIFICATION_SITUATIONAL
    },
    "followup_depth": {
        "technical": lib.C_DEPTH_TECHNICAL,
        "resume": lib.C_DEPTH_RESUME,
        "behavioral": lib.C_DEPTH_BEHAVIORAL,
        "situational": lib.C_DEPTH_SITUATIONAL
    },
    "followup_evidence": {
        "technical": lib.C_EVIDENCE_TECHNICAL,
        "resume": lib.C_EVIDENCE_RESUME,
        "behavioral": lib.C_EVIDENCE_BEHAVIORAL,
        "situational": lib.C_EVIDENCE_SITUATIONAL
    },
    "followup_challenge": {
        "technical": lib.C_TECHNICAL_CHALLENGE_TECHNICAL
    },
    "correction": {
        "technical": lib.C_CORRECTION_TECHNICAL,
        "resume": lib.C_CORRECTION_RESUME,
        "situational": lib.C_CORRECTION_SITUATIONAL
    },
    "gap_verification": {
        "technical": lib.C_GAP_VERIFICATION_TECHNICAL
    }
}

COMBINATION_ADDENDA = {
    "AD_TECH": lib.ADD_AD_TECH,
    "AD_MIXED": lib.ADD_AD_MIXED,
    "FC_TECH": lib.ADD_FC_TECH,
    "FC_RESUME": lib.ADD_FC_RESUME,
    "FC_BEHAV": lib.ADD_FC_BEHAV,
    "FC_SIT": lib.ADD_FC_SIT,
    "FC_MIXED": lib.ADD_FC_MIXED,
    "CS_TECH": lib.ADD_CS_TECH,
    "BS_TECH": lib.ADD_BS_TECH,
    "BS_RESUME": lib.ADD_BS_RESUME,
    "BS_BEHAV": lib.ADD_BS_BEHAV,
    "BS_SIT": lib.ADD_BS_SIT,
    "BS_MIXED": lib.ADD_BS_MIXED,
    "GV_TECH": lib.ADD_GV_TECH,
    "GV_MIXED": lib.ADD_GV_MIXED,
    "BA_HR": lib.ADD_BA_HR
}

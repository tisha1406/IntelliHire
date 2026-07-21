from typing import List, Literal, Optional

from pydantic import BaseModel


class VoiceConfigRequest(BaseModel):
    voice_id: str
    language: str
    accent: str


class CampaignCreateRequest(BaseModel):
    company_id: str

    name: str

    role_target: str

    interview_type: Literal[
        "technical",
        "hr",
        "behavioral",
        "mixed",
    ]

    voice_config: VoiceConfigRequest

    interview_mode: str

    delegate_language_choice_to_candidate: bool

    delegate_domain_choice_to_candidate: bool

    allowed_candidate_languages: List[str]


class CampaignUpdateRequest(BaseModel):
    name: Optional[str] = None

    role_target: Optional[str] = None

    interview_type: Optional[
        Literal[
            "technical",
            "hr",
            "behavioral",
            "mixed",
        ]
    ] = None

    interview_mode: Optional[str] = None

    status: Optional[
        Literal[
            "active",
            "closed",
        ]
    ] = None


class CampaignResponse(BaseModel):
    campaign_id: str


class CampaignUpdateResponse(BaseModel):
    updated_fields: List[str]
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Education(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None
    cgpa: Optional[str] = None


class Experience(BaseModel):
    title: str
    org: str
    description: Optional[str] = None
    duration: Optional[str] = None


class Skill(BaseModel):
    name: str
    category: Optional[str] = None
    proficiency: Optional[str] = None


class Project(BaseModel):
    name: str
    description: str
    technologies: List[str] = Field(default_factory=list)
    link: Optional[str] = None


class Certification(BaseModel):
    name: str
    issuer: str
    year: Optional[str] = None


class StructuredResume(BaseModel):
    professional_summary: Optional[str] = None
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

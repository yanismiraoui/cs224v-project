"""Core Pydantic domain models for structured career evidence."""

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceSource(BaseModel):
    """A source document or location that provides career evidence."""

    kind: Literal["resume", "github", "manual", "job_description", "website"]
    uri: str | None = None
    title: str | None = None
    extracted_text: str | None = None


class CareerClaim(BaseModel):
    """An atomic career claim extracted from one or more evidence sources."""

    id: str
    claim_type: Literal[
        "skill",
        "project",
        "experience",
        "achievement",
        "education",
        "publication",
    ]
    text: str
    skill_tags: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class TargetRole(BaseModel):
    """A target job role and the signals used to evaluate fit."""

    title: str | None = None
    organization: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    success_signals: list[str] = Field(default_factory=list)


class RoleFitReport(BaseModel):
    """Evidence-backed fit assessment for a target role."""

    target: TargetRole
    matched_claims: list[CareerClaim]
    missing_signals: list[str]
    strongest_positioning: list[str]
    risks: list[str]
    recommended_assets: list[str]


__all__ = [
    "CareerClaim",
    "EvidenceSource",
    "RoleFitReport",
    "TargetRole",
]

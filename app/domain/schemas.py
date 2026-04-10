from __future__ import annotations

from datetime import datetime

from app.domain.enums import MessageCategory
from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str


class ReadinessCheck(BaseModel):
    name: str
    ok: bool
    detail: str


class ReadinessResponse(BaseModel):
    status: str
    checks: list[ReadinessCheck]


class IntakeRequest(BaseModel):
    mailbox_connection_id: str | None = None
    since: datetime | None = None
    limit: int = Field(default=25, ge=1, le=500)


class IntakeResponse(BaseModel):
    status: str
    accepted: bool
    detail: str
    suggested_next_step: str


class ClassificationResponse(BaseModel):
    message_id: str
    category: MessageCategory
    confidence: float
    rationale: str
    provider: str
    placeholder: bool = True


class ResumeExtraction(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    summary: str | None = None


class JobDescriptionExtraction(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    summary: str | None = None


class ExtractResponse(BaseModel):
    message_id: str
    category: MessageCategory
    contractor_profile: ResumeExtraction | None = None
    job_posting: JobDescriptionExtraction | None = None
    provider: str
    placeholder: bool = True


class MatchFactor(BaseModel):
    name: str
    score: float
    weight: float
    explanation: str


class MatchCandidate(BaseModel):
    contractor_profile_id: str
    score: float
    summary: str
    factors: list[MatchFactor]


class MatchRunRequest(BaseModel):
    job_posting_id: str
    requested_by: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class MatchRunResponse(BaseModel):
    match_run_id: str
    status: str
    placeholder: bool = True
    detail: str


class MatchResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_run_id: str
    status: str
    candidates: list[MatchCandidate]
    placeholder: bool = True

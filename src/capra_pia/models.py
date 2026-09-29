from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RiskRating(str, Enum):
    PRESENT = "present"
    NOT_PRESENT = "not_present"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


class Risk(BaseModel):
    id: str
    name: str
    category: str
    source_paper: str
    source_citation: str
    frequency_count: int
    frequency_pct: float
    definition: str
    category_tag: Optional[str] = None
    note: Optional[str] = None


class CrossReference(BaseModel):
    a_risk: str
    b_risk: str
    confidence: str
    evidence_quote: str


class RiskRatingEntry(BaseModel):
    risk_id: str
    rating: RiskRating
    evidence_note: Optional[str] = None


class AssessmentRequest(BaseModel):
    system_name: str
    ratings: list[RiskRatingEntry]


class CategoryScore(BaseModel):
    category: str
    applicable_risks: int
    present_risks: int
    score_pct: float


class FlaggedRisk(BaseModel):
    risk: Risk
    rating: RiskRating
    related_cross_references: list[CrossReference] = Field(default_factory=list)


class AssessmentResult(BaseModel):
    system_name: str
    overall_score_pct: float
    category_scores: list[CategoryScore]
    flagged_high_risk: list[FlaggedRisk]
    unrated_risks: list[str]
    recommendations: list[str]

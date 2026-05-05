"""Unified schema for opportunities across all sources."""
from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class OpportunityType(StrEnum):
    SCHOLARSHIP = "scholarship"
    FELLOWSHIP = "fellowship"
    INTERNSHIP = "internship"
    CONFERENCE = "conference"
    EXCHANGE = "exchange"
    COMPETITION = "competition"
    GRANT = "grant"
    AWARD = "award"
    OTHER = "other"


class FundingLevel(StrEnum):
    FULLY_FUNDED = "fully_funded"
    PARTIAL = "partial"
    UNFUNDED = "unfunded"
    UNKNOWN = "unknown"


class StudyLevel(StrEnum):
    HIGH_SCHOOL = "high_school"
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    POSTDOC = "postdoc"
    EARLY_CAREER = "early_career"
    ANY = "any"


class Opportunity(BaseModel):
    """A single opportunity record. The shape every adapter must produce."""

    model_config = ConfigDict(use_enum_values=False)

    id: str = Field(..., description="sha1(source + canonical_url)[:16]")
    title: str
    type: OpportunityType
    summary: str = Field(..., max_length=500)
    deadline: date | None = None
    funded: FundingLevel = FundingLevel.UNKNOWN
    eligible_countries: list[str] | Literal["worldwide"] | None = None
    eligible_levels: list[StudyLevel] = Field(default_factory=list)
    host_country: str | None = None
    apply_url: AnyHttpUrl
    source_site: str
    source_url: AnyHttpUrl
    posted_at: datetime
    scraped_at: datetime
    raw_categories: list[str] = Field(default_factory=list)

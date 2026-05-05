"""Heuristic extractors for messy fields: type, summary, deadline, funding.

These are deliberately conservative — when in doubt, return UNKNOWN rather
than a confident-but-wrong guess. Adapters can layer richer logic on top.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from dateparser.search import search_dates
from selectolax.parser import HTMLParser

from .schema import FundingLevel, OpportunityType

_TYPE_KEYWORDS: dict[OpportunityType, tuple[str, ...]] = {
    OpportunityType.SCHOLARSHIP: ("scholarship", "scholarships", "tuition", "bursary"),
    OpportunityType.FELLOWSHIP: ("fellowship", "fellowships", "fellow program"),
    OpportunityType.INTERNSHIP: ("internship", "internships", "intern program", "trainee"),
    OpportunityType.EXCHANGE: ("exchange program", "exchange visit", "study abroad"),
    OpportunityType.CONFERENCE: ("conference", "summit", "forum", "symposium"),
    OpportunityType.COMPETITION: (
        "competition",
        "challenge",
        "hackathon",
        "contest",
        "olympiad",
    ),
    OpportunityType.GRANT: ("grant", "grants", "funding for"),
    OpportunityType.AWARD: ("award", "awards", "prize"),
}


_FUNDING_PATTERNS: dict[FundingLevel, tuple[str, ...]] = {
    FundingLevel.FULLY_FUNDED: (
        "fully funded",
        "fully-funded",
        "100% funded",
        "all expenses paid",
        "all-expenses-paid",
        "full scholarship",
        "full funding",
    ),
    FundingLevel.PARTIAL: (
        "partially funded",
        "partial funding",
        "tuition only",
        "stipend only",
        "partial scholarship",
    ),
    FundingLevel.UNFUNDED: (
        "self-funded",
        "self funded",
        "no funding",
        "tuition fees apply",
    ),
}


_DEADLINE_TRIGGER = re.compile(
    r"\b("
    r"deadline"
    r"|application\s+deadline"
    r"|apply\s+(?:by|before|until)"
    r"|application\s+(?:by|before|until)"
    r"|closing\s+date"
    r"|closes\s+on"
    r"|last\s+date"
    r"|due\s+(?:by|on)"
    r")\b",
    re.IGNORECASE,
)

_DATEPARSER_SETTINGS = {
    "PREFER_DATES_FROM": "future",
    "RETURN_AS_TIMEZONE_AWARE": False,
    "REQUIRE_PARTS": ["year", "month"],
}


def html_to_text(html: str) -> str:
    """Strip HTML and return plain text."""
    if not html:
        return ""
    return HTMLParser(html).text(separator=" ", strip=True)


def parse_summary(html: str, max_chars: int = 500) -> str:
    text = html_to_text(html)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def classify_type(title: str, tags: list[str] | None = None) -> OpportunityType:
    haystack = (title or "").lower()
    if tags:
        haystack += " " + " ".join(t.lower() for t in tags)
    best: tuple[OpportunityType, int] = (OpportunityType.OTHER, 0)
    for opp_type, keywords in _TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in haystack)
        if score > best[1]:
            best = (opp_type, score)
    return best[0]


def parse_funding(html: str, title: str = "") -> FundingLevel:
    text = (html_to_text(html) + " " + title).lower()
    for level, patterns in _FUNDING_PATTERNS.items():
        if any(p in text for p in patterns):
            return level
    return FundingLevel.UNKNOWN


def parse_deadline(html: str, *, posted_at: datetime | None = None) -> date | None:
    """Best-effort deadline extraction. Returns None if unparseable.

    Strategy: locate a deadline-trigger phrase ("deadline", "apply by", …) and
    feed the ~120-char window after it to ``dateparser.search.search_dates``.
    Among all candidates, prefer the soonest future date; fall back to the one
    closest to the post date.
    """
    text = html_to_text(html)
    if not text:
        return None

    candidates: list[date] = []
    for match in _DEADLINE_TRIGGER.finditer(text):
        # search_dates is sensitive to leading punctuation — skip past
        # ":", "-", whitespace etc. before the actual date string.
        window = text[match.end() : match.end() + 120].lstrip(": \t\n-–—.,;")
        if not window:
            continue
        try:
            found = search_dates(window, settings=_DATEPARSER_SETTINGS)
        except Exception:
            found = None
        if not found:
            continue
        # Take the first plausible date in the window.
        for _, parsed in found:
            candidates.append(parsed.date())
            break

    if not candidates:
        return None

    today = date.today()
    future = [d for d in candidates if d >= today - timedelta(days=14)]
    if future:
        return min(future)

    if posted_at:
        return min(candidates, key=lambda d: abs((d - posted_at.date()).days))

    return candidates[0]

"""Tests for the heuristic extractors."""
from datetime import UTC, date, datetime

from opportunity_mcp.extract import (
    classify_type,
    parse_deadline,
    parse_funding,
    parse_summary,
)
from opportunity_mcp.schema import FundingLevel, OpportunityType


class TestClassifyType:
    def test_scholarship(self):
        assert (
            classify_type("Fully Funded Master's Scholarship in Germany")
            == OpportunityType.SCHOLARSHIP
        )

    def test_fellowship(self):
        assert (
            classify_type("Mandela Washington Fellowship 2026")
            == OpportunityType.FELLOWSHIP
        )

    def test_internship(self):
        assert classify_type("UN Internship Program 2026") == OpportunityType.INTERNSHIP

    def test_competition(self):
        assert classify_type("Global AI Hackathon 2026") == OpportunityType.COMPETITION

    def test_conference(self):
        assert (
            classify_type("World Youth Forum Summit Cairo")
            == OpportunityType.CONFERENCE
        )

    def test_uses_tags_when_title_ambiguous(self):
        # Title alone is ambiguous, tags push it to scholarship.
        assert (
            classify_type("Apply now for 2026", tags=["scholarship"])
            == OpportunityType.SCHOLARSHIP
        )

    def test_falls_back_to_other(self):
        assert classify_type("Random news update") == OpportunityType.OTHER


class TestParseFunding:
    def test_fully_funded(self):
        assert (
            parse_funding("This is a fully funded program for 2026.", "")
            == FundingLevel.FULLY_FUNDED
        )

    def test_fully_funded_in_title(self):
        assert (
            parse_funding("", "100% funded scholarship in Norway")
            == FundingLevel.FULLY_FUNDED
        )

    def test_partial(self):
        assert (
            parse_funding("Partial funding available for living costs.", "")
            == FundingLevel.PARTIAL
        )

    def test_unfunded(self):
        assert (
            parse_funding("Note: this program is self-funded.", "")
            == FundingLevel.UNFUNDED
        )

    def test_unknown(self):
        assert parse_funding("Apply now.", "Some Title") == FundingLevel.UNKNOWN


class TestParseSummary:
    def test_strips_html(self):
        s = parse_summary("<p>Hello <b>world</b></p>")
        assert "Hello" in s
        assert "world" in s
        assert "<b>" not in s

    def test_truncates_long_input(self):
        long_html = "<p>" + ("hello world " * 200) + "</p>"
        summary = parse_summary(long_html, max_chars=100)
        assert len(summary) <= 100

    def test_collapses_whitespace(self):
        assert parse_summary("<p>a\n\n\nb</p>") == "a b"

    def test_empty_input(self):
        assert parse_summary("") == ""


class TestParseDeadline:
    def test_basic(self):
        html = "<p>Deadline: April 30, 2027</p>"
        posted = datetime(2026, 1, 1, tzinfo=UTC)
        assert parse_deadline(html, posted_at=posted) == date(2027, 4, 30)

    def test_apply_before(self):
        html = "<p>Apply before May 15, 2027 to be considered.</p>"
        posted = datetime(2026, 1, 1, tzinfo=UTC)
        assert parse_deadline(html, posted_at=posted) == date(2027, 5, 15)

    def test_closing_date(self):
        html = "<p>Closing date: 31 December 2027</p>"
        assert parse_deadline(html) == date(2027, 12, 31)

    def test_returns_none_when_unparseable(self):
        assert parse_deadline("<p>No date here at all.</p>") is None

    def test_picks_future_over_past(self):
        # Two dates mentioned; we want the future one.
        html = "<p>Last year deadline: April 30, 2024. New deadline: April 30, 2027.</p>"
        assert parse_deadline(html) == date(2027, 4, 30)

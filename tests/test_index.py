"""Tests for the SQLite + FTS5 index."""
from datetime import UTC, date, datetime, timedelta

import pytest

from opportunity_mcp.index import Index, _to_fts_query
from opportunity_mcp.schema import (
    FundingLevel,
    Opportunity,
    OpportunityType,
    StudyLevel,
)


def _make_opp(idx: int = 1, **overrides) -> Opportunity:
    base = dict(
        id=f"test{idx:04d}",
        title=f"Test Scholarship {idx}",
        type=OpportunityType.SCHOLARSHIP,
        summary="A great opportunity for students of the world.",
        deadline=date(2027, 12, 1),
        funded=FundingLevel.FULLY_FUNDED,
        eligible_countries="worldwide",
        eligible_levels=[StudyLevel.MASTER],
        host_country="Germany",
        apply_url="https://example.com/apply",
        source_site="test_source",
        source_url="https://example.com/post",
        posted_at=datetime.now(UTC),
        scraped_at=datetime.now(UTC),
        raw_categories=["scholarship", "germany"],
    )
    base.update(overrides)
    return Opportunity(**base)


@pytest.fixture
def idx(tmp_path):
    db = tmp_path / "test.db"
    index = Index(db)
    yield index
    index.close()


class TestUpsert:
    def test_upsert_then_get(self, idx):
        opp = _make_opp(1)
        idx.upsert_many([opp])
        got = idx.get(opp.id)
        assert got is not None
        assert got.title == opp.title

    def test_upsert_replaces(self, idx):
        idx.upsert_many([_make_opp(1, title="Original")])
        idx.upsert_many([_make_opp(1, title="Updated")])
        got = idx.get("test0001")
        assert got is not None
        assert got.title == "Updated"


class TestSearch:
    def test_finds_by_title(self, idx):
        idx.upsert_many([_make_opp(1)])
        results = idx.search("scholarship")
        assert len(results) == 1
        assert results[0].title == "Test Scholarship 1"

    def test_filters_by_type(self, idx):
        idx.upsert_many(
            [
                _make_opp(1, type=OpportunityType.SCHOLARSHIP),
                _make_opp(2, type=OpportunityType.INTERNSHIP, title="Test Internship"),
            ]
        )
        results = idx.search("test", opp_type=OpportunityType.INTERNSHIP)
        assert len(results) == 1
        assert results[0].type == OpportunityType.INTERNSHIP

    def test_filters_funded_only(self, idx):
        idx.upsert_many(
            [
                _make_opp(1, funded=FundingLevel.FULLY_FUNDED),
                _make_opp(2, funded=FundingLevel.UNFUNDED, title="Test Unfunded"),
            ]
        )
        results = idx.search("test", funded_only=True)
        assert len(results) == 1
        assert results[0].funded == FundingLevel.FULLY_FUNDED

    def test_empty_query_falls_through_to_latest(self, idx):
        idx.upsert_many([_make_opp(1)])
        # Single-char tokens are filtered; with nothing left we should still
        # get a non-error response (latest fallback).
        results = idx.search("x")
        assert isinstance(results, list)


class TestUpcomingDeadlines:
    def test_within_window(self, idx):
        idx.upsert_many(
            [
                _make_opp(1, deadline=date.today() + timedelta(days=10)),
                _make_opp(2, deadline=date.today() + timedelta(days=100)),
            ]
        )
        upcoming = idx.upcoming_deadlines(within_days=30)
        assert len(upcoming) == 1


class TestSourceStats:
    def test_counts_per_source(self, idx):
        idx.upsert_many(
            [
                _make_opp(1, source_site="site_a"),
                _make_opp(2, source_site="site_a"),
                _make_opp(3, source_site="site_b"),
            ]
        )
        stats = {row["source_site"]: row["count"] for row in idx.source_stats()}
        assert stats == {"site_a": 2, "site_b": 1}


class TestFTSQuerySanitization:
    def test_strips_short_tokens(self):
        assert _to_fts_query("a b cd") == '"cd"*'

    def test_returns_none_when_no_tokens(self):
        assert _to_fts_query("") is None
        assert _to_fts_query("a") is None

    def test_prefix_matches_each_token(self):
        assert _to_fts_query("germany scholarship") == '"germany"* "scholarship"*'

    def test_strips_fts_operators(self):
        # FTS5 operators like "AND" or quotes should be neutralized.
        q = _to_fts_query('AND "germany" OR x')
        assert q == '"AND"* "germany"* "OR"*'

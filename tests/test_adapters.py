"""Tests for the RSS adapter (parsing fake feeds)."""
from unittest.mock import MagicMock, patch

from opportunity_mcp.adapters.rss import RSSAdapter
from opportunity_mcp.schema import OpportunityType

_FAKE_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Test Feed</title>
  <link>https://example.com/</link>
  <description>Test</description>
  <item>
    <title>Fully Funded Master's Scholarship in Germany 2027</title>
    <link>https://example.com/posts/germany-scholarship</link>
    <description><![CDATA[<p>Apply by April 30, 2027. This scholarship is fully funded.</p>]]></description>
    <pubDate>Mon, 05 Jan 2026 10:00:00 GMT</pubDate>
    <category>scholarship</category>
    <category>germany</category>
  </item>
  <item>
    <title>UN Internship Program 2027</title>
    <link>https://example.com/posts/un-internship</link>
    <description><![CDATA[<p>An internship opportunity. Deadline: May 15, 2027.</p>]]></description>
    <pubDate>Mon, 05 Jan 2026 10:00:00 GMT</pubDate>
    <category>internship</category>
  </item>
</channel></rss>"""


def test_rss_adapter_parses_entries():
    adapter = RSSAdapter(
        name="test_source",
        homepage="https://example.com/",
        feed_url="https://example.com/feed/",
    )

    fake_response = MagicMock()
    fake_response.content = _FAKE_FEED
    fake_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=fake_response), patch.object(
        adapter, "respects_robots", return_value=True
    ):
        opps = list(adapter.fetch())

    assert len(opps) == 2

    scholarship = next(o for o in opps if "Scholarship" in o.title)
    assert scholarship.type == OpportunityType.SCHOLARSHIP
    assert scholarship.source_site == "test_source"
    assert scholarship.deadline is not None

    internship = next(o for o in opps if "Internship" in o.title)
    assert internship.type == OpportunityType.INTERNSHIP


def test_rss_adapter_skips_when_robots_blocked():
    adapter = RSSAdapter(
        name="blocked",
        homepage="https://example.com/",
        feed_url="https://example.com/feed/",
    )

    with patch.object(adapter, "respects_robots", return_value=False):
        assert list(adapter.fetch()) == []


def test_rss_adapter_handles_http_error():
    import httpx

    adapter = RSSAdapter(
        name="erroring",
        homepage="https://example.com/",
        feed_url="https://example.com/feed/",
    )

    with patch.object(adapter, "respects_robots", return_value=True), patch(
        "httpx.get", side_effect=httpx.ConnectError("boom")
    ):
        assert list(adapter.fetch()) == []


def test_rss_adapter_id_is_stable():
    """The same source+url must produce the same id across runs."""
    adapter = RSSAdapter(
        name="stable",
        homepage="https://example.com/",
        feed_url="https://example.com/feed/",
    )

    fake_response = MagicMock()
    fake_response.content = _FAKE_FEED
    fake_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=fake_response), patch.object(
        adapter, "respects_robots", return_value=True
    ):
        first = list(adapter.fetch())
        second = list(adapter.fetch())

    assert [o.id for o in first] == [o.id for o in second]

# Adapter guide

Adding a source is one of two patterns:

- **RSS site** — one line in `src/opportunity_mcp/adapters/__init__.py`.
- **HTML-only site** — a small subclass of `SourceAdapter`.

Both must respect `robots.txt`.

---

## Adding an RSS source (10 minutes)

1. Verify the feed:
   ```bash
   curl -I https://example.com/feed/
   ```
2. Read `https://example.com/robots.txt` and the site's ToS. Document any concerns in `docs/SOURCES.md`.
3. Append to `SOURCES` in `src/opportunity_mcp/adapters/__init__.py`:
   ```python
   RSSAdapter(
       name="example_site",
       homepage="https://example.com/",
       feed_url="https://example.com/feed/",
   ),
   ```
4. Add a row to `docs/SOURCES.md`.
5. Run the refresh and confirm new opportunities appear:
   ```bash
   uv run opportunity-mcp-refresh --source example_site
   ```
6. Open a PR.

That's it. The generic `RSSAdapter` handles HTTP, robots.txt, parsing, type-classification, deadline-extraction, and ID hashing.

---

## Adding an HTML source

For sites without a feed (e.g. `youthop.com`):

```python
# src/opportunity_mcp/adapters/html_youthop.py
from collections.abc import Iterator
from datetime import datetime, timezone
import hashlib

import httpx
from selectolax.parser import HTMLParser

from ..extract import classify_type, parse_deadline, parse_funding, parse_summary
from ..schema import Opportunity
from .base import SourceAdapter


class YouthOpAdapter(SourceAdapter):
    name = "youthop"
    homepage = "https://www.youthop.com/"

    def fetch(self) -> Iterator[Opportunity]:
        if not self.respects_robots():
            return
        # 1. fetch listing page(s)
        # 2. for each card, extract title + URL + posted date
        # 3. yield Opportunity objects
        ...
```

Then register it:

```python
# src/opportunity_mcp/adapters/__init__.py
from .html_youthop import YouthOpAdapter

SOURCES.append(YouthOpAdapter())
```

### Rules of the road

- **Always check `respects_robots()` first.** It returns `False` if the site disallows the URL — bail out gracefully.
- **Use the shared `USER_AGENT`** so site owners can identify us.
- **Never hammer.** A polite 1-second delay between requests on the same host is plenty.
- **Don't republish.** Summaries are capped at 500 chars; the full article stays at the source.
- **ID stability.** Use `hashlib.sha1(f"{self.name}:{canonical_url}".encode()).hexdigest()[:16]` so re-runs upsert rather than duplicate.

---

## Testing

Add a fixture under `tests/fixtures/` with a real article snippet, then:

```python
def test_youthop_extracts_deadline():
    with open("tests/fixtures/youthop_sample.html") as f:
        html = f.read()
    assert parse_deadline(html) == date(2027, 4, 30)
```

Adapter integration tests should be marked `@pytest.mark.network` and skipped in CI to avoid flake.

---

## Things to watch for

- Feeds that return HTML inside `<content:encoded>` vs `<description>` — `feedparser` handles both, our adapter prefers `content` then falls back to `summary`.
- Sites that 301 redirect from `https://example.com/feed` to `https://www.example.com/feed/` — `httpx` follows redirects by default, so this is fine.
- WordPress feeds that paginate (`/feed/?paged=2`) — current adapter only fetches the first page, which is enough for ~20 most-recent posts. Phase 2 will paginate.

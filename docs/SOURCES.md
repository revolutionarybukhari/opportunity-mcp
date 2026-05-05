# Indexed sources

Every adapter's `fetch()` is gated by a `robots.txt` check. Refresh runs every six hours via GitHub Actions. The HTTP `User-Agent` is `OpportunityMCP/0.1 (+https://github.com/revolutionarybukhari/opportunity-mcp)`; site owners can reach us through the repo for delisting, attribution, or contact.

## Tier 1 — RSS (verified 2026-05-04 against live feeds)

| Source | Homepage | Feed | Items at last verify | Notes |
|---|---|---|---:|---|
| `opportunities_corners` | <https://opportunitiescorners.com/> | `/feed/` | 6 | Permissive `robots.txt`. |
| `opportunities_for_youth` | <https://opportunitiesforyouth.org/> | `/feed/` | 10 | Permissive `robots.txt`. |
| `opportunity_desk` | <https://opportunitydesk.org/> | `/feed/` | 10 | Cloudflare-style content-signals `robots.txt`. Feed serves `200 OK` to a residential IP under our identifying UA but `403 Forbidden` to GitHub Actions runner IPs — see *CI quirks* below. |
| `scholarships_corner` | <https://scholarshipscorner.website/> | `/feed/` | 10 | Permissive `robots.txt`. |
| `opportunities_circle` | <https://www.opportunitiescircle.com/> | `/feed/` | 10 | Disallows only `/wp-admin/`. |

## Tier 2 — RSS, served via `www` redirect

| Source | Homepage | Feed | Items at last verify | Notes |
|---|---|---|---:|---|
| `opportunities_for_africans` | <https://www.opportunitiesforafricans.com/> | `/feed/` | 10 | Disallows only `/wp-admin/`. |
| `scholars4dev` | <https://www.scholars4dev.com/> | `/feed/` | 0 | Feed currently returns the channel header with no `<item>` elements. The adapter is correct; the upstream feed is empty. |

## Tier 3 — HTML adapters (planned)

| Source | Discovery strategy |
|---|---|
| [Youth Opportunities](https://www.youthop.com/) | Crawl `/opportunities` listing pages. |
| [After School Africa](https://www.afterschoolafrica.com/) | Category pages, with the sitemap as a discovery feed. |
| [Scholarships365](https://scholarships365.info/) | Category pages and sitemap. |

## Tier 4 — Curated, single-program official sources (later phases)

| Source | Notes |
|---|---|
| [Fastweb](https://www.fastweb.com/) | US-focused; large database, no public API. |
| [DAAD](https://www2.daad.de/) | Germany; structured search exists. |
| [Chevening](https://www.chevening.org/) | UK government; public scholarship database. |
| [Erasmus+ Opportunities](https://erasmus-plus.ec.europa.eu/opportunities) | EU; structured XML feed for some categories. |
| Schwarzman, Rhodes, Fulbright | Single-program but high-prestige; static pages. |

## CI quirks

`opportunitydesk.org` returns `200` on `/robots.txt` but `403` on `/feed/` to the IP ranges used by GitHub-hosted runners (likely a Cloudflare bot-mode rule). The adapter logs the failure and continues, so the CI-published `index.db` snapshot may exclude those records. Local refreshes from a residential IP collect them normally. If/when this matters operationally we'll move the cron to a fixed egress IP or add a self-hosted runner.

## `robots.txt` handling

Python's stdlib `urllib.robotparser` is over-conservative against Cloudflare-protected hosts: when its default user-agent is challenged with a `403`, it sets `disallow_all = True`, which produces false negatives on permissive sites. The base adapter therefore fetches `robots.txt` with `httpx` using our identifying `User-Agent` and passes the body to `RobotFileParser.parse()`. If the file is unreachable, the adapter proceeds; the actual feed request will surface any real block.

## Operating principles

1. **`robots.txt` is law.** If a site adds a `Disallow` for a path we fetch, the adapter stops fetching it — that is the correct behavior, not a bug.
2. **Polite identification.** The HTTP `User-Agent` contains the project URL so a maintainer can be contacted.
3. **Conservative refresh cadence.** Sources are polled every six hours, not on user query.
4. **Always link back.** Stored summaries are capped at 500 characters; every record links back to the originating article. The project is an aggregator, not a competitor for the source's traffic.
5. **Source removal on request.** Honored within 24 hours, with no negotiation. Email or open an issue.

# Indexed sources

Every adapter's `fetch()` is gated by `robots.txt` (per-URL `respects_robots()` check). Refresh cadence is every 6 hours via GitHub Actions. The `User-Agent` is `OpportunityMCP/0.1 (+https://github.com/opportunity-mcp/opportunity-mcp)`; site owners can reach us at the repo for delisting / attribution / contact.

## Tier 1 — RSS (verified on 2026-05-04 against live feeds)

| Source | Homepage | Feed | Live items | Notes |
|---|---|---|---|---|
| `opportunities_corners` | https://opportunitiescorners.com/ | `/feed/` | 6 | Permissive robots.txt |
| `opportunities_for_youth` | https://opportunitiesforyouth.org/ | `/feed/` | 10 | Permissive robots.txt |
| `opportunity_desk` | https://opportunitydesk.org/ | `/feed/` | 10 | Cloudflare-style content-signals robots.txt; fetched with our identifying UA |
| `scholarships_corner` | https://scholarshipscorner.website/ | `/feed/` | 10 | Permissive robots.txt |
| `opportunities_circle` | https://www.opportunitiescircle.com/ | `/feed/` | 10 | Disallows only `/wp-admin/` |

## Tier 2 — RSS via www redirect

| Source | Homepage | Feed | Live items | Notes |
|---|---|---|---|---|
| `opportunities_for_africans` | https://www.opportunitiesforafricans.com/ | `/feed/` | 10 | Disallows only `/wp-admin/` |
| `scholars4dev` | https://www.scholars4dev.com/ | `/feed/` | 0 | Feed currently returns channel header with no `<item>` elements; adapter is correct, source is empty |

> Sites under Cloudflare or similar bot protection 403 the Python stdlib `urllib` user-agent on `robots.txt`. The base adapter therefore fetches `robots.txt` with `httpx` using our identifying User-Agent and feeds the body to `urllib.robotparser`. If `robots.txt` is unreachable, we proceed; the actual feed/page request will surface real blocks.

## Tier 3 — HTML scraping required (planned)

| Source | Strategy |
|---|---|
| Youth Opportunities (`youthop.com`) | Scrape `/opportunities` listing pages |
| After School Africa | Scrape category pages; sitemap as discovery feed |
| Scholarships365 | Same as above |

## Tier 4 — Curated official sources (later phases)

- **Fastweb** (US-focused)
- **DAAD** (Germany)
- **Chevening** (UK)
- **Erasmus+ Opportunities** (EU)
- **Schwarzman / Rhodes / Fulbright** (single-program, high-prestige)

## Operating principles

1. **`robots.txt` is law.** If a site adds a `Disallow`, our adapter stops working — that's correct behavior.
2. **Polite identification.** UA contains a contact URL.
3. **Conservative refresh.** Every 6h is plenty.
4. **Always link back.** Title + ≤500-char summary + deadline + apply link is the threshold for "aggregator", not "competitor". We never republish full article bodies.
5. **Source removal on request** within 24h, no negotiation.

# Reads v2.2 — Growth Engine

v2.2 turns the existing football, personalization, community, live and production stack into a growth system designed to help people discover Reads and bring other football fans with them.

## SEO engine

`build_seo.py` creates dynamic SEO records for verified football entities and generates XML sitemaps.

The shipped build contains:
- 7,277 NFL player pages
- 109,221 college-football player pages
- 108 canonical school pages
- 32 NFL franchise pages
- 116,638 total indexable entity pages
- 4,552 verified internal entity links
- three sitemap shards plus a sitemap index

Each page API payload includes:
- title
- meta description
- canonical URL
- JSON-LD WebPage data
- entity payload
- graph-backed internal links
- relevant playable puzzle IDs when available

Pages are dynamic data objects; the frontend can render them using the existing Reads design.

## Share engine

`growth_engine.py` supports:
- general share artifacts
- spoiler-safe Daily results
- challenge shares
- deep links
- click attribution
- share/install/signup counters

`share_card_renderer.py` turns a stored share artifact into an SVG result card. The default card is intentionally simple so your production frontend/design system can restyle it.

## Daily virality

Daily results can produce Wordle-style spoiler-safe blocks without exposing answers.

Example payload:
- score
- streak
- correct/incorrect grid
- Reads deep link
- no answer text

## Challenge links

A challenge can be frozen by the existing retention system and wrapped in a short viral link. The recipient gets the same challenge ID/puzzle set rather than a newly randomized game.

## Referrals

Referral infrastructure includes:
- owner referral codes
- first-touch attribution
- source / medium / campaign
- signup / qualification timestamps
- revenue attribution field
- milestone reward rules

Default non-cash cosmetic milestones are seeded for 3, 10 and 25 qualified referrals. They do not grant paid value automatically.

## Creator discovery

`creator_discovery_scores` ranks creators using:
- play volume
- likes
- quality
- completion quality
- follower signal
- report penalties

This is separate from the existing creator leaderboard, so discovery can favor high-quality emerging creators instead of only all-time volume.

## Growth experiments

Deterministic A/B assignment is included. A subject receives the same variant on repeat visits, and assignments are stored for analysis.

## Social content queue

`social_content_queue` can stage Daily promos, challenge promos, creator highlights or live-event hooks for later publishing to social channels. v2.2 does not pretend to be connected to TikTok, Instagram, X or YouTube without real credentials.

## Growth API

Run:

```bash
python growth_api.py
```

Default port: `8794`.

Core endpoints:
- `GET /v2.2/seo/page?slug=...`
- `GET /v2.2/growth/metrics`
- `POST /v2.2/referral`
- `POST /v2.2/referral/attribute`
- `POST /v2.2/share`
- `POST /v2.2/share/daily`
- `POST /v2.2/share/challenge`
- `POST /v2.2/track`

Open `growth_dashboard.html` for a lightweight internal control surface.

## Search deployment

The package generates sitemap files under `seo_output/`. Your production web server should expose the sitemap index and dynamic entity routes at the canonical Reads URLs.

SEO traffic is never guaranteed. The engine supplies technically indexable, internally linked pages; ranking still depends on search-engine crawling, content quality, authority and user demand.

## UI rule

v2.2 is another backend/growth layer. It does not require changing the current Reads design or personalization effects.

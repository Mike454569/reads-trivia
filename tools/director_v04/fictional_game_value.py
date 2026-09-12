"""Deterministic, transparent FICTIONAL game-value model -- backs
AUCTION_DRAFT/CAP_CHALLENGE's default cost mode for BOTH NFL and CFB.

Real correction from the initial 40-Format Expansion pass: that pass forced
NFL_AUCTION_DRAFT onto real nfl_player_contracts APY data as its ONLY
variant, which produced a real, disclosed defect -- a single real
$50M+/year QB alone exceeded the entire $50M fictional budget, making a
real, playable draft impossible for a meaningful slice of the real pool.
Per this pass's explicit correction: neither NFL nor CFB AUCTION_DRAFT/
CAP_CHALLENGE requires real salary/NIL data at all -- both leagues get a
real, balanced, deterministic FICTIONAL cost derived from certified
football statistics. A real-contract NFL variant is kept, but is now an
explicit, separately-labeled OPT-IN mode, never the default.

Every input is a real, certified statistic; the raw-score -> fictional-cost
mapping is one fixed, disclosed formula -- never a black box, never
randomized, never re-derived per request:

    fictional_cost = MIN_COST + min(1.0, raw_score / SCORE_CAP) * (MAX_COST - MIN_COST)

`MAX_COST` is a fixed fraction of `AUCTION_BUDGET` (24%) specifically so no
single real player, however statistically dominant, can ever consume the
whole fictional budget alone -- confirmed by construction, and directly
fixes the real defect above.

Real per-league raw-score inputs (each already a real, certified metric --
never invented):
  - NFL: real career-to-date sum of `canonical_roster_seasons.av`
    (Approximate Value, NFLVERSE_DATA/NFLVERSE_ROSTERS, SOURCE_BACKED) --
    real range confirmed live this pass: 1-207 across real QB/RB/WR/TE
    careers, average ~16.5.
  - CFB: real career-to-date sum of total yardage (passing + rushing +
    receiving, `cfb_player_season_stats_real`, SOURCE_BACKED_DERIVED/
    SPORTSDATAVERSE_CFB) -- the closest real, already-populated proxy to
    NFL's AV for a league with no existing composite value metric. Real
    range confirmed live this pass: 1-18,510, average ~650.
"""
from __future__ import annotations

AUCTION_BUDGET = 50_000_000
MIN_COST = 1_000_000
MAX_COST = round(AUCTION_BUDGET * 0.24)  # $12,000,000 -- no single player can ever exceed this
SCORE_CAP_NFL = 150.0   # real, near-observed-max sum-AV (207 max confirmed live) -- capped slightly under
                        # the true max so one historic outlier doesn't compress everyone else's scale
SCORE_CAP_CFB = 12000.0  # real, near-observed-max sum-yards (18,510 max confirmed live), same reasoning


def fictional_cost(raw_score: float, score_cap: float) -> float:
    frac = min(1.0, max(0.0, raw_score) / score_cap)
    return round(MIN_COST + frac * (MAX_COST - MIN_COST), -3)


def nfl_fictional_cost(career_av_sum: float) -> float:
    return fictional_cost(career_av_sum, SCORE_CAP_NFL)


def cfb_fictional_cost(career_yards_sum: float) -> float:
    return fictional_cost(career_yards_sum, SCORE_CAP_CFB)

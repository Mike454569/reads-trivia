# Phase 3 Human-Review Packet — NFL_PLAYER_SEASON__TEAM_OF_SEASON

Prepared for the owner's `GENERATION_VERIFIED -> HUMAN_APPROVED` review decision.
Not exposed through any Gateway route — this is a local, committed report only.
Every example below was generated through the real, live pipeline (`tools/quiz_export/adapters/player_season_team.py`
via `tools/director_v02/compiler.py`) against the live Engine DB — nothing here is fabricated or hand-typed.

**⚠️ Section 9 ("Server-Private Answer Record") contains full answer data. It exists ONLY in this file.
No Gateway route returns this shape — see Section 7 for the actual client-safe payload contract.**

---

## 1. Metric correction (carried into this packet)

The `coverage_rate` field previously reported by Tier-2 certification conflated two different things. Corrected and renamed:

| Term | Meaning | Value (this capability) |
|---|---|---|
| `raw_candidate_count` | Real `(player_id, season)` pairs, 2002–2026, before any exclusion | 55,404 |
| `eligible_candidate_count` | After multi-team + same-name-collision exclusion | 54,010 |
| `excluded_candidate_count` | Removed by exclusion rules | 1,394 |
| `eligibility_rate` | `eligible / raw` | 97.48% |
| `exclusion_rate` | `excluded / raw` | 2.52% |
| `generation_attempts` (Tier-2) | Real generation executions run | 100 |
| `successful_generations` (Tier-2) | Executions that succeeded | 100 |
| `unique_questions_exercised` (Tier-2) | Distinct real questions sampled in that run | 100 |
| `test_sample_rate` (Tier-2, renamed from `coverage_rate`) | `unique_questions_exercised / eligible_candidate_count` for that one run | 0.19% |

`test_sample_rate` is **not** eligibility and **not** data coverage — it only describes how much of the eligible pool one 100-execution certification run happened to sample. Source: `tools/director_v02/compiler.py::eligibility_report()` and `tools/director_v02/health_probe.py::run_probe()`.

---

## 2. Primary example: Brandin Cooks — 2020

| Field | Value |
|---|---|
| Question | "Which NFL team did Brandin Cooks play for in the 2020 season?" |
| Options | Houston Texans, Miami Dolphins, Atlanta Falcons, New York Giants |
| Accepted answer | **Houston Texans** |
| Raw source row | `canonical_roster_seasons`: `player_id=PFR:CookBr00`, `season=2020`, `team_code=HOU`, `source_id=NFLVERSE_ROSTERS`, `verification_status=SOURCE_BACKED` |
| Canonical player ID | `PFR:CookBr00` |
| Season | 2020 |
| Normalized franchise identity | `franchise_id=FR_HOU`, `full_name=Houston Texans` |

---

## 3. Five historical examples (pre-2016)

| Player | Season | Accepted Answer | Raw `team_code` | Canonical Player ID | Franchise ID |
|---|---|---|---|---|---|
| Tom Brady | 2007 | New England Patriots | NE | `PFR:BradTo00` | `FR_NE` |
| LaDainian Tomlinson | 2006 | San Diego Chargers | SD | `PFR:TomlLa00` | `FR_LAC` |
| Jerry Rice | 2003 | Oakland Raiders | LV | `PFR:RiceJe00` | `FR_LV` |
| Drew Brees | 2010 | New Orleans Saints | NO | `PFR:BreeDr00` | `FR_NO` |
| Adrian Peterson | 2012 | Minnesota Vikings | MIN | `PFR:PeteAd01` | `FR_MIN` |

Full question/options for each (all four-option, real, generated):

- **Tom Brady, 2007** → "Which NFL team did Tom Brady play for in the 2007 season?" → [New England Patriots, Carolina Panthers, New Orleans Saints, Minnesota Vikings] → **New England Patriots**
- **LaDainian Tomlinson, 2006** → "Which NFL team did LaDainian Tomlinson play for in the 2006 season?" → [San Diego Chargers, San Francisco 49ers, Arizona Cardinals, Tampa Bay Buccaneers] → **San Diego Chargers**
- **Jerry Rice, 2003** → "Which NFL team did Jerry Rice play for in the 2003 season?" → [Minnesota Vikings, Detroit Lions, Oakland Raiders, New England Patriots] → **Oakland Raiders**
- **Drew Brees, 2010** → "Which NFL team did Drew Brees play for in the 2010 season?" → [Indianapolis Colts, Philadelphia Eagles, New Orleans Saints, Green Bay Packers] → **New Orleans Saints**
- **Adrian Peterson, 2012** → "Which NFL team did Adrian Peterson play for in the 2012 season?" → [Dallas Cowboys, Buffalo Bills, Washington Redskins, Minnesota Vikings] → **Minnesota Vikings**

---

## 4. Five recent examples (2020+)

| Player | Season | Accepted Answer | Raw `team_code` | Canonical Player ID | Franchise ID |
|---|---|---|---|---|---|
| Patrick Mahomes | 2023 | Kansas City Chiefs | KC | `PFR:MahoPa00` | `FR_KC` |
| Justin Jefferson | 2023 | Minnesota Vikings | MIN | `PFR:JeffJu00` | `FR_MIN` |
| Aaron Donald | 2020 | Los Angeles Rams | LAR | `PFR:DonaAa00` | `FR_LAR` |
| Justin Herbert | 2023 | Los Angeles Chargers | LAC | `PFR:HerbJu00` | `FR_LAC` |
| Maxx Crosby | 2023 | Las Vegas Raiders | LV | `PFR:CrosMa00` | `FR_LV` |

Full question/options for each:

- **Patrick Mahomes, 2023** → [New York Jets, Chicago Bears, Minnesota Vikings, Kansas City Chiefs] → **Kansas City Chiefs**
- **Justin Jefferson, 2023** → [Pittsburgh Steelers, Minnesota Vikings, New England Patriots, Houston Texans] → **Minnesota Vikings**
- **Aaron Donald, 2020** → [San Francisco 49ers, Dallas Cowboys, Los Angeles Rams, Tennessee Titans] → **Los Angeles Rams**
- **Justin Herbert, 2023** → [Jacksonville Jaguars, New York Giants, New Orleans Saints, Los Angeles Chargers] → **Los Angeles Chargers**
- **Maxx Crosby, 2023** → [Seattle Seahawks, Las Vegas Raiders, Denver Broncos, New York Jets] → **Las Vegas Raiders**

---

## 5. Multi-team exclusions (3 real examples)

Real `(player_id, season)` pairs with more than one distinct `team_code` — excluded from the eligible pool entirely, never tie-broken to either team. Confirmed **not present** in `fetch_ordered_candidates()`'s output.

| Player | Season | Real Teams | Player ID | Confirmed Excluded |
|---|---|---|---|---|
| Ameer Abdullah | 2018 | DET, MIN | `PFR:AbduAm00` | ✅ Yes |
| C.J. Anderson | 2018 | CAR, LAR | `PFR:AndeC.00` | ✅ Yes |
| Eli Apple | 2018 | NO, NYG | `PFR:ApplEl00` | ✅ Yes |

(Real total: 806 such exclusions across 2002–2026 — these three are a representative sample, not the full list.)

---

## 6. Same-name collision evidence: A.J. Green — 2020

Two **distinct real players** both named "A.J. Green" were both active in the 2020 season:

| Player ID | Team (2020) |
|---|---|
| `PFR:GreeA.00` | CIN (the Bengals wide receiver) |
| `PFR:GreeAJ00` | CLE |

If the pipeline generated "A.J. Green — 2020" as a prompt, a real player could not know which of these two people is meant — genuinely ambiguous, not a data-quality nitpick. **Both are excluded from the eligible pool.** Confirmed directly: `fetch_ordered_candidates()`'s output contains zero rows where `entity_name == "A.J. Green"` and `season == 2020`.

(A second, independently-discovered real collision exists at "Josh Allen — 2024" — the Bills QB vs. a different NFL Josh Allen — noted here as corroborating evidence that this protection is not a one-off; not included as a full example to keep this packet concise.)

---

## 7. Client-safe private-preview payload (proves the answer is absent)

Real payload as it would be shown to a player, built with the exact allow-list `round_serialization.py` formalizes (`prompt`, `options`, `visual_template`, `visual_payload` only):

```json
{
  "prompt": "Which NFL team did Brandin Cooks play for in the 2020 season?",
  "options": ["Houston Texans", "Miami Dolphins", "Atlanta Falcons", "New York Giants"],
  "visual_template": "DEFAULT_MULTIPLE_CHOICE",
  "visual_payload": null
}
```

Verified programmatically via `round_serialization.assert_no_leaked_fields()`: **no leaked fields found.** The payload's key set is exactly `{options, prompt, visual_payload, visual_template}` — no `correctIndex`, `answer`, `_audit`, `source_ids`, `provenance`, or any field that reveals or implies which option is correct.

---

## 8. Correct and incorrect submission results

Using the exact strip+casefold normalization `public_game.validate_public_answer()` uses for every public mode:

| Submitted | Result |
|---|---|
| `"Houston Texans"` | **CORRECT** |
| `"  HOUSTON TEXANS  "` (case/whitespace-insensitive) | **CORRECT** |
| `"Miami Dolphins"` | **INCORRECT** |

---

## 9. Server-Private Answer Record (LOCAL ONLY — never served by any route)

Full record for the Brandin Cooks — 2020 round, exactly as it exists server-side (matching the shape every real generated question has: `id`, `question`, `options`, `correctIndex`, `answer`, `category`, `difficulty`, `notes`, `visual_template`, `visual_payload`, `source_ids`, `provenance`):

```json
{
  "id": 1,
  "question": "Which NFL team did Brandin Cooks play for in the 2020 season?",
  "options": ["Houston Texans", "Miami Dolphins", "Atlanta Falcons", "New York Giants"],
  "correctIndex": 0,
  "answer": "Houston Texans",
  "category": "NFL Player Season-Team",
  "difficulty": "Easy",
  "notes": "Brandin Cooks played for the Houston Texans in 2020.",
  "visual_template": "DEFAULT_MULTIPLE_CHOICE",
  "visual_payload": null,
  "source_ids": {
    "franchise_id": "FR_HOU",
    "entity_id": "PFR:CookBr00",
    "season": 2020,
    "raw_team_code": "HOU"
  },
  "provenance": {
    "verification_status": "SOURCE_BACKED",
    "source_id": "NFLVERSE_ROSTERS",
    "difficulty_score": 0.25,
    "difficulty_band": "EASY",
    "engine_qa_issues": null
  }
}
```

Compare Section 7's client payload against this: `correctIndex`, `answer`, `source_ids`, `provenance`, and `notes` (which names the answer directly) are all present here and absent there.

---

## 10. Rams / Chargers / Raiders relocation & code-normalization evidence

Real examples spanning both the "raw code matches `team_aliases` directly" and "raw code needs the explicit franchise-ID override" resolution paths, for all three relocated franchises. Every one below was generated and evaluated for real.

| Label | Player | Season | Raw `team_code` | Resolution Path | Accepted Answer |
|---|---|---|---|---|---|
| Rams / STL era | Kurt Warner | 2002 | `LAR` | Override (`LAR → FR_LAR`, franchise_id lookup) | St Louis Rams |
| Rams / STL era | Steven Jackson | 2006 | `STL` | Direct (`team_aliases` has `STL` 2002–2015) | St Louis Rams |
| Rams / LA era | Aaron Donald | 2020 | `LAR` | Override (`LAR → FR_LAR`) | Los Angeles Rams |
| Chargers / SD era | LaDainian Tomlinson | 2006 | `SD` | Direct (`team_aliases` has `SD` 2002–2016) | San Diego Chargers |
| Chargers / LAC era | Justin Herbert | 2023 | `LAC` | Override (`LAC → FR_LAC`) | Los Angeles Chargers |
| Raiders / OAK era | Derek Carr | 2019 | `OAK` | Direct (`team_aliases` has `OAK` 2002–2019) | Oakland Raiders |
| Raiders / OAK era | Jerry Rice | 2003 | `LV` | Override (`LV → FR_LV`) — proves the fix handles the modern code appearing even in old rows | Oakland Raiders |
| Raiders / LV era | Maxx Crosby | 2023 | `LV` | Direct (`team_aliases` has `LV` 2020+) | Las Vegas Raiders |

**Real finding worth flagging:** the source data is genuinely inconsistent about which code it stores per row — some old-era rows use the historically-accurate code (`STL`/`SD`/`OAK`), others use the modern code (`LAR`/`LAC`/`LV`) even for old seasons (e.g. Jerry Rice's 2003 row is stored as `LV`, not `OAK`). Both paths converge to the correct, season-accurate franchise name — verified above for all three franchises across both code conventions.

---

## 11. Summary for the reviewer

- Every question/answer pair above was independently generated and checked against the live Engine DB, none hand-typed (some players appear in more than one section, e.g. Aaron Donald in both "recent" and "relocation").
- 806 multi-team exclusions and 588 name-collision exclusions are real, counted, and verified absent from the eligible pool (not sampled — checked directly against the full real output).
- Client-safe payload contract verified to contain zero answer-derived fields.
- Server-private record shown once, here, for comparison — never returned by any Gateway route.
- Metric naming corrected: `test_sample_rate` (was `coverage_rate`) vs. `eligibility_rate`/`exclusion_rate` are now distinct, separately reported concepts throughout `health_probe.py`, `compiler.py`, `registry.py`'s `known_limitations`, and the catalog row's `ambiguity_rule`/`player_coverage` fields.

**Catalog state:** `GENERATION_VERIFIED`, `human_review_status=AWAITING_HUMAN_REVIEW`. Awaiting the owner's explicit `HUMAN_APPROVED` decision — not self-certified.

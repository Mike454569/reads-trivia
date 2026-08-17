# Phase 3 Human-Review Packet — NFL_PLAYER_SEASON__TEAM_OF_SEASON

Prepared for the owner's `GENERATION_VERIFIED -> HUMAN_APPROVED` review decision.
Not exposed through any Gateway route — this is a local, committed report only.
Every example below was generated through the real, live pipeline (`tools/quiz_export/adapters/player_season_team.py`
via `tools/director_v02/compiler.py`) against the live Engine DB — nothing here is fabricated or hand-typed.

**Revision 2** (this version): corrects the question wording and adds evidence-type/season-status semantics per the
owner's Phase 3 closeout review. Revision 1's factual, identity, relocation, exclusion, and security findings all
still hold — only the wording and the eligible-pool figures (recalculated for future-season gating) changed.

**⚠️ Section 10 ("Server-Private Answer Record") contains full answer data. It exists ONLY in this file.
No Gateway route returns this shape — see Section 8 for the actual client-safe payload contract.**

---

## 1. Semantic correction: roster membership, not game participation

`canonical_roster_seasons` proves **season-level roster membership** — it does **not** prove the player actually
appeared in a game. The generated wording and internal evidence type now reflect exactly that, never more:

| Evidence type | Meaning | Wording it may use |
|---|---|---|
| `ROSTER_MEMBERSHIP` | This capability's evidence today — a real roster record for that season, nothing about games played | "was/is **ON**" |
| `GAME_PARTICIPATION` | Would require joining a real per-game appearance source for this entity — **not done here** | "played" — reserved for a future capability that actually joins that evidence |
| `STARTED_GAME` | A strictly narrower claim than `GAME_PARTICIPATION` (a starting-lineup record) — **not done here** | reserved, same rule |

**Old (incorrect) wording:** *"Which NFL team did {player} play for in the {season} season?"*
**New (corrected) wording:**
- Completed season: **"Which NFL team was {player} on during the {season} season?"**
- Active/in-progress season: **"Which NFL team is {player} on for the {season} season?"**

`evidence_type` is stored internally (`_audit.evidence_type`) and exposed in the server-side package's `provenance.evidence_type` field (additive to `game_director_v01.py`'s shared export shape; `null` for every other capability that doesn't set it). Every generated round for this capability has `evidence_type == "ROSTER_MEMBERSHIP"`, always — this capability never claims a stronger evidence type than its actual join proves.

---

## 2. Season completeness — real, measured, self-correcting

A season's status is measured live against `player_game_stats`' real regular-season (`season_type='REG'`) week rows — **never** wall-clock date:

| Status | Real signal | Pool treatment | Wording tense |
|---|---|---|---|
| `FUTURE` | Zero real `REG` week rows for that season | **Excluded from the pool entirely** — never a completed-season fact | n/a |
| `ACTIVE` | 1–16 real `REG` weeks recorded | Included | Present tense ("is on ... for") |
| `COMPLETE` | 17+ real `REG` weeks recorded (the verified real floor for every season 2002–2025) | Included | Past tense ("was on ... during") |

This is a live query, not a hardcoded date — as real weekly data is refreshed by the normal data pipeline, a season automatically moves `FUTURE -> ACTIVE -> COMPLETE` with zero code changes.

**Real, current state (as of this review):**
- Seasons 2002–2025: all `COMPLETE` (every one independently confirmed to have 17 or 18 real regular-season weeks on record).
- Season 2026: `FUTURE` — **zero** real `player_game_stats` REG rows exist for it yet, even though 2,930 raw roster rows already exist in `canonical_roster_seasons` (a preseason/training-camp snapshot). All 2,930 are excluded from the eligible pool. Confirmed directly: zero season=2026 rows appear in `fetch_ordered_candidates()`'s output.
- No season is currently `ACTIVE` (mid-progress) in the real data. The `ACTIVE` code path was verified directly using real, temporary weekly-evidence rows for a disposable season number (inserted and cleaned up within a single test) — see `gateway/tests/test_phase3_player_season_team.py::test_season_status_detects_active_from_real_partial_weekly_evidence` and `::test_phrase_membership_question_is_tense_correct_and_never_says_played_for`. The pure wording function, called directly:
  - `_phrase_membership_question(..., season_status="ACTIVE")` → `"Which NFL team is Test Player on for the 2026 season?"`
  - `_phrase_membership_question(..., season_status="COMPLETE")` → `"Which NFL team was Test Player on during the 2020 season?"`

---

## 3. Recalculated eligible pool

| Term | Value (Revision 1) | Value (Revision 2, this document) |
|---|---|---|
| `raw_candidate_count` | 55,404 | 55,404 (unchanged — a fact about the raw data) |
| `eligible_candidate_count` | 54,010 | **51,104** |
| `excluded_candidate_count` | 1,394 | **4,300** |
| `eligibility_rate` | 97.48% | **92.24%** |
| `exclusion_rate` | 2.52% | **7.76%** |
| — multi_team_exclusions | 806 | 806 (unchanged) |
| — name_collision_exclusions | 588 | 588 (unchanged) |
| — future_season_exclusions | *(did not exist)* | **2,906** (new — season 2026) |

`generation_attempts`/`successful_generations`/`unique_questions_exercised`/`test_sample_rate` (Tier-2 certification, re-run against the corrected pool): 100 / 100 / 100 / 0.20% — all pass, confirmed via a fresh full 22-capability sweep.

Source: `tools/director_v02/compiler.py::eligibility_report()` / `tools/quiz_export/adapters/player_season_team.py::eligibility_report()`, live.

---

## 4. Primary example: Brandin Cooks — 2020

| Field | Value |
|---|---|
| Question | **"Which NFL team was Brandin Cooks on during the 2020 season?"** |
| Options | Seattle Seahawks, Arizona Cardinals, Houston Texans, New York Giants |
| Accepted answer | **Houston Texans** |
| Raw source row | `canonical_roster_seasons`: `player_id=PFR:CookBr00`, `season=2020`, `team_code=HOU`, `source_id=NFLVERSE_ROSTERS`, `verification_status=SOURCE_BACKED` |
| Canonical player ID | `PFR:CookBr00` |
| Season | 2020 |
| Normalized franchise identity | `franchise_id=FR_HOU`, `full_name=Houston Texans` |
| Evidence type | `ROSTER_MEMBERSHIP` |
| Season status | `COMPLETE` |

---

## 5. Five historical examples (pre-2016)

All `COMPLETE` season status, `ROSTER_MEMBERSHIP` evidence type.

| Player | Season | Question | Accepted Answer | Raw `team_code` | Canonical Player ID |
|---|---|---|---|---|---|
| Tom Brady | 2007 | "Which NFL team was Tom Brady on during the 2007 season?" | New England Patriots | NE | `PFR:BradTo00` |
| LaDainian Tomlinson | 2006 | "Which NFL team was LaDainian Tomlinson on during the 2006 season?" | San Diego Chargers | SD | `PFR:TomlLa00` |
| Jerry Rice | 2003 | "Which NFL team was Jerry Rice on during the 2003 season?" | Oakland Raiders | LV | `PFR:RiceJe00` |
| Drew Brees | 2010 | "Which NFL team was Drew Brees on during the 2010 season?" | New Orleans Saints | NO | `PFR:BreeDr00` |
| Adrian Peterson | 2012 | "Which NFL team was Adrian Peterson on during the 2012 season?" | Minnesota Vikings | MIN | `PFR:PeteAd01` |

---

## 6. Five recent examples (2020+)

All `COMPLETE` season status, `ROSTER_MEMBERSHIP` evidence type (2020–2023 all independently confirmed 17–18 real regular-season weeks on record).

| Player | Season | Question | Accepted Answer | Raw `team_code` | Canonical Player ID |
|---|---|---|---|---|---|
| Patrick Mahomes | 2023 | "Which NFL team was Patrick Mahomes on during the 2023 season?" | Kansas City Chiefs | KC | `PFR:MahoPa00` |
| Justin Jefferson | 2023 | "Which NFL team was Justin Jefferson on during the 2023 season?" | Minnesota Vikings | MIN | `PFR:JeffJu00` |
| Aaron Donald | 2020 | "Which NFL team was Aaron Donald on during the 2020 season?" | Los Angeles Rams | LAR | `PFR:DonaAa00` |
| Justin Herbert | 2023 | "Which NFL team was Justin Herbert on during the 2023 season?" | Los Angeles Chargers | LAC | `PFR:HerbJu00` |
| Maxx Crosby | 2023 | "Which NFL team was Maxx Crosby on during the 2023 season?" | Las Vegas Raiders | LV | `PFR:CrosMa00` |

**Note:** season 2024/2025 are also `COMPLETE` in the real data and would use identical past-tense wording; 2023 was used above for recognizable, verifiable examples.

---

## 7. Multi-team exclusions (3 real examples)

Real `(player_id, season)` pairs with more than one distinct `team_code` — excluded from the eligible pool entirely, never tie-broken to either team. Confirmed **not present** in `fetch_ordered_candidates()`'s output.

| Player | Season | Real Teams | Player ID | Confirmed Excluded |
|---|---|---|---|---|
| Ameer Abdullah | 2018 | DET, MIN | `PFR:AbduAm00` | ✅ Yes |
| C.J. Anderson | 2018 | CAR, LAR | `PFR:AndeC.00` | ✅ Yes |
| Eli Apple | 2018 | NO, NYG | `PFR:ApplEl00` | ✅ Yes |

(Real total: 806 such exclusions across 2002–2026 — these three are a representative sample, not the full list.)

---

## 8. Same-name collision evidence: A.J. Green — 2020

Two **distinct real players** both named "A.J. Green" were both active in the 2020 season:

| Player ID | Team (2020) |
|---|---|
| `PFR:GreeA.00` | CIN (the Bengals wide receiver) |
| `PFR:GreeAJ00` | CLE |

If the pipeline generated "A.J. Green — 2020" as a prompt, a real player could not know which of these two people is meant — genuinely ambiguous, not a data-quality nitpick. **Both are excluded from the eligible pool.** Confirmed directly: `fetch_ordered_candidates()`'s output contains zero rows where `entity_name == "A.J. Green"` and `season == 2020`.

(A second, independently-discovered real collision exists at "Josh Allen — 2024" — the Bills QB vs. a different NFL Josh Allen — noted here as corroborating evidence that this protection is not a one-off.)

---

## 9. Future-season exclusion evidence: season 2026

| Signal | Value |
|---|---|
| Real `player_game_stats` REG week rows for 2026 | **0** |
| Raw `canonical_roster_seasons` rows for 2026 | 2,930 (a real preseason/training-camp roster snapshot) |
| Computed `season_status(2026)` | `FUTURE` |
| Any 2026 rows in the eligible pool | **No** — confirmed directly, zero |

This is the concrete case the owner's correction targets: a real roster snapshot exists, but with zero verified regular-season evidence, it is never presented as a completed-season fact. As soon as the 2026 regular season begins and real weekly data is ingested by the normal data-refresh pipeline, this reclassifies automatically (`FUTURE -> ACTIVE -> COMPLETE`) with no code change.

---

## 10. Client-safe private-preview payload (proves the answer is absent)

Real payload as it would be shown to a player, built with the exact allow-list `round_serialization.py` formalizes (`prompt`, `options`, `visual_template`, `visual_payload` only):

```json
{
  "prompt": "Which NFL team was Brandin Cooks on during the 2020 season?",
  "options": ["Seattle Seahawks", "Arizona Cardinals", "Houston Texans", "New York Giants"],
  "visual_template": "DEFAULT_MULTIPLE_CHOICE",
  "visual_payload": null
}
```

Verified programmatically via `round_serialization.assert_no_leaked_fields()`: **no leaked fields found.** The payload's key set is exactly `{options, prompt, visual_payload, visual_template}` — no `correctIndex`, `answer`, `_audit`, `source_ids`, `provenance`, or `evidence_type`.

---

## 11. Correct and incorrect submission results

Using the exact strip+casefold normalization `public_game.validate_public_answer()` uses for every public mode:

| Submitted | Result |
|---|---|
| `"Houston Texans"` | **CORRECT** |
| `"  HOUSTON TEXANS  "` (case/whitespace-insensitive) | **CORRECT** |
| `"Seattle Seahawks"` | **INCORRECT** |

---

## 12. Server-Private Answer Record (LOCAL ONLY — never served by any route)

Full record for the Brandin Cooks — 2020 round, exactly as it exists server-side:

```json
{
  "id": 1,
  "question": "Which NFL team was Brandin Cooks on during the 2020 season?",
  "options": ["Seattle Seahawks", "Arizona Cardinals", "Houston Texans", "New York Giants"],
  "correctIndex": 2,
  "answer": "Houston Texans",
  "category": "NFL Player Season-Team",
  "difficulty": "Easy",
  "notes": "Brandin Cooks was on the Houston Texans roster during the 2020 season.",
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
    "engine_qa_issues": null,
    "evidence_type": "ROSTER_MEMBERSHIP"
  }
}
```

Compare Section 10's client payload against this: `correctIndex`, `answer`, `source_ids`, `provenance` (including the new `evidence_type` field), and `notes` (which names the answer directly) are all present here and absent there.

---

## 13. Rams / Chargers / Raiders relocation & code-normalization evidence

Real examples spanning both the "raw code matches `team_aliases` directly" and "raw code needs the explicit franchise-ID override" resolution paths, for all three relocated franchises. Every one below was generated and evaluated for real, with the corrected wording.

| Label | Player | Season | Raw `team_code` | Resolution Path | Question | Accepted Answer |
|---|---|---|---|---|---|---|
| Rams / STL era | Kurt Warner | 2002 | `LAR` | Override (`LAR → FR_LAR`) | "...was Kurt Warner on during the 2002 season?" | St Louis Rams |
| Rams / STL era | Steven Jackson | 2006 | `STL` | Direct (`team_aliases` has `STL` 2002–2015) | "...was Steven Jackson on during the 2006 season?" | St Louis Rams |
| Rams / LA era | Aaron Donald | 2020 | `LAR` | Override (`LAR → FR_LAR`) | "...was Aaron Donald on during the 2020 season?" | Los Angeles Rams |
| Chargers / SD era | LaDainian Tomlinson | 2006 | `SD` | Direct (`team_aliases` has `SD` 2002–2016) | "...was LaDainian Tomlinson on during the 2006 season?" | San Diego Chargers |
| Chargers / LAC era | Justin Herbert | 2023 | `LAC` | Override (`LAC → FR_LAC`) | "...was Justin Herbert on during the 2023 season?" | Los Angeles Chargers |
| Raiders / OAK era | Derek Carr | 2019 | `OAK` | Direct (`team_aliases` has `OAK` 2002–2019) | "...was Derek Carr on during the 2019 season?" | Oakland Raiders |
| Raiders / OAK era | Jerry Rice | 2003 | `LV` | Override (`LV → FR_LV`) — proves the fix handles the modern code appearing even in old rows | "...was Jerry Rice on during the 2003 season?" | Oakland Raiders |
| Raiders / LV era | Maxx Crosby | 2023 | `LV` | Direct (`team_aliases` has `LV` 2020+) | "...was Maxx Crosby on during the 2023 season?" | Las Vegas Raiders |

**Real finding worth flagging:** the source data is genuinely inconsistent about which code it stores per row — some old-era rows use the historically-accurate code (`STL`/`SD`/`OAK`), others use the modern code (`LAR`/`LAC`/`LV`) even for old seasons (e.g. Jerry Rice's 2003 row is stored as `LV`, not `OAK`). Both paths converge to the correct, season-accurate franchise name — verified above for all three franchises across both code conventions.

---

## 14. Summary for the reviewer

- Every question/answer pair above was independently generated and checked against the live Engine DB, none hand-typed (some players appear in more than one section, e.g. Aaron Donald in both "recent" and "relocation").
- Wording corrected everywhere: "was/is ON [team]" (roster membership), never "played for" (game participation, not joined by this capability). Verified via a direct check across a real 50-round batch: zero occurrences of "played for".
- Season completeness is a real, live, self-correcting measurement (player_game_stats regular-season weeks) — no wall-clock date read anywhere.
- 2,906 additional rows (season 2026, a real preseason-only snapshot) are now correctly excluded as a `FUTURE` season; recalculated eligible pool is 51,104 (was 54,010), eligibility_rate 92.24% (was 97.48%).
- 806 multi-team exclusions and 588 name-collision exclusions are unchanged, real, counted, and verified absent from the eligible pool.
- Client-safe payload contract verified to contain zero answer-derived fields, including the new `evidence_type` field.
- Server-private record shown once, here, for comparison — never returned by any Gateway route.
- Full 22-capability Tier-2 sweep re-run under all corrections above: all pass.

**Catalog state:** `GENERATION_VERIFIED`, `human_review_status=AWAITING_HUMAN_REVIEW`. Awaiting the owner's explicit `HUMAN_APPROVED` decision — not self-certified.

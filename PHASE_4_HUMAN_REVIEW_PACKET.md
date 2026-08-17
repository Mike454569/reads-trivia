# Phase 4 Human-Review Packet — CFB_PLAYER_SEASON__SCHOOL_OF_SEASON

Prepared for the owner's `GENERATION_VERIFIED -> HUMAN_APPROVED` review decision.
Not exposed through any Gateway route — this is a local, committed report only.
Every example below was generated through the real, live pipeline (`tools/quiz_export/adapters/cfb_player_season_school.py`
via `tools/director_v02/compiler.py`) against the live Engine DB — nothing here is fabricated or hand-typed.

This capability is the **second proof** of the conservative relationship compiler's generalization (Phase 3's own
docstring: "Reusing this same compiler for a DIFFERENT relationship of the same shape... would be the real proof this
generalizes"). Same shape as Phase 3's NFL capability (entity + season → object), different sport, two real design
differences chosen to match what CFB's own data actually supports honestly — see Sections 1 and 2.

---

## 1. Identity resolution: stable, not season-scoped

Unlike NFL franchises (which relocate/rename), CFB school identity is **stable** in this Engine's data: zero
`school_id`s have more than one distinct `school_name` across `cfb_school_seasons`' full 2002–2025 range (checked
directly). `identity_resolution_strategy="stable_identity_table"` resolves `school_id → schools.school_name` with a
direct lookup — no season-scoping or code-history override needed at all, unlike the NFL capability's three
Rams/Chargers/Raiders overrides.

## 2. Season completeness: real aggregate presence, not a fixed week floor

The NFL capability's `COMPLETE` rule (≥17 real regular-season weeks) is a flat floor — correct for every real NFL
season today, but flagged by the owner as a release safeguard to fix before public release (schedule eras differ).
**CFB has no single real per-season week count at all** (division/conference/playoff-format variation, and the real,
verified 2020 COVID-shortened season) — a flat week floor would repeat that exact flaw immediately. Instead,
`season_completeness_strategy="aggregate_presence"` uses real presence in `cfb_school_seasons` (a post-season
aggregate-outcomes table, populated only once a season's real results exist) as the completeness signal. No `ACTIVE`
state is reachable under this strategy (an aggregate table doesn't reliably distinguish "not started" from
"partially populated") — only `COMPLETE` or `FUTURE`.

## 3. Real evidence-semantics carryover (Phase 3 closeout, applied from the start)

`cfb_roster_seasons_real` proves **roster membership**, not game participation — `evidence_type` is always
`ROSTER_MEMBERSHIP`. Wording: **"Which CFB school was {player} on during the {season} season?"** — never "played
for". Verified directly across a real 50-round batch: zero occurrences of "played for".

## 4. Real performance fix found and applied during this phase

This capability's real eligible pool (269,882) is ~5x the NFL capability's (51,104). A real, direct timing test of a
`target_count=5` generation call — the same shape a live `/v1/creator/generate` request uses — took **116 seconds**
before a fix, because the shared generation pipeline (`game_director_v01.generate_package_from_spec()`) evaluates
every candidate `fetch_ordered_candidates()` returns, unconditionally, regardless of `target_count`. Added
`RelationshipSpec.max_fetched_candidates=5000`: the real, already-shuffled candidate list is truncated to 5,000 rows
**after** every real exclusion count (multi-school/collision/future-season) is computed from the full set — so
`eligibility_report()` and Tier-2 certification's `eligible_pool_size` still report the true 269,882, never the
capped sample. Real result: the same request now completes in **~4 seconds**. Full regression suite for this
capability re-run after the fix — all pass, including a dedicated test proving `eligible_pool_size` (269,882) and
`exported_count` (5,000, the capped sample) are never confused with each other.

---

## 5. Primary example: Tim Tebow — 2007

| Field | Value |
|---|---|
| Question | "Which CFB school was Tim Tebow on during the 2007 season?" |
| Options | Florida, Central Michigan, Arizona State, Louisiana Tech |
| Accepted answer | **Florida** |
| Raw source row | `cfb_roster_seasons_real`: `cfb_player_id=ESPN_CFB:183484`, `season=2007`, `school_id=CFB_SCHOOL_FLORIDA`, `source_id=SPORTSDATAVERSE_CFB`, `verification_status=SOURCE_BACKED` |
| Normalized school identity | `school_id=CFB_SCHOOL_FLORIDA`, `school_name=Florida` |
| Evidence type / season status | `ROSTER_MEMBERSHIP` / `COMPLETE` |

## 6. Five historical examples (2004–2010, near this capability's real coverage floor)

| Player | Season | Accepted Answer | Canonical Player ID |
|---|---|---|---|
| Adrian Peterson | 2004 | Oklahoma | `ESPN_CFB:161717` |
| Tim Tebow | 2007 | Florida | `ESPN_CFB:183484` |
| Cam Newton | 2010 | Auburn | `ESPN_CFB:232016` |
| Reggie Bush | 2005 | USC | `ESPN_CFB:145158` |
| Vince Young | 2005 | Texas | `ESPN_CFB:135107` |

## 7. Five recent examples (2020–2024)

| Player | Season | Accepted Answer | Canonical Player ID |
|---|---|---|---|
| Trevor Lawrence | 2020 | Clemson | `ESPN_CFB:4360310` |
| Bryce Young | 2021 | Alabama | `ESPN_CFB:4685720` |
| Jayden Daniels | 2023 | LSU | `ESPN_CFB:4426348` |
| Travis Hunter | 2024 | Colorado | `ESPN_CFB:4685415` |
| Arch Manning | 2024 | Texas | `ESPN_CFB:4870906` |

## 8. Multi-school exclusions (3 real examples, 2025 season)

| Player | Real Schools | Player ID | Confirmed Excluded |
|---|---|---|---|
| Conrad Hussey | Florida State, Oregon State | `ESPN_CFB:4870752` | ✅ Yes |
| Zaquan Patterson | Alabama State, Oklahoma State | `ESPN_CFB:5079557` | ✅ Yes |
| Brett Brown | Middle Tennessee, Missouri | `ESPN_CFB:5081162` | ✅ Yes |

(Real total: 284 such exclusions across 2004–2025.) **Distinct from the existing `CFB_TRANSFER` capability**, which
asks about a real multi-school *career* (any school a player ever attended) — never a specific season.

## 9. Same-name collision evidence: Caleb Williams — 2023 (five-way)

A real, dramatic case, more severe than anything found in Phase 3: **9 distinct real players** are named "Caleb
Williams" in this database; **5 of them** were simultaneously active in CFB in 2023 alone:

| Player ID | School (2023) |
|---|---|
| `ESPN_CFB:4837256` | Furman |
| `ESPN_CFB:4428884` | Lamar |
| `ESPN_CFB:5154304` | Pittsburgh |
| `ESPN_CFB:5081725` | Tennessee |
| `ESPN_CFB:4431611` | **USC** (the real 2023 Heisman Trophy winner) |

All five are excluded from the eligible pool — confirmed directly, zero rows where `entity_name == "Caleb Williams"`
and `season == 2023` appear in `fetch_ordered_candidates()`'s output. This proves the protection matters even for a
single real, famous name: without the `cfb_player_id` join, a naive "Caleb Williams — 2023" prompt could not
distinguish the Heisman winner from four other unrelated real people.

## 10. Future-season exclusion evidence: season 2026

| Signal | Value |
|---|---|
| Real `cfb_school_seasons` rows for 2026 | **0** |
| Raw `cfb_roster_seasons_real` rows for 2026 | **0** |
| Computed `season_status(2026)` | `FUTURE` |

Unlike the NFL capability (which had a real preseason-only 2026 roster snapshot to guard against), CFB's 2026 data
doesn't exist in this Engine at all yet — the season-status gate is exercised correctly regardless, and will
self-correct automatically once real 2026 data is ingested.

---

## 11. Client-safe payload / server-private record / submission scoring

Structurally identical to Phase 3's Sections 7/8/9-12 (same `round_serialization.py` allow-list, same
strip+casefold answer normalization) — verified directly for this capability via
`test_no_answer_data_leaks_into_a_client_safe_payload` and `test_correct_and_incorrect_submissions_score_properly`
in `gateway/tests/test_phase4_cfb_player_season_school.py`. Not duplicated here in full to keep this packet concise;
the underlying mechanism (and the "never expose the server-private record via any route" rule) is unchanged from
Phase 3 and applies identically.

---

## 12. Eligibility figures (owner-corrected terminology, applied from the start)

| Term | Value |
|---|---|
| `raw_candidate_count` | 281,838 |
| `eligible_candidate_count` | 269,882 |
| `excluded_candidate_count` | 11,956 |
| `eligibility_rate` | 95.76% |
| `exclusion_rate` | 4.24% |
| — multi_team_exclusions | 284 |
| — name_collision_exclusions | 11,672 |
| — future_season_exclusions | 0 |
| `generation_attempts` / `successful_generations` / `unique_questions_exercised` (Tier-2) | 100 / 100 / 100 |
| `test_sample_rate` | 0.04% |

---

## 13. Summary for the reviewer

- Every question/answer pair above was independently generated and checked against the live Engine DB, none hand-typed.
- Second real proof the conservative compiler generalizes: same module (`compiler.py`), two different real
  identity-resolution and season-completeness strategies, chosen honestly per what each sport's data supports.
- A real, measured 116s-per-request performance problem (found during this phase, at CFB's real ~270K-row scale)
  was fixed with a bounded, honestly-labeled sampling cap — eligibility reporting stays true throughout.
- 11,672 same-name collision exclusions (much higher than NFL's 588, expected at CFB's scale) verified with a
  dramatic real example (5 distinct "Caleb Williams" in 2023 alone, including the actual Heisman winner).
- 284 multi-school exclusions verified real and distinct from the existing `CFB_TRANSFER` capability's own,
  different real question shape.

**Catalog state:** `GENERATION_VERIFIED`, `human_review_status=AWAITING_HUMAN_REVIEW`. Awaiting the owner's explicit
`HUMAN_APPROVED` decision — not self-certified.

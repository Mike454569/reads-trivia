# Reads v1.5 — NFL ↔ CFB Identity Bridge

v1.5 connects CFB and NFL identities conservatively. A link is production-safe only when the existing high-confidence candidate is unique, the normalized player name matches exactly, CFB evidence resolves to one school, and the NFL draft year follows the CFB evidence within five years.

The bridge never promotes ambiguous names. Unresolved players remain unresolved.

## New production relationships
- `SAME_PERSON_AS`
- `ATTENDED_BEFORE_DRAFT`
- `WON_CFB_AWARD_BEFORE_NFL_DRAFT`

## New generated modes
- `cross_school_to_draft_team`
- `cross_award_to_draft_team`

The Game Factory now supports award-before-draft natural-language requests using only production-safe bridge rows.

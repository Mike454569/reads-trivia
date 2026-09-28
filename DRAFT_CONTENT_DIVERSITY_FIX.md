# Draft Content Diversity Fix

This update keeps draft trivia inside modes that are explicitly about the NFL Draft. General-purpose formats now use broader football content.

## Changed modes

- Risk It: NFL passing, rushing, and receiving leaderboard seasons
- Double or Nothing: NFL passing, rushing, and receiving leaderboard seasons
- Three Strikes: NFL passing, rushing, and receiving leaderboard seasons
- Fact or Fake: Super Bowl results and NFL team records
- Reverse Trivia: player passing seasons and team-season records
- Common Link: shared NFL roster relationships (team, season, or position)
- Wager Mode: NFL team records, Heisman winners, and Super Bowl champions
- Category Roulette: NFL team records, Heisman winners, and Super Bowl champions

The public mode and variant IDs were intentionally left unchanged for backward compatibility. Package schema versions were bumped to `1.1`, so deployed package caches cannot keep serving the old draft-heavy rounds.

## Safeguards

- Normal sessions use deterministic balanced category rotation.
- Draft questions are excluded from the eight general-purpose modes above.
- Existing draft-specific games remain available and unchanged.
- Regression assertions now fail if draft copy reappears in the general modes.

## Verification completed

- Python syntax compilation for every changed generator and registry file
- JavaScript syntax check for `engine-game-ui.js`
- Targeted generator checks for stat questions, team-record questions, unique answer options, and non-draft prompts

The full pytest suite requires the production-sized `reads_football_v4.0.sqlite` database and pytest, neither of which was included in the uploaded ZIP/runtime.

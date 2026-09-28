# Reads UX Energy Pass

This pass addresses the parts of the app that felt visually flat without changing the underlying game rules.

## Home

- Added a stronger hero message and two immediate play actions.
- Added league subtitles and real game counts.
- Converted secondary modes into compact horizontal rails on mobile, reducing the wall-of-cards effect.
- Tightened secondary card hierarchy with shorter descriptions and icon containers.

## Pregame screens

- Rebuilt NFL and CFB Immaculate Grid intros as game launch screens with visual previews, feature callouts, and stronger calls to action.
- Rebuilt 17-0 and CFB 12-0 intros around the actual fantasy of chasing a perfect season.

## Active gameplay

- Added game HUDs, live progress bars, and score cards to both Grid modes.
- Restyled both grids as contained game boards rather than plain tables.
- Rebuilt NFL and CFB fantasy-draft choices as player cards with position badges, value meters, and clear draft actions.
- Added on-the-clock team reveals, roster progress, and confirmation after each pick.

## Feedback

- Correct and incorrect quiz feedback now appears in a visually distinct result card.
- Existing motion, sound, scoring, ranking, sharing, and game-state behavior remains intact.

## Deployment

The service-worker cache was bumped from `reads-v30` to `reads-v31` so returning players receive the new JavaScript and CSS after deployment.

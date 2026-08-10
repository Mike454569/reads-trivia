# League API contract

Recommended production routes:

`GET /competitions`
Returns NFL and CFB.

`GET /modes?competition=CFB`
Returns mode template + concrete binding/status.

`GET /daily?competition=CFB&date=YYYY-MM-DD`
Returns CFB daily modes.

`GET /pack?competition=CFB&mode=cfb_connections&seed=...`
Returns a deterministic generated pack.

`GET /graph/path?...&competition=CFB`
Use the same graph engine with competition/entity filters.

The client should render mechanics (`matching`, `ordering`, `connections`, `elimination`, `guess`, `path`) rather than hard-coding every named game.

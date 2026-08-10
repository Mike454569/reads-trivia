# Game Factory API v1.4

The existing API endpoints stay backward compatible. Advanced rules are returned inside `spec.rules`.

- `POST /factory/analyze` — compile idea + capability check.
- `POST /factory/preview` — generate QA-passed examples.
- `POST /factory/publish` — publish a spec into `puzzle_catalog`.
- `POST /factory/unpublish` — disable a published Factory mode.
- `GET /factory/capabilities` — base capability list.

Example:
```json
{"description":"Four CFB players who transferred exactly once"}
```

The frontend contract remains unchanged because published candidates still land in the standard `puzzle_catalog`.

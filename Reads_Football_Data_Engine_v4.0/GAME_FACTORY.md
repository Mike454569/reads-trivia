# Reads Football Game Factory v1.4

The Factory converts a game idea into a structured, source-aware rule spec and then generates deterministic puzzle candidates.

## Pipeline
`Describe → Parse rules → Capability check → Generate → QA → Preview → Publish`

## New in v1.4
- Composite conditions: **same X AND same Y**.
- Contrast rules: **four share X+Y; the fifth shares X but not Y**.
- Count conditions: e.g. **transferred exactly once**.
- Time-bounded relationships: e.g. **teammates before 2015**.
- Cross-domain sequence guardrails: e.g. award-before-draft stays blocked until identity joins are verified enough.
- Rule AST persisted in `game_factory_specs.rules_json`.
- Capability registry in `factory_rule_capabilities`.

## Examples now supported
```text
Four NFL players drafted by the same team and same position
Five CFB players: four from the same school and same position, fifth same school/different position
Four CFB players who transferred exactly once
Four NFL players who were teammates before 2015
```

## Deliberately blocked example
```text
Four players who won an award before being drafted
```
The current NFL↔CFB identity bridge is not verified enough to publish that cross-domain rule safely, so v1.4 returns `NEEDS_IDENTITY`.

## CLI
```bash
python game_factory.py analyze "Four CFB players who transferred exactly once"
python game_factory.py preview "Four NFL players drafted by the same team and same position" --limit 12
python game_factory.py publish SPEC:... --mode-id my_mode
python game_factory.py unpublish my_mode
```

"""Shared static Quiz export framework for Reads Football Data Engine v4.0.

Owns only the infrastructure proven common across three independent domain
pilots (Draft, QB/Season, Championship/Postseason): production-safety
enforcement, contract validation, duplicate detection, difficulty
normalization, deterministic seeding, JS serialization, funnel/audit
statistics, and human-review report support.

Domain-specific football logic (table selection, identity resolution,
ambiguity rules, distractor construction, notes construction) lives in
tools/quiz_export/adapters/, not here. See
QUIZ_EXPORT_FRAMEWORK_REFACTOR_PLAN.md for the full design rationale.
"""

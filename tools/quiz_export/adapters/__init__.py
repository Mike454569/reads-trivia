"""Domain adapters for the shared quiz export framework.

Each adapter module owns everything football-domain-specific: table
selection, identity resolution, ambiguity rules, distractor construction,
Engine difficulty sourcing, and notes/context construction. See
QUIZ_EXPORT_FRAMEWORK_REFACTOR_PLAN.md for the shared interface each module
exposes to tools/quiz_export/core.py.
"""

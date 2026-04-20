"""ClearPath Global – M2 Rules Engine.

Public surface: a single entry-point function ``run_evaluation`` that takes an
active-rule list and a flat client-data payload and returns a fully-structured
result dict ready to be returned as an ``EvaluationResponse``.

All sub-modules are pure functions with no database imports.
"""

from app.engine.report import run_evaluation

__all__ = ["run_evaluation"]

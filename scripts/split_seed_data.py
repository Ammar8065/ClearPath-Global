"""Split seed_data.py into data modules.

seed_sources.py ← SOURCE_FIXTURES
seed_rules.py   ← simple_condition/all_conditions/any_conditions + RULE_FIXTURES
seed_data.py    ← the orchestrator (upsert/reset/recreate/seed/CLI)

Byte-exact extraction of line ranges. Run once:
    python scripts/split_seed_data.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "seed_data.py"

# Current line layout in seed_data.py:
#   1-11    imports
#   12-97   SOURCE_FIXTURES (with header comments)
#   98-111  blank + "# ── Helpers ──" + helpers
#   112-711 "# ── Rules ──" header + RULE_FIXTURES
#   712-813 orchestrator functions + CLI

SRC_SOURCES_START = 12   # "# ── Knowledge Sources ──" banner
SRC_SOURCES_END   = 97   # closing "]" of SOURCE_FIXTURES
SRC_HELPERS_START = 100  # "# ── Helpers ──" banner
SRC_HELPERS_END   = 110  # end of any_conditions
SRC_RULES_START   = 113  # "# ── Rules ──" banner
SRC_RULES_END     = 711  # closing "]" of RULE_FIXTURES


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    def slice_(start: int, end: int) -> str:
        return "".join(lines[start - 1 : end])

    sources_block = slice_(SRC_SOURCES_START, SRC_SOURCES_END)
    helpers_block = slice_(SRC_HELPERS_START, SRC_HELPERS_END)
    rules_block   = slice_(SRC_RULES_START, SRC_RULES_END)

    # ── seed_sources.py ──
    (ROOT / "seed_sources.py").write_text(
        '"""Knowledge source fixtures for the ClearPath seeding pipeline."""\n'
        "from app.models.knowledge_source import SourceType\n\n"
        + sources_block,
        encoding="utf-8",
    )

    # ── seed_rules.py ──
    (ROOT / "seed_rules.py").write_text(
        '"""Rule fixtures + condition helpers for the ClearPath seeding pipeline."""\n'
        "from datetime import date\n\n"
        "from app.models.rule import ConfidenceLevel, RiskLevel, RuleCategory\n\n"
        + helpers_block
        + "\n"
        + rules_block,
        encoding="utf-8",
    )

    # ── seed_data.py (orchestrator) ──
    orchestrator = (
        "import argparse\n"
        "from datetime import date  # noqa: F401  (kept for backwards-compat imports)\n"
        "\n"
        "from sqlalchemy import delete, select\n"
        "\n"
        "from app.database.base import Base\n"
        "from app.database.init_db import init_db\n"
        "from app.database.session import SessionLocal, engine\n"
        "from app.models.knowledge_source import KnowledgeSource\n"
        "from app.models.rule import Rule\n"
        "\n"
        "from seed_sources import SOURCE_FIXTURES\n"
        "from seed_rules import (\n"
        "    RULE_FIXTURES,\n"
        "    all_conditions,     # noqa: F401  (re-exported helper)\n"
        "    any_conditions,     # noqa: F401  (re-exported helper)\n"
        "    simple_condition,   # noqa: F401  (re-exported helper)\n"
        ")\n"
        "\n"
        "\n"
        + slice_(714, 814)  # upsert_sources through end of file (CLI)
    )
    (ROOT / "seed_data.py").write_text(orchestrator, encoding="utf-8")

    print("[ok] seed_sources.py written")
    print("[ok] seed_rules.py written")
    print("[ok] seed_data.py (orchestrator) rewritten")


if __name__ == "__main__":
    main()

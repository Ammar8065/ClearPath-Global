"""Split styles.css into modular files under styles/.

Byte-exact extraction of line ranges — no content modification.
Run once from the project root:
    python scripts/split_styles.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "styles.css"
OUT = ROOT / "styles"
OUT.mkdir(exist_ok=True)

# (filename, start_line, end_line_inclusive, description)
# Line numbers reference the current styles.css structure.
SECTIONS = [
    ("tokens.css",            1,   84,  "Design tokens (CSS variables) + header"),
    ("base.css",              85, 114,  "Reset, body, paper-grain texture"),
    ("shell.css",            115, 123,  "App shell flex container"),
    ("sidebar.css",          124, 375,  "Sidebar / masthead navigation"),
    ("main.css",             376, 513,  "Main column, topbar, sections"),
    ("dashboard.css",        514, 1132, "Dashboard cards, stats, distribution, CTAs"),
    ("buttons.css",         1133, 1203, "Button variants"),
    ("cards.css",           1204, 1268, "Cards + two-column layout"),
    ("forms.css",           1269, 1391, "Inputs, selects, labels, fieldsets"),
    ("lists.css",           1392, 1471, "Item lists"),
    ("badges.css",          1472, 1533, "Badges & pills (printed stamps)"),
    ("empty.css",           1534, 1553, "Empty state"),
    ("evaluation.css",      1554, 2348, "Private assessment / evaluation layout"),
    ("evaluation-report.css", 2349, 2762, "Evaluation report, score gauge, category, citations"),
    ("tenants.css",         2763, 2811, "Tenant cards"),
    ("responsive.css",      2812, 2861, "Responsive breakpoints"),
]


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    total = len(lines)

    header = (
        "/* ClearPath Global — auto-split module. Do not edit the full file;\n"
        "   edit the individual section source. */\n\n"
    )

    written = 0
    for fname, start, end, desc in SECTIONS:
        if end > total:
            raise SystemExit(f"Section {fname}: end {end} > total {total}")
        chunk = "".join(lines[start - 1 : end])
        banner = f"/* {desc} */\n"
        (OUT / fname).write_text(banner + chunk, encoding="utf-8")
        written += 1
        print(f"[ok] {fname:<24} lines {start}-{end} ({end - start + 1} lines)")

    # Build the index file that imports every module in order.
    index_lines = ["/* ClearPath Global — styles index. Import order matters:",
                   "   tokens → base → layout → components → feature-sections → responsive. */",
                   ""]
    for fname, _, _, _ in SECTIONS:
        index_lines.append(f'@import url("./{fname}");')
    (OUT / "index.css").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"[ok] index.css             ({len(SECTIONS)} @import rules)")
    print(f"\nTotal: {written} modules written to {OUT}")


if __name__ == "__main__":
    main()

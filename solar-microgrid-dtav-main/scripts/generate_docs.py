"""Build the documentation index from canonical Markdown, without overwriting it.

Markdown chapters are the editable source of truth. Generated hardware tables
come from generate_hardware.py/wiring_details.py; PDFs come from build_report.py.
"""

from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
paths = [ROOT / "START_HERE.md", ROOT / "README.md"]
paths += sorted(p for p in (ROOT / "docs").rglob("*.md") if p.name != "INDEX.md")
paths += sorted((ROOT / "hardware").rglob("*.md"))
lines = [
    "# Documentation index",
    "",
    "All current documents describe revision 2: one shared protected PV bus, "
    "continuous protected MPPT input, KPV solar-converter enable, PB10 charge "
    "inhibit and PB1 PV-voltage sensing.",
    "",
    "Edit the Markdown chapters directly. Run `python scripts/regenerate_design.py` "
    "to rebuild tables, diagrams and both PDFs; this indexer never recreates old chapter text.",
    "",
]
for path in paths:
    title = next(
        (
            line.lstrip("# ").strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("# ")
        ),
        path.stem,
    )
    link = os.path.relpath(path, ROOT / "docs").replace(os.sep, "/")
    lines.append(f"- [{title}]({link})")
(ROOT / "docs/INDEX.md").write_text(
    "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
)
print(f"Indexed {len(paths)} current Markdown documents")

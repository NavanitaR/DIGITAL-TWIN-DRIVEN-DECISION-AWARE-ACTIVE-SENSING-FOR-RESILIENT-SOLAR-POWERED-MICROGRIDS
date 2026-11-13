from pathlib import Path
import re
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[1]
diagrams = list((R / "hardware/schematics").glob("*.svg"))
for p in diagrams:
    ET.parse(p)
for p in R.rglob("*.md"):
    if any(x in p.parts for x in (".venv", "node_modules", ".pio", ".git", "tmp")):
        continue
    text = p.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if target.startswith(("http", "mailto:", "#")):
            continue
        if not (p.parent / target.split("#")[0]).exists():
            raise AssertionError(f"Broken link {p}: {target}")
assert (R / "docs/bom/BOM.xlsx").stat().st_size > 1000
assert (R / "docs/TECHNICAL_REPORT.pdf").stat().st_size > 1000
print(
    f"Parsed {len(diagrams)} SVGs; local Markdown links and generated artifacts verified"
)

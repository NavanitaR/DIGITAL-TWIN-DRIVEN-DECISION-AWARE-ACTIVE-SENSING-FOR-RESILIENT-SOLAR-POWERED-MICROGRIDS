"""Regression checks for the shared-PV documentation and regeneration sources."""

import csv
import shutil
import subprocess
import sys
from pathlib import Path

from openpyxl import load_workbook
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def test_current_sources_have_no_operational_time_division_claims():
    forbidden = [
        "Solar allocation is time divided.",
        "KPV charging NC",
        "No simultaneous charging and direct solar load supply.",
        "KPV COM=PV_COMB; NC=MPPT_IN",
        "conservative8W capacity",
    ]
    paths = [ROOT / "README.md", ROOT / "START_HERE.md"]
    for folder in ["docs", "hardware", "scripts"]:
        paths += [
            p
            for p in (ROOT / folder).rglob("*")
            if p.suffix in (".md", ".py", ".svg", ".csv", ".sch", ".json")
        ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, (path, phrase)


def test_mppt_wiring_is_independent_of_kpv_nc():
    rows = read_csv(ROOT / "hardware/wiring/full_connections.csv")
    assert not any(
        r["source_module"] == "KPV" and r["source_pin"] == "NC" for r in rows
    )
    assert any(
        r["source_module"] == "PV_COMB"
        and r["destination_module"] == "Charger branch fuse/reverse protection"
        for r in rows
    )
    assert any(
        r["source_module"] == "Charger branch fuse/reverse protection"
        and r["destination_module"] == "BQ24650"
        and r["destination_pin"] == "VIN"
        for r in rows
    )
    pins = read_csv(ROOT / "hardware/wiring/controller_wiring.csv")
    assert (
        next(
            r
            for r in pins
            if r["source_module"] == "stm32-f411" and r["source_pin"] == "PB1"
        )["signal_type"]
        == "analog"
    )
    assert (
        "MPPSET"
        in next(
            r
            for r in pins
            if r["source_module"] == "stm32-f411" and r["source_pin"] == "PB10"
        )["purpose"]
    )


def test_bom_workbook_and_csv_agree():
    rows = read_csv(ROOT / "docs/bom/BOM.csv")
    sheet = load_workbook(ROOT / "docs/bom/BOM.xlsx", data_only=True).active
    for row_index, row in enumerate(rows, 10):
        assert sheet.cell(row_index, 1).value == row["component"]
        assert sheet.cell(row_index, 2).value == float(row["quantity"])
        assert sheet.cell(row_index, 4).value == row["electrical_ratings"]
        assert sheet.cell(row_index, 7).value == float(row["total_price_INR"])
    assert sheet["C8"].value == 32376
    relay = next(row for row in rows if row["component"].endswith("relay KPV"))
    assert "NC unused" in relay["electrical_ratings"]


def test_both_pdfs_contain_current_shared_pv_interfaces():
    for name in ["TECHNICAL_REPORT.pdf", "WORKING_GUIDE.pdf"]:
        text = "\n".join(
            page.extract_text() or "" for page in PdfReader(ROOT / "docs" / name).pages
        )
        assert "PB10" in text and "MPPSET" in text and "PB1" in text
        assert "KPV charging NC" not in text
        assert "Solar allocation is time divided." not in text
        assert "conservative8W capacity" not in text
        assert "NC is unused and insulated" in text or "NC unused and insulated" in text


def test_regeneration_cannot_restore_old_power_routing(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ["generate_hardware.py", "wiring_details.py"]:
        shutil.copyfile(ROOT / "scripts" / name, scripts / name)
        subprocess.run(
            [sys.executable, str(scripts / name)],
            cwd=tmp_path,
            check=True,
            stdout=subprocess.PIPE,
        )
    rows = read_csv(tmp_path / "hardware/wiring/full_connections.csv")
    assert not any(
        r["source_module"] == "KPV" and r["source_pin"] == "NC" for r in rows
    )
    budget = (tmp_path / "docs/bom/POWER_BUDGET.md").read_text(encoding="utf-8")
    assert "MPPT input remains connected" in budget
    assert "time divided" not in budget
    assert "conservative8W capacity" not in budget

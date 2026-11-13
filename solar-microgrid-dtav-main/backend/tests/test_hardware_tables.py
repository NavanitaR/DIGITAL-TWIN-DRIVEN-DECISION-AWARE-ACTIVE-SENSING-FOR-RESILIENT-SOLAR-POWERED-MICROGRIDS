import csv
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_address_uniqueness_and_shunt_ranges():
    rows = list(csv.DictReader((ROOT / "hardware/wiring/ina226_addresses.csv").open()))
    assert len(rows) == 13
    for bus, n in [("S3", 6), ("STM32", 7)]:
        selected = [r for r in rows if r["bus"] == bus]
        assert len(selected) == n
        assert len({r["address"] for r in selected}) == n
        assert all(float(r["shunt_ohms"]) > 0 for r in selected)


def test_gpio_map_has_no_unintentional_pin_duplicates():
    rows = list(csv.DictReader((ROOT / "hardware/wiring/controller_wiring.csv").open()))
    assigned = [(r["source_module"], r["source_pin"]) for r in rows]
    assert len(set(assigned)) == len(assigned)
    assert len([r for r in rows if r["purpose"].endswith("button")]) == 5


def test_bom_totals_and_no_ownership_claims():
    rows = list(csv.DictReader((ROOT / "docs/bom/BOM.csv").open()))
    assert sum(float(r["total_price_INR"]) for r in rows) == 26980
    assert all(
        float(r["quantity"]) * float(r["unit_price_INR"]) == float(r["total_price_INR"])
        for r in rows
    )
    assert all("Unverified" in r["price_evidence"] for r in rows)

# Documentation consistency audit - 2026-11-09

The repository audit found stale operational text in generator templates, the original technical-report PDF, KPV BOM wording and reset-state descriptions. These have been corrected at their source rather than covered by supersession banners.

Current invariant: four protected panels share PV_COMB; MPPT has a continuous dedicated protected input; KPV NO enables only the solar converter and NC is unused/insulated. PB10 drives MPPSET inhibition and PB1 senses PV voltage. Six relays and13 INA226 monitors remain. A nominal8W proof load establishes only the measured7.5W capacity bound.

Canonical Markdown is preserved by the index generator. Hardware tables,197 module/net connections,10 SVGs, the KiCad integration map, BOM CSV/JSON/XLSX and both PDFs are rebuilt through `scripts/regenerate_design.py`. The old migration script was removed, and generator templates no longer recreate the earlier input-transfer scheme. Workbook totals remain INR26,980 + INR5,396 contingency = INR32,376, using unverified planning allowances.

Automated regression checks inspect current source statements and both PDF texts, validate PV routing and PB1/PB10 roles, compare workbook rows with CSV, and regenerate hardware/wiring in an isolated temporary directory. CI additionally rebuilds non-workbook artifacts and repeats the consistency checks. The complete local validation includes30 backend tests, native C checks, frontend checks and three firmware builds; exact output is retained in `simulation/results/validation.json`.

This audit verifies documentation/software consistency, not analog stability or electrical safety. Physical charger/converter interaction, hardware protection, actual module ratings and commissioning remain open as documented.

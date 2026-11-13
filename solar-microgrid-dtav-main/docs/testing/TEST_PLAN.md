# Verification plan and limits

Automated software: pytest backend/tests; frontend npm test and build; GCC native firmware/tests/native.c; PlatformIO three builds; seeded scripts/experiment.py. Tests cover wire CRC/COBS/fragmentation/resync, source deadtime/target revalidation, sensor NaN handling, low battery, priority shedding/staggered restore, command validation, model energy integration, modes, SQLite, API and DTAV action ambiguity. Browser QA uses local backend and Vite, checks responsive topology and explicit provenance.

Protocol simulation encodes/decodes each logical hop and exercises reverse requests/ACKs. It is not a bit-accurate emulator of all MCU peripherals, radio airtime/collisions, UART interrupts or MQTT broker networking. Simulated faults modify plant/connection models; no electrical fault tests occurred. Native tests execute portable shared logic on desktop, not CortexM watchdog or gate drivers.

Hardware tests must be recorded separately: monitor offset/gain and burden, battery charge profile/NTC, converter UVLO/ripple/thermal/inrush, branch eFuse trips/reverse current, relay BBM/bounce/contact welding response, fault interruption, e-stop, RF ERP/emissions/duty cycle, radio range/packet loss, actual motor stall, watchdog/reset outputs and board boot pins. The commissioning checklist defines gating sequence. No short test on a real pack/PV is authorised by software simulation.

For each regression retain command, tool versions, exit code and relevant summary in VALIDATION.md. Do not turn a planned test into a pass without running it. CI repeats buildable checks on Ubuntu with PlatformIO and pinned lockfiles. Hardware commissioning gates remain open until signed evidence exists.

## Documentation regeneration and consistency

`scripts/regenerate_design.py` rebuilds controller/monitor tables, detailed wiring, SVGs, the KiCad integration map, index, BOM workbook and both PDFs. Markdown chapters are canonical; no migration pass recreates or patches an obsolete topology. `generate_docs.py` indexes those chapters without overwriting them.

`backend/tests/test_documentation_consistency.py` rejects obsolete routing statements, verifies MPPT is not connected to KPV NC, checks PB1/PB10 roles, compares workbook rows/totals with CSV, inspects both PDF texts and runs hardware/wiring generators in a temporary workspace. CI performs an explicit non-workbook rebuild and reruns these checks. A skipped workbook is never presented as regenerated; CSV/workbook mismatch still fails validation.

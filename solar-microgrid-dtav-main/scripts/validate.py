"""Run reproducible host/device checks and retain an honest machine-readable record."""

from pathlib import Path
import datetime
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NPM = shutil.which("npm.cmd") or shutil.which("npm")
jobs = [
    ("backend", [sys.executable, "-m", "pytest", "-q"], ROOT),
    (
        "native_compile",
        [
            "gcc",
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Ifirmware/shared",
            "firmware/tests/native.c",
            "-lm",
            "-o",
            "tmp/native-check.exe",
        ],
        ROOT,
    ),
    ("native_execute", [str(ROOT / "tmp/native-check.exe")], ROOT),
    ("frontend_tests", [NPM, "test"], ROOT / "frontend"),
    ("frontend_build", [NPM, "run", "build"], ROOT / "frontend"),
    ("frontend_audit", [NPM, "audit", "--audit-level=moderate"], ROOT / "frontend"),
]
jobs += [
    (
        target,
        [sys.executable, "-m", "platformio", "run", "-d", "firmware/" + target],
        ROOT,
    )
    for target in [
        "esp32-s3-sensor-node",
        "stm32-central-controller",
        "esp32-c3-wifi-gateway",
    ]
]
(ROOT / "tmp").mkdir(exist_ok=True)
results = []
for name, command, cwd in jobs:
    print("Checking " + name, flush=True)
    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=600,
        )
        output = process.stdout
        code = process.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        output = str(exc)
        code = 1
    (ROOT / "tmp" / f"{name}.txt").write_text(output, encoding="utf-8")
    results.append(
        {
            "check": name,
            "exit_code": code,
            "command": command,
            "output_tail": output[-2000:],
        }
    )
    print(name + ": " + ("PASS" if code == 0 else "FAIL"), flush=True)
record = {
    "at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "hardware_tested": False,
    "browser_visual_qa": "Blocked: browser access host unavailable",
    "results": results,
}
(ROOT / "simulation/results/validation.json").write_text(
    json.dumps(record, indent=2), encoding="utf-8"
)
sys.exit(int(any(r["exit_code"] for r in results)))

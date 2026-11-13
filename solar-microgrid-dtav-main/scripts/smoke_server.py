"""Start a real local API process on an isolated test port and verify mode barriers."""

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

R = Path(__file__).resolve().parents[1]


def request(path, data=None):
    raw = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        "http://127.0.0.1:18000" + path,
        data=raw,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.load(response)


with tempfile.TemporaryDirectory(prefix="microgrid-smoke-") as directory:
    env = dict(
        os.environ,
        MICROGRID_DB=str(Path(directory) / "smoke.db"),
        MICROGRID_DTAV_ARMED="0",
    )
    with (R / "tmp/smoke-server.txt").open("w") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--app-dir",
                "backend",
                "--host",
                "127.0.0.1",
                "--port",
                "18000",
            ],
            cwd=R,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            for _ in range(50):
                try:
                    state = request("/api/state")
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("API did not become ready")
            assert state["mode"] == "simulation" and state["provenance"] == "simulated"
            request("/api/settings", {"mode": "hardware", "strategy": "dtav"})
            time.sleep(1.2)
            state = request("/api/state")
            assert (
                state["mode"] == "hardware"
                and state["stale"]
                and "solar_w" not in state
            )
            request("/api/settings", {"mode": "simulation", "strategy": "dtav"})
            time.sleep(1.2)
            state = request("/api/state")
            assert state["provenance"] == "simulated"
            print(
                "Real API startup, empty hardware-mode boundary and return-to-simulation passed"
            )
        finally:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
            else:
                process.terminate()
            process.wait(timeout=10)

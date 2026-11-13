"""Run paired, seeded scenarios. Metrics describe simulation only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import csv, json, argparse
import numpy as np
from app.engine import Engine
from app.store import Store
from app.models import Injection, Command


def run(seconds=300, seeds=5):
    rows = []
    for seed in range(seeds):
        weather = np.random.default_rng(seed).normal(0, 0.04, seconds)
        for strategy in ("continuous", "periodic", "event", "dtav"):
            e = Engine(Store(":memory:"))
            e.switch("simulation", strategy)
            errors = []
            detection = None
            restored = None
            for t in range(seconds):
                e.twin.shade = [max(0, min(1, 1 + weather[t]))] * 4
                if 80 <= t < 150:
                    e.twin.shade = [0.1] * 4
                s = e.tick()
                errors.append(s["research"]["model_error_w"])
                if (
                    80 <= t < 150
                    and detection is None
                    and s["research"]["estimate"] < 4
                ):
                    detection = t - 80
                if t >= 150 and restored is None and s["research"]["estimate"] > 8:
                    restored = t - 150
            rows.append(
                dict(
                    seed=seed,
                    strategy=strategy,
                    reports=e.sensing.reports,
                    requests=e.sensing.requests,
                    savings=1 - e.sensing.reports / seconds,
                    mae_w=float(np.mean(errors)),
                    unserved_wh=e.twin.unserved_wh,
                    detection_s=detection,
                    restoration_s=restored,
                )
            )
    out = Path(__file__).resolve().parents[1] / "simulation/results"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "comparison.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    summary = {
        strategy: {
            key: dict(mean=float(np.mean(vals)), std=float(np.std(vals)), n=len(vals))
            for key in (
                "reports",
                "mae_w",
                "unserved_wh",
                "detection_s",
                "restoration_s",
            )
            if (
                vals := [
                    r[key]
                    for r in rows
                    if r["strategy"] == strategy and r[key] is not None
                ]
            )
        }
        for strategy in ("continuous", "periodic", "event", "dtav")
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return rows


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seconds", type=int, default=300)
    p.add_argument("--seeds", type=int, default=5)
    args = p.parse_args()
    run(args.seconds, args.seeds)

from pathlib import Path
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = Path(__file__).resolve().parents[1]
d = pd.read_csv(R / "simulation/results/comparison.csv")
names = ["continuous", "periodic", "event", "dtav"]
g = d.groupby("strategy")
fig, axes = plt.subplots(1, 3, figsize=(12, 4), layout="constrained")
for ax, metric, label in zip(
    axes,
    ["reports", "mae_w", "unserved_wh"],
    ["Optional reports / 300s", "Estimator MAE (W)", "Unserved energy (Wh)"],
):
    means = g[metric].mean().reindex(names)
    std = g[metric].std().reindex(names)
    ax.bar(
        names,
        means,
        yerr=std,
        capsize=3,
        color=["#425466", "#86b8bc", "#d4ae6c", "#518e78"],
    )
    ax.set_title(label)
    ax.tick_params(axis="x", rotation=20)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.15)
    ax.set_axisbelow(True)
fig.suptitle(
    "Software simulation only / paired seeds / error bars: sample standard deviation",
    fontsize=11,
)
fig.savefig(R / "simulation/results/comparison.png", dpi=180)
fig.savefig(R / "simulation/results/comparison.svg")
print("Exported comparison PNG/SVG")

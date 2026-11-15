
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# 1. LOAD DATA
# ============================================================

results_folder = Path("vrishin_analysis/results")
figures_folder = Path("vrishin_analysis/figures")

figures_folder.mkdir(parents=True, exist_ok=True)

pairs = pd.read_csv(
    results_folder / "paired_3d_7d_and_cell_exit.csv"
)

alternative = pd.read_csv(
    results_folder / "alternative_exit_comparison.csv"
)

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 11,
    "figure.dpi": 120,
    "savefig.dpi": 300
})


# ============================================================
# FIGURE 1: TIME TO LEAVE INITIAL GRID CELL
# Kaplan-Meier cumulative departure estimate
# ============================================================

km = pairs[
    ["cell_exit_days", "cell_exit_observed"]
].dropna().copy()

km["cell_exit_observed"] = (
    km["cell_exit_observed"].astype(bool)
)

events = (
    km.groupby("cell_exit_days")["cell_exit_observed"]
    .agg(total="size", exits="sum")
    .sort_index()
)

at_risk = len(km)
survival = 1.0

times = [0.0]
departures = [0.0]

for t, row in events.iterrows():
    if at_risk <= 0:
        break

    survival *= (1 - row["exits"] / at_risk)

    times.append(float(t))
    departures.append(100 * (1 - survival))

    at_risk -= row["total"]

times = np.asarray(times)
departures = np.asarray(departures)

def cumulative_departure(day):
    idx = np.searchsorted(times, day, side="right") - 1
    return float(departures[max(0, idx)])

day3 = cumulative_departure(3)
day7 = cumulative_departure(7)

median_indices = np.flatnonzero(departures >= 50)
median_days = (
    float(times[median_indices[0]])
    if len(median_indices) else np.nan
)

fig, ax = plt.subplots(figsize=(9, 5.3))

ax.step(
    times,
    departures,
    where="post",
    linewidth=2.3,
    color="#2166AC",
    label="Kaplan-Meier cumulative departures"
)

ax.axhline(
    50, color="grey", linestyle=":",
    linewidth=1.3, alpha=0.75
)

ax.axvline(
    3, color="#D95F02", linestyle="--",
    linewidth=1.3, alpha=0.8
)

ax.axvline(
    7, color="#238B45", linestyle="--",
    linewidth=1.3, alpha=0.8
)

ax.scatter(
    [3, 7],
    [day3, day7],
    color=["#D95F02", "#238B45"],
    s=55, zorder=5
)

ax.annotate(
    f"Day 3: {day3:.1f}%",
    xy=(3, day3),
    xytext=(3.3, 39),
    arrowprops={"arrowstyle": "-", "color": "#D95F02"},
    color="#B34B00",
    fontsize=10
)

ax.annotate(
    f"Day 7: {day7:.1f}%",
    xy=(7, day7),
    xytext=(5.15, 84),
    arrowprops={"arrowstyle": "-", "color": "#238B45"},
    color="#17682E",
    fontsize=10
)

if np.isfinite(median_days):
    ax.scatter(
        [median_days], [50],
        color="#333333", s=35, zorder=6
    )

    ax.annotate(
        f"Median: {median_days:.2f} days",
        xy=(median_days, 50),
        xytext=(4, 70),
        arrowprops={"arrowstyle": "-", "color": "#444444"},
        fontsize=10
    )

ax.set(
    xlim=(0, 7.3),
    ylim=(0, 100),
    xlabel="Days since starting observation",
    ylabel="Cumulative cell departures (%)",
    title="Time to Leave the Initial 2° Grid Cell"
)

ax.grid(alpha=0.18)
ax.legend(loc="lower right", frameon=False)

fig.text(
    0.12, 0.01,
    "Kaplan-Meier estimate with right-censoring. "
    "Overlapping observations from the same drifter are dependent.",
    fontsize=8.5,
    color="#555555"
)

plt.tight_layout(rect=[0, 0.045, 1, 1])

plt.savefig(
    figures_folder / "vrishin_cell_exit_curve.png",
    bbox_inches="tight"
)
plt.close()


# ============================================================
# FIGURE 2: 3-DAY VS 7-DAY REGIONAL FIRST EXITS
# ============================================================

paired = pairs.dropna(
    subset=["first3", "first7"]
).copy()

directions = ["West", "East", "South", "North"]
codes = [234, 235, 236, 237]

p3 = np.array([
    paired["first3"].eq(code).mean() * 100
    for code in codes
])

p7 = np.array([
    paired["first7"].eq(code).mean() * 100
    for code in codes
])

x = np.arange(len(directions))
width = 0.34

fig, ax = plt.subplots(figsize=(9, 5.3))

bars3 = ax.bar(
    x - width / 2,
    p3,
    width,
    label="3-day horizon",
    color="#377EB8"
)

bars7 = ax.bar(
    x + width / 2,
    p7,
    width,
    label="7-day horizon",
    color="#FF7F00"
)

ax.bar_label(
    bars3, fmt="%.2f%%",
    padding=3, fontsize=10
)

ax.bar_label(
    bars7, fmt="%.2f%%",
    padding=3, fontsize=10
)

ax.set(
    xticks=x,
    xticklabels=directions,
    ylabel="Cumulative first-exit probability (%)",
    title="Regional First-Exit Probabilities: 3-Day vs 7-Day"
)

ax.set_ylim(0, max(p3.max(), p7.max()) * 1.3)

ax.legend(frameon=False)
ax.grid(axis="y", alpha=0.18)
ax.set_axisbelow(True)

fig.text(
    0.12, 0.01,
    "Paired starting observations (n = "
    f"{len(paired):,}). Longer horizons allow more time "
    "for exits; bars do not measure predictive accuracy.",
    fontsize=8.5,
    color="#555555"
)

plt.tight_layout(rect=[0, 0.045, 1, 1])

plt.savefig(
    figures_folder / "vrishin_3day_vs_7day.png",
    bbox_inches="tight"
)
plt.close()


# ============================================================
# FIGURE 3: ALTERNATIVE EXIT-RULE SENSITIVITY
# Focus on the classifications that actually changed
# ============================================================

changed_mask = alternative["changed"].astype(bool)
reentry_mask = alternative["reentered"].astype(bool)

total = len(alternative)

changed = int(changed_mask.sum())
unchanged = total - changed

reentered = int(
    (changed_mask & reentry_mask).sum()
)

other_changes = changed - reentered

if changed == 0:
    raise ValueError(
        "No changed classifications found."
    )

categories = [
    "Re-entry after first exit",
    "Other classification changes"
]

values = [reentered, other_changes]

fig, ax = plt.subplots(figsize=(9, 4.8))

bars = ax.barh(
    categories,
    values,
    color=["#2166AC", "#E69F00"],
    height=0.52
)

ax.invert_yaxis()

for bar, value in zip(bars, values):
    pct = value / changed * 100

    ax.text(
        value + max(values) * 0.012,
        bar.get_y() + bar.get_height() / 2,
        f"{value:,} ({pct:.1f}%)",
        va="center",
        fontsize=11
    )

ax.set(
    xlabel="Number of changed seven-day classifications",
    title="Why First-Exit and Endpoint Rules Disagree"
)

ax.set_xlim(0, max(values) * 1.23)
ax.grid(axis="x", alpha=0.18)
ax.set_axisbelow(True)

fig.text(
    0.12, 0.015,
    f"Of {total:,} comparable seven-day pairs, "
    f"{changed:,} ({changed / total * 100:.2f}%) changed. "
    "Percentages in bars are among changed cases.",
    fontsize=9,
    color="#555555"
)

plt.tight_layout(rect=[0, 0.06, 1, 1])

plt.savefig(
    figures_folder / "vrishin_alternative_exit_rule.png",
    bbox_inches="tight"
)
plt.close()


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\nTHREE UPDATED FIGURES SAVED")
print("1. vrishin_cell_exit_curve.png")
print("2. vrishin_3day_vs_7day.png")
print("3. vrishin_alternative_exit_rule.png")

print("\nCELL EXIT")
print(f"Median exit time: {median_days:.3f} days")
print(f"Departures by day 3: {day3:.2f}%")
print(f"Departures by day 7: {day7:.2f}%")

print("\n3-DAY VS 7-DAY")
for direction, a, b in zip(directions, p3, p7):
    print(f"{direction}: {a:.2f}% vs {b:.2f}%")

print("\nALTERNATIVE EXIT RULE")
print(f"Comparable pairs: {total:,}")
print(f"Changed: {changed:,}")
print(f"Unchanged: {unchanged:,}")
print(f"Re-entry changes: {reentered:,}")
print(f"Other changes: {other_changes:,}")

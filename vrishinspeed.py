import pandas as pd
import numpy as np
from clouddrift.datasets import gdp1h

# ==================================================
# STEP 1: Load the classified seven-day pairs
# ==================================================

pairs = pd.read_csv("pairs7_drogue.csv")

print("Total pairs:", len(pairs))

# ==================================================
# STEP 2: Load NOAA hourly data
# ==================================================

print("\nLoading NOAA GDP dataset...")
ds = gdp1h()

# Check which velocity variables are available
print("\nVELOCITY VARIABLES")

for name in ["ve", "vn", "drogue_status"]:
    if name in ds:
        print(
            name,
            "| units:",
            ds[name].attrs.get("units", "not specified"),
            "| dimensions:",
            ds[name].dims
        )
    else:
        print(name, "NOT FOUND")

# Confirm observation indexing
print("\nOBSERVATION INDEX CHECK")
print("Maximum obs_row:", pairs["obs_row"].max())
print("Total NOAA observations:", len(ds["time"]))

# ==================================================
# STEP 3: Extract velocity at each starting observation
# ==================================================

obs_indices = pairs["obs_row"].to_numpy(dtype=int)

# Load only the velocity values needed for our observations
print("\nExtracting velocity components...")

ve = ds["ve"].isel(obs=obs_indices).values
vn = ds["vn"].isel(obs=obs_indices).values

# Calculate speed in metres per second
pairs["speed_ms"] = np.sqrt(ve**2 + vn**2)

# Check NOAA's recorded drogue status against our classification
pairs["noaa_drogue_status"] = (
    ds["drogue_status"].isel(obs=obs_indices).values
)

print("\nSPEED DATA CHECK")
print("Missing speeds:", pairs["speed_ms"].isna().sum())
print("Speed summary (m/s):")
print(pairs["speed_ms"].describe())

print("\nNOAA drogue-status values:")
print(pairs["noaa_drogue_status"].value_counts(dropna=False))


# ==================================================
# STEP 4: Compare speeds by drogue status
# ==================================================

speed_data = pairs[
    pairs["drogue_category"].isin(["Drogued", "Undrogued"])
    & np.isfinite(pairs["speed_ms"])
].copy()

speed_summary = speed_data.groupby("drogue_category").agg(
    n_observations=("speed_ms", "size"),
    n_drifters=("traj", "nunique"),
    mean_speed=("speed_ms", "mean"),
    median_speed=("speed_ms", "median"),
    std_speed=("speed_ms", "std")
)

print("\nDROGUE SPEED COMPARISON")
print(speed_summary.round(4).to_string())

# Calculate the difference in average speed
mean_difference = (
    speed_summary.loc["Drogued", "mean_speed"]
    - speed_summary.loc["Undrogued", "mean_speed"]
)

print(
    "\nMean speed difference (Drogued - Undrogued):",
    round(mean_difference, 4),
    "m/s"
)

speed_summary.to_csv("drogue_speed_comparison.csv")
print("\nSaved: drogue_speed_comparison.csv")


# ==================================================
# STEP 5: Verify starting drogue-status agreement
# ==================================================

expected_status = speed_data["drogue_category"].eq("Drogued")
recorded_status = speed_data["noaa_drogue_status"].astype(bool)

agreement = (expected_status == recorded_status)

print("\nDROGUE STATUS VERIFICATION")
print("Observations checked:", len(agreement))
print("Matching statuses:", agreement.sum())
print("Agreement percentage:", round(100 * agreement.mean(), 3))


# ==================================================
# STEP 6: Compare speed within starting cells
# ==================================================

cell_speed = speed_data.groupby(
    ["origin_cell", "drogue_category"]
).agg(
    n_observations=("speed_ms", "size"),
    n_drifters=("traj", "nunique"),
    mean_speed=("speed_ms", "mean"),
    median_speed=("speed_ms", "median")
).reset_index()

# Require at least 10 distinct drifters per category
supported = cell_speed[
    cell_speed["n_drifters"] >= 10
]

# Keep cells containing both categories
both_speed = supported.pivot(
    index="origin_cell",
    columns="drogue_category",
    values=[
        "n_observations",
        "n_drifters",
        "mean_speed",
        "median_speed"
    ]
).dropna()

# Difference: drogued minus undrogued
both_speed["speed_difference"] = (
    both_speed[("mean_speed", "Drogued")]
    - both_speed[("mean_speed", "Undrogued")]
)

# Weight each cell by its combined observations
speed_weights = (
    both_speed[("n_observations", "Drogued")]
    + both_speed[("n_observations", "Undrogued")]
)

weighted_speed_difference = np.average(
    both_speed["speed_difference"],
    weights=speed_weights
)

print("\nWITHIN-CELL SPEED COMPARISON")
print("Supported cells:", len(both_speed))

print("\nDistribution of cell-level differences:")
print(both_speed["speed_difference"].describe())

print(
    "\nWeighted speed difference:",
    round(weighted_speed_difference, 4),
    "m/s"
)

print(
    "Weighted speed difference:",
    round(weighted_speed_difference * 100, 2),
    "cm/s"
)

both_speed.to_csv("drogue_speed_by_cell.csv")
print("\nSaved: drogue_speed_by_cell.csv")


# ==================================================
# STEP 7: Whole-drifter bootstrap for speed
# ==================================================

# Keep the original 153 supported cells
eligible_cells = both_speed.index.to_numpy(dtype=int)
fixed_weights = speed_weights.to_numpy(dtype=float)

# Only use observations in eligible cells
boot_data = speed_data[
    speed_data["origin_cell"].isin(eligible_cells)
].copy()

# Aggregate observations by entire drifter, cell and status
drifter_speed = boot_data.groupby(
    ["traj", "origin_cell", "drogue_category"]
).agg(
    n=("speed_ms", "size"),
    speed_sum=("speed_ms", "sum")
).reset_index()

drifters = drifter_speed["traj"].unique()

rng = np.random.default_rng(42)
n_bootstrap = 500

bootstrap_differences = []
valid_cell_counts = []

# Fixed order of starting cells and drogue categories
all_groups = pd.MultiIndex.from_product(
    [eligible_cells, ["Drogued", "Undrogued"]],
    names=["origin_cell", "drogue_category"]
)

print("\nRunning whole-drifter speed bootstrap...")

for b in range(n_bootstrap):

    # Sample entire drifters with replacement
    sampled_drifters = rng.choice(
        drifters,
        size=len(drifters),
        replace=True
    )

    multiplicities = (
        pd.Series(sampled_drifters).value_counts()
    )

    sample = drifter_speed[
        drifter_speed["traj"].isin(multiplicities.index)
    ].copy()

    sample["mult"] = sample["traj"].map(
        multiplicities
    )

    # Include all observations each selected drifter contributed
    sample["n"] *= sample["mult"]
    sample["speed_sum"] *= sample["mult"]

    aggregated = sample.groupby(
        ["origin_cell", "drogue_category"]
    )[["n", "speed_sum"]].sum()

    aggregated = aggregated.reindex(
        all_groups,
        fill_value=0
    )

    # Recalculate mean speeds by cell and drogue status
    mean_speeds = (
        aggregated["speed_sum"]
        / aggregated["n"].replace(0, np.nan)
    ).unstack()

    differences = (
        mean_speeds["Drogued"]
        - mean_speeds["Undrogued"]
    )

    valid = differences.notna()
    valid_cell_counts.append(int(valid.sum()))

    if not valid.any():
        continue

    # Same original cell weights
    boot_difference = np.average(
        differences[valid],
        weights=fixed_weights[valid.to_numpy()]
    )

    bootstrap_differences.append(boot_difference)


# ==================================================
# STEP 8: Confidence interval and diagnostics
# ==================================================

bootstrap_differences = np.array(
    bootstrap_differences
)

if len(bootstrap_differences) == 0:
    raise RuntimeError("No valid bootstrap replicates.")

lower, upper = np.percentile(
    bootstrap_differences,
    [2.5, 97.5]
)

print("\nSPEED BOOTSTRAP DIAGNOSTICS")
print("Successful replicates:", len(bootstrap_differences))
print("Minimum valid cells:", min(valid_cell_counts))
print("Median valid cells:", np.median(valid_cell_counts))
print("Maximum valid cells:", max(valid_cell_counts))

print(
    "Replicates retaining all cells:",
    sum(n == len(eligible_cells) for n in valid_cell_counts)
)

print("\nSPEED BOOTSTRAP RESULTS")
print(
    f"Adjusted difference: "
    f"{weighted_speed_difference * 100:.2f} cm/s"
)

print(
    f"95% bootstrap CI: "
    f"[{lower * 100:.2f}, {upper * 100:.2f}] cm/s"
)

# Save bootstrap replicates
pd.DataFrame({
    "speed_difference_ms": bootstrap_differences
}).to_csv(
    "drogue_speed_bootstrap.csv",
    index=False
)

print("\nSaved: drogue_speed_bootstrap.csv")


# ==================================================
# STEP 9: Plot adjusted speed difference with 95% CI
# ==================================================

import matplotlib.pyplot as plt

estimate = weighted_speed_difference * 100
ci_low = lower * 100
ci_high = upper * 100

fig, ax = plt.subplots(figsize=(8, 3))

ax.errorbar(
    estimate,
    0,
    xerr=[[estimate - ci_low], [ci_high - estimate]],
    fmt="o",
    color="navy",
    capsize=7,
    markersize=9,
    linewidth=2.5
)

ax.axvline(
    0,
    color="red",
    linestyle="--",
    linewidth=1.5,
    label="No difference"
)

ax.set_yticks([0])
ax.set_yticklabels(["Mean speed"])
ax.set_ylim(-0.5, 0.5)

ax.set_xlabel(
    "Drogued - Undrogued speed (cm/s)"
)

ax.set_title(
    "Drogue Status and Drifter Speed\n"
    "Location-adjusted difference with 95% bootstrap CI"
)

ax.grid(axis="x", alpha=0.2)
ax.legend(loc="upper right")

plt.tight_layout()
plt.savefig(
    "drogue_speed_confidence_intervals.png",
    dpi=300,
    bbox_inches="tight"
)
plt.show()

print("\nSaved: drogue_speed_confidence_intervals.png")

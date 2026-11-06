
import pandas as pd
import numpy as np

# ==================================================
# STEP 1: Load Lucy's seven-day pairs
# ==================================================

pairs = pd.read_csv("pairs7.csv")

pairs["time"] = pd.to_datetime(pairs["time"], utc=True)
pairs["end_time"] = pairs["time"] + pd.Timedelta(days=7)

print("Total pairs:", len(pairs))
print(pairs[["traj", "time", "end_time"]].head())


# ==================================================
# STEP 2: Load and attach drogue-loss dates
# ==================================================

drogue_info = pd.read_csv("drogue_info.csv")

drogue_info["drogue_lost_date"] = pd.to_datetime(
    drogue_info["drogue_lost_date"],
    utc=True
)

pairs = pairs.merge(
    drogue_info,
    on="traj",
    how="left",
    validate="many_to_one"
)

assert len(pairs) == 154139, "Unexpected number of pairs"


# ==================================================
# STEP 3: Classify drogue status over seven days
# ==================================================

def classify_drogue(row):
    lost = row["drogue_lost_date"]
    start = row["time"]
    end = row["end_time"]

    if pd.isna(lost):
        return "Unknown"

    if lost <= start:
        return "Undrogued"

    if lost > end:
        return "Drogued"

    return "Lost during window"


pairs["drogue_category"] = pairs.apply(
    classify_drogue,
    axis=1
)

print("\nDROGUE CLASSIFICATION")
print(pairs["drogue_category"].value_counts())

print("\nPercentage breakdown:")
print(
    pairs["drogue_category"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)

pairs.to_csv("pairs7_drogue.csv", index=False)
print("\nSaved: pairs7_drogue.csv")


# ==================================================
# STEP 4: Compare seven-day first-exit probabilities
# ==================================================

comparison = pairs[
    pairs["drogue_category"].isin(
        ["Drogued", "Undrogued"]
    )
].copy()

summary = comparison.groupby("drogue_category").agg(
    n_pairs=("traj", "size"),
    n_drifters=("traj", "nunique")
)

for name, code in [
    ("west", 234),
    ("east", 235),
    ("south", 236),
    ("north", 237)
]:
    summary[f"p_{name}"] = (
        comparison["dest"].eq(code)
        .groupby(comparison["drogue_category"])
        .mean()
    )

print("\nDROGUE EXIT COMPARISON")
print(summary.to_string(float_format=lambda x: f"{x:.4f}"))

summary.to_csv("drogue_exit_comparison.csv")
print("\nSaved: drogue_exit_comparison.csv")


# ==================================================
# STEP 5: Compare drogue groups within starting cells
# ==================================================

cell_summary = comparison.groupby(
    ["origin_cell", "drogue_category"]
).agg(
    n_pairs=("traj", "size"),
    n_drifters=("traj", "nunique"),
    p_west=("dest", lambda x: (x == 234).mean()),
    p_east=("dest", lambda x: (x == 235).mean())
).reset_index()

# Require at least 10 distinct drifters per group
supported = cell_summary[
    cell_summary["n_drifters"] >= 10
]

# Keep cells with both drogue groups represented
both = supported.pivot(
    index="origin_cell",
    columns="drogue_category",
    values=["n_pairs", "n_drifters", "p_west", "p_east"]
).dropna()

print("\nCELLS WITH BOTH DROGUE GROUPS SUPPORTED:")
print(len(both))

# Difference = drogued minus undrogued
both["west_difference"] = (
    both[("p_west", "Drogued")]
    - both[("p_west", "Undrogued")]
)

both["east_difference"] = (
    both[("p_east", "Drogued")]
    - both[("p_east", "Undrogued")]
)

print("\nWESTWARD EXIT DIFFERENCES")
print(both["west_difference"].describe())

print("\nEASTWARD EXIT DIFFERENCES")
print(both["east_difference"].describe())

both.to_csv("drogue_cell_comparison.csv")
print("\nSaved: drogue_cell_comparison.csv")


# ==================================================
# STEP 6: Weighted within-cell comparison
# ==================================================

# Weight each cell by its total number of pairs
weights = (
    both[("n_pairs", "Drogued")]
    + both[("n_pairs", "Undrogued")]
)

weighted_west = np.average(
    both["west_difference"],
    weights=weights
)

weighted_east = np.average(
    both["east_difference"],
    weights=weights
)

print("\nWEIGHTED WITHIN-CELL COMPARISON")
print("Cells included:", len(both))

print(
    "Weighted west difference:",
    round(weighted_west * 100, 3),
    "percentage points"
)

print(
    "Weighted east difference:",
    round(weighted_east * 100, 3),
    "percentage points"
)


# ==================================================
# STEP 7: Check informative starting cells
# ==================================================

informative = both[
    (both[("p_west", "Drogued")] > 0)
    | (both[("p_west", "Undrogued")] > 0)
    | (both[("p_east", "Drogued")] > 0)
    | (both[("p_east", "Undrogued")] > 0)
]

print("\nINFORMATIVE STARTING CELLS")
print("Supported cells:", len(both))
print(
    "Cells with at least one west/east exit:",
    len(informative)
)

print("\nCELLS WITH LARGEST WEST DIFFERENCES")
print(
    both["west_difference"]
    .abs()
    .sort_values(ascending=False)
    .head(10)
)

print("\nCELLS WITH LARGEST EAST DIFFERENCES")
print(
    both["east_difference"]
    .abs()
    .sort_values(ascending=False)
    .head(10)
)


# ==================================================
# STEP 8: Whole-drifter bootstrap confidence intervals
# ==================================================

# Retain original supported cells and weights
eligible_cells = both.index.to_numpy(dtype=int)
fixed_weights = weights.to_numpy(dtype=float)

# Prepare data
boot_data = comparison[
    comparison["origin_cell"].isin(eligible_cells)
].copy()

boot_data["is_west"] = (
    boot_data["dest"] == 234
).astype(int)

boot_data["is_east"] = (
    boot_data["dest"] == 235
).astype(int)

# Aggregate observations for each drifter
drifter_counts = boot_data.groupby(
    ["traj", "origin_cell", "drogue_category"]
).agg(
    n=("dest", "size"),
    west=("is_west", "sum"),
    east=("is_east", "sum")
).reset_index()

drifters = drifter_counts["traj"].unique()

rng = np.random.default_rng(42)

bootstrap_results = []

# Diagnostics: one entry per bootstrap replicate
valid_cell_counts = []

n_bootstrap = 500

for b in range(n_bootstrap):

    # Resample entire drifters with replacement
    sampled_drifters = rng.choice(
        drifters,
        size=len(drifters),
        replace=True
    )

    # Count how often each drifter is selected
    multiplicities = (
        pd.Series(sampled_drifters)
        .value_counts()
    )

    sample = drifter_counts[
        drifter_counts["traj"].isin(
            multiplicities.index
        )
    ].copy()

    sample["mult"] = sample["traj"].map(
        multiplicities
    )

    # Preserve every selected drifter's observations
    for col in ["n", "west", "east"]:
        sample[col] = sample[col] * sample["mult"]

    # Recalculate cell/category counts
    aggregated = sample.groupby(
        ["origin_cell", "drogue_category"]
    )[["n", "west", "east"]].sum()

    # Ensure identical ordering of cells/categories
    all_groups = pd.MultiIndex.from_product(
        [
            eligible_cells,
            ["Drogued", "Undrogued"]
        ],
        names=["origin_cell", "drogue_category"]
    )

    aggregated = aggregated.reindex(
        all_groups,
        fill_value=0
    )

    # Recalculate exit probabilities
    west_probs = (
        aggregated["west"]
        / aggregated["n"].replace(0, np.nan)
    ).unstack()

    east_probs = (
        aggregated["east"]
        / aggregated["n"].replace(0, np.nan)
    ).unstack()

    west_diff = (
        west_probs["Drogued"]
        - west_probs["Undrogued"]
    )

    east_diff = (
        east_probs["Drogued"]
        - east_probs["Undrogued"]
    )

    # Find cells with both groups present
    valid = (
        west_diff.notna()
        & east_diff.notna()
    )

    # Record valid-cell count for EVERY replicate
    valid_cell_counts.append(int(valid.sum()))

    # Skip replicate if no valid cells
    if not valid.any():
        continue

    # Keep original cell weights for valid cells
    current_weights = fixed_weights[
        valid.to_numpy()
    ]

    boot_west = np.average(
        west_diff[valid],
        weights=current_weights
    )

    boot_east = np.average(
        east_diff[valid],
        weights=current_weights
    )

    bootstrap_results.append([
        boot_west,
        boot_east
    ])


# ==================================================
# STEP 9: Bootstrap diagnostics
# ==================================================

print("\nBOOTSTRAP DIAGNOSTICS")

print(
    "Minimum valid cells:",
    min(valid_cell_counts)
)

print(
    "Median valid cells:",
    np.median(valid_cell_counts)
)

print(
    "Maximum valid cells:",
    max(valid_cell_counts)
)

print(
    f"Replicates retaining all {len(eligible_cells)} cells:",
    sum(
        n == len(eligible_cells)
        for n in valid_cell_counts
    )
)

print(
    "Successful bootstrap replicates:",
    len(bootstrap_results),
    "out of",
    n_bootstrap
)


# ==================================================
# STEP 10: Bootstrap confidence intervals
# ==================================================

bootstrap_results = np.array(bootstrap_results)

if len(bootstrap_results) == 0:
    raise RuntimeError(
        "No valid bootstrap replicates were produced."
    )

print("\nWHOLE-DRIFTER BOOTSTRAP RESULTS")

for i, direction in enumerate(["West", "East"]):

    lower, upper = np.percentile(
        bootstrap_results[:, i],
        [2.5, 97.5]
    )

    original = (
        weighted_west
        if direction == "West"
        else weighted_east
    )

    print(
        f"{direction}: "
        f"estimate = {original * 100:.3f} pp, "
        f"95% CI = "
        f"[{lower * 100:.3f}, "
        f"{upper * 100:.3f}] pp"
    )

pd.DataFrame(
    bootstrap_results,
    columns=[
        "west_difference",
        "east_difference"
    ]
).to_csv(
    "drogue_bootstrap_results.csv",
    index=False
)

print("\nSaved: drogue_bootstrap_results.csv")

# ==================================================
# STEP 11: Plot adjusted drogue differences with 95% CIs
# ==================================================

import matplotlib.pyplot as plt

estimates = np.array([weighted_west, weighted_east]) * 100

ci_lower = np.percentile(
    bootstrap_results, 2.5, axis=0
) * 100

ci_upper = np.percentile(
    bootstrap_results, 97.5, axis=0
) * 100

errors = np.vstack([
    estimates - ci_lower,
    ci_upper - estimates
])

fig, ax = plt.subplots(figsize=(8, 4.5))

ax.errorbar(
    estimates,
    ["Westward exit", "Eastward exit"],
    xerr=errors,
    fmt="o",
    capsize=6,
    markersize=8,
    linewidth=2,
    color="navy"
)

ax.axvline(
    0,
    color="red",
    linestyle="--",
    linewidth=1.5,
    label="No difference"
)

ax.set_xlabel(
    "Drogued − Undrogued (percentage points)"
)

ax.set_title(
    "Drogue Status and Seven-Day Exit Probabilities"
)

ax.legend()
ax.grid(axis="x", alpha=0.2)

plt.tight_layout()

plt.savefig(
    "drogue_exit_confidence_intervals.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
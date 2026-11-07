"""Yoyo - 2-degree coverage / support map for the 7-day transition matrix (Stage 2 Task C, Stage 7 Task B).

The poster's 171/178 statistic counted drifters that VISITED a cell. The matrix rows are estimated
from valid 7-day pairs, so here support = number of distinct drifters that contribute at least one
valid 7-day pair STARTING in the cell (Lucy's pairs7.csv, first-exit rule, unresolved pairs dropped).

Outputs (yoyo_outputs/):
  coverage_2deg_cells.csv            one row per 2-degree cell: pairs, distinct drifters, threshold flags
  coverage_2deg_by_season.csv        the same counts per season
  coverage_2deg_summary.csv          how many cells pass 10 / 25 / 50 distinct drifters
  fig_coverage_2deg.png              main map (for the slides)
  fig_coverage_2deg_by_season.png    the same map for each season
  fig_threshold_ci_width.png         how the bootstrap CI narrows as support grows (threshold check)
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Rectangle

from yoyo_common import (CELLS_ABC, LAT_EDGES, LON_EDGES, N_CELLS, OUT, SEASON_MONTHS, SEASONS, cell_bounds,
                         ci, draw_land, drifter_bootstrap, load_pairs7, mark_abc, style_map, to_grid)

THRESHOLDS = [10, 25, 50]
pairs = load_pairs7()

# ---------------------------------------------------------------- per-cell support
per_cell = pairs.groupby("origin_cell").agg(n_pairs=("traj", "size"), n_drifters=("traj", "nunique"),
                                            p_west=("west", "mean"), p_east=("east", "mean"))
cells = pd.DataFrame(index=pd.RangeIndex(N_CELLS, name="cell"))
b = np.array([cell_bounds(c) for c in cells.index])
cells["lon_min"], cells["lon_max"], cells["lat_min"], cells["lat_max"] = b.T
cells = cells.join(per_cell)
cells[["n_pairs", "n_drifters"]] = cells[["n_pairs", "n_drifters"]].fillna(0).astype(int)
for t in THRESHOLDS:
    cells[f"ge{t}"] = cells.n_drifters >= t
cells["abc"] = cells.index.map({v: k for k, v in CELLS_ABC.items()})

# Threshold check: whole-drifter bootstrap CI of P(drifter has left its starting cell after 7 days)
# for every cell. Defined for every cell (exit probabilities are ~0 in interior cells).
groups, den, rates, *_ = drifter_bootstrap(pairs, "origin_cell", ["left_cell"], n_boot=1000, seed=42)
lo, hi = ci(rates["left_cell"])
cells.loc[groups, "ci_width_left_cell"] = hi - lo
cells.loc[cells.n_drifters < 2, "ci_width_left_cell"] = np.nan  # one drifter: bootstrap CI is meaningless
cells.to_csv(OUT / "coverage_2deg_cells.csv")

occupied = cells[cells.n_pairs > 0]
summary = pd.DataFrame({
    "cells_total": [N_CELLS],
    "cells_with_valid_pairs": [len(occupied)],
    **{f"cells_ge{t}_drifters": [int((occupied.n_drifters >= t).sum())] for t in THRESHOLDS},
    "median_drifters_per_cell": [float(occupied.n_drifters.median())],
    "p25_drifters_per_cell": [float(occupied.n_drifters.quantile(0.25))],
    "share_of_pairs_in_ge10_cells": [occupied.loc[occupied.ge10, "n_pairs"].sum() / occupied.n_pairs.sum()],
})
summary.to_csv(OUT / "coverage_2deg_summary.csv", index=False)
print("\n2-degree support from valid 7-day pairs (poster visitation stat was 171/178 cells with >=10 drifters):")
print(summary.T.to_string(header=False))
print("\nA/B/C support:")
print(cells.loc[list(CELLS_ABC.values()), ["abc", "lon_min", "lon_max", "lat_min", "lat_max", "n_pairs", "n_drifters"]])

# CI width by support band
band = pd.cut(occupied.n_drifters, [0, 9, 24, 49, 99, 10**6], labels=["1-9", "10-24", "25-49", "50-99", "100+"])
ci_by_band = cells.loc[occupied.index].groupby(band, observed=True).ci_width_left_cell.agg(["size", "median", "max"])
ci_by_band.to_csv(OUT / "coverage_ci_width_by_band.csv")
print("\nBootstrap 95% CI width of P(left starting cell in 7 days), by distinct-drifter band:")
print(ci_by_band.round(3))

# ---------------------------------------------------------------- per-season support
by_season = (pairs.groupby(["season", "origin_cell"], observed=True)
             .agg(n_pairs=("traj", "size"), n_drifters=("traj", "nunique")).reset_index())
by_season.to_csv(OUT / "coverage_2deg_by_season.csv", index=False)
season_summary = by_season.groupby("season", observed=True).agg(
    cells_with_pairs=("origin_cell", "size"),
    cells_ge10=("n_drifters", lambda x: int((x >= 10).sum())),
    cells_ge25=("n_drifters", lambda x: int((x >= 25).sum())),
    median_drifters=("n_drifters", "median"))
print("\nSupport per season:")
print(season_summary)

# ---------------------------------------------------------------- figures
BINS = [1, 10, 25, 50, 100, 150, max(250, int(cells.n_drifters.max()) + 1)]
CMAP = ListedColormap(["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#104281"])
CMAP.set_bad((0, 0, 0, 0))
NORM = BoundaryNorm(BINS, CMAP.N)


def coverage_panel(ax, n_by_cell, fontsize=9):
    grid = to_grid(n_by_cell)
    grid[grid == 0] = np.nan
    draw_land(ax)
    mesh = ax.pcolormesh(LON_EDGES, LAT_EDGES, grid, cmap=CMAP, norm=NORM, edgecolor="white", linewidth=0.4, zorder=1)
    for cell, n in dict(n_by_cell).items():          # outline cells below the 10-drifter threshold
        if 0 < n < 10:
            lon0, lon1, lat0, lat1 = cell_bounds(cell)
            ax.add_patch(Rectangle((lon0, lat0), lon1 - lon0, lat1 - lat0, fill=False, edgecolor="#d1495b",
                                   linewidth=1.2, zorder=4))
    mark_abc(ax, fontsize=fontsize)
    style_map(ax, fontsize=fontsize - 1)
    return mesh


fig, ax = plt.subplots(figsize=(8.5, 6.2))
mesh = coverage_panel(ax, cells.n_drifters, fontsize=11)
cb = fig.colorbar(mesh, ax=ax, shrink=0.8, ticks=BINS[:-1])
cb.set_label("Distinct drifters with valid 7-day pairs starting in the cell", fontsize=10)
n_ok = int(occupied.ge10.sum())
ax.set_title(f"2° support for the 7-day transition matrix: {n_ok}/{len(occupied)} starting cells "
             f"have ≥10 drifters\n(red outline = fewer than 10 drifters; A, B, C = poster starting cells)",
             fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "fig_coverage_2deg.png", dpi=200)
plt.close(fig)

fig, axes = plt.subplots(2, 2, figsize=(12, 9.2))
for ax, s in zip(axes.flat, SEASONS):
    sub = by_season[by_season.season == s].set_index("origin_cell").n_drifters
    mesh = coverage_panel(ax, sub)
    ax.set_title(f"{s} ({SEASON_MONTHS[s]}): {int((sub >= 10).sum())}/{len(sub)} cells ≥10 drifters", fontsize=11)
fig.colorbar(mesh, ax=axes, shrink=0.6, ticks=BINS[:-1], label="Distinct drifters with valid 7-day pairs")
fig.suptitle("2° support by season of the pair's start date (red outline = fewer than 10 drifters)", fontsize=12)
fig.savefig(OUT / "fig_coverage_2deg_by_season.png", dpi=170, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(7.5, 4.8))
o = cells.loc[occupied.index]
ax.scatter(o.n_drifters, o.ci_width_left_cell, s=14, color="#3987e5", alpha=0.75)
for t, ls in zip(THRESHOLDS, [":", "--", "-."]):
    ax.axvline(t, color="#d1495b", linestyle=ls, linewidth=1, label=f"{t} drifters")
for name, cell in CELLS_ABC.items():
    ax.annotate(name, (o.n_drifters[cell], o.ci_width_left_cell[cell]), xytext=(4, 4),
                textcoords="offset points", fontweight="bold")
ax.set_xscale("log")
ax.set_xlabel("Distinct drifters with valid 7-day pairs (log scale)")
ax.set_ylabel("Width of 95% bootstrap CI")
ax.set_title("Uncertainty vs support: P(drifter has left its starting cell after 7 days)", fontsize=11)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUT / "fig_threshold_ci_width.png", dpi=200)
plt.close(fig)
print(f"\nSaved figures and tables to {OUT}")

"""Yoyo - drogued vs undrogued transport from A, B and C (Stage 7 Task A).

Builds on Vrishin's vrishindrogue.py, which compares 7-day first-exit probabilities per starting cell.
None of the A/B/C starts exits within 7 days, so for those cells this script uses the same approach as
the seasonal analysis:

Drogue status of a 7-day pair (Vrishin's rule, drogue_info.csv):
  Drogued    the drogue is lost AFTER the 7-day window ends
  Undrogued  the drogue was lost on or before the start
  pairs where the drogue is lost during the window, or the date is unknown, are left out

Part 1  Support: distinct drifters per 2-degree cell for drogued-only and undrogued-only pairs;
        which cells fall below 10 drifters (plan: "report which cells fall below the support threshold").
Part 2  Matrix: P from drogued-only pairs vs P from undrogued-only pairs (Vrishin's
        build_transition_matrix, all drifters as in the poster), west / east exit from A, B, C at
        28 / 56 / 91 days, whole-drifter bootstrap CIs and a paired CI of drogued - undrogued.
Part 3  Observed: Lucy's week-by-week chaining (train + val drifters, test locked), split by the
        drogue status at the START. A drogued start can lose its drogue before day 91, so this is
        "drogued at release", which is what matters for e.g. a freshly deployed drifter.

Outputs (yoyo_outputs/):
  drogue_support_cells.csv, drogue_ABC_matrix.csv, drogue_ABC_observed.csv, drogue_ABC_observed_support.csv,
  fig_drogue_support.png, fig_drogue_ABC.png
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Rectangle

from yoyo_common import (CELLS_ABC, HERE, LAT_EDGES, LON_EDGES, MIN_DRIFTERS, N_CELLS, N_STATES, OUT, cell_bounds,
                         chain_outcomes, ci, draw_land, exit_at, find_split, load_pairs7, load_shared_functions,
                         mark_abc, style_map, to_grid, to_P)

N_BOOT = 1000
HORIZONS = {28: 4, 56: 8, 91: 13}
GROUPS = ["Drogued", "Undrogued"]
MIN_EFFECT = 0.01   # 1 pp, same reason as yoyo_seasonal_validation.py
build_transition_matrix, _ = load_shared_functions()
pd.set_option("display.width", 220)

pairs = load_pairs7()
lost = pd.read_csv(HERE / "drogue_info.csv")
lost = pd.to_datetime(pairs.traj.map(dict(zip(lost.traj, lost.drogue_lost_date))), utc=True)
t0 = pd.to_datetime(pairs.time, utc=True)
pairs["drogue"] = np.select([lost.isna(), lost <= t0, lost > t0 + pd.Timedelta(days=7)],
                            ["Unknown", "Undrogued", "Drogued"], "Lost during window")
print("Pairs by drogue status:", pairs.drogue.value_counts().to_dict())
# same split as Vrishin's drogue_exit_comparison.csv
vr = pd.read_csv(HERE / "drogue_exit_comparison.csv").set_index("drogue_category")
for g in GROUPS:
    assert (pairs.drogue == g).sum() == vr.loc[g, "n_pairs"], f"{g} pair count differs from Vrishin's"

# ============================================================== Part 1: support
sup = (pairs[pairs.drogue.isin(GROUPS)].groupby(["origin_cell", "drogue"]).traj.nunique()
       .unstack(fill_value=0).reindex(range(N_CELLS), fill_value=0)[GROUPS])
sup["All"] = pairs.groupby("origin_cell").traj.nunique().reindex(range(N_CELLS), fill_value=0)
sup.index.name = "cell"
sup.to_csv(OUT / "drogue_support_cells.csv")
ok_all = sup.All >= MIN_DRIFTERS
print(f"\nPart 1. Cells with >= {MIN_DRIFTERS} distinct drifters (of {int((sup.All > 0).sum())} cells with pairs):")
for g in ["All"] + GROUPS:
    print(f"  {g:10s}: {int((sup[g] >= MIN_DRIFTERS).sum())}")
print(f"  supported overall but < {MIN_DRIFTERS} drogued drifters: {int((ok_all & (sup.Drogued < MIN_DRIFTERS)).sum())}")
print(f"  supported overall but < {MIN_DRIFTERS} undrogued drifters: {int((ok_all & (sup.Undrogued < MIN_DRIFTERS)).sum())}")
print("  A/B/C:", sup.loc[list(CELLS_ABC.values()), GROUPS].rename(index={v: k for k, v in CELLS_ABC.items()})
      .to_dict("index"))

# ============================================================== Part 2: matrix, drogued vs undrogued
steps = list(HORIZONS.values())
sub = {g: pairs[pairs.drogue == g] for g in GROUPS}
P_shared = {g: build_transition_matrix(sub[g])[0] for g in GROUPS}

traj_codes, traj_idx = np.unique(pairs.traj.to_numpy(), return_inverse=True)
D = len(traj_codes)
codes = pairs.origin_cell.to_numpy() * N_STATES + pairs.dest.to_numpy()
masks = {g: (pairs.drogue == g).to_numpy() for g in GROUPS}


def P_for(weights, g):
    m = masks[g]
    return to_P(np.bincount(codes[m], weights=weights[traj_idx][m], minlength=N_STATES ** 2)
                .reshape(N_STATES, N_STATES))


for g in GROUPS:
    assert np.allclose(P_for(np.ones(D), g), P_shared[g]), "rebuild differs from build_transition_matrix"

rng = np.random.default_rng(3001)
W = rng.multinomial(D, np.full(D, 1.0 / D), size=N_BOOT).astype(float)
cells = list(CELLS_ABC.values())
point = {g: {c: exit_at(P_shared[g], c, steps) for c in cells} for g in GROUPS}
boot = {g: np.zeros((N_BOOT, len(cells), len(steps), 2)) for g in GROUPS}
print(f"\nBootstrapping drogued / undrogued matrices ({N_BOOT} resamples)...")
for b in range(N_BOOT):
    for g in GROUPS:
        P = P_for(W[b], g)
        for i, c in enumerate(cells):
            e = exit_at(P, c, steps)
            boot[g][b, i] = [e[k] for k in steps]

rows = []
for i, (name, c) in enumerate(CELLS_ABC.items()):
    for h, (days, k) in enumerate(HORIZONS.items()):
        for j, side in enumerate(["west", "east"]):
            r = dict(cell=name, days=days, side=side)
            for g in GROUPS:
                r[g] = point[g][c][k][j]
                r[f"{g}_lo"], r[f"{g}_hi"] = ci(boot[g][:, i, h, j])
            d = r["Drogued"] - r["Undrogued"]
            lo, hi = ci(boot["Drogued"][:, i, h, j] - boot["Undrogued"][:, i, h, j])
            r.update(diff=d, diff_lo=lo, diff_hi=hi, exceeds_uncertainty=bool((lo > 0 or hi < 0) and abs(d) >= MIN_EFFECT))
            rows.append(r)
mat = pd.DataFrame(rows)
mat.to_csv(OUT / "drogue_ABC_matrix.csv", index=False)


def pct(p, lo, hi):
    return "n/a" if pd.isna(p) else f"{100 * p:4.1f} [{100 * lo:4.1f}, {100 * hi:4.1f}]"


print("\nPart 2. Matrix exit probability from A/B/C, drogued vs undrogued (%, 95% whole-drifter bootstrap CI):")
t = mat[mat.days.isin([56, 91])]
print(pd.DataFrame({"cell": t.cell, "days": t.days, "side": t.side,
                    "drogued": [pct(r.Drogued, r.Drogued_lo, r.Drogued_hi) for r in t.itertuples()],
                    "undrogued": [pct(r.Undrogued, r.Undrogued_lo, r.Undrogued_hi) for r in t.itertuples()],
                    "drogued - undrogued": [pct(r.diff, r.diff_lo, r.diff_hi) + (" *" if r.exceeds_uncertainty else "")
                                            for r in t.itertuples()]}).to_string(index=False))

# ============================================================== Part 3: observed, by status at the start
split = pd.read_csv(find_split())
dev = pairs[pairs.traj.map(dict(zip(split.traj, split.split))) != "test"].reset_index(drop=True)
d_codes, d_idx = np.unique(dev.traj.to_numpy(), return_inverse=True)
Dd = len(d_codes)
pos_of = pd.Series(np.arange(Dd), index=d_codes)
Wd = np.random.default_rng(13).multinomial(Dd, np.full(Dd, 1.0 / Dd), size=N_BOOT).astype(float)
rows, support = [], []
for days, k in HORIZONS.items():
    o_all = chain_outcomes(dev, cells, k)
    o_all = o_all[o_all.drogue.isin(GROUPS)]
    for name, c in CELLS_ABC.items():
        oc = o_all[o_all.origin_cell == c]
        for g in GROUPS:
            og = oc[oc.drogue == g]
            support.append(dict(cell=name, days=days, group=g, starts=len(og),
                                censored=int((og.out == "censored").sum()),
                                drifters=og[og.out != "censored"].traj.nunique()))
        oc = oc[oc.out != "censored"]
        p = pos_of[oc.traj.values].values
        gk = (oc.drogue == "Undrogued").to_numpy(int)
        n_dg = np.zeros((Dd, 2))
        np.add.at(n_dg, (p, gk), 1)
        den = Wd @ n_dg
        for side in ["west", "east"]:
            hit = (oc.out == side).to_numpy(float)
            num_dg = np.zeros((Dd, 2))
            np.add.at(num_dg, (p, gk), hit)
            with np.errstate(invalid="ignore", divide="ignore"):
                bs = (Wd @ num_dg) / den
                est = num_dg.sum(0) / n_dg.sum(0)
            r = dict(cell=name, days=days, side=side)
            for q, g in enumerate(GROUPS):
                r[g] = est[q]
                r[f"{g}_lo"], r[f"{g}_hi"] = ci(bs[:, q])
                r[f"{g}_drifters"] = oc[oc.drogue == g].traj.nunique()
            d = est[0] - est[1]
            lo, hi = ci(bs[:, 0] - bs[:, 1])
            r.update(diff=d, diff_lo=lo, diff_hi=hi, exceeds_uncertainty=bool((lo > 0 or hi < 0) and abs(d) >= MIN_EFFECT))
            rows.append(r)
obs = pd.DataFrame(rows)
obs.to_csv(OUT / "drogue_ABC_observed.csv", index=False)
pd.DataFrame(support).to_csv(OUT / "drogue_ABC_observed_support.csv", index=False)
print("\nPart 3. Observed exits (train + val drifters), by drogue status at the start (%, 95% CI):")
t = obs[obs.days.isin([56, 91])]
print(pd.DataFrame({"cell": t.cell, "days": t.days, "side": t.side,
                    "n_drg": t.Drogued_drifters, "drogued": [pct(r.Drogued, r.Drogued_lo, r.Drogued_hi) for r in t.itertuples()],
                    "n_und": t.Undrogued_drifters,
                    "undrogued": [pct(r.Undrogued, r.Undrogued_lo, r.Undrogued_hi) for r in t.itertuples()],
                    "drogued - undrogued": [pct(r.diff, r.diff_lo, r.diff_hi) + (" *" if r.exceeds_uncertainty else "")
                                            for r in t.itertuples()]}).to_string(index=False))

# ============================================================== figures
BINS = [1, 10, 25, 50, 100, 150, max(250, int(sup.All.max()) + 1)]
CMAP = ListedColormap(["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#104281"])
NORM = BoundaryNorm(BINS, CMAP.N)
fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
for ax, g in zip(axes, GROUPS):
    n = sup[g]
    grid = to_grid(n.where(n > 0))
    draw_land(ax)
    mesh = ax.pcolormesh(LON_EDGES, LAT_EDGES, grid, cmap=CMAP, norm=NORM, edgecolor="white", linewidth=0.4, zorder=1)
    for cell in sup.index[ok_all & (n < MIN_DRIFTERS)]:
        lon0, lon1, lat0, lat1 = cell_bounds(cell)
        ax.add_patch(Rectangle((lon0, lat0), lon1 - lon0, lat1 - lat0, fill=False, edgecolor="#d1495b",
                               linewidth=1.2, zorder=4))
    mark_abc(ax)
    style_map(ax)
    lost_cells = int((ok_all & (n < MIN_DRIFTERS)).sum())
    ax.set_title(f"{g} pairs: {int((n >= MIN_DRIFTERS).sum())} cells ≥{MIN_DRIFTERS} drifters\n"
                 f"red: <{MIN_DRIFTERS} {g.lower()} drifters ({lost_cells} cells)", fontsize=11)
fig.colorbar(mesh, ax=axes, shrink=0.8, ticks=BINS[:-1], label="Distinct drifters with valid 7-day pairs")
fig.savefig(OUT / "fig_drogue_support.png", dpi=180, bbox_inches="tight")
plt.close(fig)

COL = {"Drogued": "#3987e5", "Undrogued": "#edae49"}
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
x = np.arange(len(CELLS_ABC))
for ax, side in zip(axes, ["west", "east"]):
    for q, g in enumerate(GROUPS):
        m91 = mat[(mat.days == 91) & (mat.side == side)].set_index("cell").loc[list(CELLS_ABC)]
        o91 = obs[(obs.days == 91) & (obs.side == side)].set_index("cell").loc[list(CELLS_ABC)]
        off = (q - 0.5) * 0.36
        ax.errorbar(x + off - 0.07, 100 * m91[g], yerr=[100 * (m91[g] - m91[f"{g}_lo"]), 100 * (m91[f"{g}_hi"] - m91[g])],
                    fmt="o", mfc="white", color=COL[g], capsize=3, ms=7, label=f"{g}, matrix P¹³")
        ax.errorbar(x + off + 0.07, 100 * o91[g], yerr=[100 * (o91[g] - o91[f"{g}_lo"]), 100 * (o91[f"{g}_hi"] - o91[g])],
                    fmt="o", color=COL[g], capsize=3, ms=7, label=f"{g}, observed")
    ax.set_xticks(x)
    ax.set_xticklabels(list(CELLS_ABC))
    ax.set_title(f"{side.capitalize()} exit by day 91", fontsize=11)
    ax.grid(axis="y", alpha=0.3)
axes[0].set_ylabel("% of starts")
axes[1].legend(frameon=False, fontsize=8)
fig.suptitle("Drogued vs undrogued starts from A, B, C at 91 days (95% whole-drifter bootstrap CIs)\n"
             "open = matrix from that group's pairs (all drifters); filled = observed outcome (train + val drifters)",
             fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "fig_drogue_ABC.png", dpi=180)
plt.close(fig)
print(f"\nSaved tables and figures to {OUT}")

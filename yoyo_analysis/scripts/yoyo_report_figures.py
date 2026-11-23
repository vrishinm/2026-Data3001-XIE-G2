"""Report Figures 5.1 and 5.2, drawn on the same samples the report uses.

1. Exit-probability maps for every start cell (RQ2). The matrix is fitted on training drifters only,
   as in Table 6.5 and Section 7, so B gives 20.0% west / 4.4% east by day 91 and C gives 38.0% east.
   Cells with fewer than 10 training drifters are hatched. Drawn at 91 days (main) and 28 days (option).
2. Drogued vs undrogued exits by day 91 at A, B and C: observed week-by-week paths, censoring-corrected,
   training + validation drifters, 95% whole-drifter bootstrap CIs (results/drogue_ABC_observed.csv,
   written by yoyo_drogue_ABC.py, so run that script first).
   No matrix markers, so test drifters are not used anywhere.

Output: yoyo_analysis/figures/fig_exit_maps_91d_train.png (Figure 5.1), fig_exit_maps_28d_train.png (not in
the report), fig_drogue_ABC_91d.png (Figure 5.2) and results/exit_maps_ABC_check.csv. 300 dpi, A4 text width.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from yoyo_common import (CELLS_ABC, EXIT, FIG, LAT_EDGES, LON_EDGES, MIN_DRIFTERS, N_STATES, OUT, cell_bounds,
                         draw_land, find_split, load_pairs7, mark_abc, style_map, to_P, to_grid)

WEST_C, EAST_C = "#2E6F9E", "#D8613C"
DROGUED_C, UNDROGUED_C = "#3D405B", "#1B998B"
INK, MUTED = "#1F2933", "#5B6670"

plt.rcParams.update({
    "font.family": "Arial", "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.edgecolor": "#C9CED4", "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold",
    "axes.titlecolor": INK, "savefig.dpi": 300, "savefig.bbox": "tight",
})


def save(fig, name):
    fig.savefig(FIG / name, facecolor="white")
    plt.close(fig)
    print("wrote", FIG / name)


# ---------- 1. exit maps, training drifters only ----------
pairs = load_pairs7()
split = pd.read_csv(find_split())
train_ids = set(split.loc[split["split"] == "train", "traj"])
tr = pairs[pairs.traj.isin(train_ids)]
print(f"training: {len(tr):,} pairs, {tr.traj.nunique()} drifters")

counts = np.bincount(tr.origin_cell.to_numpy() * N_STATES + tr.dest.to_numpy(),
                     minlength=N_STATES * N_STATES).reshape(N_STATES, N_STATES).astype(float)
P = to_P(counts)
support = tr.groupby("origin_cell").traj.nunique()
shown = support[support >= MIN_DRIFTERS].index
print(f"cells with >= {MIN_DRIFTERS} training drifters: {len(shown)} of {len(support)} with pairs")

bins = [0, 5, 10, 20, 30, 40, 60, 100]
rows = []
for steps in (13, 4):
    Pk = np.linalg.matrix_power(P, steps)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.75))
    for ax, side, cm in [(axes[0], "west", plt.cm.Blues), (axes[1], "east", plt.cm.Oranges)]:
        vals = {c: 100 * Pk[c, EXIT[side]] for c in shown}
        cmap = ListedColormap(cm(np.linspace(0.12, 0.95, 7)))
        cmap.set_bad((0, 0, 0, 0))
        draw_land(ax)
        mesh = ax.pcolormesh(LON_EDGES, LAT_EDGES, to_grid(vals), cmap=cmap, norm=BoundaryNorm(bins, cmap.N),
                             edgecolor="white", linewidth=0.3, zorder=1)
        for c, n in support.items():
            if n < MIN_DRIFTERS:
                x0, x1, y0, y1 = cell_bounds(c)
                ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#EEF0F2", edgecolor="#B0B7BF",
                                       hatch="////", linewidth=0.4, zorder=2))
        mark_abc(ax, fontsize=8)
        style_map(ax, fontsize=7)
        label = "West (Atlantic)" if side == "west" else "East (Indian Ocean)"
        ax.set_title(f"{label} exit by day {7 * steps}", loc="left")
        cb = fig.colorbar(mesh, ax=ax, shrink=0.8, ticks=bins, pad=0.02)
        cb.set_label("% of starts", fontsize=8)
        cb.ax.tick_params(labelsize=7)
        for name, cell in CELLS_ABC.items():
            rows.append(dict(days=7 * steps, cell=name, side=side, matrix_pct=round(100 * Pk[cell, EXIT[side]], 1)))
    fig.tight_layout(w_pad=1.0)
    save(fig, f"fig_exit_maps_{7 * steps}d_train.png")
check = pd.DataFrame(rows)
print(check.to_string(index=False))
check.to_csv(OUT / "exit_maps_ABC_check.csv", index=False)

# ---------- 2. drogued vs undrogued, observed only ----------
do = pd.read_csv(OUT / "drogue_ABC_observed.csv")
do = do[do.days == 91]
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7), sharey=True)
x = np.arange(3)
for ax, side, title in [(axes[0], "west", "West (Atlantic) exit by day 91"),
                        (axes[1], "east", "East (Indian Ocean) exit by day 91")]:
    d = do[do.side == side].set_index("cell").loc[list(CELLS_ABC)]
    for off, g, col in [(-0.14, "Drogued", DROGUED_C), (0.14, "Undrogued", UNDROGUED_C)]:
        y = 100 * d[g].to_numpy()
        err = [y - 100 * d[f"{g}_lo"].to_numpy(), 100 * d[f"{g}_hi"].to_numpy() - y]
        ax.errorbar(x + off, y, yerr=err, fmt="o", color=col, markersize=5, capsize=3, linewidth=1.2)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{c}\n(n = {int(d.loc[c, 'Drogued_drifters'])} / {int(d.loc[c, 'Undrogued_drifters'])})"
                        for c in CELLS_ABC])
    ax.set_xlim(-0.5, 2.5)
    ax.set_title(title, loc="left")
    ax.grid(axis="y", color="#E6E9ED")
axes[0].set_ylabel("Starts that left R (%)")
handles = [Line2D([], [], color=DROGUED_C, marker="o", lw=1.2, markersize=5, label="Drogued at start"),
           Line2D([], [], color=UNDROGUED_C, marker="o", lw=1.2, markersize=5, label="Undrogued at start")]
fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.06))
fig.tight_layout(rect=(0, 0.06, 1, 1))
save(fig, "fig_drogue_ABC_91d.png")
print(do[["cell", "side", "Drogued", "Drogued_lo", "Drogued_hi", "Drogued_drifters",
          "Undrogued", "Undrogued_lo", "Undrogued_hi", "Undrogued_drifters"]].round(3).to_string(index=False))

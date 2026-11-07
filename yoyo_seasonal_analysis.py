"""Yoyo - seasonal transport analysis (Stage 5 Task A).

Each 7-day pair from Lucy's pairs7.csv gets the austral season of its START date
(Summer Dec-Feb, Autumn Mar-May, Winter Jun-Aug, Spring Sep-Nov).

Part 1  Seasonal 7-day transition matrices built with Vrishin's build_transition_matrix.
Part 2  Region-wide 7-day west / east first-exit probability per season, 95% CI from Vrishin's
        whole-drifter bootstrap_exit_probability (all starting cells pooled).
Part 3  Starting cells A, B, C. They sit well inside R, so NO drifter leaves R within 7 days from
        them; the poster's A/B/C numbers are multi-step (P^n). Here: west / east exit probability at
        28 days (P^4) and 91 days (P^13, unvalidated projection) from each season's matrix, with
        whole-drifter bootstrap CIs (the same resampled drifters for every season, so
        "season minus rest of year" differences get a valid paired CI).
Part 4  Per-cell seasonal 7-day exit probabilities (maps), cells with >= 10 distinct drifters only.

Outputs go to yoyo_outputs/ (see the README section "Yoyo - seasonal analysis").
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from yoyo_common import (CELLS_ABC, EXIT, LAT_EDGES, LON_EDGES, MIN_DRIFTERS, N_CELLS, OUT, SEASON_MONTHS, SEASONS,
                         ci, draw_land, drifter_bootstrap, load_pairs7, load_shared_functions, mark_abc, style_map,
                         to_grid)

N_BOOT = 1000
N_STATES = N_CELLS + 4
HORIZONS = {7: 1, 28: 4, 91: 13}       # days -> number of 7-day steps
MIN_EFFECT = 0.001  # 0.1 pp: smaller "significant" differences are numerical zeros (no exits at all)
build_transition_matrix, bootstrap_exit_probability = load_shared_functions()
pairs = load_pairs7()
pd.set_option("display.width", 220)


def fmt(p, lo, hi):
    return "n/a" if pd.isna(p) else f"{p:.1%} [{lo:.1%}, {hi:.1%}]"


# ============================================================== Part 1: seasonal matrices (shared function)
mats, shared_P = {}, {}
for s in ["All year"] + SEASONS:
    sub = pairs if s == "All year" else pairs[pairs.season == s]
    P, C, rt = build_transition_matrix(sub)
    shared_P[s] = P
    key = s.replace(" ", "_")
    mats[f"{key}_P"], mats[f"{key}_counts"] = P, C
np.savez_compressed(OUT / "seasonal_matrices.npz", **mats)

# ============================================================== Part 2: region-wide 7-day exits
rows = []
pooled = pairs.assign(origin_cell=-1)            # every pair labelled the same -> Vrishin's bootstrap pools all cells
for s in ["All year"] + SEASONS:
    sub = pooled if s == "All year" else pooled[pooled.season == s]
    row = dict(season=s, months=SEASON_MONTHS.get(s, "Jan-Dec"), n_pairs=len(sub), n_drifters=sub.traj.nunique())
    for side in ["west", "east"]:
        est, lo, hi, _ = bootstrap_exit_probability(sub, starting_cell=-1, exit_state=EXIT[side],
                                                    n_bootstrap=N_BOOT, seed=42)
        row.update({f"p_{side}": est, f"p_{side}_lo": lo, f"p_{side}_hi": hi})
    rows.append(row)
region = pd.DataFrame(rows)
region.to_csv(OUT / "seasonal_region_7day_exits.csv", index=False)

contr = []
groups, den, rates, W, n = drifter_bootstrap(pairs, "season", ["west", "east"], n_boot=N_BOOT, seed=7)
for side in ["west", "east"]:
    num = rates[side] * den
    obs = pairs.groupby("season", observed=True)[side].agg(["sum", "size"])
    for j, s in enumerate(groups):
        rest = (num.sum(1) - num[:, j]) / (den.sum(1) - den[:, j])
        est = obs.loc[s, "sum"] / obs.loc[s, "size"] - (obs["sum"].sum() - obs.loc[s, "sum"]) / (
            obs["size"].sum() - obs.loc[s, "size"])
        lo, hi = ci(rates[side][:, j] - rest)
        contr.append(dict(unit="Region (all cells)", horizon_days=7, side=side, season=s, diff_vs_rest=est,
                          lo=lo, hi=hi, exceeds_uncertainty=bool((lo > 0 or hi < 0) and abs(est) >= MIN_EFFECT)))

print("\nPart 2. Region-wide 7-day first-exit probability by season (95% whole-drifter bootstrap CI):")
print(pd.DataFrame({"season": region.season, "pairs": region.n_pairs, "drifters": region.n_drifters,
                    "west": [fmt(r.p_west, r.p_west_lo, r.p_west_hi) for r in region.itertuples()],
                    "east": [fmt(r.p_east, r.p_east_lo, r.p_east_hi) for r in region.itertuples()]}).to_string(index=False))

# ============================================================== Part 3: A, B, C at 28 / 91 days
abc_7day = pairs[pairs.origin_cell.isin(CELLS_ABC.values())].groupby("origin_cell")[["west", "east"]].sum()
print("\nPart 3. Exits within 7 days from A/B/C (all seasons):", abc_7day.to_dict("index"),
      "-> A/B/C need multi-step horizons")

traj_codes, traj_idx = np.unique(pairs.traj.to_numpy(), return_inverse=True)
codes = pairs.origin_cell.to_numpy() * N_STATES + pairs.dest.to_numpy()
season_idx = pairs.season.cat.codes.to_numpy()
starts = np.array(list(CELLS_ABC.values()))


def to_P(counts):
    """Same rule as Vrishin's build_transition_matrix: row-normalise, unsupported rows stay zero, exits absorbing."""
    rt = counts.sum(1)
    P = np.divide(counts, rt[:, None], out=np.zeros_like(counts), where=rt[:, None] > 0)
    P[N_CELLS:, N_CELLS:] = np.eye(4)
    return P, rt


def season_counts(weights):
    """(4, N_STATES, N_STATES) transition counts, each pair weighted by how often its drifter was drawn."""
    w = weights[traj_idx]
    return np.stack([np.bincount(codes[season_idx == k], weights=w[season_idx == k],
                                 minlength=N_STATES ** 2).reshape(N_STATES, N_STATES) for k in range(4)])


def horizon_probs(P, rt):
    """For starts A, B, C: (west, east, unresolved) mass at each horizon. nan if the start row is unsupported."""
    v = np.zeros((len(starts), N_STATES))
    v[np.arange(len(starts)), starts] = 1.0
    out = {}
    for step in range(1, max(HORIZONS.values()) + 1):
        v = v @ P
        if step in HORIZONS.values():
            res = np.stack([v[:, EXIT["west"]], v[:, EXIT["east"]], 1 - v.sum(1)], axis=1)
            res[rt[starts] == 0] = np.nan
            out[step] = res
    return out


def all_configs(weights):
    """Horizon probabilities for All year, each season, and each season's rest-of-year complement."""
    sc = season_counts(weights)
    tot = sc.sum(0)
    res = {"All year": horizon_probs(*to_P(tot))}
    for k, s in enumerate(SEASONS):
        res[s] = horizon_probs(*to_P(sc[k]))
        res[f"rest:{s}"] = horizon_probs(*to_P(tot - sc[k]))
    return res


point = all_configs(np.ones(len(traj_codes)))
# The weighted rebuild must reproduce the shared function exactly
for s in ["All year"] + SEASONS:
    sc = season_counts(np.ones(len(traj_codes)))
    P_mine = to_P(sc.sum(0) if s == "All year" else sc[SEASONS.index(s)])[0]
    assert np.allclose(P_mine, shared_P[s]), f"matrix rebuild differs from build_transition_matrix ({s})"
print("Check: weighted rebuild == Vrishin's build_transition_matrix for all-year and every season")

rng = np.random.default_rng(2026)
D = len(traj_codes)
boot = []
for b in range(N_BOOT):
    boot.append(all_configs(rng.multinomial(D, np.full(D, 1.0 / D)).astype(float)))
    if (b + 1) % 250 == 0:
        print(f"  bootstrap {b + 1}/{N_BOOT}")

abc_rows = []
names = list(CELLS_ABC)
for cfg in ["All year"] + SEASONS:
    sub = pairs if cfg == "All year" else pairs[pairs.season == cfg]
    for i, name in enumerate(names):
        cell = CELLS_ABC[name]
        start_sub = sub[sub.origin_cell == cell]
        for days, step in HORIZONS.items():
            if days == 7:
                continue
            row = dict(cell=name, origin_cell=cell, season=cfg, months=SEASON_MONTHS.get(cfg, "Jan-Dec"),
                       horizon_days=days, validated=(days <= 28),
                       start_pairs=len(start_sub), start_drifters=start_sub.traj.nunique(),
                       season_drifters=sub.traj.nunique())
            samples = np.array([bb[cfg][step][i] for bb in boot])            # (N_BOOT, 3)
            for k, side in enumerate(["west", "east", "unresolved"]):
                row[f"p_{side}"] = point[cfg][step][i, k]
                row[f"p_{side}_lo"], row[f"p_{side}_hi"] = ci(samples[:, k])
            abc_rows.append(row)
            if cfg != "All year":
                rest = np.array([bb[f"rest:{cfg}"][step][i] for bb in boot])
                for k, side in enumerate(["west", "east"]):
                    lo, hi = ci(samples[:, k] - rest[:, k])
                    d = point[cfg][step][i, k] - point[f"rest:{cfg}"][step][i, k]
                    contr.append(dict(unit=f"{name} (cell {cell})", horizon_days=days, side=side, season=cfg,
                                      diff_vs_rest=d, lo=lo, hi=hi,
                                      exceeds_uncertainty=bool((lo > 0 or hi < 0) and abs(d) >= MIN_EFFECT)))
abc = pd.DataFrame(abc_rows)
abc.to_csv(OUT / "seasonal_ABC_exit_probabilities.csv", index=False)
contr = pd.DataFrame(contr)
contr.to_csv(OUT / "seasonal_contrasts.csv", index=False)

support = (pairs[pairs.origin_cell.isin(CELLS_ABC.values())]
           .groupby(["origin_cell", "season"], observed=True).agg(n_pairs=("traj", "size"), n_drifters=("traj", "nunique"))
           .reset_index())
support["cell"] = support.origin_cell.map({v: k for k, v in CELLS_ABC.items()})
support = pd.concat([support, region.assign(cell="Region", origin_cell=-1)[
    ["cell", "origin_cell", "season", "n_pairs", "n_drifters"]].query("season != 'All year'")])
support["enough_support"] = support.n_drifters >= MIN_DRIFTERS
support.to_csv(OUT / "seasonal_support.csv", index=False)

poster = abc[(abc.season == "All year") & (abc.horizon_days == 91)].set_index("cell")
print(f"\nPoster check (all-year, 91 days): B west {poster.loc['B', 'p_west']:.1%} (poster 17.8%), "
      f"C east {poster.loc['C', 'p_east']:.1%} (poster 38.7%)")
print("\nA/B/C west / east exit probability by season (95% whole-drifter bootstrap CI):")
show = abc.assign(west=[fmt(r.p_west, r.p_west_lo, r.p_west_hi) for r in abc.itertuples()],
                  east=[fmt(r.p_east, r.p_east_lo, r.p_east_hi) for r in abc.itertuples()],
                  unresolved=abc.p_unresolved.clip(lower=0).map("{:.1%}".format))
print(show[["cell", "horizon_days", "season", "start_drifters", "west", "east", "unresolved"]].to_string(index=False))
print("\nSeason minus rest of year (percentage points, paired whole-drifter bootstrap); * = CI excludes 0:")
c2 = contr.assign(diff=[f"{100 * r.diff_vs_rest:+.1f} [{100 * r.lo:+.1f}, {100 * r.hi:+.1f}]{' *' if r.exceeds_uncertainty else ''}"
                        for r in contr.itertuples()])
print(c2.pivot_table(index=["unit", "horizon_days", "side"], columns="season", values="diff", aggfunc="first",
                     observed=True)[SEASONS].to_string())

# ============================================================== Part 4: per-cell seasonal maps
cell_season = (pairs.groupby(["season", "origin_cell"], observed=True)
               .agg(n_pairs=("traj", "size"), n_drifters=("traj", "nunique"),
                    p_west=("west", "mean"), p_east=("east", "mean")).reset_index())
cell_season["enough_support"] = cell_season.n_drifters >= MIN_DRIFTERS
cell_season.to_csv(OUT / "seasonal_cell_exit_probs.csv", index=False)

# ============================================================== figures
COLORS = {"All year": "#9a9a9a", "Summer": "#d1495b", "Autumn": "#edae49", "Winter": "#00798c", "Spring": "#66a182"}
CFGS = ["All year"] + SEASONS


def bars(ax, table, xcats, xkey, side, ylabel):
    width = 0.16
    for k, s in enumerate(CFGS):
        d = table[table.season == s].set_index(xkey).loc[xcats]
        x = np.arange(len(xcats)) + (k - 2) * width
        y = 100 * d[f"p_{side}"].to_numpy()
        err = np.vstack([y - 100 * d[f"p_{side}_lo"].to_numpy(), 100 * d[f"p_{side}_hi"].to_numpy() - y])
        ax.bar(x, y, width, color=COLORS[s], edgecolor="white", label=f"{s} ({SEASON_MONTHS.get(s, 'Jan-Dec')})")
        ax.errorbar(x, y, yerr=err, fmt="none", ecolor="#222", elinewidth=1, capsize=2.5)
    ax.set_xticks(np.arange(len(xcats)))
    ax.set_xticklabels(xcats, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)


fig, axes = plt.subplots(2, 2, figsize=(13, 9))
for r, days in enumerate([28, 91]):
    for c, (side, label) in enumerate([("west", "West exit (Atlantic)"), ("east", "East exit (Indian Ocean)")]):
        ax = axes[r, c]
        bars(ax, abc[abc.horizon_days == days], names, "cell", side, f"P(first exit {side}) (%)")
        tag = "" if days <= 28 else "  - projection, not yet validated"
        ax.set_title(f"{label} within {days} days{tag}", fontsize=11)
axes[0, 0].legend(frameon=False, fontsize=9, title="Season of start date", title_fontsize=9)
fig.suptitle("Starting cells A, B, C: exit probability by season, from each season's 7-day matrix "
             "(P⁴ = 28 d, P¹³ = 91 d)\nbars = estimate, whiskers = 95% whole-drifter bootstrap CI", fontsize=12)
fig.tight_layout()
fig.savefig(OUT / "fig_seasonal_exit_ABC.png", dpi=200)
plt.close(fig)

fig, ax = plt.subplots(figsize=(7.5, 4.6))
reg = region.assign(unit="Region")
for k, side in enumerate(["west", "east"]):
    for j, s in enumerate(CFGS):
        r = region.set_index("season").loc[s]
        x = k + (j - 2) * 0.16
        y = 100 * r[f"p_{side}"]
        ax.bar(x, y, 0.16, color=COLORS[s], edgecolor="white", label=s if k == 0 else None)
        ax.errorbar(x, y, yerr=[[y - 100 * r[f"p_{side}_lo"]], [100 * r[f"p_{side}_hi"] - y]], fmt="none",
                    ecolor="#222", elinewidth=1, capsize=2.5)
ax.set_xticks([0, 1])
ax.set_xticklabels(["West exit", "East exit"], fontsize=11)
ax.set_ylabel("P(first exit within 7 days) (%)")
ax.set_title("All starting cells pooled: 7-day exit probability by season (95% CI)", fontsize=11)
ax.legend(frameon=False, fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "fig_seasonal_region_7day.png", dpi=200)
plt.close(fig)

fig, axes = plt.subplots(2, 4, figsize=(19, 8.6))
for i, side in enumerate(["west", "east"]):
    vmax = max(0.05, float(cell_season.loc[cell_season.enough_support, f"p_{side}"].quantile(0.98)))
    for j, s in enumerate(SEASONS):
        ax = axes[i, j]
        d = cell_season[(cell_season.season == s) & cell_season.enough_support].set_index("origin_cell")
        draw_land(ax)
        mesh = ax.pcolormesh(LON_EDGES, LAT_EDGES, to_grid(d[f"p_{side}"]), cmap="magma_r", vmin=0, vmax=vmax,
                             edgecolor="white", linewidth=0.3, zorder=1)
        mark_abc(ax, color="#1f77b4", fontsize=9)
        style_map(ax, fontsize=8)
        ax.set_title(f"{s} ({SEASON_MONTHS[s]}): {side} exit", fontsize=11)
    fig.colorbar(mesh, ax=axes[i, :], shrink=0.85, label=f"P(first exit {side} within 7 days)")
fig.suptitle("7-day first-exit probability by starting cell and season (cells with ≥10 distinct drifters; blank = too few)",
             fontsize=13)
fig.savefig(OUT / "fig_seasonal_exit_maps.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"\nSaved figures and tables to {OUT}")

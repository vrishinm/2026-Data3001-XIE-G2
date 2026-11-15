"""Yoyo - checking the seasonal 56 / 91-day numbers against what the drifters actually did.

Lucy's Step 11 (notebook "Matrix vs observed outcomes at longer horizons") showed that the all-year
matrix gets B west right at 91 days but underestimates eastward exits (C east 62% observed vs 38%
matrix, B east 17% vs 4%). Here the same week-by-week chaining is applied per season.

Observed outcome: start from a 7-day pair in A, B or C and follow the drifter through its own pairs
(t, t+7d, t+14d, ...). The first exit decides the outcome, exactly like the matrix. If a week is missing
(record ended or gap) the start is "censored" and left out.

Drifters: Zack's split (drifter_split.csv). Test drifters stay locked, so everything here uses the
train + val drifters only.

Part 1  Sanity check: reproduce Lucy's all-year table (matrix fit on train, observed on val).
Part 2  Observed west / east exits by season at 28 / 56 / 91 days, with whole-drifter bootstrap CIs
        and paired season-vs-rest-of-year contrasts. This does not use the matrix at all.
Part 3  Seasonal matrix (P^k, fit on the same train + val drifters) vs the observed share, with a
        paired bootstrap CI of the gap. A gap here means the Markov (memoryless) assumption fails,
        not overfitting, because both sides use the same drifters.

Outputs (yoyo_analysis/results and yoyo_analysis/figures):
  seasonal_observed_exits.csv        observed and matrix exit shares, gap and CIs, per cell x season x horizon
  seasonal_observed_contrasts.csv    observed season - rest of year, per cell x horizon x side
  seasonal_observed_support.csv      starts, censored starts and drifters per cell x season x horizon
  validation_lucy_check.csv          Part 1 table
  fig_seasonal_observed_vs_matrix.png
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from yoyo_common import (FIG, CELLS_ABC, N_STATES, OUT, SEASONS, chain_outcomes, ci, exit_at, find_split, load_pairs7,
                         load_shared_functions, to_P)

N_BOOT = 1000
HORIZONS = {28: 4, 56: 8, 91: 13}
CFGS = ["All year"] + SEASONS
# 1 pp: when no drifter in a group exits, every bootstrap resample is also 0 and the CI collapses to
# [0, 0], so tiny gaps (e.g. observed 0.0% vs matrix 0.3%) would look "significant". Ignore those.
MIN_EFFECT = 0.01
build_transition_matrix, _ = load_shared_functions()
pd.set_option("display.width", 220)


pairs = load_pairs7()
split = pd.read_csv(find_split())
pairs["split"] = pairs.traj.map(dict(zip(split.traj, split.split)))
assert pairs.split.notna().all(), "every drifter in pairs7.csv should be in drifter_split.csv"
print("drifters per split:", pairs.groupby("split").traj.nunique().to_dict())
dev = pairs[pairs.split != "test"].reset_index(drop=True)   # train + val; test stays locked

# ============================================================== Part 1: reproduce Lucy's all-year check
train, val = pairs[pairs.split == "train"], pairs[pairs.split == "val"]
P_train = build_transition_matrix(train)[0]
rows = []
for name, cell in CELLS_ABC.items():
    mat = exit_at(P_train, cell, HORIZONS.values())
    for days, k in HORIZONS.items():
        o = chain_outcomes(val, [cell], k)
        o = o[o.out != "censored"]
        for j, side in enumerate(["west", "east"]):
            rows.append(dict(cell=name, days=days, side=side, observed_val=(o.out == side).mean(),
                             matrix_train=mat[k][j], starts=len(o), val_drifters=o.traj.nunique()))
lucy = pd.DataFrame(rows)
lucy.to_csv(OUT / "validation_lucy_check.csv", index=False)
print("\nPart 1. All-year check (matrix from train drifters, observed on val drifters), same design as Lucy:")
print(lucy[lucy.days == 91].assign(observed_val=lambda d: (100 * d.observed_val).round(1),
                                   matrix_train=lambda d: (100 * d.matrix_train).round(1)).to_string(index=False))

# ============================================================== Parts 2 + 3: seasons, train + val drifters
traj_codes, traj_idx = np.unique(dev.traj.to_numpy(), return_inverse=True)
D = len(traj_codes)
pos_of = pd.Series(np.arange(D), index=traj_codes)
rng = np.random.default_rng(91)
W = rng.multinomial(D, np.full(D, 1.0 / D), size=N_BOOT).astype(float)   # whole-drifter resamples, shared by all parts

# matrix side: weighted transition counts per season for every resample
codes = dev.origin_cell.to_numpy() * N_STATES + dev.dest.to_numpy()
sidx = dev.season.cat.codes.to_numpy()


def counts_for(weights, mask):
    return np.bincount(codes[mask], weights=weights[traj_idx][mask], minlength=N_STATES ** 2).reshape(N_STATES, N_STATES)


masks = {"All year": np.ones(len(dev), bool), **{s: sidx == k for k, s in enumerate(SEASONS)}}
for s in CFGS:   # the unweighted rebuild must equal the shared function
    sub = dev if s == "All year" else dev[dev.season == s]
    assert np.allclose(to_P(counts_for(np.ones(D), masks[s])), build_transition_matrix(sub)[0])

steps = list(HORIZONS.values())
mat_point, mat_boot = {}, {}
for s in CFGS:
    P = to_P(counts_for(np.ones(D), masks[s]))
    mat_point[s] = {c: exit_at(P, c, steps) for c in CELLS_ABC.values()}
print(f"\nBootstrapping seasonal matrices ({N_BOOT} resamples x {len(CFGS)} configs)...")
for s in CFGS:
    res = np.zeros((N_BOOT, len(CELLS_ABC), len(steps), 2))
    for b in range(N_BOOT):
        P = to_P(counts_for(W[b], masks[s]))
        for i, c in enumerate(CELLS_ABC.values()):
            e = exit_at(P, c, steps)
            res[b, i] = [e[k] for k in steps]
    mat_boot[s] = res

# observed side
obs_rows, contr_rows, support = [], [], []
for h, (days, k) in enumerate(HORIZONS.items()):
    o_all = chain_outcomes(dev, list(CELLS_ABC.values()), k)
    for name, cell in CELLS_ABC.items():
        oc = o_all[o_all.origin_cell == cell]
        for s in SEASONS:
            os_ = oc[oc.season == s]
            support.append(dict(cell=name, days=days, season=s, starts=len(os_),
                                censored=int((os_.out == "censored").sum()),
                                drifters=os_[os_.out != "censored"].traj.nunique()))
        oc = oc[oc.out != "censored"]
        p = pos_of[oc.traj.values].values
        sk = oc.season.cat.codes.to_numpy()
        n_ds = np.zeros((D, 4))
        np.add.at(n_ds, (p, sk), 1)
        den = W @ n_ds                                           # (N_BOOT, 4)
        for j, side in enumerate(["west", "east"]):
            hit = (oc.out == side).to_numpy(float)
            num_ds = np.zeros((D, 4))
            np.add.at(num_ds, (p, sk), hit)
            num = W @ num_ds
            n0, h0 = n_ds.sum(0), num_ds.sum(0)
            for cfg in CFGS:
                if cfg == "All year":
                    est, bs = h0.sum() / n0.sum(), num.sum(1) / den.sum(1)
                    n_starts, n_dr = int(n0.sum()), oc.traj.nunique()
                else:
                    q = SEASONS.index(cfg)
                    est = h0[q] / n0[q] if n0[q] else np.nan
                    with np.errstate(invalid="ignore", divide="ignore"):
                        bs = num[:, q] / den[:, q]
                    n_starts, n_dr = int(n0[q]), oc[oc.season == cfg].traj.nunique()
                    rest_est = (h0.sum() - h0[q]) / (n0.sum() - n0[q])
                    with np.errstate(invalid="ignore", divide="ignore"):
                        rest_bs = (num.sum(1) - num[:, q]) / (den.sum(1) - den[:, q])
                    lo, hi = ci(bs - rest_bs)
                    d = est - rest_est
                    contr_rows.append(dict(cell=name, days=days, side=side, season=cfg, observed=est,
                                           rest_of_year=rest_est, diff_vs_rest=d, lo=lo, hi=hi,
                                           exceeds_uncertainty=bool((lo > 0 or hi < 0) and abs(d) >= MIN_EFFECT)))
                ci_i = list(CELLS_ABC).index(name)
                m_est = mat_point[cfg][cell][k][j]
                m_bs = mat_boot[cfg][:, ci_i, h, j]
                olo, ohi = ci(bs)
                mlo, mhi = ci(m_bs)
                glo, ghi = ci(bs - m_bs)
                gap = est - m_est
                obs_rows.append(dict(cell=name, days=days, side=side, season=cfg, starts=n_starts, drifters=n_dr,
                                     observed=est, obs_lo=olo, obs_hi=ohi, matrix=m_est, mat_lo=mlo, mat_hi=mhi,
                                     gap=gap, gap_lo=glo, gap_hi=ghi,
                                     gap_exceeds_uncertainty=bool((glo > 0 or ghi < 0) and abs(gap) >= MIN_EFFECT)))

obs = pd.DataFrame(obs_rows)
contr = pd.DataFrame(contr_rows)
supp = pd.DataFrame(support)
obs.to_csv(OUT / "seasonal_observed_exits.csv", index=False)
contr.to_csv(OUT / "seasonal_observed_contrasts.csv", index=False)
supp.to_csv(OUT / "seasonal_observed_support.csv", index=False)


def pct(p, lo, hi):
    return "n/a" if pd.isna(p) else f"{100 * p:4.1f} [{100 * lo:4.1f}, {100 * hi:4.1f}]"


print("\nSupport at 91 days (train + val drifters; censored = record ends or gap before the horizon):")
print(supp[supp.days == 91].pivot(index="cell", columns="season", values=["drifters", "starts", "censored"])
      .reindex(columns=SEASONS, level=1).to_string())
for days in [56, 91]:
    print(f"\nParts 2-3. {days} days: observed share vs seasonal matrix (%, 95% whole-drifter bootstrap CI)")
    t = obs[obs.days == days]
    print(pd.DataFrame({"cell": t.cell, "side": t.side, "season": t.season, "drifters": t.drifters,
                        "observed": [pct(r.observed, r.obs_lo, r.obs_hi) for r in t.itertuples()],
                        "matrix": [pct(r.matrix, r.mat_lo, r.mat_hi) for r in t.itertuples()],
                        "obs - matrix": [pct(r.gap, r.gap_lo, r.gap_hi) + (" *" if r.gap_exceeds_uncertainty else "")
                                         for r in t.itertuples()]}).to_string(index=False))
print("\nObserved season - rest of year that exceeds the bootstrap uncertainty:")
sig = contr[contr.exceeds_uncertainty]
print(sig.assign(**{c: (100 * sig[c]).round(1) for c in ["observed", "rest_of_year", "diff_vs_rest", "lo", "hi"]})
      .to_string(index=False) if len(sig) else "  none")

# ============================================================== figure: 91 days, observed vs matrix
COLORS = {"All year": "#9a9a9a", "Summer": "#d1495b", "Autumn": "#edae49", "Winter": "#00798c", "Spring": "#66a182"}
fig, axes = plt.subplots(2, 3, figsize=(13, 7.4), sharey="row")
t91 = obs[obs.days == 91]
for r, side in enumerate(["west", "east"]):
    for c, name in enumerate(CELLS_ABC):
        ax = axes[r, c]
        t = t91[(t91.cell == name) & (t91.side == side)].set_index("season").loc[CFGS]
        x = np.arange(len(CFGS))
        for i, cfg in enumerate(CFGS):
            row = t.loc[cfg]
            ax.errorbar(i - 0.13, 100 * row.observed, yerr=[[100 * (row.observed - row.obs_lo)],
                                                            [100 * (row.obs_hi - row.observed)]],
                        fmt="o", color=COLORS[cfg], capsize=3, ms=7, label="observed (drifters)" if i == 0 else None)
            ax.errorbar(i + 0.13, 100 * row.matrix, yerr=[[100 * (row.matrix - row.mat_lo)],
                                                          [100 * (row.mat_hi - row.matrix)]],
                        fmt="o", mfc="white", color=COLORS[cfg], capsize=3, ms=7,
                        label="matrix P¹³" if i == 0 else None)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{s}\n(n={int(t.loc[s].drifters)})" for s in CFGS], fontsize=8)
        ax.set_title(f"{name}: {side} exit by day 91", fontsize=11)
        ax.grid(axis="y", alpha=0.3)
        if c == 0:
            ax.set_ylabel("% of starts")
axes[0, 0].legend(frameon=False, fontsize=9)
fig.suptitle("Seasonal 91-day exits: what drifters actually did (filled) vs the seasonal matrix (open)\n"
             "train + val drifters, 95% whole-drifter bootstrap CIs, n = drifters with an uncensored 91-day outcome",
             fontsize=11)
fig.tight_layout()
fig.savefig(FIG / "fig_seasonal_observed_vs_matrix.png", dpi=180)
plt.close(fig)
print(f"\nSaved tables and figure to {OUT.parent}")

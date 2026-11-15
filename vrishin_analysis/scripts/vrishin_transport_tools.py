"""DATA3001: audit Lucy's pairs and estimate an empirical 7-day matrix.

Usage:
  python vrishin_friday_starter.py '/path/to/pairs7.csv'

Bootstrap resamples whole drifters. Requires pandas and numpy.
This script cannot verify exit classification against original NOAA tracks;
that requires the full dataset and Lucy's notebook.
"""
import sys
import numpy as np
import pandas as pd

N_INTERIOR = 234
N_STATES = 238
EXIT_CODES = {'west': 234, 'east': 235, 'south': 236, 'north': 237}


def audit_pairs(df):
    required = {'origin_cell', 'dest', 'traj', 'time', 'obs_row'}
    if not required.issubset(df.columns):
        raise ValueError(f'Missing columns: {required - set(df.columns)}')
    print('Pairs:', len(df), '| contributing drifters:', df.traj.nunique())
    print('Missing values:', df[list(required)].isna().sum().to_dict())
    print('Duplicated drifter + start date:', df.duplicated(['traj', 'time']).sum())
    print('Invalid origin codes:', (~df.origin_cell.between(0, N_INTERIOR - 1)).sum())
    print('Invalid destination codes:', (~df.dest.between(0, N_STATES - 1)).sum())
    print('Seven-day exit pairs:', df.dest.ge(N_INTERIOR).sum())
    for label, code in EXIT_CODES.items():
        print(f'  {label}: {(df.dest == code).sum():,}')
    support = df.groupby('origin_cell').traj.nunique()
    print('Cells with at least 10 contributing drifters:', (support >= 10).sum())
    print('Cells with at least one pair:', len(support), 'out of', N_INTERIOR)
    return support


def build_transition_matrix(df, unsupported="nan"):

    """Return (probability_matrix, count_matrix, row_totals).

    ``unsupported='nan'`` leaves unsupported interior rows undefined, suitable
    for descriptive analyses. ``unsupported='self_loop'`` is an explicit
    absorbing-self-loop ASSUMPTION suitable for exploring matrix powers, but
    sensitivity to that assumption must be reported.
    """
    o = df.origin_cell.to_numpy(dtype=int)
    d = df.dest.to_numpy(dtype=int)
    if np.any((o < 0) | (o >= N_INTERIOR) | (d < 0) | (d >= N_STATES)):
        raise ValueError('State codes outside allowed range')
    counts = np.zeros((N_STATES, N_STATES), dtype=np.int64)
    np.add.at(counts, (o, d), 1)
    total = counts.sum(axis=1)
    P = np.full((N_STATES, N_STATES), np.nan, dtype=float)
    supported = np.flatnonzero(total[:N_INTERIOR] > 0)
    P[supported] = counts[supported] / total[supported, None]
    for state in EXIT_CODES.values():
        P[state] = 0.0
        P[state, state] = 1.0
    if unsupported not in ("nan", "self_loop"):
        raise ValueError("unsupported must be 'nan' or 'self_loop'")
    missing = np.flatnonzero(total[:N_INTERIOR] == 0)
    if unsupported == "self_loop":
        # This is a modeling ASSUMPTION, not an observed probability.
        P[missing] = 0.0
        P[missing, missing] = 1.0
    assert np.allclose(P[supported].sum(axis=1), 1)
    if unsupported == "self_loop":
        assert np.allclose(P.sum(axis=1), 1.0)
    return P, counts, total


def bootstrap_exit_probability(df, origin_cell, exit_code, B=500, seed=3001):
    """Percentile interval for DIRECT seven-day exit rate from a starting cell.

    Resamples whole drifters WITH replacement; each selected drifter's entire
    set of pairs is counted once per draw. This is not an interval for P**13.
    """
    if exit_code not in EXIT_CODES.values():
        raise ValueError('Not an exit code')
    ids = df.traj.unique()
    # Number of pairs in target origin, and target-origin pairs that exit.
    target = df.origin_cell.eq(origin_cell)
    counts = df.assign(_tot=target.astype(int),
                       _hit=(target & df.dest.eq(exit_code)).astype(int)) \
               .groupby('traj')[['_tot', '_hit']].sum().reindex(ids, fill_value=0)
    tot = counts['_tot'].to_numpy()
    hit = counts['_hit'].to_numpy()
    if tot.sum() == 0:
        raise ValueError('No observed pairs from requested starting cell')
    point = hit.sum() / tot.sum()
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(B):
        draw = rng.integers(0, len(ids), size=len(ids))
        denom = tot[draw].sum()
        if denom:
            estimates.append(hit[draw].sum() / denom)
    if len(estimates) < B * .9:
        print('Warning: target origin often absent in bootstrap resamples')
    return point, np.quantile(estimates, [.025, .975]), len(estimates)



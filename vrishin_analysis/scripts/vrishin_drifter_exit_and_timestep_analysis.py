"""
DATA3001: Drifter timestep, cell-exit and exit-rule sensitivity analysis.

Requirements: numpy, pandas, clouddrift.

Run from the repository root:
    python vrishin_analysis/scripts/vrishin_drifter_exit_and_timestep_analysis.py

Inputs:
    pairs7.csv
    NOAA GDP hourly trajectories via clouddrift

Outputs:
    vrishin_analysis/results/

The analysis uses the same contributing drifters and starting
observations for both the 3-day and 7-day comparisons.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from vrishin_transport_tools import build_transition_matrix, audit_pairs, N_INTERIOR

OUTDIR = Path('vrishin_analysis/results')
OUTDIR.mkdir(exist_ok=True)
WEST, EAST, SOUTH, NORTH, GRID = 10., 45., -45., -20., 2.
N_COLS = int(np.ceil((EAST - WEST) / GRID))
N_ROWS = int(np.ceil((NORTH - SOUTH) / GRID))
assert N_COLS * N_ROWS == N_INTERIOR
DAY_NS = 86_400_000_000_000


def inside(lon, lat):
    return np.isfinite(lon) & np.isfinite(lat) & (lon >= WEST) & (lon <= EAST) & (lat >= SOUTH) & (lat <= NORTH)


def cell(lon, lat):
    c = np.clip(np.floor((lon - WEST) / GRID).astype(int), 0, N_COLS - 1)
    r = np.clip(np.floor((lat - SOUTH) / GRID).astype(int), 0, N_ROWS - 1)
    return r * N_COLS + c


def outcome(lon, lat, index):
    """First outside observation/endpoint: directional code or interior cell."""
    x, y = lon[index], lat[index]
    if x < WEST: return 234
    if x > EAST: return 235
    if y < SOUTH: return 236
    if y > NORTH: return 237
    return int(cell(x, y))


def km_summary(times_days, event):
    """Kaplan-Meier summary; censoring at last observed trajectory position."""
    data = pd.DataFrame({'t': times_days, 'event': event}).dropna()
    events = data.loc[data.event, 't'].value_counts().sort_index()
    durations = data.t.to_numpy()
    surv = 1.0
    median = np.nan
    vals = {}
    for t in sorted(set(events.index) | {3., 7.}):
        if t in events.index:
            at_risk = int((durations >= t).sum())
            if at_risk:
                surv *= (1 - int(events.loc[t]) / at_risk)
        if np.isnan(median) and surv <= .5:
            median = t
        if t in (3., 7.):
            vals[int(t)] = 1 - surv
    return len(data), int(data.event.sum()), median, vals[3], vals[7]


def process_pairs(ds, pairs):
    """Read whole tracks of drifters represented by pairs, not all 197M observations."""
    sizes = ds['rowsize'].values.astype(np.int64)
    ends = np.cumsum(sizes)
    starts = ends - sizes
    out = []
    for k, (traj, group) in enumerate(pairs.groupby('traj', sort=True), 1):
        traj = int(traj)
        a, b = int(starts[traj]), int(ends[traj])
        lon = ds['lon'].isel(obs=slice(a,b)).values
        lat = ds['lat'].isel(obs=slice(a,b)).values
        t = ds['time'].isel(obs=slice(a,b)).values.astype('datetime64[ns]').astype('int64')
        if np.any(np.diff(t) <= 0):
            raise ValueError(f'Time not strictly increasing in traj={traj}')
        in_r = inside(lon,lat)
        starts_local = group.obs_row.to_numpy(dtype=np.int64) - a
        if not np.all((starts_local >= 0) & (starts_local < len(t))):
            raise ValueError(f'Bad obs_row mapping traj={traj}')
        if not np.all(in_r[starts_local]):
            raise ValueError(f'Origin outside region for traj={traj}')
        # Pre-compute next time the location changes to a different 2-degree cell,
        # treating a departure from R as a cell exit.
        state = np.full(len(t), -1, dtype=np.int32)
        state[in_r] = cell(lon[in_r], lat[in_r])
        change = np.r_[np.flatnonzero(state[1:] != state[:-1]) + 1, len(t)]
        next_change = change[np.searchsorted(change, np.arange(len(t)), side='right')]

        for j, origin in enumerate(starts_local):
            origin = int(origin)
            t0 = t[origin]
            original = group.iloc[j]
            rec = {'origin_cell': int(original.origin_cell), 'traj': traj,
                   'time': original.time, 'obs_row': int(original.obs_row),
                   'original_dest7': int(original.dest)}
            if int(cell(lon[origin],lat[origin])) != rec['origin_cell']:
                raise ValueError(f'Cell mismatch for traj={traj}, row={origin+a}')
            # Time-to-first departure from original 2-degree cell.
            ix = int(next_change[origin])
            observed = ix < len(t)
            endix = ix if observed else len(t)-1
            rec['cell_exit_days'] = (t[endix] - t0) / DAY_NS
            rec['cell_exit_observed'] = bool(observed)

            for days in (3,7):
                target = t0 + days * DAY_NS
                upper = int(np.searchsorted(t, target, side='right'))
                inside_range = in_r[origin+1:upper]
                outside_pos = np.flatnonzero(~inside_range)
                # Only classify finite outside positions; missing coordinates
                # would instead need an explicit missing-observation policy.
                if outside_pos.size:
                    first = origin + 1 + int(outside_pos[0])
                    if not np.isfinite(lon[first]) or not np.isfinite(lat[first]):
                        raise ValueError('Missing coordinate in a first-exit window; inspect trajectory')
                    rec[f'first{days}'] = outcome(lon, lat, first)
                    rec[f'first_exit_days{days}'] = (t[first] - t0) / DAY_NS
                else:
                    rec[f'first{days}'] = np.nan
                    rec[f'first_exit_days{days}'] = np.nan
                endpoint = int(np.searchsorted(t,target,side='left'))
                exact = endpoint < len(t) and t[endpoint] == target
                rec[f'endpoint{days}'] = outcome(lon,lat,endpoint) if exact else np.nan
                if outside_pos.size == 0 and exact:
                    rec[f'first{days}'] = rec[f'endpoint{days}']
            out.append(rec)
        if k % 100 == 0:
            print(f'Processed {k:,}/{pairs.traj.nunique():,} drifters...', flush=True)
    return pd.DataFrame(out)


def main():
    pairs = pd.read_csv('pairs7.csv')
    audit_pairs(pairs)
    print('Opening NOAA GDP hourly data; reading only contributing drifter tracks...')
    from clouddrift.datasets import gdp1h
    ds = gdp1h()
    results = process_pairs(ds, pairs)
    # Reproduction check: no change to existing 7-day rule is acceptable unless
    # fully investigated. If this fails, don't report sensitivity results yet.
    valid7 = results.first7.notna()
    if not valid7.all():
        raise AssertionError(f'{(~valid7).sum()} original 7-day pairs not reproduced')
    incorrect = results.first7.astype(int) != results.original_dest7
    if incorrect.any():
        results.loc[incorrect].to_csv(OUTDIR/'first_exit_mismatches.csv',index=False)
        raise AssertionError(f'{incorrect.sum()} 7-day outcomes disagree with Lucy! Inspect first_exit_mismatches.csv')
    print('PASS: all existing 7-day first-exit labels reproduced')
    results.to_csv(OUTDIR/'paired_3d_7d_and_cell_exit.csv',index=False)

    # 3d vs 7d: compare *the same starts* (paired cohort).
    valid3 = results.first3.notna()
    paired = results[valid3].copy()
    print('\nPAIRED 3-DAY VS 7-DAY')
    print('3d known and 7d known:',len(paired),'of 7d pairs:',len(results))
    for days in (3,7):
        counts = paired[f'first{days}'].value_counts().sort_index()
        print(f'{days}-day first-exit proportions (west/east/south/north):',
              [(counts.get(code,0)/len(paired)) for code in range(234,238)])
    print('Different 3d versus 7d destinations:',
          int((paired.first3 != paired.first7).sum()),'/',len(paired))
    for days in (3,7):
        d = paired.rename(columns={f'first{days}':'dest'})[['origin_cell','dest','traj']].copy()
        P, counts, rows = build_transition_matrix(d,unsupported='nan')
        np.save(OUTDIR/f'P{days}_nan_unsupported.npy',P)
        np.save(OUTDIR/f'counts{days}.npy',counts)
        print(f'P{days}: supported origins =',(rows[:234]>0).sum())

    # Alternative rule: exact endpoint 7 days later, or censored if absent.
    endpoint_known = results.endpoint7.notna()
    comp = results[endpoint_known].copy()
    comp['changed'] = comp.first7 != comp.endpoint7
    comp['reentered'] = (comp.first7 >= 234) & (comp.endpoint7 < 234)
    print('\nALTERNATIVE 7-DAY ENDPOINT RULE')
    print('Pairs with exact day-7 endpoint:',len(comp))
    print('Classification changed:',int(comp.changed.sum()),f'({comp.changed.mean():.1%})')
    print('First-exit then reentered:',int(comp.reentered.sum()),f'({comp.reentered.mean():.1%})')
    print('7-day first-exit counts:',comp.first7.value_counts().sort_index().to_dict())
    print('7-day endpoint counts:',comp.endpoint7.value_counts().sort_index().to_dict())
    pd.crosstab(comp.first7, comp.endpoint7).to_csv(OUTDIR/'first_exit_vs_endpoint7.csv')
    comp[['traj','obs_row','origin_cell','first7','endpoint7','changed','reentered']].to_csv(
        OUTDIR/'alternative_exit_comparison.csv',index=False)

    # Kaplan-Meier: right-censored if the same cell is never left before the
    # end of that trajectory; observations with a track ending are not departures.
    n, events, median, p3, p7 = km_summary(results.cell_exit_days, results.cell_exit_observed)
    print('\nTIME TO LEAVE INITIAL 2-DEGREE CELL (Kaplan-Meier)')
    print('Origins:',n,'observed cell exits:',events,'right-censored:',n-events)
    print('Median days:',median,'cumulative departures by day 3:',p3,'day 7:',p7)
    print('NOTE: overlapping daily starts from each drifter are dependent;')
    print('do not treat these as independent observations for standard errors.')
    print('Saved outputs in',OUTDIR)

if __name__=='__main__':
    main()

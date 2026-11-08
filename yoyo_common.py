"""Shared helpers for Yoyo's seasonal analysis and 2-degree coverage map.

- Loads Lucy's pairs7.csv and tags each pair with its (austral) season.
- Loads Vrishin's shared functions (build_transition_matrix, bootstrap_exit_probability)
  straight from vrishinanalysis.py, so every member uses the same code. Only the function
  definitions are executed, not the script's top-level checks and plots.
- A fast whole-drifter bootstrap for comparing several groups at once (seasons, cells).
- Grid geometry and map styling copied from Lucy's notebook (Figure 1).
"""
import ast
import json
import os
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "yoyo_outputs"
OUT.mkdir(exist_ok=True)

# Region R and the 2-degree grid used by pairs7.csv (Lucy's cell_of): cell = row * 18 + col
WEST, EAST, SOUTH, NORTH = 10, 45, -45, -20
GRID = 2
N_COLS = int(np.ceil((EAST - WEST) / GRID))    # 18
N_ROWS = int(np.ceil((NORTH - SOUTH) / GRID))  # 13
N_CELLS = N_COLS * N_ROWS                      # 234
N_STATES = N_CELLS + 4                         # cells + 4 absorbing exits
EXIT = {"west": 234, "east": 235, "south": 236, "north": 237}

# Starting cells used throughout the poster (names = {99: "A", 58: "B", 44: "C"} in Lucy's notebook)
CELLS_ABC = {"A": 99, "B": 58, "C": 44}

# Austral seasons, assigned by the START time of each 7-day pair
SEASON_OF_MONTH = {12: "Summer", 1: "Summer", 2: "Summer",
                   3: "Autumn", 4: "Autumn", 5: "Autumn",
                   6: "Winter", 7: "Winter", 8: "Winter",
                   9: "Spring", 10: "Spring", 11: "Spring"}
SEASONS = ["Summer", "Autumn", "Winter", "Spring"]
SEASON_MONTHS = {"Summer": "Dec-Feb", "Autumn": "Mar-May", "Winter": "Jun-Aug", "Spring": "Sep-Nov"}

MIN_DRIFTERS = 10  # support threshold from the proposal (reviewed in the coverage map)


def cell_bounds(cell):
    """(lon0, lon1, lat0, lat1) of a 2-degree cell, clipped to R."""
    r, c = divmod(int(cell), N_COLS)
    lon0, lat0 = WEST + c * GRID, SOUTH + r * GRID
    return lon0, min(lon0 + GRID, EAST), lat0, min(lat0 + GRID, NORTH)


def cell_label(cell):
    lon0, lon1, lat0, lat1 = cell_bounds(cell)
    return f"{lon0}-{lon1}°E, {-lat1}-{-lat0}°S"


def find_pairs7():
    for p in [os.environ.get("PAIRS7"), HERE / "pairs7.csv", HERE.parent / "pairs7.csv"]:
        if p and Path(p).exists():
            return Path(p)
    raise FileNotFoundError("pairs7.csv not found: put it next to this script (from the DATA3001 handover folder)")


def load_pairs7():
    path = find_pairs7()
    pairs = pd.read_csv(path)
    assert len(pairs) == 154139, f"unexpected pairs7.csv length {len(pairs)}"
    t = pd.to_datetime(pairs["time"], utc=True)
    pairs["month"] = t.dt.month
    pairs["year"] = t.dt.year
    pairs["season"] = pd.Categorical(pairs["month"].map(SEASON_OF_MONTH), categories=SEASONS, ordered=True)
    pairs["west"] = pairs["dest"].eq(EXIT["west"])
    pairs["east"] = pairs["dest"].eq(EXIT["east"])
    pairs["left_cell"] = pairs["dest"].ne(pairs["origin_cell"])
    print(f"Loaded {path} : {len(pairs):,} pairs, {pairs.traj.nunique():,} drifters")
    return pairs


def find_split():
    for p in [os.environ.get("DRIFTER_SPLIT"), HERE / "drifter_split.csv", HERE.parent / "drifter_split.csv"]:
        if p and Path(p).exists():
            return Path(p)
    raise FileNotFoundError("drifter_split.csv (Zack's train/val/test split) not found")


def load_shared_functions():
    """Return Vrishin's build_transition_matrix and bootstrap_exit_probability from vrishinanalysis.py."""
    src_path = HERE / "vrishinanalysis.py"
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    defs = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)], type_ignores=[])
    ns = {"np": np, "pd": pd}
    exec(compile(defs, str(src_path), "exec"), ns)
    return ns["build_transition_matrix"], ns["bootstrap_exit_probability"]


def drifter_bootstrap(df, group_col, event_cols, n_boot=1000, seed=42):
    """Whole-drifter bootstrap of event rates for every group at once.

    Resamples drifters (all their pairs together) with replacement, using the SAME resample for
    every group, so differences between groups (e.g. one season minus the rest of the year)
    get a valid paired CI even when a drifter contributes to several groups.

    Returns (groups, den, rates): den is (n_boot, n_groups) resampled pair counts, rates maps
    each event column to a (n_boot, n_groups) array of resampled proportions (nan if den == 0).
    """
    n = df.groupby(["traj", group_col], observed=True).size().unstack(fill_value=0)
    groups = list(n.columns)
    rng = np.random.default_rng(seed)
    D = len(n)
    W = rng.multinomial(D, np.full(D, 1.0 / D), size=n_boot).astype(float)  # how often each drifter is drawn
    den = W @ n.to_numpy(float)
    rates = {}
    for e in event_cols:
        num = (df[e].astype(int).groupby([df["traj"], df[group_col]], observed=True).sum()
               .unstack(fill_value=0).reindex(index=n.index, columns=n.columns, fill_value=0))
        with np.errstate(invalid="ignore", divide="ignore"):
            rates[e] = np.where(den > 0, (W @ num.to_numpy(float)) / den, np.nan)
    return groups, den, rates, W, n


WEEK = np.int64(7 * 86_400 * 10**9)
SIDE_OF = {v: k for k, v in EXIT.items()}


def chain_outcomes(df, start_cells, weeks):
    """Lucy's chain_outcomes (notebook Step 11) for several start cells.

    Follows every start in `start_cells` week by week through its own 7-day pairs and returns the
    starting rows with an extra column `out`: "west"/"east"/"south"/"north" (first exit), "inR", or
    "censored" (record ends or has a gap before the horizon)."""
    t_ns = pd.to_datetime(df.time, utc=True).values.astype("datetime64[ns]").astype(np.int64)
    look = dict(zip(zip(df.traj.values, t_ns), df.dest.values))
    sel = np.flatnonzero(df.origin_cell.isin(start_cells).values)
    out = []
    for i in sel:
        tj, t, res = df.traj.values[i], t_ns[i], "inR"
        for _ in range(weeks):
            dst = look.get((tj, t))
            if dst is None:
                res = "censored"
                break
            if dst >= N_CELLS:
                res = SIDE_OF[dst]
                break
            t += WEEK
        out.append(res)
    o = df.iloc[sel].copy()
    o["out"] = out
    return o


def to_P(counts):
    """Same rule as build_transition_matrix: row-normalise, unsupported rows stay zero, exits absorbing."""
    rt = counts.sum(1)
    P = np.divide(counts, rt[:, None], out=np.zeros_like(counts), where=rt[:, None] > 0)
    P[N_CELLS:, N_CELLS:] = np.eye(4)
    return P


def exit_at(P, cell, steps):
    v = np.zeros(N_STATES)
    v[cell] = 1.0
    out = {}
    for k in range(1, max(steps) + 1):
        v = v @ P
        if k in steps:
            out[k] = (v[EXIT["west"]], v[EXIT["east"]])
    return out


def ci(samples, axis=0):
    lo, hi = np.nanpercentile(samples, [2.5, 97.5], axis=axis)
    return lo, hi


# ---------- maps (styling from Lucy's Figure 1) ----------
_LAND = None


def _land():
    global _LAND
    if _LAND is None:
        cache = OUT / ".ne_110m_land.geojson"
        try:
            if not cache.exists():
                url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson"
                cache.write_bytes(urllib.request.urlopen(url, timeout=20).read())
            _LAND = json.loads(cache.read_text(encoding="utf-8"))
        except Exception as e:  # maps still work without a coastline
            print(f"coastline not loaded ({e!r}); maps drawn without land")
            _LAND = {"features": []}
    return _LAND


def draw_land(ax):
    from matplotlib.patches import Polygon
    for feat in _land()["features"]:
        g = feat["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for p in polys:
            ax.add_patch(Polygon(np.array(p[0]), closed=True, facecolor="#e8e6e1", edgecolor="none", zorder=0))
            ax.add_patch(Polygon(np.array(p[0]), closed=True, fill=False, edgecolor="#6b6a66", linewidth=0.8, zorder=3))


def style_map(ax, fontsize=9):
    ax.set_xlim(WEST, EAST)
    ax.set_ylim(SOUTH, NORTH)
    ax.set_aspect(1 / np.cos(np.deg2rad((NORTH + SOUTH) / 2)))
    ax.set_xticks(range(WEST, EAST + 1, 5))
    ax.set_yticks(range(SOUTH, NORTH + 1, 5))
    ax.set_xticklabels([f"{x}°E" for x in range(WEST, EAST + 1, 5)], fontsize=fontsize, color="#555")
    ax.set_yticklabels([f"{-y}°S" for y in range(SOUTH, NORTH + 1, 5)], fontsize=fontsize, color="#555")
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_color("#bbb")


LON_EDGES = WEST + np.arange(N_COLS + 1) * GRID
LAT_EDGES = SOUTH + np.arange(N_ROWS + 1) * GRID


def to_grid(values_by_cell):
    """Series/dict indexed by cell -> (N_ROWS, N_COLS) array, nan where missing."""
    g = np.full(N_CELLS, np.nan)
    for c, v in dict(values_by_cell).items():
        g[int(c)] = v
    return g.reshape(N_ROWS, N_COLS)


def mark_abc(ax, color="#111", fontsize=10):
    from matplotlib.patches import Rectangle
    for name, cell in CELLS_ABC.items():
        lon0, lon1, lat0, lat1 = cell_bounds(cell)
        ax.add_patch(Rectangle((lon0, lat0), lon1 - lon0, lat1 - lat0, fill=False,
                               edgecolor=color, linewidth=1.6, zorder=5))
        ax.text((lon0 + lon1) / 2, (lat0 + lat1) / 2, name, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color=color, zorder=6)

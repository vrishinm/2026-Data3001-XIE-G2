import os
import json
import time as _time

import numpy as np
import pandas as pd
from clouddrift.datasets import gdp1h
from clouddrift.ragged import obs_index_to_row

OUT = "gdp_out"
os.makedirs(OUT, exist_ok=True)

REGION = dict(name="greater Agulhas Current system", lon_min=10, lon_max=45, lat_min=-45, lat_max=-20)
GRID_DEG = 2
HORIZON_DAYS = 7
HORIZON_ROWS = HORIZON_DAYS * 24  # exact row offset on the hourly grid, 168


def load_values(da, name, tries=5, base_delay=3.0):
    """.values, retried a few times — the public S3 backend behind gdp1h()
    occasionally drops mid-transfer, and has no built-in retry of its own."""
    last = None
    for i in range(tries):
        try:
            return da.values
        except Exception as e:
            last = e
            wait = base_delay * (i + 1)
            print(f"  {name}: fetch failed ({e!r}), retrying in {wait:.0f}s [{i+1}/{tries}]", flush=True)
            _time.sleep(wait)
    raise last


def main():
    t0 = _time.time()

    print("opening gdp1h() via clouddrift ...", flush=True)
    ds = gdp1h()

    print("pulling lon/lat/time/rowsize (the actual network fetch) ...", flush=True)
    lon = load_values(ds["lon"], "lon")
    print(f"  lon done, elapsed={_time.time()-t0:.0f}s", flush=True)
    lat = load_values(ds["lat"], "lat")
    print(f"  lat done, elapsed={_time.time()-t0:.0f}s", flush=True)
    time_raw = load_values(ds["time"], "time")
    print(f"  time done, elapsed={_time.time()-t0:.0f}s", flush=True)
    rowsize = load_values(ds["rowsize"], "rowsize")
    print(f"  rowsize done, elapsed={_time.time()-t0:.0f}s", flush=True)

    n_obs = lon.shape[0]
    n_traj = rowsize.shape[0]
    assert int(rowsize.astype(np.int64).sum()) == n_obs
    print(f"n_obs={n_obs} n_traj={n_traj} elapsed={_time.time()-t0:.0f}s", flush=True)

    # ---- obs -> trajectory index (clouddrift's own ragged-array utility) ----
    cum_end = np.cumsum(rowsize.astype(np.int64))
    obs_idx = np.arange(n_obs, dtype=np.int64)
    traj_of_obs = np.asarray(obs_index_to_row(obs_idx, rowsize), dtype=np.int64)

    times = pd.to_datetime(time_raw)
    t_ns = times.values.astype("datetime64[ns]").astype(np.int64)

    # =====================================================================
    # 1. DATA AUDIT (slide 9: inspect before you trust any count)
    # =====================================================================
    print("\n=== data audit ===", flush=True)
    missing_lon = int(np.isnan(lon).sum())
    missing_lat = int(np.isnan(lat).sum())
    out_of_range = int(((lon < -180) | (lon > 360) | (lat < -90) | (lat > 90)).sum())

    # duplicate timestamps and interruptions in the hourly sequence. Data is
    # already stored trajectory-by-trajectory and time-ordered within each
    # trajectory, so traj_of_obs is already non-decreasing — no sort needed,
    # just look at where trajectory boundaries fall.
    same_traj = np.diff(traj_of_obs) == 0
    dt = np.diff(t_ns)
    one_hour_ns = np.int64(3600) * np.int64(1_000_000_000)
    duplicate_timestamps = int(((dt == 0) & same_traj).sum())
    non_hourly_gaps = int(((dt != one_hour_ns) & (dt != 0) & same_traj).sum())

    audit = dict(
        n_obs=n_obs,
        n_traj=n_traj,
        missing_lon=missing_lon,
        missing_lat=missing_lat,
        out_of_range_coords=out_of_range,
        duplicate_timestamps_within_traj=duplicate_timestamps,
        non_hourly_gaps_within_traj=non_hourly_gaps,
    )
    print(json.dumps(audit, indent=2), flush=True)

    # =====================================================================
    # 2. GLOBAL 1-DEG GRID + (cell, trajectory) PAIRS (region adequacy check)
    # =====================================================================
    print("\n=== building global 1-deg grid + (cell, trajectory) pairs ===", flush=True)
    conv360 = bool(np.nanmax(lon) > 180.0)
    # the region indexing below (x + 180) and the exit-side test in section 3
    # both assume -180..180 longitudes, which is what gdp1h() returns
    assert not conv360, "expected -180..180 longitudes"
    valid = np.isfinite(lon) & np.isfinite(lat)
    lonv = np.mod(lon, 360.0) if conv360 else lon + 180.0
    xi = np.clip(np.floor(lonv).astype(np.int64), 0, 359)
    yi = np.clip(np.floor(lat + 90.0).astype(np.int64), 0, 179)
    cell = xi + 360 * yi

    obs_grid = np.bincount(cell[valid], minlength=360 * 180)
    pairs = np.unique(cell[valid].astype(np.int64) * 100000 + traj_of_obs[valid])
    pc = (pairs // 100000).astype(np.int32)
    pt = (pairs % 100000).astype(np.int32)
    og = obs_grid.reshape(180, 360)

    def stats_1deg(x0, x1, y0, y1):
        xi0, xi1, yi0, yi1 = x0 + 180, x1 + 180, y0 + 90, y1 + 90
        sub = og[yi0:yi1, xi0:xi1]
        sel = (pc % 360 >= xi0) & (pc % 360 < xi1) & (pc // 360 >= yi0) & (pc // 360 < yi1)
        nz = sub[sub > 0]
        return dict(
            lon_min=x0, lon_max=x1, lat_min=y0, lat_max=y1, grid_deg=1,
            hourly_records=int(sub.sum()),
            distinct_drifters=int(np.unique(pt[sel]).size),
            cells_occupied=int((sub > 0).sum()),
            median_obs_per_cell=int(np.median(nz)) if nz.size else 0,
        )

    def stats_2deg(x0, x1, y0, y1):
        xi0, xi1, yi0, yi1 = x0 + 180, x1 + 180, y0 + 90, y1 + 90
        sub = og[yi0:yi1, xi0:xi1]
        nx, ny = -(-(x1 - x0) // GRID_DEG), -(-(y1 - y0) // GRID_DEG)
        sel = (pc % 360 >= xi0) & (pc % 360 < xi1) & (pc // 360 >= yi0) & (pc // 360 < yi1)
        bx = (pc[sel] % 360 - xi0) // GRID_DEG
        by = (pc[sel] // 360 - yi0) // GRID_DEG
        key = np.unique((by * nx + bx) * 100000 + pt[sel])
        nr = np.bincount(key // 100000, minlength=nx * ny).astype(np.int64)
        nz = nr[nr > 0]
        return dict(
            lon_min=x0, lon_max=x1, lat_min=y0, lat_max=y1, grid_deg=GRID_DEG,
            hourly_records=int(sub.sum()),
            distinct_drifters=int(np.unique(pt[sel]).size),
            cells_occupied=int(nz.size),
            cells_total=int(nx * ny),
            cells_with_ge10_drifters=int((nz >= 10).sum()),
            median_drifters_per_cell=int(np.median(nz)) if nz.size else 0,
            drifter_p25=int(np.percentile(nz, 25)) if nz.size else 0,
            drifter_p75=int(np.percentile(nz, 75)) if nz.size else 0,
        )

    eac = stats_1deg(145, 165, -45, -15)
    print(f"EAC check: {eac['distinct_drifters']} distinct drifters (slide reports 452)", flush=True)

    chosen_stats = stats_2deg(REGION["lon_min"], REGION["lon_max"], REGION["lat_min"], REGION["lat_max"])

    # =====================================================================
    # 3. 7-DAY ORIGIN-DESTINATION PAIRS (slide 11/15: the number that
    #    actually determines transition-matrix feasibility, not just raw
    #    drifter counts per cell)
    #
    #    Same exact-row-offset idea as before (+168 rows, timestamp checked),
    #    with three changes so the pairs match the README method:
    #      (a) one origin per day (00:00 UTC) instead of every hour —
    #          neighbouring hours are near-duplicates, not new information;
    #      (b) every hourly position between origin and day 7 is checked, so a
    #          drifter that leaves R and comes back still counts as an exit
    #          (outside is an absorbing state in the matrix);
    #      (c) the exit is labelled by the side of R it crossed
    #          (W = towards the Atlantic, E, S, N), which is what the
    #          leakage-vs-retroflection question needs.
    #    A drifter whose record ends inside R before day 7 is dropped
    #    (we don't know where it went); if it had already exited, the exit
    #    is kept because exit is absorbing.
    # =====================================================================
    print(f"\n=== {HORIZON_DAYS}-day origin-destination pairs, Agulhas 2-deg cells ===", flush=True)

    x0, x1, y0, y1 = REGION["lon_min"], REGION["lon_max"], REGION["lat_min"], REGION["lat_max"]
    xi0, xi1, yi0, yi1 = x0 + 180, x1 + 180, y0 + 90, y1 + 90
    nx = -(-(x1 - x0) // GRID_DEG)
    ny = -(-(y1 - y0) // GRID_DEG)
    n_cells = int(nx * ny)
    EXIT_W, EXIT_E, EXIT_S, EXIT_N = n_cells, n_cells + 1, n_cells + 2, n_cells + 3
    one_day_ns = np.int64(86400) * np.int64(1_000_000_000)
    seven_days_ns = np.int64(HORIZON_DAYS) * one_day_ns

    in_box = (xi >= xi0) & (xi < xi1) & (yi >= yi0) & (yi < yi1) & valid
    out_box = valid & ~in_box
    # cs[m] = number of outside-R rows among rows 0..m-1, so the number of
    # outside rows in (a, b] is cs[b + 1] - cs[a + 1]
    cs = np.concatenate([[0], np.cumsum(out_box, dtype=np.int64)])

    # (a) daily origins inside R
    origin = np.where(in_box & (t_ns % one_day_ns == 0))[0]
    traj_o = traj_of_obs[origin]
    last_row = np.minimum(origin + HORIZON_ROWS, cum_end[traj_o] - 1)

    # (b) first row outside R after the origin, within the 7-day window
    n_out = cs[last_row + 1] - cs[origin + 1]
    first_out = np.searchsorted(cs, cs[origin + 1] + 1, side="left") - 1
    exited = n_out > 0
    exited &= (t_ns[np.where(exited, first_out, origin)] - t_ns[origin]) <= seven_days_ns

    # non-exited pairs still need a valid position exactly 7 days later
    dst = origin + HORIZON_ROWS
    full_window = dst < cum_end[traj_o]
    dst_safe = np.where(full_window, dst, origin)
    exact_horizon = full_window & ((t_ns[dst_safe] - t_ns[origin]) == seven_days_ns)
    stayed = ~exited & exact_horizon & in_box[dst_safe]
    keep = exited | stayed

    def cell2d(rows):
        return ((yi[rows] - yi0) // GRID_DEG * nx + (xi[rows] - xi0) // GRID_DEG).astype(np.int64)

    # (c) destination: a 2-deg cell, or the side of R the drifter left through
    dest = np.full(origin.size, -1, dtype=np.int64)
    dest[stayed] = cell2d(dst[stayed])
    fo = first_out[exited]
    side = np.where(lon[fo] < x0, EXIT_W,
           np.where(lon[fo] >= x1, EXIT_E,
           np.where(lat[fo] < y0, EXIT_S, EXIT_N)))
    dest[exited] = side

    # how often the old endpoint-only rule would have called an exit "stayed"
    exit_and_return = int((exited & exact_horizon & in_box[dst_safe]).sum())

    o_rows = origin[keep]
    pair_origin = cell2d(o_rows)
    pair_dest = dest[keep]
    pair_traj = traj_of_obs[o_rows]

    pair_counts = np.bincount(pair_origin, minlength=n_cells)
    key = np.unique(pair_origin * 100000 + pair_traj)
    distinct_drifters_per_cell = np.bincount(key // 100000, minlength=n_cells)

    nz_pairs = pair_counts[pair_counts > 0]
    nz_drift = distinct_drifters_per_cell[distinct_drifters_per_cell > 0]
    n_exit = int(exited.sum())
    od_summary = dict(
        horizon_days=HORIZON_DAYS,
        origins_per_drifter_day=1,
        candidate_daily_origins=int(origin.size),
        total_valid_pairs=int(keep.sum()),
        pairs_dropped_record_ended_or_gap=int((~keep).sum()),
        pairs_stayed_in_R=int(stayed.sum()),
        pairs_exited=n_exit,
        exits_by_side={s: int((pair_dest == c).sum()) for s, c in
                       [("west", EXIT_W), ("east", EXIT_E), ("south", EXIT_S), ("north", EXIT_N)]},
        exit_and_return_pairs=exit_and_return,
        exit_and_return_share_of_exits=round(exit_and_return / n_exit, 4) if n_exit else 0.0,
        cells_with_any_pairs=int((pair_counts > 0).sum()),
        cells_with_ge10_pairs=int((pair_counts >= 10).sum()),
        cells_with_ge10_distinct_drifters=int((distinct_drifters_per_cell >= 10).sum()),
        median_pairs_per_occupied_cell=int(np.median(nz_pairs)) if nz_pairs.size else 0,
        median_distinct_drifters_per_occupied_cell=int(np.median(nz_drift)) if nz_drift.size else 0,
    )
    print(json.dumps(od_summary, indent=2), flush=True)

    np.savez_compressed(
        os.path.join(OUT, "agulhas_7day_pairs.npz"),
        origin_cell=pair_origin, dest=pair_dest, traj=pair_traj, origin_time_ns=t_ns[o_rows],
        n_cells=n_cells, nx=nx, ny=ny, exit_codes=np.array([EXIT_W, EXIT_E, EXIT_S, EXIT_N]),
    )

    # =====================================================================
    # 4. COVERAGE MAPS (slide 10: obs count and distinct drifter count,
    #    same colour scale, side by side)
    # =====================================================================
    print("\n=== rendering coverage maps ===", flush=True)
    try:
        import matplotlib.pyplot as plt

        sub_obs = og[yi0:yi1, xi0:xi1]
        sel = (pc % 360 >= xi0) & (pc % 360 < xi1) & (pc // 360 >= yi0) & (pc // 360 < yi1)
        drift_grid = np.zeros_like(sub_obs, dtype=np.int64)
        by1 = pc[sel] // 360 - yi0
        bx1 = pc[sel] % 360 - xi0
        for yy, xx in zip(by1, bx1):
            drift_grid[yy, xx] += 1  # occupied-by-any-drifter tally, cheap loop over 1-deg cells only

        vmax_obs = sub_obs.max()
        vmax_drift = drift_grid.max()
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        im0 = axes[0].imshow(sub_obs, origin="lower", vmin=0, vmax=vmax_obs,
                              extent=[x0, x1, y0, y1], aspect="auto")
        axes[0].set_title("Hourly observations per 1° cell")
        fig.colorbar(im0, ax=axes[0])
        im1 = axes[1].imshow(drift_grid, origin="lower", vmin=0, vmax=vmax_drift,
                              extent=[x0, x1, y0, y1], aspect="auto")
        axes[1].set_title("Distinct drifters per 1° cell")
        fig.colorbar(im1, ax=axes[1])
        for ax in axes:
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
        fig.suptitle(REGION["name"])
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, "agulhas_coverage_maps.png"), dpi=150)
        print(f"saved {os.path.join(OUT, 'agulhas_coverage_maps.png')}", flush=True)
    except Exception as e:
        print(f"map rendering skipped: {e!r}", flush=True)

    # =====================================================================
    # 5. SAVE EVERYTHING
    # =====================================================================
    np.savez_compressed(
        os.path.join(OUT, "gdp_1deg_grids.npz"),
        obs_grid=og, pairs_cell=pc, pairs_traj=pt,
    )

    result = {
        "dataset": {
            "name": "NOAA Global Drifter Program hourly dataset v2.01.1",
            "access": "clouddrift.datasets.gdp1h()",
            "citation": "Elipot et al. (2022), doi:10.25921/x46c-3620",
            "total_hourly_records": n_obs,
            "total_deployments": n_traj,
            "lon_convention": "0..360" if conv360 else "-180..180 degrees East",
        },
        "data_audit": audit,
        "pipeline_validation_eac": eac,
        "chosen_region": {
            "name": REGION["name"],
            **chosen_stats,
            "same_box_1deg": stats_1deg(x0, x1, y0, y1),
        },
        "alternates_rejected": {
            "tighter_10_40E_25_45S": stats_2deg(10, 40, -45, -25),
            "source_only_20_45E_20_40S": stats_2deg(20, 45, -40, -20),
        },
        "benguela_comparison": stats_2deg(-15, 10, -35, -15),
        "seven_day_origin_destination_feasibility": od_summary,
    }

    with open(os.path.join(OUT, "region_adequacy_results.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2), flush=True)
    print(f"TOTAL elapsed {_time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()

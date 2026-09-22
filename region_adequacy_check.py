import os
import json
import math
import time
import threading
import concurrent.futures as cf

import numpy as np
import requests
import numcodecs

BASE = "https://noaa-oar-hourly-gdp-pds.s3.amazonaws.com/latest/gdp-v2.01.1.zarr"
OUT = "gdp_out"
os.makedirs(OUT, exist_ok=True)
N_OBS = 197214787
CHUNK = 385186
N_CHUNKS = math.ceil(N_OBS / CHUNK)
N_TRAJ = 19396
BATCH = 24
WORKERS = 12
COMP = numcodecs.Blosc(cname="lz4", clevel=5, shuffle=1)

_tls = threading.local()


def session():
    if not hasattr(_tls, "s"):
        s = requests.Session()
        s.headers.update({"User-Agent": "region-adequacy-check/1.0"})
        _tls.s = s
    return _tls.s


def fetch(url, tries=4):
    last = None
    for i in range(tries):
        try:
            r = session().get(url, timeout=120)
            r.raise_for_status()
            return r.content
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def decode(raw):
    return np.frombuffer(COMP.decode(raw), dtype="<f8")


def get_chunk(var, i):
    raw = fetch(f"{BASE}/{var}/{i}")
    return i, len(raw), decode(raw)


def main():
    t0 = time.time()
    print("fetching rowsize ...", flush=True)
    rowsize = np.frombuffer(COMP.decode(fetch(f"{BASE}/rowsize/0")), dtype="<i4")
    assert rowsize.shape[0] == N_TRAJ and int(rowsize.astype(np.int64).sum()) == N_OBS, \
        (rowsize.shape, int(rowsize.astype(np.int64).sum()))
    cum_end = np.cumsum(rowsize.astype(np.int64))

    print("checking lon convention ...", flush=True)
    i0, n0, lon0 = get_chunk("lon", 0)
    conv360 = bool(np.nanmax(lon0) > 180.0)
    print(f"first chunk max lon {np.nanmax(lon0):.2f} -> 0..360 convention: {conv360}", flush=True)

    obs_grid = np.zeros(360 * 180, dtype=np.int64)
    pairs = []
    bytes_dl = n0 + 0
    t0b = time.time()

    def process(i, nbytes, lon, lat):
        nonlocal obs_grid
        off = i * CHUNK
        k = len(lon)
        assert len(lat) == k
        obs_idx = np.arange(off, off + k, dtype=np.int64)
        traj = np.searchsorted(cum_end, obs_idx, side="right")
        valid = np.isfinite(lon) & np.isfinite(lat)
        if conv360:
            lonv = np.mod(lon, 360.0)
        else:
            lonv = lon + 180.0
        xi = np.clip(np.floor(lonv).astype(np.int64), 0, 359)
        yi = np.clip(np.floor(lat + 90.0).astype(np.int64), 0, 179)
        cell = xi + 360 * yi
        c = cell[valid]
        t = traj[valid]
        obs_grid += np.bincount(c, minlength=360 * 180)
        pairs.append(np.unique(c * 100000 + t))

    done = 0
    for b0 in range(0, N_CHUNKS, BATCH):
        batch = list(range(b0, min(b0 + BATCH, N_CHUNKS)))
        with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = {}
            for i in batch:
                futs[ex.submit(get_chunk, "lon", i)] = (i, "lon")
                futs[ex.submit(get_chunk, "lat", i)] = (i, "lat")
            results = {}
            for f in cf.as_completed(futs):
                i, var = futs[f]
                _, nb, arr = f.result()
                bytes_dl += nb
                results.setdefault(i, {})[var] = (nb, arr)
            for i in batch:
                _, lon = results[i]["lon"]
                _, lat = results[i]["lat"]
                process(i, 0, lon, lat)
                done += 1
        el = time.time() - t0b
        print(f"chunks {done}/{N_CHUNKS}  downloaded {bytes_dl/1e6:.0f} MB  "
              f"elapsed {el:.0f}s  speed {bytes_dl/1e6/el:.2f} MB/s", flush=True)

    print("reducing pairs ...", flush=True)
    pairs = np.unique(np.concatenate(pairs))
    pc = (pairs // 100000).astype(np.int32)
    pt = (pairs % 100000).astype(np.int32)
    drifter_grid = np.bincount(pc, minlength=360 * 180).astype(np.int32)

    np.savez_compressed(
        os.path.join(OUT, "gdp_grids.npz"),
        obs_grid=obs_grid.reshape(180, 360),
        drifter_grid=drifter_grid.reshape(180, 360),
        pairs_cell=pc,
        pairs_traj=pt,
    )

    boxes = {
        "A 15-40E 25-42S": (15, 40, -42, -25),
        "B 10-40E 25-45S": (10, 40, -45, -25),
        "C 20-45E 20-40S": (20, 45, -40, -20),
        "D 12-40E 24-44S": (12, 40, -44, -24),
        "E 15-35E 25-40S": (15, 35, -40, -25),
        "F 15-40E 25-45S": (15, 40, -45, -25),
        "G 20-40E 25-40S": (20, 40, -40, -25),
        "H 10-35E 25-44S": (10, 35, -44, -25),
    }
    og = obs_grid.reshape(180, 360)
    dg = drifter_grid.reshape(180, 360)
    out = {}
    for name, (x0, x1, y0, y1) in boxes.items():
        xi0, xi1 = x0 + 180, x1 + 180
        yi0, yi1 = y0 + 90, y1 + 90
        sub_obs = og[yi0:yi1, xi0:xi1]
        obs_n = int(sub_obs.sum())
        cells_any = int((sub_obs > 0).sum())
        cells_20 = int((sub_obs >= 20).sum())
        cells_100 = int((sub_obs >= 100).sum())
        sel = (pc % 360 >= xi0) & (pc % 360 < xi1) & (pc // 360 >= yi0) & (pc // 360 < yi1)
        traj_n = int(np.unique(pt[sel]).size)
        med = float(np.median(sub_obs[sub_obs > 0])) if cells_any else 0.0
        out[name] = dict(obs=obs_n, traj=traj_n, cells_any=cells_any, cells_20=cells_20,
                         cells_100=cells_100, median_obs_per_cell=med)
        print(f"{name}: obs={obs_n:,}  traj={traj_n:,}  cells>0={cells_any}  "
              f"cells>=20={cells_20}  cells>=100={cells_100}  median_obs/cell={med:.0f}", flush=True)

    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"TOTAL elapsed {time.time()-t0:.0f}s, downloaded {bytes_dl/1e6:.0f} MB", flush=True)


if __name__ == "__main__":
    main()

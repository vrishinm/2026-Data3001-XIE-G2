"""Prepare proposal evidence from local caches and Lucy's saved notebook.

No network access and no notebook execution. Saved outputs are distinguished
from statistics recomputed from the spatial occupancy cache.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "analysis" / "section2_lucy.ipynb"


def saved_text(cell: dict) -> str:
    parts = []
    for output in cell.get("outputs", []):
        value = output.get("text") or output.get("data", {}).get("text/plain")
        if value:
            parts.append("".join(value) if isinstance(value, list) else value)
    return "\n".join(parts)


def box_stats(cache, box, step: int) -> dict:
    west, east, south, north = box
    cells = cache["pairs_cell"]
    tracks = cache["pairs_traj"]
    cols, rows = cells % 360, cells // 360
    mask = ((cols >= west + 180) & (cols < east + 180)
            & (rows >= south + 90) & (rows < north + 90))
    nx = int(np.ceil((east - west) / step))
    ny = int(np.ceil((north - south) / step))
    local = ((rows[mask] - south - 90) // step) * nx
    local += (cols[mask] - west - 180) // step
    # Use a column-wise unique operation rather than a magic ID multiplier.
    unique = np.unique(np.column_stack((local, tracks[mask])), axis=0)
    counts = np.bincount(unique[:, 0], minlength=nx * ny)
    occupied = counts[counts > 0]
    records = cache["obs_grid"][south + 90:north + 90, west + 180:east + 180]
    return {
        "box": list(box), "boundary_convention": "half-open",
        "grid_degrees": step, "records": int(records.sum()),
        "drifters": int(np.unique(tracks[mask]).size),
        "total_cells": nx * ny, "occupied_cells": int(occupied.size),
        "cells_at_least_10_drifters": int((counts >= 10).sum()),
        "median_drifters": float(np.median(occupied)),
        "p25_drifters": float(np.percentile(occupied, 25)),
        "p75_drifters": float(np.percentile(occupied, 75)),
    }


def main() -> None:
    notebook_raw = NOTEBOOK.read_bytes()
    notebook = json.loads(notebook_raw)
    cells = notebook["cells"]
    text_by_cell = {i: saved_text(cell) for i, cell in enumerate(cells)}
    figures = ROOT / "figures"
    figures.mkdir(exist_ok=True)
    extracted = []
    for index, name in [(12, "coverage_1deg"), (13, "drifters_per_year"),
                        (14, "drogued_coverage_1deg")]:
        images = [o["data"]["image/png"] for o in cells[index].get("outputs", [])
                  if "image/png" in o.get("data", {})]
        if len(images) != 1:
            raise ValueError(f"Expected one saved PNG in notebook cell {index}")
        value = images[0]
        raw = base64.b64decode("".join(value) if isinstance(value, list) else value)
        path = figures / f"{name}.png"
        path.write_bytes(raw)
        extracted.append({"file": path.relative_to(ROOT).as_posix(),
                          "notebook_cell": index, "sha256": hashlib.sha256(raw).hexdigest()})

    season_rows = []
    pattern = re.compile(r"^(DJF|MAM|JJA|SON)\s+\([^)]*\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$", re.M)
    for season, records, tracks, occupied, median, supported in pattern.findall(text_by_cell[13]):
        season_rows.append({"season": season, "records": int(records),
                            "drifters": int(tracks), "occupied_1deg_cells": int(occupied),
                            "median_drifters_per_1deg_cell": int(median),
                            "cells_at_least_10_drifters": int(supported)})
    if len(season_rows) != 4 or sum(x["records"] for x in season_rows) != 3848969:
        raise ValueError("Saved seasonal outputs do not match the proposal totals")

    with np.load(ROOT / "gdp_1deg_grids.npz") as cache:
        agulhas1 = box_stats(cache, (10, 45, -45, -20), 1)
        agulhas2 = box_stats(cache, (10, 45, -45, -20), 2)
        benguela = box_stats(cache, (0, 20, -38, -15), 1)
        eac = box_stats(cache, (145, 165, -45, -15), 1)
    assert (agulhas2["records"], agulhas2["drifters"], agulhas2["occupied_cells"],
            agulhas2["cells_at_least_10_drifters"], agulhas2["median_drifters"]) == (3848967, 1149, 178, 171, 116)
    assert (benguela["records"], benguela["drifters"]) == (2538266, 706)
    assert eac["drifters"] == 452
    data = {
        "prepared_on": "2026-10-06", "model_results": False,
        "provenance": {"notebook": "analysis/section2_lucy.ipynb",
                       "local_ref": "origin/lucy", "source_commit": "4e3d1ef",
                       "notebook_sha256": hashlib.sha256(notebook_raw).hexdigest(),
                       "cache": "gdp_1deg_grids.npz",
                       "scope": "Offline cache re-counts and extraction of saved notebook outputs; no timed trajectory or model run."},
        "recomputed_cache": {"agulhas_1deg": agulhas1, "agulhas_2deg": agulhas2,
                             "benguela_proposal_box": benguela, "eac_validation": eac},
        "saved_notebook": {"inclusive_agulhas_records": 3848969,
                           "source_text": {str(i): text_by_cell[i] for i in [11, 12, 13, 14, 15]},
                           "seasonal_1deg_coverage": season_rows},
        "figures": extracted,
        "interpretation": ["Occupancy is not training transition support.",
                           "Seasonal drifter counts overlap between seasons.",
                           "Final position outside R is not a daily first-exit count.",
                           "The old JSON Benguela comparison uses a different box and is retained as historical evidence."]
    }
    target = ROOT / "analysis" / "proposal_evidence.json"
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {target.relative_to(ROOT)} and {len(extracted)} original notebook figures.")
    print("Verified Agulhas/Benguela/EAC cache counts and seasonal record total.")


if __name__ == "__main__":
    main()

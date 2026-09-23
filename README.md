# DATA3001 Term 3 2026 — Project 3.2.2: "Where things end up"

## A surface-transport operator for the Agulhas region

Project proposal / repository README (15%, 3 A4 pages + references).
Due Sunday Week 3 per the project brief (Week-1 slides say Week 4 — **TODO: confirm with lecturer**).

**Client:** Shane Elipot (Rosenstiel School, University of Miami)
**Group:** 2
**Repository:** `https://github.com/cestbon0309/DATA3001-T3`

---

## 1. Region and motivation

**Region R.** R is the greater Agulhas Current system, defined as the box

> **R = 10°E–40°E, 25°S–45°S** (30° × 20°; 483 occupied 1° cells)

The box was selected against the data-adequacy comparison in Section 2: it holds 3.0 million hourly records from 1,051 independent drifters, while remaining small enough that most 1° cells are sampled by many independent drifters.

**Why this region matters.** The Agulhas Current is one of the strongest western boundary currents in the Southern Hemisphere; it carries warm, saline Indian Ocean water southwest along the South African coast before retroflecting south of the continent and returning east as the Agulhas Return Current (Lutjeharms, 2006). Rings shed at the retroflection export Indian Ocean water into the South Atlantic — "Agulhas leakage" — a process implicated in the Atlantic overturning circulation and in past climate change (de Ruijter et al., 1999; Beal et al., 2011). The system also supports major regional fisheries, and it underlies search-and-rescue, debris- and spill-response planning along one of the world's busiest shipping routes: in each case the operative question is where the surface water — and anything floating in it — goes. R is also among the best-sampled regions of the Global Drifter Program, which makes a data-driven transport operator feasible here.

**Multiple flow regimes.** R is expected to contain several distinct regimes — the Mozambique Channel inflow in the north-east, the narrow Agulhas core jet along the coast, the retroflection and ring-shedding corridor in the south-west, and the eastward return current — so material transport within R is likely to be strongly asymmetric and directional rather than diffusive.

---

## 2. Data availability

**Source.** NOAA Global Drifter Program hourly dataset, v2.01.1 (NCEI accession 0248584; Elipot et al., 2022), accessed through the CloudDrift `gdp1h()` interface on 23 September 2026. The release covers 2 October 1987 to 31 October 2022: 197,214,787 hourly records from 19,396 drifter trajectories. A record is counted as in R if its position lies inside the box, boundaries included.

**Validation.** Our pipeline reproduces the course's published Week 1 counts exactly for both boxes we examined (Xie, 2026, slide 7), which confirms that the data release and counting method match.

| Box | Longitude | Latitude | Hourly records | Distinct drifters | Course figure |
|---|---|---|---|---|---|
| **R — Agulhas (chosen)** | 10–45°E | 45–20°S | 3,848,969 | 1,149 | matches exactly |
| Benguela (alternative) | 0–20°E | 38–15°S | 2,538,266 | 706 | matches exactly |
| Tighter Agulhas box (sensitivity) | 10–40°E | 45–25°S | 3,020,670 | 1,051 | — |

**Why this is enough.** Raw record counts overstate how much information the data contain, because the hourly product interpolates each deployment onto a full hourly grid and one drifter can stay in the same cell for hundreds of hours. We therefore count the number of *different* drifters that visit each cell, on the 2° grid recommended as a starting resolution for the transport analysis. The box has 18 × 13 = 234 cells; 178 contain data, and the 56 empty cells are almost all land (South Africa, Mozambique, southern Madagascar). The median occupied cell is visited by **116** different drifters (10th–90th percentile: 28–222), and 171 of the 178 cells have at least 10. Transition probabilities can therefore be estimated from many independent realisations across most of R; the 7 cells below this threshold will be merged with neighbouring cells.

**Why Agulhas rather than Benguela.** Benguela has 706 drifters against Agulhas's 1,149, a gap that matters more once adequacy is measured per cell rather than in total records. More importantly, the Agulhas retroflection splits material between two genuinely different outcomes — back east into the Indian Ocean or west into the Atlantic — so a transition matrix has a substantive question to answer. Benguela's alongshore/offshore contrast offers a narrower transport question. Shrinking the box to 10–40°E, 45–25°S would lose 98 drifters and most of the Mozambique Channel inflow described in Section 1.

**Endpoints versus censoring.** Each trajectory records why it ended (`typedeath`). Only code 1 (ran aground) is a genuine destination produced by the flow; codes 0 and 2–6 (still active at the release cut-off, picked up by a vessel, stopped transmitting, sporadic transmissions, battery failure, inactive) end the record for reasons unrelated to transport and will be treated as censored. Code 3 near the coast may hide an unrecorded grounding and will be checked separately.

---

## 3. Project definition



---

## 4. Method plan



---

## 5. Team and timeline

---

## References

- Beal, L. M., de Ruijter, W. P. M., Biastoch, A., Zahn, R., & SCOR/WCRP/IAPSO Working Group 136 (2011). On the role of the Agulhas system in ocean circulation and climate. *Nature*, 472(7344), 429–436.
- de Ruijter, W. P. M., Biastoch, A., Drijfhout, S. S., Lutjeharms, J. R. E., Matano, R. P., Pichevin, T., van Leeuwen, P. J., & Weijer, W. (1999). Indian–Atlantic interocean exchange: Dynamics, estimation and impact. *Journal of Geophysical Research: Oceans*, 104(C9), 20885–20910.
- Lutjeharms, J. R. E. (2006). *The Agulhas Current*. Springer, Berlin.
- Elipot, S., Lumpkin, R., Perez, R. C., Lilly, J. M., Early, J. J., & Sykulski, A. M. (2016). A global surface drifter data set at hourly resolution. *Journal of Geophysical Research: Oceans*, 121, 2937–2966. doi:10.1002/2016JC011716
- Elipot, S., Sykulski, A., Lumpkin, R., Centurioni, L., & Pazos, M. (2022). Hourly location, current velocity, and temperature collected from Global Drifter Program drifters world-wide [Data set, v2.01.1, NCEI accession 0248584, accessed 2026-09-23]. NOAA National Centers for Environmental Information. doi:10.25921/x46c-3620
- Elipot, S., Sykulski, A., Lumpkin, R., Centurioni, L., & Pazos, M. (2022). A dataset of hourly sea surface temperature from drifting buoys. *Scientific Data*, 9, 567. doi:10.1038/s41597-022-01670-2
- Xie, Y. (2026). *DATA3001 Week 1: A Worked Example — Preliminary regional results and a California Current illustration*. Course slides, UNSW Sydney.

---

## Supporting files (region data-adequacy check)

| File | Description |
|---|---|
| `region_adequacy_results.json` | Full statistics for every candidate box, including the EAC validation |
| `gdp_1deg_grids.npz` | 1° grids from the full hourly dataset: `obs_grid` (records per cell), `drifter_grid` (distinct drifters per cell), `pairs_cell`/`pairs_traj` (unique cell–trajectory pairs) |
| `region_adequacy_check.py` | Script that streamed lon/lat from the public Zarr store and produced the grids (run with Python 3 + numpy, requests, numcodecs) |

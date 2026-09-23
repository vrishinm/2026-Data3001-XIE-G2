# DATA3001 Term 3 2026 — Project 3.2.2: "Where things end up"

## A surface-transport operator for the Agulhas region

Project proposal / repository README (15%, 3 A4 pages + references).
Due Sunday Week 3 per the project brief

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

### **Table 1.** Hourly records and distinct drifters in the chosen region and one rejected alternative.

| Box | Longitude | Latitude | Hourly records | Distinct drifters |
|---|---|---|---|---|
| **chosen R (Agulhas)** | 10°E–45°E | 45°S–20°S | 3,848,969 | 1,149 |
| Benguela (rejected) | 0°–20°E | 38°S–15°S | 2,538,266 | 706 |

Both boxes use the boundaries given in the Week 1 illustration, and our pipeline reproduces
the published counts for each exactly, which validates the counting method.

**Why this is enough.** Adequacy is judged by independent drifters per cell, not by raw record count: the hourly product interpolates every deployment onto a full hourly grid, so raw records overstate the information content. In R the median 1° cell is visited by 77 independent drifters and 470 of 483 occupied cells are visited by at least 10; only one occupied cell has fewer than 20 hourly records. Cell-to-cell transition probabilities can therefore be estimated from many independent realisations rather than from a handful of long tracks.

**Why Agulhas over Benguela**

We compared both regions before committing. Benguela has 706 drifters against Agulhas's 1,149, and once we started thinking in terms of independent drifters per cell rather than raw records, that gap mattered more than it first looked. The bigger reason is what each region asks of a transition matrix. In Agulhas the retroflection splits material between two genuinely different outcomes, either back east into the Indian Ocean or west into the Atlantic, so the matrix has something interesting to estimate. Benguela's alongshore/offshore contrast felt like a thinner question to build a whole project around.

---

## 3. Project definition — TODO 



---

## 4. Method plan — TODO



---

## 5. Team and timeline — TODO

---

## References

- Beal, L. M., de Ruijter, W. P. M., Biastoch, A., Zahn, R., & SCOR/WCRP/IAPSO Working Group 136 (2011). On the role of the Agulhas system in ocean circulation and climate. *Nature*, 472(7344), 429–436.
- de Ruijter, W. P. M., Biastoch, A., Drijfhout, S. S., Lutjeharms, J. R. E., Matano, R. P., Pichevin, T., van Leeuwen, P. J., & Weijer, W. (1999). Indian–Atlantic interocean exchange: Dynamics, estimation and impact. *Journal of Geophysical Research: Oceans*, 104(C9), 20885–20910.
- Lutjeharms, J. R. E. (2006). *The Agulhas Current*. Springer, Berlin.
- Elipot, S., Lumpkin, R., Perez, R. C., Lilly, J. M., Early, J. J., & Sykulski, A. M. (2016). A global surface drifter data set at hourly resolution. *Journal of Geophysical Research: Oceans*, 121, 2937–2966. doi:10.1002/2016JC011716
- Elipot, S., Sykulski, A., Lumpkin, R., Centurioni, L., & Pazos, M. (2022). Hourly location, current velocity, and temperature collected from Global Drifter Program drifters world-wide [Data set, v2.01.1, accessed 2026-09-22]. NOAA National Centers for Environmental Information. doi:10.25921/x46c-3620
- Elipot, S., Sykulski, A., Lumpkin, R., Centurioni, L., & Pazos, M. (2022). A dataset of hourly sea surface temperature from drifting buoys. *Scientific Data*, 9, 567. doi:10.1038/s41597-022-01670-2

---

## Supporting files (region data-adequacy check)

| File | Description |
|---|---|
| `region_adequacy_results.json` | Full statistics for every candidate box, including the EAC validation |
| `gdp_1deg_grids.npz` | 1° grids from the full hourly dataset: `obs_grid` (records per cell), `drifter_grid` (distinct drifters per cell), `pairs_cell`/`pairs_traj` (unique cell–trajectory pairs) |
| `region_adequacy_check.py` | Script that streamed lon/lat from the public Zarr store and produced the grids (run with Python 3 + numpy, requests, numcodecs) |

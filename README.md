# 2026-DATA3001-Yiyuan Xie-Group2

---

## Research questions and objectives

**Region R.** R is the Agulhas Current system, defined as the box
> **R = [10°E, 45°E] × [45°S, 20°S].**

The box covers the current along the South African east coast, the retroflection south of Africa, and the exits both west into the Atlantic and east into the Indian Ocean.

**Project.**"Where things end up" (Project 3.2.2 (Transport)): a surface-transport operator for R.

**Aim.** When something is lost at sea, such as a person in a life raft, an oil slick or floating debris, responders need to know where it is likely to drift. We will build a transition matrix that estimates where surface drifters starting anywhere in R are found after a week, a month and a year, and where they eventually leave the region. The product describes the movement of near-surface water as sampled by drogued drifters; applying it to particular floating objects would need extra assumptions about wind and waves.

**Primary question.** How do starting locations in R affect westward versus eastward destinations? South of Africa the current turns back east, while some water enters the Atlantic.

- **RQ1: Where things end up.** Something goes into the water at a chosen point in R, such as a container off a ship, a life raft or a slick of oil. Where has the surface flow taken it a week later, a month later, and a year later? We answer this for three supported starting cells.
- **RQ2: Connectivity.** At the scale of the whole box, which parts of R feed which others, and which are cut off from the rest? Where does R as a whole gather material, and where does it lose it?
- **RQ3: Reliability.** How well do predicted destinations match observed destinations for held-out drifters? How sensitive are the results to the chosen interval, to drogue status and to season?

**Objectives.**

- **O1 Data.** Preserve drifter identity and timestamps, including the observations outside R that are needed to establish destinations. Count the usable endpoint pairs and the distinct drifters per starting cell. Separate observed exits from missing future observations.
- **O2 Transition matrix.** Estimate $P_{ij} = \Pr(X_{t+7\ \mathrm{days}} \in j \mid X_t \in i)$ from observed endpoint pairs on 2° cells, with an absorbing outside-region state that represents the first recorded exit. Combine poorly supported cells.
- **O3 Product.** Deliver a transition matrix that someone else can pick up and iterate forward, together with what it says about where the chosen release points end up, and about where R as a whole gathers material and where it loses it.
- **O4 Validation.** Split training and evaluation data by drifter, and compare predicted with observed destinations for the held-out drifters.
- **O5 Sensitivity.** Test how sensitive the results are to the chosen interval. Account for drogue status, because drifters that have lost their drogue have velocities contaminated by wind slip. Inspect seasonal coverage before pooling transitions.
- **O6 Region-independence.** Nothing in the code depends on the exact R, so all functions work when given a different region.

---

## 1. Region and motivation

**Region R.** R is the greater Agulhas Current system, defined as the box

> **R = 10°E–45°E, 20°S–45°S** (35° × 25°; 178 of 234 occupied 2° cells)

The box was selected against the data-adequacy comparison in Section 2: it holds 3.85 million hourly records from 1,149 independent drifters, and most 1° cells are visited by many independent drifters.

**Why this region matters.** The Agulhas Current is one of the strongest western boundary currents in the Southern Hemisphere; it carries warm, saline Indian Ocean water southwest along the South African coast before retroflecting south of the continent and returning east as the Agulhas Return Current (Lutjeharms, 2006). Rings shed at the retroflection export Indian Ocean water into the South Atlantic — "Agulhas leakage" — a process implicated in the Atlantic overturning circulation and in past climate change (de Ruijter et al., 1999; Beal et al., 2011). The system also supports major regional fisheries, and it underlies search-and-rescue, debris- and spill-response planning along one of the world's busiest shipping routes: in each case the operative question is where the surface water — and anything floating in it — goes. R is also among the best-sampled regions of the Global Drifter Program, which makes a data-driven transport operator feasible here.

**Multiple flow regimes.** R is expected to contain several distinct regimes — the Mozambique Channel inflow in the north-east, the narrow Agulhas core jet along the coast, the retroflection and ring-shedding corridor in the south-west, and the eastward return current — so material transport within R is likely to be strongly asymmetric and directional rather than diffusive.

---

## 2. Data availability

### **Table 1.** Hourly records and distinct drifters in the chosen region and one rejected alternative.

| Box | Longitude | Latitude | Hourly records | Distinct drifters |
|---|---|---|---|---|
| **chosen R (Agulhas)** | 10°E–45°E | 45°S–20°S | 3,848,969 | 1,149 |
| Benguela (rejected) | 0°–20°E | 38°S–15°S | 2,538,266 | 706 |

Both boxes use the boundaries given in the Week 1 illustration. Counts are from the NOAA Global Drifter Program hourly dataset v2.01.1 (Elipot et al., 2022; see References). The course pipeline (clouddrift `gdp1h()`) produced Table 1; an independent direct-Zarr stream of the same data reproduces every drifter and per-cell statistic (record counts differ by at most two at the box edges), which validates the counting method. Our count for the worked-example East Australian Current box similarly reproduces the lecturer's published 452 drifters.

**Why this is enough.** Adequacy is judged by independent drifters per cell, not by raw record count: the hourly product interpolates every deployment onto a full hourly grid, so raw records overstate the information content. On the 2° grid used by the transport model, the median cell in R is visited by 116 different drifters (interquartile range 76–168), and 171 of the 178 occupied cells are visited by at least 10. Cell-to-cell transition probabilities can therefore be estimated from many independent realisations rather than from a handful of long tracks.

**Why Agulhas over Benguela**

We compared both regions before committing. Benguela has 706 drifters against Agulhas's 1,149, and once we started thinking in terms of independent drifters per cell rather than raw records, that gap mattered more than it first looked. The bigger reason is what each region asks of a transition matrix. In Agulhas the retroflection splits material between two genuinely different outcomes, either back east into the Indian Ocean or west into the Atlantic, so the matrix has something interesting to estimate. Benguela's alongshore/offshore contrast felt like a thinner question to build a whole project around.

---

## 3. Project definition — draft starters

- **Transport question:** estimate the 7-day transition probabilities `P_ij = Pr(X_{t+7 days} ∈ cell j | X_t ∈ cell i)` on a 2° grid over R, with 7 / 30 / 365-day horizons.
- **Product:** a surface-transport operator (transition matrix) that can be iterated forward, plus where chosen release points end up and where R gathers/loses material.
- **States and boundaries (typedeath):** include an absorbing outside-region state; beachings (`typedeath = 1`) are true endpoints, while all other terminations (drogue loss, battery/signal loss) are censored observations, not arrivals.
- **Planned extensions:** seasonal split; sensitivity to grid resolution and horizon; drogued vs undrogued.

---

## 4. Method plan — draft starters

- Build starting cells and pair every hourly position with its position 7 days later (positions from clouddrift `gdp1h()`; gaps and interpolation uncertainty flagged).
- Absorbing state handling: censored tracks are removed from destination counts rather than treated as arrivals; beachings count as exits.
- Validation: train/test split by drifter (never by observation), compare predicted vs actual destination distributions on held-out drifters.
- Caveats: outside-region absorbing state; missing observations vs genuine exits; uneven sampling across cells.

---

## 5. Team and timeline

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
| `region_adequacy_results.json` | Full statistics for the chosen box, the rejected alternates, the Benguela comparison, and the EAC validation |
| `gdp_1deg_grids.npz` | Global 1° grids from the full hourly dataset: `obs_grid` (records per cell), `drifter_grid` (distinct drifters per cell), `pairs_cell`/`pairs_traj` (unique cell–trajectory pairs) |
| `region_adequacy_check.py` | Script that streamed lon/lat from the public Zarr store, built the grids, and computed the 2° summary statistics (run with Python 3 + numpy, requests, numcodecs) |

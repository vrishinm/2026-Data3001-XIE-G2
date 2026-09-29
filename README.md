# 2026-DATA3001-Yiyuan Xie-Group2

---

## 1. Research questions and objectives

**Project.** "Where things end up" (Project 3.2.2 (Transport)): a surface-transport operator for the Agulhas Current region R, defined in Section 2.

**Aim.** When something is lost at sea, such as a person in a life raft, an oil slick or floating debris, responders need to know where it is likely to drift. We will build a transition matrix that estimates where surface drifters starting anywhere in R are found after a week, a month and a year, and where they eventually leave the region. It is estimated from all drifters, drogued and undrogued, so it describes near-surface drift including some wind effect; results from drogued drifters alone are reported for comparison (Section 2). Applying it to particular floating objects would still need extra assumptions about wind and waves.

**Primary question.** How do starting locations in R affect westward versus eastward destinations? South of Africa the current turns back east, while some water enters the Atlantic.

- **RQ1: Where things end up.** Something goes into the water at a chosen point in R, such as a container off a ship, a life raft or a slick of oil. Where has the surface flow taken it a week later, a month later, and a year later? We answer this for three supported starting cells.
- **RQ2: Connectivity.** At the scale of the whole box, which parts of R feed which others, and which are cut off from the rest? Where does R as a whole gather material, and where does it lose it?
- **RQ3: Reliability.** How well do predicted destinations match observed destinations for held-out drifters? How sensitive are the results to the chosen interval, to drogue status and to season?

**Objectives.**

- **1. Data.** Preserve drifter identity and timestamps, including the observations outside R that are needed to establish destinations. Count the usable endpoint pairs and the distinct drifters per starting cell. Separate observed exits from missing future observations.
- **2. Transition matrix.** Estimate $P_{ij} = \Pr(X_{t+7\ \mathrm{days}} \in j \mid X_t \in i)$ from observed endpoint pairs on 2° cells, with an absorbing outside-region state that represents the first recorded exit. Combine poorly supported cells.
- **3. Product.** Deliver a transition matrix that someone else can pick up and iterate forward, together with what it says about where the chosen release points end up, and about where R as a whole gathers material and where it loses it.
- **4. Validation.** Split training and evaluation data by drifter, and compare predicted with observed destinations for the held-out drifters.
- **5. Sensitivity.** Test how sensitive the results are to the chosen interval. Account for drogue status, because drifters that have lost their drogue have velocities contaminated by wind slip. Inspect seasonal coverage before pooling transitions.
- **6. Region-independence.** Nothing in the code depends on the exact R, so all functions work when given a different region.

---

## Data/region and data description

**Region.** R is the Agulhas Current system, defined as the box

> **R = [10°E, 45°E] × [45°S, 20°S]**

The box covers the current along the South African east coast, the retroflection south of Africa, and the exits both west into the Atlantic and east into the Indian Ocean. Extending the box west to 10°E keeps both outcomes, westward into the Atlantic and eastward back into the Indian Ocean, inside R.

**Data.** We use the NOAA Global Drifter Program hourly product, version 2.01.1 (Elipot et al., 2016; 2022; doi:10.25921/x46c-3620), accessed through CloudDrift (`gdp1h()`). The hourly product runs from October 1987 to October 2022, but drifter records inside R begin on 31 March 1995. Irregular satellite fixes are mapped onto a uniform one-hour grid, which gives position, eastward and northward velocity, and an uncertainty for every estimate. Trajectory metadata and `rowsize` identify which observations belong to each drifter.

**Variables used.** Drifter identity and time; longitude and latitude, to assign cells and build 7-day endpoint pairs; drogue-loss date, to separate drogued from undrogued records; and type of death (`typedeath`), to separate drifters that ran aground, which is a true endpoint, from records that end for other reasons, which are censored.

### **Table 1.** Hourly records and distinct drifters in the chosen region and one rejected alternative.

| Box | Longitude | Latitude | Hourly records | Distinct drifters |
|---|---|---|---|---|
| **chosen R (Agulhas)** | 10°E–45°E | 45°S–20°S | 3,848,969 | 1,149 |
| Benguela (rejected) | 0°–20°E | 38°S–15°S | 2,538,266 | 706 |

Both boxes use the boundaries given in the Week 1 illustration. Counts are from the NOAA Global Drifter Program hourly dataset v2.01.1 (Elipot et al., 2022; see References). The course pipeline (clouddrift `gdp1h()`) produced Table 1; an independent direct-Zarr stream of the same data reproduces every drifter and per-cell statistic (record counts differ by at most two at the box edges), which validates the counting method. Our count for the worked-example East Australian Current box similarly reproduces the lecturer's published 452 drifters.

**Coverage.** Repeated records within a trajectory are not independent samples, so we count distinct drifters per cell rather than records (Figure 1). On a 1° grid, 649 of the 875 cells in R contain records, and nearly all the empty cells are land. The median occupied cell is visited by 71 distinct drifters (10th–90th percentile 24–138), and 614 cells are visited by at least 10; the 35 thinner cells lie along the Namibian and Mozambican coasts. Coverage grows over time (Figure 2): a median of 7 drifters per year were in R in 1995–1999, 62 in 2000–2009 and 83 in 2010–2022, so estimates mainly reflect the last two decades. The four austral seasons are evenly sampled (676–735 drifters each), and 533–560 cells per season are still visited by at least 10 drifters.

**Data issues.**

- *Drogue loss.* A drifter that loses its drogue has its velocity contaminated by wind slip, so it reads systematically faster. Only 33.3% of the records in R are drogued; two independent drogue flags in the dataset agree on 99.9% of records, and drogues typically last about six months (median 173 days). Restricted to drogued records, the median cell falls to 22 drifters and 94 cells drop below 10, mostly along the Agulhas Current core off the east coast (Figure 3). We therefore estimate the main operator from all drifters and repeat it with drogued drifters only as a sensitivity check.
- *How records end.* Only `typedeath = 1` (ran aground) is a real endpoint. The other endings, such as transmitter failure, pick-up by a vessel or bad batteries, are censored and are not treated as arrivals.
- *Uneven sampling.* Drifters gather where surface water converges and are swept out of where it diverges, so coverage is uneven across R.
- *Usable pairs.* Taking one start per drifter per day (00:00 UTC), R yields 153,746 usable 7-day endpoint pairs from 1,121 drifters; 6.1% of them end outside R. A further 2,173 daily starts are censored because the record stops within 7 days, and 4,581 are dropped because of gaps in the hourly record.

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

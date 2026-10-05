# Where things end up in the Agulhas: a drifter-based transport matrix

**DATA3001 Term 3 2026 · Group 2 · Project proposal**

**Project.** "Where things end up" (GDP Overview, Project 3.2.2): a surface-transport operator for the Agulhas Current region.
**Code.** `Proposal_code.ipynb` reproduces every number and figure in this proposal from the raw data, top to bottom.

---

## 1. Research questions and objectives

**Aim.** If a life raft, an oil slick or floating debris goes into the water off South Africa, responders need a quick answer about where it is likely to drift. We want to build a transition matrix from past drifter tracks that gives this answer for any starting point in R, and that others can reuse and iterate forward.

**Primary question.** How does the starting location in R decide whether material heads west into the Atlantic or turns back east into the Indian Ocean? We chose this because the retroflection splits the flow into two very different outcomes, and a transition matrix should be able to show where that split happens.

- **RQ1.** For three well-supported starting cells, chosen on different sides of where the current turns back, where are drifters found after 7 and 28 days, and what share has left R to the west (towards the Atlantic) versus the east within 7, 28 and 364 days (1, 4 and 52 weekly steps)?
- **RQ2.** Which parts of R feed which others, which are cut off from the rest, and where does R gather or lose material? In particular, which starting cells send most of their drifters out to the west, and which send them east?
- **RQ3.** How well does the matrix predict held-out drifters, and how sensitive is it to the time step, drogue status and season?

We kept the questions narrow on purpose. RQ1 is the concrete "drop something here" answer, RQ2 zooms out to the whole box, and RQ3 is there so we can say how much the first two should be trusted.

**Objectives.**
1. Build 7-day pairs, keeping each drifter's identity, timestamps and positions outside R, so that leaving the box counts as an outcome rather than as missing data.
2. Count usable pairs and distinct drifters for each starting cell, and merge poorly supported cells with a neighbour before trying anything more complicated.
3. Separate real exits from records that simply stop. A drifter's first recorded exit ends the pair in an absorbing outside state, and we check the hourly records in between, since a drifter can leave and come back within the 7 days.
4. Estimate $P_{ij}=\Pr(X_{t+7\,\text{days}} \in j \mid X_t \in i)$ on 2° cells, which are coarser than our 1° data summary, so each row rests on enough drifters.
5. Get the 28- and 364-day answers by applying P repeatedly ($P^4$, $P^{52}$) instead of relying on the few tracks that stay in R for a whole year. This assumes the next week depends only on where a drifter is now, which we test in RQ3.
6. Look at seasonal coverage before pooling all transitions into one matrix.
7. Hold out whole drifters, not single records, since records from the same drifter are strongly linked.
8. Save P and the code so that someone else can load the matrix and rerun it for a different region. Nothing in the code depends on the exact box.

**What counts as success.** (a) Every row of P rests on at least 10 distinct drifters; (b) on held-out drifters, P's top three cells catch the true 7-day destination clearly more often than the "stays put" baseline; (c) started near 31°E, 32°S, our matrix gives an Atlantic share in the same range as McAdam and van Sebille (2018). If (c) fails, we would rather explain why than tune the matrix until it matches.

## 2. Region and data

**Region.** R = [10°E, 45°E] × [45°S, 20°S], with points on the boundary counted as inside. The box follows the Agulhas Current down the east coast of South Africa, through the retroflection, and out towards both oceans. We pushed the western edge out to 10°E on purpose. If the box stopped at the tip of Africa, drifters heading into the Atlantic would leave almost straight away, and we couldn't compare the two outcomes we care about.

Before committing we ran the same counting on four boxes (Table 1). Benguela has far fewer drifters, and when we looked at it per cell rather than in total, its 25th percentile is only 29 drifters per cell against 76 for Agulhas. The two tighter Agulhas boxes actually have slightly better support per cell, but the "source only" box cuts off the retroflection, and the tighter box loses the northern source region, which is where our upstream starting cell would sit. So we accepted a few thinner edge cells in exchange for keeping the whole system in one box.

**Table 1.** The same counts applied to every candidate box (2° cells).

| Box | Longitude | Latitude | Hourly records | Distinct drifters | Occupied cells | Cells with ≥10 drifters | Median drifters/cell (25th pct) |
|---|---|---|---|---|---|---|---|
| **Chosen R (Agulhas)** | 10°E–45°E | 45°S–20°S | 3,848,969 | 1,149 | 178 / 234 | 171 | 116 (76) |
| Benguela (rejected) | 0°–20°E | 38°S–15°S | 2,538,266 | 706 | 97 / 120 | 84 | 118 (29) |
| Tighter Agulhas | 10°E–40°E | 45°S–25°S | 3,020,671 | 1,051 | 125 / 150 | 123 | 137 (101) |
| Source region only | 20°E–45°E | 40°S–20°S | 1,827,496 | 628 | 92 / 130 | 90 | 98 (70) |

**Data.** We use the NOAA Global Drifter Program hourly product v2.01.1 (Elipot et al., 2016; 2022), accessed through CloudDrift `gdp1h()` on 22/09/26. Each drifter follows the water at 15 m through its drogue and gives an hourly position, velocity and sea-surface temperature, each with an uncertainty. For a transition matrix we only need `lon`, `lat`, `time` and `rowsize` (to know which rows belong to which drifter), plus `drogue_lost_date` and `typedeath` per drifter.

A few things we checked before trusting any count:

- **Pipeline check.** Our code reproduces the 452 drifters in the Week 1 East Australian Current example and the 3,848,969 Agulhas records in the Week 1 table, so our filtering matches the course's.
- **Data audit.** No missing or out-of-range coordinates and no duplicate timestamps, but 0.04% of time steps are not exactly one hour. That is why we match pairs by elapsed time rather than assuming 168 rows means 7 days.
- **Record length.** Although the product starts in 1987, the first record inside R is from 31 March 1995, so we really have about 27 years of data (1995–2022).
- **Counting drifters, not records.** One slow drifter can fill a cell with hundreds of near-identical hourly records, so raw counts overstate how much information we have. Counting distinct drifters instead, 171 of the 178 occupied 2° cells are visited by at least 10 (median 116), so most rows of the matrix rest on many separate tracks, not one or two.

## 3. Why this problem matters

We picked this project because of a simple question: when something goes into the sea, the first thing anyone wants to know is where it will end up. That question sits behind search and rescue, oil spill response and tracking plastic. What makes it hard in the Agulhas is that the current is fast and full of eddies. Looking at the global drifter record, western boundary currents like this one have some of the highest eddy energy anywhere (Lumpkin & Johnson, 2013). So we don't think a single "best guess" path is very useful here. A small shift in where something starts could send it somewhere completely different, which is why we want a spread of possible destinations instead.

The west-versus-east split is the part we find most interesting. South of Africa most of the current turns back east, but some water carries on into the Atlantic, so this is a place where two oceans swap surface water. Drifters are useful here because they follow the flow itself rather than inferring it from sea-surface height like satellites do, and they are already used to check ocean forecasting systems (Centurioni et al., 2019). We also know their limits: oil and debris don't move exactly like water (Centurioni et al., 2019), so our results are a starting point, not a forecast for a real spill.

## 4. Background and existing studies

The Agulhas runs south-west along the South African coast at mean speeds of 60–150 cm/s (Lumpkin & Johnson, 2013), then turns back on itself south of Africa. Studies do not agree on exactly where this happens. Drifter averages put the turn at 20–23°E (Lumpkin & Johnson, 2013), while 26 years of satellite data place it at 15–20°E and show it moving, with early turns more common in spring and summer (Russo et al., 2021). To us this means the split is not fixed, which is why we check seasons.

Our question has partly been asked before. McAdam and van Sebille (2018) built transition matrices from GDP drifters and released tracer at one point in the Agulhas Current (31°E, 32°S). They found that 18–25% leaked into the Atlantic and 55–61% entered the Return Current. They also warned that putting trajectories on a grid creates "artificial dispersion", which grows with larger cells and shorter time steps, so results shift with the time step chosen. Miron et al. (2017) used the same drifter-based idea to map which parts of the Gulf of Mexico are connected, which shows the method can say something about a whole region, not just one release point.

We see three things we can add:
1. They released tracer from a single point, whereas we want to know how the Atlantic share changes with the starting cell, which is our primary question.
2. They used the older 6-hourly data with steps of 5–180 days. We use the hourly product with a 7-day step, and their warning about artificial dispersion is exactly why RQ3 tests the step length.
3. We check predictions against drifters held out of the matrix. Their 18–25% also gives us a sanity check: our matrix, started near 31°E, 32°S, should land somewhere close.

## 5. Proposed method

We work in Python on Google Colab, using CloudDrift to load the data and GitHub to share code.

**Building the pairs.** For every drifter that enters R, we take its 00:00 UTC position on each day it is inside R and find where it is 7 days later. One origin per day, not per hour, because neighbouring hours are near-duplicates. We use the drifter's whole track, including the parts outside R, otherwise we couldn't see it leave.

- If it leaves R at any hour in those 7 days, the pair ends in an absorbing outside state, labelled by the side of R it first crossed (west, east, south or north). We check every hourly position in between, not just day 7, and this turned out to matter: 1,448 of the 11,246 exits (12.9%) were back inside R by day 7, so looking only at the endpoint would have counted them as staying.
- If its record ends inside R before day 7, we currently drop the pair, since we don't know where it went (6,361 pairs). The next step is to split out drifters that ran aground (`typedeath` = 1) into their own "grounded" state, because grounding is a real outcome of the flow, the same as oil washing up on a beach. This matters more than we expected: 190 of our 1,149 drifters ran aground, 70 of them inside R.
- So far this gives 154,139 usable pairs. We use all drifters, drogued or not, as McAdam and van Sebille (2018) also did, and keep a drogue flag for RQ3.

**The matrix.** We count the pairs between 2° cells and divide each row by its total, so each row adds to 1. 171 of the 177 starting cells already have at least 10 distinct drifters, and the other 6 are merged with a neighbour so no row rests on one or two tracks.

**Answering the RQs.**
- *RQ1.* We apply $P$, $P^4$ (28 days, our "month") and $P^{52}$ (a year) to a starting vector that puts all material in one cell. Because the outside states are absorbing, the 364-day answer should be read as "what share has left R through each side within a year", not where it physically is after a year. We think that is the more honest way to state it, since once a drifter leaves R the matrix knows nothing about it.
- *RQ2.* We read off P which cells send material to which, and which cells are rarely reached from anywhere else. To see where R gathers material, we spread material evenly over R, apply P repeatedly, and look at where it piles up and which cells empty fastest. For the primary question we map, for every starting cell, the share that eventually leaves west versus east.
- *RQ3.* See below.

**Checking (RQ3).**
- We hold out 20% of drifters as whole tracks. For their 7-day moves, we record how often the true cell is among P's three most likely cells, and compare this with guessing that the drifter stays put.
- We compare $P^4$ against directly observed 28-day pairs. If they disagree a lot, the "next week only depends on where you are now" assumption is not holding, and our year-long answer from $P^{52}$ needs a stronger caveat.
- We rebuild P with drogued drifters only, with a 3-day step, and by season. McAdam and van Sebille (2018) showed that gridding adds artificial spread that depends on cell size and time step, so if our answers change a lot between versions, we will report that rather than pick the most convenient one.

## 6. Initial analysis and visualisation

Everything here comes from `Proposal_code.ipynb`. Our main takeaway is that the data can support the matrix overall, but drogue status and the sparse late-1990s are the two places where we have to be careful.

**Spatial coverage.** Figure 1 shows distinct drifters per 1° cell. 614 of the 649 occupied cells have at least 10 drifters (median 71). The thin cells are mostly at the far south-west corner and right against the coast, which are also where we expect to merge cells.

<img width="700" height="551" alt="download (1)" src="https://github.com/user-attachments/assets/867b32f4-f4e6-4626-b74c-1ea8ec5ffd68" />
*Figure 1. Distinct drifters per 1° cell in R, 1995–2022. Crosses mark cells with fewer than 10 drifters; white ocean cells have no records.*

**Coverage over time and season.** Every year from 1995 to 2022 has at least one drifter in R, but the early years are very thin: a median of 7 drifters per year in 1995–1999, against 62 in 2000–2009 and 83 in 2010–2022 (Figure 2). In practice our matrix mostly describes the 2000s onwards, which is fine for a transport question but means we shouldn't use it to say anything about change over time. Seasons are much more even (Table 2), so splitting by season in RQ3 looks feasible.

<img width="684" height="301" alt="download (2)" src="https://github.com/user-attachments/assets/1dad5d05-3649-475a-96bd-33ea248e1791" />
*Figure 2. Distinct drifters in R per year.*

**Table 2.** Coverage by austral season (1° cells).

| Season | Hourly records | Distinct drifters | Occupied cells | Median drifters/cell | Cells with ≥10 drifters |
|---|---|---|---|---|---|
| DJF (summer) | 858,391 | 676 | 634 | 18 | 533 |
| MAM (autumn) | 1,012,587 | 704 | 639 | 21 | 543 |
| JJA (winter) | 1,047,302 | 735 | 637 | 21 | 560 |
| SON (spring) | 930,689 | 714 | 640 | 19 | 554 |

**Drogue status.** Only 33.3% of records in R come from drogued drifters (we checked this two ways, using `drogue_lost_date` and the per-record `drogue_status` flag, and they agree 99.9% of the time). With drogued drifters only, the median per 1° cell drops from 71 to 22, and 94 cells that were well supported fall below 10 (Figure 3). This is why we use all drifters for the main matrix and treat the drogued-only version as a check on 2° cells, rather than the other way round. Undrogued drifters are pushed faster by the wind, so if the two versions disagree, we will learn something about how much wind slip affects the west/east split.

<img width="700" height="551" alt="download (3)" src="https://github.com/user-attachments/assets/8a74825c-d758-4ac9-8aaf-900aac8ea19c" />
*Figure 3. Distinct drogued drifters per 1° cell in R, same colour bins as Figure 1.*

**How drifters end.** Table 3 shows most drifters (840, 73.1%) leave R before their record ends, which is exactly what the outside states are for. The 203 drifters that "stop transmitting" inside R worry us a little: near the coast, some of them may really have run aground without being recorded as such.

**Table 3.** How the 1,149 drifters that enter R end.

| `typedeath` | Meaning | How we treat it | Drifters | Record ends inside R |
|---|---|---|---|---|
| 0 | still alive | censored | 61 | 22 |
| 1 | ran aground | real endpoint | 190 | 70 |
| 2 | picked up by vessel | censored | 27 | 12 |
| 3 | stop transmitting | censored | 857 | 203 |
| 5 | bad batteries | censored | 1 | 0 |
| 6 | inactive status | censored | 13 | 2 |
| | **Total** | | **1,149** | **309** |

**First look at the 7-day pairs.** Of 154,139 pairs, 92.7% stay inside R after 7 days. Of the 11,246 that leave, 32.0% leave west, 47.5% east, 15.9% south and 4.7% north. So even at one week, more material leaves towards the Indian Ocean than the Atlantic, which fits the idea that most of the current turns back. We are careful not to read the 32% as "Agulhas leakage" yet: this is pooled over every starting cell, and some of the western exits are probably drifters already in the Benguela flow off the west coast. Separating those by starting cell is exactly what the primary question is for.

## 7. Timeline and plan

Week 1 started on 14 September. Weeks 1–3 are done: region chosen, data loaded, audit and coverage checks finished, and the 7-day pairs built.

| Week (starting) | Task | Output |
|---|---|---|
| 1–3 (14 Sep) | Region choice, data access, audit, coverage, 7-day pairs | Done: Tables 1–3, Figures 1–3, `pairs7.csv` |
| 4 (5 Oct) | Proposal | This README (due 8 Oct) |
| 5 (12 Oct) | Add grounded state; merge the 6 thin cells; build P; 80/20 split by drifter | First version of P, row checks |
| 6 (19 Oct, flexibility week) | RQ1: three starting cells at 7, 28, 364 days; sanity check at 31°E, 32°S | RQ1 maps; comparison with McAdam and van Sebille (2018) |
| 7 (26 Oct) | RQ2: connectivity, where R gathers and loses material, west/east map by starting cell | RQ2 maps |
| 8 (2 Nov) | RQ3: top-3 hit rate vs "stays put"; $P^4$ vs direct 28-day pairs; drogued-only, 3-day and seasonal versions | Validation table and sensitivity figures |
| 9 (9 Nov) | Package P with a loader function; test on another box; draft report | Reusable product; report draft |
| 10 (16 Nov) | Final report and presentation | Submission (dates per Moodle) |

**Risks and fallbacks.** We tried to plan for what could go wrong, following the "fix the data before adding complexity" idea from Week 1.

| Risk | What we would see | Fallback |
|---|---|---|
| Some rows too thin, especially by season or drogued-only | Fewer than 10 drifters in a starting cell | Merge with a neighbour, or pool seasons into two halves of the year |
| The one-week memory assumption fails | $P^4$ disagrees with direct 28-day pairs | Report 28-day results from direct pairs, and keep $P^{52}$ as a rough guide only |
| Artificial dispersion from the grid | Answers shift a lot between 7-day and 3-day steps | Report the range across versions instead of one number |
| Data download drops mid-transfer | CloudDrift / S3 errors in Colab | Already handled with retries in the loader; results saved to `gdp_out/` so we don't reload |

This scope fits the remaining six weeks because the slowest part, building clean pairs, is already done, and P is just a counting step on top of it. The extra weeks go into checking, which is where we think most of the marks and most of the real learning are.

## References

- Centurioni, L. R., et al. (2019). Global in situ observations of essential climate and ocean variables at the air–sea interface. *Frontiers in Marine Science*, 6, 419.
- Elipot, S., Lumpkin, R., Perez, R. C., Lilly, J. M., Early, J. J., & Sykulski, A. M. (2016). A global surface drifter data set at hourly resolution. *Journal of Geophysical Research: Oceans*, 121, 2937–2966. doi:10.1002/2016JC011716
- Elipot, S., Sykulski, A., Lumpkin, R., Centurioni, L., & Pazos, M. (2022). Hourly location, current velocity, and temperature collected from Global Drifter Program drifters world-wide (v2.01.1). NOAA National Centers for Environmental Information. doi:10.25921/x46c-3620. Accessed 22/09/26.
- Lumpkin, R., & Johnson, G. C. (2013). Global ocean surface velocities from drifters: Mean, variance, El Niño–Southern Oscillation response, and seasonal cycle. *Journal of Geophysical Research: Oceans*, 118, 2992–3006.
- McAdam, R., & van Sebille, E. (2018). Surface connectivity and interocean exchanges from drifter-based transition matrices. *Journal of Geophysical Research: Oceans*, 123, 514–532. doi:10.1002/2017JC013363
- Miron, P., Beron-Vera, F. J., Olascoaga, M. J., Sheinbaum, J., Pérez-Brunius, P., & Froyland, G. (2017). Lagrangian dynamical geography of the Gulf of Mexico. *Scientific Reports*, 7, 7021.
- Russo, C. S., Lamont, T., & Krug, M. (2021). Spatial and temporal variability of the Agulhas Retroflection: Observations from a new objective detection method. *Remote Sensing of Environment*, 253, 112239.

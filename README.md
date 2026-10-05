# Proposal

---
## Research questions and objectives
**Project.** “Where things end up” (Project 3.2.2, Transport): a surface-transport operator for the Agulhas Current region R (Section 2).

**Aim.** If a life raft, an oil slick or floating debris goes into the water off South Africa, responders need a quick answer about where it is likely to drift. We want to build a transition matrix from past drifter tracks that gives this answer for any starting point in R, and that others can reuse and iterate forward.

**Primary question.** How does the starting location in R decide whether material heads west into the Atlantic or turns back east into the Indian Ocean? We chose this because the retroflection splits the flow into two very different outcomes, and a transition matrix should be able to show where that split happens.
- RQ1. For three well-supported starting cells, where are drifters found after 7, 30 and 364 days, i.e. 4 and 52 weekly steps?
- RQ2. Which parts of R feed which others, which are cut off from the rest, and where does R gather or lose material?
- RQ3. How well does the matrix predict held-out drifters, and how sensitive is it to the time interval, drogue status and season?

**Objectives.**
- Build 7-day pairs, keeping positions outside R so that leaving the box counts as an outcome rather than as missing data.
- Estimate $P_{ij}=Pr(X_{t+7 days} ∈ j | X_t ∈ i )$  on 2° cells, which are coarser than our 1° data summary, so each row rests on enough drifters.
- Get the 30- and 365-day answers by applying P repeatedly ($P^4, P^{52}$) instead of relying on the few tracks that stay in R for a whole year. This assumes the next week depends only on where a drifter is now, which we will test in RQ3.
- Hold out whole drifters, not single records, since records from the same drifter are strongly linked. We will count how often a drifter's actual 7-day position falls in the matrix's top three predicted cells, compare this with simply assuming it stays put, and repeat the analysis with drogued drifters only and with a 3-day interval.
- Save P and the code so that someone else can load the matrix and rerun it for a different region.

## Data/region and data description
**Region.** R = [10°E, 45°E] × [45°S, 20°S], with points on the boundary counted as inside. The box follows the Agulhas Current down the east coast of South Africa, through the retroflection, and out towards both oceans. We pushed the western edge out to 10°E on purpose. If the box stopped at the tip of Africa, drifters heading into the Atlantic would leave almost straight away, and we couldn't compare the two outcomes we care about.
We also looked at the Benguela box from Table 1. Agulhas has more drifters, but what decided it for us was the question: the retroflection gives the matrix two clearly different outcomes to estimate.

### **Table 1.** Hourly records and distinct drifters in the chosen region and one rejected alternative.

| Box | Longitude | Latitude | Hourly records | Distinct drifters |
|---|---|---|---|---|
| **chosen R (Agulhas)** | 10°E–45°E | 45°S–20°S | 3,848,969 | 1,149 |
| Benguela (rejected) | 0°–20°E | 38°S–15°S | 2,538,266 | 706 |

**Data.** We use the NOAA Global Drifter Program hourly product v2.01.1 (Elipot et al., 2016; 2022), accessed through CloudDrift on 22/09/26. One thing we didn't expect: although the product starts in 1987, the first record inside R is from March 1995, so we really have about 27 years of data. We checked the records before counting anything. Nothing was missing or duplicated, but 0.04% of time steps weren't exactly one hour, so we match pairs by time rather than assuming 168 rows means 7 days. Our pipeline also reproduces the 452 drifters in the Week 1 East Australian Current example. Since one slow drifter can fill a cell with hundreds of near-identical hourly records, we count distinct drifters instead: 171 of the 178 occupied 2° cells are visited by at least 10 (median 116), so most rows of the matrix rest on many separate tracks, not one or two.

## Why this problem is important
We picked this project because of a simple question: when something goes into the sea, the first thing anyone wants to know is where it will end up. That question sits behind search and rescue, oil spill response and tracking plastic. What makes it hard in the Agulhas is that the current is fast and full of eddies. Looking at the global drifter record, western boundary currents like this one have some of the highest eddy energy anywhere (Lumpkin & Johnson, 2013). So we don't think a single "best guess" path is very useful here. A small shift in where something starts could send it somewhere completely different, which is why we want a spread of possible destinations instead.

The west-versus-east split is the part we find most interesting. South of Africa most of the current turns back east, but some water carries on into the Atlantic, so this is a place where two oceans swap surface water. Drifters are useful here because they follow the flow itself, and they are already used to check ocean forecasting systems (Centurioni et al., 2019). We also know their limits: oil and debris don't move exactly like water (Centurioni et al., 2019), so our results are a starting point, not a forecast for a real spill.

## Background and existing studies
The Agulhas runs south-west along the South African coast at mean speeds of 60–150 cm/s (Lumpkin & Johnson, 2013), then turns back on itself south of Africa. Studies do not agree on exactly where this happens. Drifter averages put the turn at 20–23°E (Lumpkin & Johnson, 2013), while 26 years of satellite data place it at 15–20°E and show it moving, with early turns more common in spring and summer (Russo et al., 2021). To us this means the split is not fixed, which is why we check seasons.

Our question has partly been asked before. McAdam and van Sebille (2018) built transition matrices from GDP drifters and released tracer at one point in the Agulhas Current (31°E, 32°S). They found that 18–25% leaked into the Atlantic and 55–61% entered the Return Current. They also warned that putting trajectories on a grid creates "artificial dispersion", which grows with larger cells and shorter time steps, so results shift with the time step chosen.

We see three things we can add. First, they released tracer from a single point, whereas we want to know how the leakage share changes with the starting cell, which is our primary question. Second, they used the older 6-hourly data with steps of 5–180 days. We use the hourly product with a 7-day step, and their warning is exactly why RQ3 tests the interval. Third, we check predictions against drifters held out of the matrix. Their 18–25% also gives us a sanity check: our matrix, started near 31°E, 32°S, should land somewhere close.

## Proposed method
We will work in Python on Colab, using CloudDrift to load the data and GitHub to share code.

**Building the pairs.** For every drifter, we take its 00:00 UTC position on each day it is inside R and find where it is 7 days later. If it has left R, the pair ends in an absorbing outside state, labelled by the side of R it first crossed. We check every hourly position in between, not just day 7, and this turned out to matter: 1,448 of the 11,246 exits (12.9%) were back inside R by day 7, so looking only at the endpoint would have counted them as staying. If a drifter runs aground (typedeath = 1), the pair ends in a "grounded" state, which we need because 190 of our 1,149 drifters ran aground, 70 of them inside R. If a drifter simply stops transmitting, we drop the pair, since we don't know where it went. So far this gives 154,139 pairs. We use all drifters, drogued or not, as McAdam and van Sebille (2018) also did, and keep a drogue flag for later.

**The matrix.** We count the pairs between 2° cells and divide each row by its total, so each row adds to 1. 171 of the 177 starting cells already have at least 10 distinct drifters, and the other 6 are merged with a neighbour so no row rests on one or two tracks. This is the same drifter-based approach Miron et al. (2017) used to map connections in the Gulf of Mexico.

**Answering the RQs.** For RQ1 we apply $P, P^4$ (28 days, our "month") and $P^{52}$ (a year) to each starting cell. For RQ2 and our primary question, we split the outside state by the side of R it crosses (west, east, south or north), so we can see how much material leaves towards the Atlantic versus the Indian Ocean. We also read off P which cells send material to which, and which are rarely reached from anywhere else. To see where R gathers material, we spread material evenly over R, apply P repeatedly, and look at where it piles up and which cells empty fastest.

**Checking.** We hold out 20% of drifters as whole tracks. For their 7-day moves, we record how often the true cell is among P's three most likely cells, and compare this with guessing that the drifter stays put. We then rebuild P with drogued drifters only, with a 3-day step, and by season. McAdam and van Sebille (2018) showed that gridding adds artificial spread that depends on cell size and time step, so if our answers change a lot between versions, we will report that rather than pick the most convenient one.

## Reference
- Centurioni, L. R., et al. (2019). Global in situ observations of essential climate and ocean variables at the air–sea interface. Frontiers in Marine Science, 6, 419.
- Lumpkin, R., & Johnson, G. C. (2013). Global ocean surface velocities from drifters: Mean, variance, El Niño–Southern Oscillation response, and seasonal cycle. Journal of Geophysical Research: Oceans, 118, 2992–3006.
- Miron, P., Beron-Vera, F. J., Olascoaga, M. J., Sheinbaum, J., Pérez-Brunius, P., & Froyland, G. (2017). Lagrangian dynamical geography of the Gulf of Mexico. Scientific Reports, 7, 7021.
- Russo, C. S., Lamont, T., & Krug, M. (2021). Spatial and temporal variability of the Agulhas Retroflection: Observations from a new objective detection method. Remote Sensing of Environment, 253, 112239.

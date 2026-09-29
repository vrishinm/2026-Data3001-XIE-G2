# 2026-DATA3001-Yiyuan Xie-Group2

---
## Research questions and objectives
**Project.** “Where things end up” (Project 3.2.2, Transport): a surface-transport operator for the Agulhas Current region R (Section 2).

**Aim.** If a life raft, an oil slick or floating debris goes into the water off South Africa, responders need a quick answer about where it is likely to drift. We want to build a transition matrix from past drifter tracks that gives this answer for any starting point in R, and that others can reuse and iterate forward.

**Primary question.** How does the starting location in R decide whether material heads west into the Atlantic or turns back east into the Indian Ocean? We chose this because the retroflection splits the flow into two very different outcomes, and a transition matrix should be able to show where that split happens.
- RQ1. For three well-supported starting cells, where are drifters found after 7, 30 and 365 days?
- RQ2. Which parts of R feed which others, which are cut off from the rest, and where does R gather or lose material?
- RQ3. How well does the matrix predict held-out drifters, and how sensitive is it to the time interval, drogue status and season?

**Objectives.**
- Build 7-day endpoint pairs, keeping positions outside R so that leaving the box counts as an outcome rather than as missing data.
- Estimate $P_{ij}=Pr(X_{t+7 days} ∈ j | X_t ∈ i )$  on 2° cells, which are coarser than our 1° data summary, so each row rests on enough drifters.
- Get the 30- and 365-day answers by applying P repeatedly (P4, P52) instead of relying on the few tracks that stay in R for a whole year. This assumes the next week depends only on where a drifter is now, which we will test in RQ3.
- Hold out whole drifters, not single records, since records from the same drifter are strongly linked. We will count how often a drifter's actual 7-day position falls in the matrix's top three predicted cells, compare this with simply assuming it stays put, and repeat the analysis with drogued drifters only and with a 3-day interval.
- Save P and the code so that someone else can load the matrix and rerun it for a different region.

## Data/region and data description
**Region.** R = [10°E, 45°E] × [45°S, 20°S]. The box follows the Agulhas Current down the east coast of South Africa, through the retroflection, and out towards both oceans. We pushed the western edge out to 10°E on purpose. If the box stopped at the tip of Africa, drifters heading into the Atlantic would leave almost straight away, and we couldn't compare the two outcomes we care about.
We also looked at the Benguela box from Table . Agulhas has more drifters, but what decided it for us was the question: the retroflection gives the matrix two clearly different outcomes to estimate.
Table 1. Records and distinct drifters in the two candidate boxes.

### **Table 1.** Hourly records and distinct drifters in the chosen region and one rejected alternative.

| Box | Longitude | Latitude | Hourly records | Distinct drifters |
|---|---|---|---|---|
| **chosen R (Agulhas)** | 10°E–45°E | 45°S–20°S | 3,848,969 | 1,149 |
| Benguela (rejected) | 0°–20°E | 38°S–15°S | 2,538,266 | 706 |

**Data.** We use the NOAA Global Drifter Program hourly product v2.01.1 (Elipot et al., 2016; 2022), accessed through CloudDrift on [date]. One thing we didn't expect: although the product starts in 1987, the first record inside R is from March 1995, so we really have about 27 years of data. Because each drifter reports every hour, one slow drifter can fill a cell with hundreds of almost identical records. We therefore count distinct drifters rather than records.
Variables. Drifter ID, time, latitude, longitude, drogue-loss date and typedeath. That's all the matrix needs: where a drifter is now and where it is a week later.

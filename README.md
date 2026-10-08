# Where things end up in the Agulhas: a drifter-based transport matrix

**DATA3001 Term 3 2026 · Group 2 · Project proposal**

**Project.** "Where things end up" (Project 3.2.2): a surface-transport operator for the Agulhas Current region.
**Code.** `Proposal_code.ipynb` reproduces every number and figure in this proposal from the raw data, top to bottom.

---

## 1. Research questions and objectives

**Aim.** 
If a life raft, an oil slick or floating debris goes into the water off South Africa, responders need a quick answer about where it is likely to drift. We want to build a transition matrix from past drifter tracks that gives this answer for any starting point in R, and that someone else can pick up and iterate forward.

**Primary question.** 
How does the starting location in R decide whether material heads west into the Atlantic or turns back east into the Indian Ocean? We chose it because the retroflection splits the flow into two very different outcomes, and a transition matrix should be able to show where that split happens.

- **RQ1.**
    For three well-supported starting cells across the Agulhas Current and its retroflection, where are drifters likely to be within the region after 7 and 28 days, and what proportion are expected to have exited through the western (Atlantic) or eastern (Indian Ocean) boundary? How might these exit probabilities develop over longer periods, including 364 days, if the model is sufficiently validated?
- **RQ2.** 
      How are different areas within the R region connected by ocean currents, and which areas are more likely to accumulate or lose floating material? In particular, how does the starting location influence whether drifters exit the region through the western or eastern boundary?
- **RQ3.**
    How well does the matrix predict held-out drifters, and how sensitive are the results to the time step, drogue status, and season?

We kept the questions narrow on purpose. RQ1 focuses on the effect an object's location in R has on its movement, RQ2 considers the region as a whole, and RQ3 assesses how much the results from the first two questions can be trusted.

**Objectives.**
1. Build 7-day pairs while retaining each drifter's identity, timestamps, and positions outside R, so that leaving the box is treated as an outcome rather than as missing data.
2. Count usable pairs and distinct drifters for each starting cell, and merge poorly supported cells with a neighbouring cell before applying more complex methods.
3. Distinguish exits from records that simply stop. A drifter's first recorded exit ends the pair in an absorbing outside state. We check the hourly records between the starting point and day 7, since a drifter can leave R and come back within the 7 day period.
4. Estimate a seven-day transition matrix, $P_{ij} = \Pr(S_{t+7}=j \mid S_t=i)$, using 2° grid cells. Here, $S$ represents the drifter's location within the region until its first exit, after which it enters a permanent absorbing exit state (west, east, south or north). Therefore, the matrix estimates the probability of remaining within a particular cell without having previously exited, or of having first exited through a specified boundary within seven days, rather than simply recording the drifter's actual position at the end of the period.
5. Get the 28- and 364-day answers by applying P repeatedly ($P^4$, $P^{52}$) rather than relying on the small number of tracks that remain in R for a whole year. This assumes the next week's movement depends only on the drifter's current location, which we test in RQ3.
6. Examine seasonal coverage before pooling all transitions into one matrix.
7. Hold out complete drifter tracks rather than single records, since records from the same drifter are strongly linked.
8. Save P and the code so that someone else can apply the matrix and code to a different region. Nothing in the code depends on the exact region.

**What counts as success.** 
(a) Every row of P is supported by at least 10 distinct drifters; 
(b) on held-out drifters, the three most likely cells from P contains the true 7-day destination clearly more often than the "stays put" baseline **(I dont get this part, needs elaborating)**; 
(c) when starting near 31°E, 32°S, our matrix produces an Atlantic share in the same range as McAdam and van Sebille (2018). 

If (c) fails, we would rather explain why than adjust the matrix until it matches.

## 2. Region and data

**Region.** We chose Agulhas as our region (R = [10°E, 45°E] × [45°S, 20°S]), with points on the boundary counted as inside. We kept this region after testing alternatives because it follows the current down the east coast of South Africa and goes through a process called retroflection (where an ocean current bends back or reverses direction), and out towards both oceans. The western edge at 10°E is the most important part. If the region stopped at the tip of Africa, drifters heading into the Atlantic would leave almost immediately, making it difficult to compare the two outcomes we are interested in.

We ran the same counts on four regions (Table 1). Benguela has far fewer drifters, and when we considered per cell rather than in total, its 25th percentile is only 29 drifters per cell compared to the 76 drifters per cell for Agulhas. The two smaller Agulhas boxes actually has slightly better support per cell, but the "source only" box cuts off the retroflection, and the smaller box loses the northern source region, which is where our upstream starting cell would be located. Therefore, we accepted some thinner edge cells in exchange for keeping the whole system in one box. Since changing the boundary also changes the question being studied, we preferred to choose the region based on the research question rather than on which region had the best data coverage. **(NEED CLARIFICATION ON THIS)**

**Table 1.** The same counts applied to every candidate box (2° cells).

| Box | Longitude | Latitude | Hourly records | Distinct drifters | Occupied cells | Cells with ≥10 drifters | Median drifters/cell (25th pct) |
|---|---|---|---|---|---|---|---|
| **Chosen R (Agulhas)** | 10°E–45°E | 45°S–20°S | 3,848,969 | 1,149 | 178 / 234 | 171 | 116 (76) |
| Benguela | 0°–20°E | 38°S–15°S | 2,538,266 | 706 | 97 / 120 | 84 | 118 (29) |
| Tighter Agulhas | 10°E–40°E | 45°S–25°S | 3,020,671 | 1,051 | 125 / 150 | 123 | 137 (101) |
| Source region only | 20°E–45°E | 40°S–20°S | 1,827,496 | 628 | 92 / 130 | 90 | 98 (70) |

**Data.** We use the NOAA Global Drifter Program hourly product v2.01.1 (Elipot et al., 2016; 2022), accessed through CloudDrift `gdp1h()` on 22 September 2026. Each drifter follows the water at 15 m through its drogue, and the hourly product gives a position, velocity and sea-surface temperature on a regular one-hour grid, each with an uncertainty. For a transition matrix we only need `lon`, `lat`, `time` and `rowsize` (to know which rows belong to which drifter), plus `drogue_lost_date` and `typedeath` per drifter.

A few things we checked before trusting any count: 

- **Pipeline check.** To verify that our code correctly processes and filters the data, we compared our results with the course's examples. Our code identified the same 452 drifters in the East Australian Current region and 3,848,969 observations in the Agulhas region. This confirms that our data filtering produces results consistent with those provided in the course materials.
- **Data audit.** We checked the dataset for missing or invalid coordinates, duplicate timestamps and irregular time intervals. We found no missing or out-of-range coordinates or duplicate timestamps. However, approximately 0.04% of consecutive observations were not exactly one hour apart. To account for these irregularities, we use the actual time difference between observations when identifying seven-day transitions, rather than assuming that 168 consecutive observations always represent seven days.
- **Record length.** Although the Global Drifter Program dataset contains observations dating back to 1987, the earliest observation within our chosen Agulhas region was recorded on 31 March 1995. Therefore, our analysis covers approximately 27 years of regional data, from 1995 to 2022.
- **Counting drifters, not records.** Since each drifter records its position every hour, a single drifter can produce hundreds of observations within the same cell. These observations are closely related and should not be treated as independent data points. To avoid overestimating data coverage, we count the number of unique drifters passing through each cell rather than the total number of observations. Our analysis shows that 171 of the 178 occupied 2° cells contain observations from at least 10 distinct drifters, with a median of 116 drifters per cell. This indicates that most cells have sufficient coverage from multiple drifters to support our transition matrix analysis.

## 3. Why this problem matters
We chose this project because understanding where floating objects travel in the ocean is important for real world applications such as search and rescue, oil spill response and fisheries management. The Agulhas Current is worth obtaining information from due to its strong currents and large number of eddies, which create complex and unpredictable movement patterns. In fact, the retroflection process in the Agulhas is considered one of the most dense regions for ocean eddies, alongside the Gulf Stream and Kuroshio (Lumpkin & Johnson, 2013). As a result, predicting a single path may not accurately represent where floating material could travel. Instead, our project aims to estimate the probabilities of different destinations, providing a better understanding of the possible transport pathways.

One of the main reasons we selected the Agulhas region is the way the current splits near the southern coast of Africa. While most of the water turns back east towards the Indian Ocean, some currents continue west into the Atlantic Ocean. This makes the region particularly useful for investigating how the starting location of floating material influences its direction and destination. Drifter data is well suited to this analysis because drifters move with ocean currents, allowing us to observe how water travels over time. In comparison, satellites estimate ocean currents indirectly and may miss smaller-scale features below approximately 100 kilometres, which may change how the data perceives the eddies' influence on the direction of transport in the Agulhas region.

However, it is important to recognise the limitations of our analysis. The probabilities generated by our transition matrix represent the movement patterns observed in historical drifter data, rather than the actual volume of water transported between the two oceans. Additionally, objects such as oil and debris may be affected by wind and waves differently from drogued drifters, which are designed to follow ocean currents at a depth of approximately 15 metres. Therefore, our model aims to provide useful insights into likely transport pathways rather than precise predictions of real-world events.

## 4. Background and existing studies
The Agulhas Current flows southwest along the South African coast at average speeds of 0.6–1.5 m/s (Lumpkin & Johnson, 2013), before turning back east towards the Indian Ocean through the retroflection process. However, the exact location of this turning point varies between studies. Lumpkin and Johnson (2013) estimated that the current typically turns between 20°E and 23°E using drifter observations, while Russo et al. (2021) analysed 26 years of satellite data (1993–2018) and found that retroflection generally occurs between 15°E and 20°E. Their research also showed that the turning point changes over time, with earlier retroflections occurring more frequently during austral spring and summer. These findings suggest that ocean circulation in the Agulhas region varies seasonally, which is why our project will investigate the influence of seasons on transport patterns.

Previous research has explored similar questions using drifter data and transition matrices. McAdam and van Sebille (2018) developed transition matrices using Global Drifter Program data to investigate the movement of particles released from a location within the Agulhas Current (31°E, 32°S). Using a 60-day time step, they estimated that approximately 18–25% of the released tracer entered the Atlantic Ocean by crossing the Good Hope line, while 55–61% returned east through the retroflection. However, they also identified a limitation known as *artificial dispersion*, where dividing ocean trajectories into grid cells can introduce additional spreading that does not necessarily reflect the actual movement of water. This effect generally increases with larger grid cells and shorter time steps, potentially influencing the estimated transport probabilities. Similarly, Miron et al. (2017) used drifter-based transition matrices to investigate connectivity between different areas of the Gulf of Mexico, demonstrating how this approach can be applied to understand transport patterns across an entire region.

Although our project builds on these existing studies, we aim to extend their work in three main ways:

1. **Starting location and transport probabilities.** McAdam and van Sebille (2018) investigated the movement of tracer released from a single starting location. In comparison, our project will examine multiple starting cells across the Agulhas region to understand how starting location influences the probability of westward transport into the Atlantic Ocean or eastward transport towards the Indian Ocean.

2. **Higher temporal resolution.** McAdam and van Sebille (2018) used six-hourly drifter data with time steps of 5, 20, 60 and 180 days. Our project uses the newer hourly GDP dataset, which provides greater temporal detail and reduces the aliasing of tidal and inertial movements associated with six-hourly sampling. This allows us to identify drifters that temporarily leave the region and return within a seven-day period, rather than relying only on their final position. We will also investigate how different time steps influence our results, particularly given the effects of artificial dispersion identified in previous research.

3. **Model validation and reliability.** Our project will evaluate the transition matrix using drifters that were not included when estimating the model. By comparing predicted transport probabilities with observed outcomes, we aim to assess how reliably the matrix represents movement within the region. We will also compare our findings with McAdam and van Sebille (2018) to provide context for our estimated westward transport probabilities. However, a direct numerical comparison is not appropriate because our western exit boundary is defined at 10°E, whereas their study used the Good Hope line. Differences in grid resolution and time steps may also influence the results. Therefore, their findings will serve as a reference for interpretation rather than a specific target our model must achieve.

## 5. Proposed Method

We use Python in Google Colab and VS Code, with CloudDrift to access the dataset and GitHub for version control and collaboration.

**Building the pairs.** For each drifter entering our study region (R), we use its position at 00:00 UTC on each day it is within R as a starting point, then examine its movement over the following seven days. Using one starting point per day reduces the number of highly similar observations compared with hourly sampling. We retain each drifter's full trajectory, including positions outside R, to accurately identify when it leaves the region. We also use actual timestamps to identify seven-day intervals, rather than assuming that 168 consecutive observations always represent seven days.

- **First exits.** If a drifter leaves R within the seven-day period, we record its first observed exit according to the boundary crossed (west, east, south or north). This exit is treated as an absorbing state, meaning the drifter remains classified as having exited even if it later returns. Our preliminary analysis found that 1,448 of the 11,246 recorded exits (12.9%) had returned to R by day seven. This demonstrates why examining the full trajectory is important, as using only the final position would incorrectly classify these movements as remaining within the region.

- **Incomplete observations and grounding.** If a drifter's record ends before day seven, we retain any confirmed first exit that occurred before the record ended. However, if no exit is observed and the seven-day destination cannot be established, the pair is treated as incomplete and excluded from the transition estimates. We will also investigate grounding events using `typedeath = 1` and the recorded end time, assigning a separate grounded state only where grounding can be established within the relevant seven-day window. This is important because 190 of the 1,149 drifters entering R were recorded as grounded, including 70 whose records ended within the region.

- **Data selection.** Our preliminary analysis produced 154,139 usable seven-day pairs, although this number may change after refining the treatment of incomplete observations and grounding. We include both drogued and undrogued drifters, consistent with McAdam and van Sebille (2018), while retaining drogue status for the sensitivity analysis in RQ3.

**The matrix.** We divide the Agulhas region into 2° grid cells and include four additional exit states representing the western, eastern, southern and northern boundaries. For each drifter starting within the region, we examine its observed movement over the following seven days. If the drifter remains within the region throughout this period, its destination is the grid cell occupied at day seven. However, if it crosses the region's boundary at any point, we record the direction of its first exit, even if it subsequently returns. These exit states are treated as absorbing, meaning that once a drifter is classified as having exited, it remains in that state for all subsequent modelled transitions.

We construct the transition matrix $P$ by counting the observed transitions between starting cells and their outcomes, then dividing each count by the total number of usable transitions from that starting cell. Each row therefore sums to one and represents a probability distribution across possible outcomes. Importantly, $P$ describes movement within the region up to the first departure, followed by an absorbing exit state. It does not track the physical location of drifters after they leave the region. Our preliminary analysis identified 171 of 177 starting cells with at least 10 distinct drifters, and we plan to merge the remaining six cells with neighbouring cells to improve statistical support.

**Answering the Research Questions.**

- **RQ1.** We apply the seven-day transition matrix $P$ to three well-supported starting cells to estimate transport probabilities after 7, 28 and 364 days, using $P$, $P^4$ and $P^{52}$ respectively. As the exit states are absorbing, these projections represent the probability of remaining within specific cells or having first exited through a particular boundary. They do not describe a drifter's physical location after leaving R. Longer-term projections, particularly at 364 days, will be interpreted cautiously and depend on the model's validation results.

- **RQ2.** We use the transition matrix to investigate how different areas of R are connected and identify which cells are more likely to receive or lose floating material. To examine regional transport patterns, we begin with an equal amount of material in each grid cell and apply the matrix repeatedly to observe how it is redistributed. This approach reduces the influence of uneven drifter sampling, as some areas contain more observations due to the currents and deployment patterns. We also map the probability of westward and eastward exits for each starting cell to identify how transport pathways vary across the region.

- **RQ3.** We evaluate the matrix using held-out drifters and investigate how its results change with different time steps, grid resolutions, drogue status and seasons, as described below.

**Model Evaluation and Sensitivity Analysis (RQ3).**

- **Predictive performance.** We propose splitting the dataset into training (60%), validation (20%) and testing (20%) sets, keeping entire drifter trajectories within a single set to prevent data leakage. The training set will be used to construct the matrix, the validation set to select model settings, and the test set to assess final performance. We will use the multiclass Brier score to evaluate the accuracy of predicted destination and exit probabilities, alongside the top-three destination hit rate. Results will be compared against simple baseline models, including predicting that a drifter remains in its starting cell.

- **Longer-term reliability.** We compare the 28-day probabilities estimated by $P^4$ with directly observed 28-day outcomes, using the same first-exit classification rule. This allows us to assess whether repeatedly applying the seven-day matrix provides reasonable longer-term estimates. Substantial differences would suggest limitations in the model's assumptions, particularly its dependence on the current state alone, and would reduce our confidence in the 364-day projections.

- **Sensitivity analysis.** We investigate how the estimated transport probabilities change when using only drogued drifters, shorter three-day time steps, different grid resolutions and separate seasons. Previous research by McAdam and van Sebille (2018) showed that grid-based transition matrices can introduce artificial dispersion, particularly with larger cells and shorter time steps. Comparing these model variations will help us assess the robustness of our findings and identify any important limitations.

## 6. Initial Analysis and Visualisation

Our preliminary analysis, conducted using `Proposal_code.ipynb`, indicates that the Agulhas region has sufficient drifter coverage to support the proposed transition matrix. However, uneven temporal coverage and differences in drogue status may affect the reliability of our estimates. The figures use a single-hue blue colour scale for readability, while cells containing fewer than 10 distinct drifters are marked with crosses to highlight areas with limited data.

**Spatial coverage.** Figure 1 shows the number of distinct drifters passing through each 1° grid cell. Of the 649 occupied cells, 614 contain observations from at least 10 distinct drifters, with a median of 71 drifters per cell. Areas with lower coverage are mainly located along the Namibian and South African coastlines and near Madagascar, while the open ocean generally has stronger coverage. A particularly high concentration of drifter observations occurs around 38–41°S, following the Agulhas Return Current. This pattern may reflect the influence of strong ocean circulation on where drifters travel and are sampled. However, higher drifter density does not necessarily indicate that floating material accumulates in these areas, as the observations are influenced by both ocean dynamics and sampling patterns. **CHECKED AND CHANGED USING CHAT UNTIL HERE**

<img width="700" height="551" alt="download (1)" src="https://github.com/user-attachments/assets/867b32f4-f4e6-4626-b74c-1ea8ec5ffd68" />

**Coverage over time and season.** Every year from 1995 to 2022 has at least one drifter in R, but the early years are very thin: a median of 7 drifters per year in 1995–1999, against 62 in 2000–2009 and 83 in 2010–2022 (Figure 2). There is also a dip around 2012–2014. In practice our matrix mostly describes the 2000s onwards. That's fine for a transport question, but we shouldn't use it to say anything about change over time. Seasons are much more even (Table 2), so splitting by season in RQ3 looks feasible.

<img width="684" height="301" alt="download (2)" src="https://github.com/user-attachments/assets/1dad5d05-3649-475a-96bd-33ea248e1791" />

**Table 2.** Coverage by austral season (1° cells).

| Season | Hourly records | Distinct drifters | Occupied cells | Median drifters/cell | Cells with ≥10 drifters |
|---|---|---|---|---|---|
| DJF (summer) | 858,391 | 676 | 634 | 18 | 533 |
| MAM (autumn) | 1,012,587 | 704 | 639 | 21 | 543 |
| JJA (winter) | 1,047,302 | 735 | 637 | 21 | 560 |
| SON (spring) | 930,689 | 714 | 640 | 19 | 554 |

**Drogue status.** Only 33.3% of records in R come from drogued drifters. We checked this two ways, using `drogue_lost_date` and the per-record `drogue_status` flag, and they agree 99.9% of the time. With drogued drifters only, the median per 1° cell drops from 71 to 22, and 94 cells that were well supported fall below 10. What worried us when we looked at Figure 3 is where those gaps are. They cluster along the Agulhas Current itself, roughly 32–38°S between 32°E and 45°E, which is the source region our upstream starting cell sits in and close to McAdam and van Sebille's release point. So the drogued-only check is weakest exactly where our question matters most. That is why we use all drifters for the main matrix and treat the drogued-only version as a check on 2° cells. Undrogued drifters read systematically faster because of wind slip, so if the two versions disagree, we will learn something about how much wind affects the west/east split.

<img width="700" height="551" alt="download (3)" src="https://github.com/user-attachments/assets/8a74825c-d758-4ac9-8aaf-900aac8ea19c" />

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

**First look at the 7-day pairs.** Of 154,139 pairs, 92.7% stay inside R after 7 days. Of the 11,246 that leave, 32.0% leave west, 47.5% east, 15.9% south and 4.7% north. So even at one week, more material leaves towards the Indian Ocean than the Atlantic, which fits the idea that most of the current turns back. We are careful not to read the 32% as "Agulhas leakage" yet. It is pooled over every starting cell, and some of the western exits are probably drifters already in the Benguela flow off the west coast. Separating those by starting cell is exactly what the primary question is for.

## 7. Timeline and Plan

**Progress and approach.** Our project began in Week 1 (14 September) with selecting a suitable region and assessing whether the available drifter data could support our research questions. We compared four candidate regions using observation counts, spatial coverage and the number of distinct drifters per grid cell. We selected the Agulhas region because it provided strong data coverage while capturing both the Agulhas Current and its retroflection, allowing us to investigate westward and eastward transport.

During Weeks 2–3, we accessed the hourly GDP dataset through CloudDrift and verified our filtering against the course's East Australian Current example. We then conducted data quality checks, examined coverage across different years and seasons, and investigated drogue status and how drifter records end. These analyses helped us identify potential sampling limitations and informed our decision to use 2° cells for the transition matrix.

We also developed a preliminary method for constructing seven-day origin-destination pairs, using daily starting observations and tracking drifters beyond the regional boundaries to identify first exits. This produced 154,139 preliminary usable pairs and confirmed the feasibility of constructing a transition matrix. Following lecturer feedback, we will refine the handling of incomplete observations, grounding events and the first-exit rule before estimating the final matrix.

**Implementation timeline.** The remaining work is organised around the course assessments, with each stage producing a result that contributes directly to the final transport model.

| Week | Planned activities | Deliverables |
|---|---|---|
| **1–3 (14 Sep)** | Select and justify the region, access and verify the dataset, conduct data audits and coverage analysis, and construct preliminary seven-day pairs. | Completed: Tables 1–3, Figures 1–3 and `pairs7.csv`. |
| **4 (5 Oct)** | Finalise research questions, proposed methodology, preliminary findings and implementation plan, incorporating lecturer feedback. | **Project Proposal/README**, Thu 8 Oct. |
| **5 (12 Oct)** | Refine the seven-day pairs to handle first exits, incomplete follow-up and grounding. Address poorly supported cells and construct the initial transition matrix using a drifter-level training split. Produce preliminary destination and exit probabilities for selected starting cells. | Initial matrix, probability results and **poster session**, Thu 15 Oct. |
| **6 (19 Oct)** | Refine the three starting-cell analyses, examine seven-day transport patterns and develop 28-day projections. Incorporate feedback from the poster session. | RQ1 probability maps, exit summaries and **poster peer review**, Thu 22 Oct. |
| **7 (26 Oct)** | Investigate connectivity between grid cells, regional redistribution and how westward and eastward exit probabilities vary by starting location. | RQ2 connectivity and regional transport maps. |
| **8 (2 Nov)** | Evaluate predictive performance using separate training, validation and test drifters, the multiclass Brier score, top-three hit rate and baseline comparisons. Compare $P^4$ with directly observed 28-day outcomes and test sensitivity to time step, grid resolution, drogue status and season. | RQ3 validation results and sensitivity figures. |
| **9 (9 Nov)** | Refine the model based on validation results, assess whether 364-day projections are reliable enough to report, and package the matrix and code for reuse with other regions. | Final transport model, reproducible code and report outline. |
| **10 (16 Nov)** | Consolidate findings, prepare visualisations and rehearse the group presentation. | **Group presentation**, 12 + 3 minutes, in class. |
| **11 (23 Nov)** | Finalise the methodology, findings, limitations and conclusions, incorporating feedback from the presentation. | **Final modelling report**, Thu 26 Nov. |

**Evaluation and project management.** Our approach prioritises developing a reliable seven-day transition matrix before extending it to longer periods. We will separate drifters into training (60%), validation (20%) and testing (20%) sets, ensuring that observations from the same drifter do not appear across multiple sets. Model settings will be selected using validation data, while the test set will provide an independent assessment of performance. Longer-term projections will only be interpreted where supported by these checks.

We use GitHub to manage code and documentation, with Google Colab and VS Code supporting analysis and development. Our notebooks and saved outputs allow us to reproduce preliminary results and revisit earlier decisions. We will use feedback from the proposal, poster and peer-review sessions to refine the methodology before the final presentation and report.

**Risks and contingency plans.** We have identified several challenges that could affect the accuracy or feasibility of our analysis, along with practical alternatives.

| Risk | Potential impact | Mitigation strategy |
|---|---|---|
| **Insufficient data in some grid cells** | Unreliable transition probabilities, particularly for seasonal or drogued-only analyses. | Check distinct drifters contributing valid transitions and merge poorly supported neighbouring cells. Pool seasonal categories if necessary. |
| **Incomplete trajectories or uncertain grounding events** | Incorrect classification of seven-day outcomes. | Retain confirmed first exits, verify grounding within the observation window and exclude unresolved outcomes from complete-case transition estimates. |
| **Limitations of the Markov assumption** | Iterating the weekly matrix may produce unreliable longer-term projections. | Compare $P^4$ with directly observed 28-day outcomes. Prioritise validated short-term results and treat $P^{52}$ as exploratory if necessary. |
| **Artificial dispersion from grid resolution or time step** | Estimated transport probabilities may depend heavily on modelling choices. | Compare different grid sizes and time steps, and report the sensitivity of key findings. |
| **Uneven spatial and temporal sampling** | Some regions or periods may be disproportionately represented. | Examine coverage by cell, year, season and drogue status, and acknowledge limitations where coverage is insufficient. |
| **Data access or processing failures** | Delays in analysis and model development. | Use the existing retry mechanism for CloudDrift downloads and save intermediate results to avoid repeated processing. |

**Feasibility.** Our preliminary analysis has established that the Agulhas region contains sufficient observations for the proposed modelling approach and that seven-day transitions can be constructed from the available records. The main remaining challenge is therefore not data availability, but ensuring that the transition probabilities are correctly defined, statistically reliable and appropriately interpreted. By prioritising the initial matrix, evaluating its performance before extending the time horizon, and retaining simpler alternatives where necessary, we believe the project is achievable within the remaining teaching period.

**Repository.** We will tidy the repo into a clearer layout: `src/` for data access, filtering and the matrix code, `results/` for P and the summary counts, `figures/` for maps, and an `environment.yml` and `data/README.md` recording package versions and the data release, so someone else can rerun everything.

## References

**Data**

- Elipot, S., Sykulski, A., Lumpkin, R., Centurioni, L., & Pazos, M. (2022). *Hourly location, current velocity, and temperature collected from Global Drifter Program drifters world-wide* (Version 2.01.1) [22/09/26]. NOAA National Centers for Environmental Information. https://doi.org/10.25921/x46c-3620. Accessed 22 September 2026 via CloudDrift.

**Literature**

- Elipot, S., Lumpkin, R., Perez, R. C., Lilly, J. M., Early, J. J., & Sykulski, A. M. (2016). A global surface drifter data set at hourly resolution. *Journal of Geophysical Research: Oceans, 121*(5), 2937–2966. https://doi.org/10.1002/2016JC011716
- Lumpkin, R., & Johnson, G. C. (2013). Global ocean surface velocities from drifters: Mean, variance, El Niño–Southern Oscillation response, and seasonal cycle. *Journal of Geophysical Research: Oceans, 118*(6), 2992–3006. https://doi.org/10.1002/jgrc.20210
- McAdam, R., & van Sebille, E. (2018). Surface connectivity and interocean exchanges from drifter-based transition matrices. *Journal of Geophysical Research: Oceans, 123*(1), 514–532. https://doi.org/10.1002/2017JC013363
- Miron, P., Beron-Vera, F. J., Olascoaga, M. J., Sheinbaum, J., Pérez-Brunius, P., & Froyland, G. (2017). Lagrangian dynamical geography of the Gulf of Mexico. *Scientific Reports, 7*, Article 7021. https://doi.org/10.1038/s41598-017-07177-w
- Russo, C. S., Lamont, T., & Krug, M. (2021). Spatial and temporal variability of the Agulhas Retroflection: Observations from a new objective detection method. *Remote Sensing of Environment, 253*, Article 112239. https://doi.org/10.1016/j.rse.2020.112239

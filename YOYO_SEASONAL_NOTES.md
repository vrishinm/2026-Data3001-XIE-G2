# Yoyo – seasonal analysis and 2° coverage map (Stage 5 Task A, Stage 2 Task C)

Status 9 Nov: seasonal results checked against observed 56 / 91-day outcomes (Lucy's chaining method). **For Lucy's checks on 10 and 12 Nov.**

**Summary for the meeting (9 Nov)**
1. **B west in Winter is the solid result.** Westward (Atlantic) exits from B by day 91 drop in Winter. This shows up in the matrix (11.3% vs about 19–23%) *and* directly in the drifters (6.8% vs 22.0% for the rest of the year, −15.2 pp [−28.4, −0.1]). The seasonal matrix matches the observed B west share in every season.
2. **C east is underestimated by the matrix, and the observed data show a Summer effect the matrix misses.** Observed 91-day east exit from C is 38% in Summer vs 63% in the rest of the year (−25.4 pp [−49.1, −1.1]). The matrix gives 35–45% in every season, so it hides this. The gap is largest in Autumn and Spring (+25 and +35 pp).
3. **Drop the "A turns east in Winter" claim.** It came from the matrix only. Observed A east in Winter is 12.3% [0.0, 39.3] from 18 drifters, so it is not supported.

## How to reproduce

Put `pairs7.csv` (DATA3001 handover folder) next to the scripts, or one folder up, then run:

```bash
python yoyo_coverage_map.py
python yoyo_seasonal_analysis.py
python yoyo_seasonal_validation.py
```

Each takes 30–60 s and writes everything to `yoyo_outputs/`. `yoyo_seasonal_validation.py` also needs Zack's `drifter_split.csv` (in the repo). The only packages needed are numpy, pandas and matplotlib.

## Lucy's check items

- **Shared code is used.** Both functions, `build_transition_matrix` and `bootstrap_exit_probability`, are loaded directly from Vrishin's `vrishinanalysis.py`. `yoyo_common.load_shared_functions` runs only the function definitions, not the script's top-level checks. Each season's matrix comes from `build_transition_matrix`. The region-wide 7-day CIs come from `bootstrap_exit_probability`. The A/B/C bootstrap rebuilds P with weighted counts, and the script asserts that this rebuild equals `build_transition_matrix` exactly, for all-year and for each season.
- **The poster numbers are reproduced.** All-year 91-day results: B west 17.8% (poster 17.8%) and C east 38.7% (poster 38.7%).
- **Drifters per season and cell.** Full table in `seasonal_support.csv`:

  | | Summer (Dec–Feb) | Autumn (Mar–May) | Winter (Jun–Aug) | Spring (Sep–Nov) |
  |---|---|---|---|---|
  | A (cell 99, 28–30°E 33–35°S) | 39 drifters / 281 pairs | 47 / 327 | 36 / 226 | 40 / 247 |
  | B (cell 58, 18–20°E 37–39°S) | 47 / 184 | 54 / 247 | 49 / 200 | 54 / 184 |
  | C (cell 44, 26–28°E 39–41°S) | 34 / 242 | 72 / 541 | 54 / 398 | 44 / 287 |
  | Region (all cells) | 658 / 34,335 | 683 / 40,735 | 723 / 42,098 | 701 / 36,971 |

  Every A/B/C × season row clears the 10-drifter threshold.
- **Conclusions stay within the CIs.** A season counts as different only when the paired 95% CI of (season − rest of year) excludes 0. Differences smaller than 0.1 percentage points are ignored, because those are numerical zeros. Results are in `seasonal_contrasts.csv`.

## Method

- **Season.** Assigned by the start date of each 7-day pair, using austral seasons.
- **Matrices.** One 7-day matrix per season, plus one for all-year (`seasonal_matrices.npz`).
- **A, B and C use multi-step horizons.** None of the 3,364 pairs starting in A, B or C leaves R within 7 days. So for these cells we report 28 days (P⁴) and 91 days (P¹³) from each season's own matrix. The 91-day numbers are a projection and are not yet validated, following the plan: show 91 days only if P⁴ passes Zack's 28-day check.
- **Uncertainty.** Whole-drifter bootstrap with 1,000 resamples. Every season uses the same resampled drifters, so the difference between a season and the rest of the year gets a valid paired CI even when one drifter has pairs in several seasons.
- **Unresolved mass.** When a seasonal matrix sends probability into a cell with no pairs in that season, that probability is lost, and we report it as `p_unresolved`. It is at most 0.6% (Summer, 91 days).

## Findings (preliminary)

1. **Region-wide 7-day exits.**
   - West exits are more likely in **Summer and Spring** (3.0% [2.5, 3.6] and 2.8% [2.3, 3.4]) than in **Autumn and Winter** (1.9% [1.5, 2.3] and 1.8% [1.4, 2.2]). All four season-vs-rest differences exceed the uncertainty (about ±0.6–0.9 pp).
   - East exits are highest in **Winter**: 4.1% [3.6, 4.7], +0.9 pp [+0.3, +1.6] above the rest of the year.
2. **B (retroflection, west outcome).**
   - The 91-day west exit drops in **Winter**: 11.3% [6.8, 16.4], compared with about 19–23% in the other seasons. Winter minus rest of year is **−9.5 pp [−15.7, −3.3]**. This is the largest seasonal effect we found.
   - Summer and Spring are higher, but their CIs include 0.
3. **A (upstream Agulhas Current).**
   - In **Winter**, the matrix says more A drifters turn back east by 91 days: 18.8% [13.6, 24.8], +7.6 pp [+1.7, +14.0].
   - Fewer go west in Winter: 1.1%, −2.5 pp [−4.1, −1.2].
   - **Not confirmed by the observed outcomes** (next section), so not for the slides.
4. **C (return current).** In the matrix there is no clear seasonal effect: the 91-day east exit is 36–42% in every season. **The observed outcomes disagree** (next section): C east is much lower in Summer.
5. **28 days is too short for A, B and C to reach the boundary.** All 28-day exit probabilities are below 1%. This matters for the validation storyline: P⁴ vs observed 28-day outcomes should compare destination cells, not just exits.
6. **One consistent pattern.** Taken together, Winter has fewer westward (Atlantic) exits and more eastward exits, both region-wide and from A and B. The seasonal differences are mostly smaller than the differences between starting cells.

Caveats:
- A seasonal matrix applied for 91 days assumes the season's conditions hold for 13 weeks, so the 91-day numbers are indicative only.
- These results show association, not cause.
- When we compare with Russo et al. (2021), who report retroflection timing varying by season, we need to check their definitions first.

## Checking the 56 / 91-day numbers against observed outcomes (`yoyo_seasonal_validation.py`)

Lucy found that the all-year matrix gets B west right at 91 days but underestimates eastward exits, and suggested the same check for the seasonal numbers.

**Method**
- Same chaining as Lucy's notebook (Step 11): start from a pair in A, B or C, follow the drifter through its own 7-day pairs, and record the first exit. Starts with a missing week before the horizon are censored and left out.
- Drifters: Zack's split. **Test drifters are not used**; everything here uses train + val (901 drifters).
- Part 1 reproduces Lucy's all-year table exactly (matrix from train, observed on val): B west 20.0% vs 20.0%, B east 17.1% vs 4.4%, C east 61.9% vs 38.0% (`validation_lucy_check.csv`).
- Part 2 gives the observed seasonal shares directly, with no matrix involved, plus paired season-vs-rest contrasts.
- Part 3 compares each season's P⁸ / P¹³ (fit on the same train + val drifters) with the observed share, with a paired bootstrap CI of the gap. Since both sides use the same drifters, a gap means the memoryless (Markov) assumption fails, not overfitting.
- A gap or contrast counts only if its CI excludes 0 **and** it is at least 1 pp. When no drifter in a group exits, the bootstrap CI collapses to [0, 0], so smaller gaps are not meaningful.

**91 days, observed vs seasonal matrix** (%, 95% CI; n = drifters with an uncensored outcome)

| Cell, side | Season | n | Observed | Matrix P¹³ | Observed − matrix |
|---|---|---|---|---|---|
| B west | Summer | 31 | 23.6 [10.9, 41.4] | 23.3 [14.0, 33.6] | +0.3 |
| | Autumn | 33 | 13.0 [3.0, 27.7] | 21.6 [13.9, 30.6] | −8.6 [−20.7, 6.1] |
| | **Winter** | 23 | **6.8** [0.0, 18.8] | **10.0** [5.7, 14.8] | −3.2 |
| | Spring | 33 | 32.1 [14.6, 52.8] | 23.2 [15.3, 32.5] | +9.0 [−7.2, 26.8] |
| C east | **Summer** | 22 | **38.0** [15.2, 59.4] | 34.5 [25.9, 45.3] | +3.5 |
| | Autumn | 52 | 66.6 [50.4, 80.2] | 41.1 [33.1, 50.8] | **+25.5** [9.2, 38.6] |
| | Winter | 40 | 52.8 [29.8, 74.9] | 45.4 [35.8, 55.5] | +7.4 |
| | Spring | 30 | 69.1 [50.2, 87.3] | 34.7 [25.3, 44.9] | **+34.5** [16.9, 50.5] |
| A east | Winter | 18 | 12.3 [0.0, 39.3] | 20.5 [14.7, 27.9] | −8.3 [−23.5, 19.3] |

Full table, including 28 and 56 days and all sides: `seasonal_observed_exits.csv`.

**Observed seasonal contrasts that exceed the uncertainty** (season − rest of year, `seasonal_observed_contrasts.csv`)

| Cell | Days | Side | Season | Observed | Rest of year | Difference |
|---|---|---|---|---|---|---|
| B | 91 | west | Winter | 6.8% | 22.0% | −15.2 pp [−28.4, −0.1] |
| C | 91 | east | Summer | 38.0% | 63.4% | −25.4 pp [−49.1, −1.1] |
| A | 91 | west | Autumn | 0.6% | 6.4% | −5.9 pp [−13.3, −0.3] |
| B | 56 | west | Autumn | 0.6% | 9.1% | −8.5 pp [−15.2, −2.5] |
| B | 56 | west | Spring | 16.3% | 3.7% | +12.6 pp [+0.2, +27.8] |
| C | 56 | east | Summer | 3.5% | 25.1% | −21.6 pp [−30.2, −11.5] |
| A | 56 | east | Summer / Winter | 0.0% | about 3% | about −3 pp |

**What this means**
- **B west / Winter holds up.** The matrix fits B west in every season, and the observed Winter drop is the largest B effect. The observed CI only just excludes 0 (upper end −0.1 pp), so present it as "lower in Winter in both the matrix and the drifters", not as a precise size.
- **C east: the matrix is too low in Autumn and Spring, not in Summer and Winter.** So the all-year underestimate Lucy found comes mainly from Autumn and Spring starts. The observed Summer drop at C (also at 56 days: 3.5% vs 25.1%) is a real seasonal signal that the matrix flattens out.
- **A: most seasonal claims go.** A Winter east (+7.6 pp in the matrix) is not seen in the drifters. A west in Autumn is lower in the drifters, but the levels are small (0.6% vs 6.4%).
- **Caveats.**
  - Only 18–52 drifters per cell and season, so the observed CIs are wide.
  - Censoring is uneven: in Winter, 41% of A starts and 49% of B starts lose their record before day 91, compared with 9–29% in other seasons. If drifters that die early behave differently, the Winter observed shares could be biased.
  - These are in-sample for train + val; the test drifters are still locked for the final evaluation.

## 2° coverage / support map (`yoyo_coverage_map.py`)

- Here, support means distinct drifters with at least one **valid 7-day pair starting in the cell**. This replaces the poster's visitation count.
- Results:
  - 177 cells have valid pairs. Of these, **171 have ≥10 drifters**, 158 have ≥25, and 148 have ≥50.
  - The median is 107 drifters per cell; the 25th percentile is 70.
  - The 171 cells with ≥10 drifters hold 99.9% of all pairs.
  - The 6 cells below 10 drifters are along the NW coast (Namibia, 10–16°E, 20–25°S), at 18–20°E 31–33°S, and in the NE corner.
- **Threshold check (`fig_threshold_ci_width.png`).** Using the bootstrap CI width of P(leaving the starting cell within 7 days):

  | Drifters | Median CI width |
  |---|---|
  | 10–24 | 0.36 |
  | 25–49 | 0.20 |
  | 50–99 | 0.14 |
  | 100+ | 0.13 |

  The CI stops narrowing at about 50 drifters. So 10 drifters is a minimum for including a row, but cells with 10–49 drifters should be described as uncertain.
- **By season.** 150–156 cells per season have ≥10 drifters. The median per season is 29–36 drifters per cell, so per-cell seasonal maps are noisier than the all-year map (`fig_coverage_2deg_by_season.png`).

## Figures for the slides

| File | Use |
|---|---|
| `fig_coverage_2deg.png` | 2° support map (feedback item: coverage map to match the 2° matrix) |
| `fig_seasonal_observed_vs_matrix.png` | **Main seasonal figure now**: observed vs matrix at 91 days, per season, for A/B/C |
| `fig_seasonal_exit_ABC.png` | Matrix-only A/B/C at 28 and 91 days with CIs (backup) |
| `fig_seasonal_region_7day.png` | Region-wide 7-day seasonal exits |
| `fig_seasonal_exit_maps.png` | Where west/east exits happen, by season (backup slide) |
| `fig_threshold_ci_width.png` | Why 10 drifters is a minimum (Q&A backup) |
| `fig_coverage_2deg_by_season.png` | Seasonal support (Q&A backup) |

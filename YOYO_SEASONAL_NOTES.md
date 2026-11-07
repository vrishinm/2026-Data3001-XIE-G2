# Yoyo – seasonal analysis and 2° coverage map (Stage 5 Task A, Stage 2 Task C)

Status 7 Nov: first full results. **For Lucy's checks on 10 and 12 Nov.**

## How to reproduce

Put `pairs7.csv` (DATA3001 handover folder) next to the scripts, or one folder up, then run:

```bash
python yoyo_coverage_map.py
python yoyo_seasonal_analysis.py
```

Each takes about 30 s and writes everything to `yoyo_outputs/`. The only packages needed are numpy, pandas and matplotlib.

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
   - In **Winter**, more A drifters turn back east by 91 days: 18.8% [13.6, 24.8], +7.6 pp [+1.7, +14.0].
   - Fewer go west in Winter: 1.1%, −2.5 pp [−4.1, −1.2].
4. **C (return current).** There is no clear seasonal effect. The 91-day east exit is 36–42% in every season, and every CI overlaps the others.
5. **28 days is too short for A, B and C to reach the boundary.** All 28-day exit probabilities are below 1%. This matters for the validation storyline: P⁴ vs observed 28-day outcomes should compare destination cells, not just exits.
6. **One consistent pattern.** Taken together, Winter has fewer westward (Atlantic) exits and more eastward exits, both region-wide and from A and B. The seasonal differences are mostly smaller than the differences between starting cells.

Caveats:
- A seasonal matrix applied for 91 days assumes the season's conditions hold for 13 weeks, so the 91-day numbers are indicative only.
- These results show association, not cause.
- When we compare with Russo et al. (2021), who report retroflection timing varying by season, we need to check their definitions first.

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
| `fig_seasonal_exit_ABC.png` | Main seasonal figure: A/B/C at 28 and 91 days with CIs |
| `fig_seasonal_region_7day.png` | Region-wide 7-day seasonal exits |
| `fig_seasonal_exit_maps.png` | Where west/east exits happen, by season (backup slide) |
| `fig_threshold_ci_width.png` | Why 10 drifters is a minimum (Q&A backup) |
| `fig_coverage_2deg_by_season.png` | Seasonal support (Q&A backup) |

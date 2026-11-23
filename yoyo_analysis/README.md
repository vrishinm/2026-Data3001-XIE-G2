# Yoyo: 2° support map, seasonal analysis and drogue results for A, B and C

This folder holds the code and outputs behind the 2° support numbers (report Sections 3 and 7), the seasonal matrix values in Section 5.3, the drogue results for A, B and C (Section 5.2 and Table 6.5) and report Figures 5.1 and 5.2.

Start cells: A = cell 99 (28–30°E, 33–35°S), B = cell 58 (18–20°E, 37–39°S), C = cell 44 (26–28°E, 39–41°S).

## How to run

From the repository root, in this order (numpy, pandas and matplotlib only; 10–80 s each):

```bash
python yoyo_analysis/scripts/yoyo_coverage_map.py
python yoyo_analysis/scripts/yoyo_seasonal_analysis.py
python yoyo_analysis/scripts/yoyo_seasonal_validation.py
python yoyo_analysis/scripts/yoyo_drogue_ABC.py
python yoyo_analysis/scripts/yoyo_report_figures.py      # reads results/drogue_ABC_observed.csv
```

Inputs: `pairs7.csv` in the repository root, which is not committed; make it with `python generate_pairs.py` (see the main README) or point `PAIRS7=<path>` to a copy. The others are in the repository: `drifter_split.csv` and `drogue_info.csv` (root), Vrishin's `vrishin_analysis/scripts/vrishinanalysis.py` and `vrishin_analysis/results/drogue_exit_comparison.csv`. The first map run downloads a Natural Earth coastline file and caches it in `results/`. The outputs are the same with the versions in `requirements.txt` (Python 3.13) and with Python 3.10 (numpy 1.23, pandas 2.0), apart from rounding at the 16th decimal place.

## Which drifters are used

- **Matrices and observed paths: training + validation drifters only** (901 drifters, 122,775 pairs). The 225 test drifters in `drifter_split.csv` are left out by `yoyo_common.drop_test`, so the test set stays locked for Zack's final scores.
- **Support counts: all 1,126 drifters.** `yoyo_coverage_map.py`, Part 1 of `yoyo_drogue_ABC.py` and the pair-count check against Vrishin's file describe the data and do not fit anything.
- **Report Figure 5.1** uses the matrix from training drifters only, as in Table 6.5 and Section 7.
- An earlier version of `yoyo_seasonal_analysis.py` and of the drogue matrices used all 1,126 drifters, including test drifters (poster values: B west 17.8%, C east 38.7% by day 91). The current outputs replace those; with training + validation drifters the same numbers are 18.2% and 39.0%.

## Scripts and outputs

| Script | What it does | Outputs (`results/`, `figures/`) |
|---|---|---|
| `yoyo_common.py` | Loads `pairs7.csv` and the split, assigns austral seasons, loads Vrishin's `build_transition_matrix` and `bootstrap_exit_probability`, week-by-week chaining (Lucy's method), map helpers | |
| `yoyo_coverage_map.py` | Distinct drifters with a valid 7-day pair starting in each 2° cell; bootstrap CI width against support | `coverage_2deg_*.csv`, `coverage_ci_width_by_band.csv`, `fig_coverage_2deg*.png`, `fig_threshold_ci_width.png` |
| `yoyo_seasonal_analysis.py` | One 7-day matrix per season; region-wide 7-day exits; A, B, C at 28 and 91 days with paired whole-drifter bootstrap CIs (1,000 resamples) | `seasonal_matrices.npz`, `seasonal_region_7day_exits.csv`, `seasonal_ABC_exit_probabilities.csv`, `seasonal_contrasts.csv`, `seasonal_cell_exit_probs.csv`, `seasonal_support.csv`, `fig_seasonal_*.png` |
| `yoyo_seasonal_validation.py` | Observed 28/56/91-day exits by season from A, B, C, compared with each season's matrix; reproduces Lucy's all-year check | `seasonal_observed_*.csv`, `validation_lucy_check.csv`, `fig_seasonal_observed_vs_matrix.png` |
| `yoyo_drogue_ABC.py` | Support for drogued-only and undrogued-only pairs; drogued vs undrogued matrices; observed exits by drogue status at the start | `drogue_support_cells.csv`, `drogue_ABC_matrix.csv`, `drogue_ABC_observed*.csv`, `fig_drogue_support.png`, `fig_drogue_ABC.png` |
| `yoyo_report_figures.py` | Report Figure 5.1 (exit maps by day 91, training-drifter matrix) and Figure 5.2 (drogue at A, B, C by day 91) | `fig_exit_maps_91d_train.png`, `fig_exit_maps_28d_train.png` (not in the report), `fig_drogue_ABC_91d.png`, `exit_maps_ABC_check.csv` |

The seasonal, validation and drogue scripts rebuild matrices with bootstrap weights; each rebuild is checked against Vrishin's `build_transition_matrix` with an assertion.

## Observed estimates: complete records, not censoring-corrected

The observed shares in this folder follow each start week by week through its own 7-day pairs and **leave out starts whose record ends or has a gap before the horizon**. The report's main seasonal numbers (Table 5.3, Figure 5.3, Table 6.5 apart from its undrogued row) come instead from Lucy's notebook, Section 12, which keeps those starts until their record ends (censoring-corrected). The two versions are close but not identical:

| 91 days | This folder (complete records) | Report (censoring-corrected, Lucy's notebook) |
|---|---|---|
| B west, winter | 6.8%; winter − rest −15.2 pp [−28.4, −0.1], 23 drifters | 5.5% [0.0, 12.8]; −15.3 pp [−26.4, −3.1], 37 drifters |
| C east, summer | 38.0%; −25.4 pp [−49.1, −1.1] | 37.9%; −25.0 pp [−49.9, −1.3] |

The report uses the complete-record B result as its censoring check in Section 5.3. The drogue numbers below, which the report quotes in Sections 5.2, 6.2 and Table 6.5, are complete-record estimates.

## Results

**Support (Sections 3 and 7).** 177 cells have valid 7-day pairs; 171 have at least 10 drifters and hold 99.9% of all pairs. The median bootstrap CI width of the 7-day cell-exit probability is 0.36 for 10–24 drifters, 0.20 for 25–49, 0.14 for 50–99 and 0.13 for 100 or more, so the CI stops narrowing at about 50 drifters.

**Seasonal matrices, 91 days (Section 5.3, matrix values in Figure 5.3).** Training + validation drifters, 95% whole-drifter bootstrap CI.

| | Summer | Autumn | Winter | Spring |
|---|---|---|---|---|
| Drifters starting at A / B / C | 35 / 39 / 25 | 37 / 45 / 55 | 31 / 37 / 45 | 31 / 44 / 38 |
| B west | 23.3% [15.0, 34.6] | 21.6% [13.8, 29.9] | **10.0%** [6.0, 15.0] | 23.2% [15.0, 32.2] |
| C east | 34.5% [25.4, 47.0] | 41.1% [33.0, 50.6] | 45.4% [35.2, 55.9] | 34.7% [25.3, 44.9] |

In the matrix, winter minus the rest of the year at B west is −11.8 pp [−18.6, −5.3]. The matrix also gives more east exits from A in winter (+10.2 pp [+3.5, +18.3]), but the observed paths do not support it (+0.9 pp [−16.3, +26.5] in the report), so it is not reported as a finding. Region-wide 7-day exits differ by season by about 1 pp or less (`seasonal_region_7day_exits.csv`).

**Observed vs seasonal matrix (`yoyo_seasonal_validation.py`).** The matrix matches the observed B west share in every season. At C it is too low in autumn (41.1% against 66.6% observed) and spring (34.7% against 69.1%), so the all-year under-prediction of east exits comes mainly from those seasons. Full table: `seasonal_observed_exits.csv`.

**Drogued vs undrogued, 91 days (Section 5.2, Figure 5.2, Table 6.5).** Observed, complete records, by drogue status at the start; n = drifters.

| | Drogued | Undrogued | Drogued − undrogued |
|---|---|---|---|
| B west | 7.0% [0.8, 17.1] (31) | 25.4% [16.1, 35.9] (69) | −18.4 pp [−30.7, −4.5] |
| B east | 2.5% [0.0, 6.8] (31) | 13.2% [5.4, 23.6] (69) | −10.7 pp [−21.2, −2.0] |
| C east | 39.8% [19.3, 63.7] (33) | 65.9% [53.6, 77.3] (95) | −26.1 pp [−49.6, +1.4] |
| A east | 8.6% [1.4, 25.1] (23) | 13.2% [5.3, 22.5] (61) | −4.6 pp [−17.8, +15.5] |

The drogued and undrogued matrices (training + validation drifters) agree in direction: B west 10.0% against 25.8% (−15.8 pp [−23.3, −8.8]) and C east 25.8% against 45.9% (−20.1 pp [−29.7, −9.2]); `drogue_ABC_matrix.csv`. Drogue status is fixed at the start: a drogued start can lose its drogue before day 91. 154 cells have at least 10 drogued drifters and 164 at least 10 undrogued drifters (`drogue_support_cells.csv`).

**Figure 5.1 check values** (`exit_maps_ABC_check.csv`, training-drifter matrix, 91 days): A 3.2% west / 11.6% east, B 20.0% / 4.4%, C 0.1% / 38.0%, matching Table 6.5 and Section 7.

## Limits

- 25–55 drifters per season and start cell, so the observed CIs are wide, and the 20 seasonal contrasts share drifters and are not independent tests.
- A seasonal matrix applied for 91 days assumes the release season lasts all 13 weeks, so seasonal matrix values at 91 days are a rough guide.
- In winter, 49% of B starts lose their record before day 91 (18–29% in other seasons); see the complete-record note above.
- These are associations: season and drogue status also differ in wind and years sampled.

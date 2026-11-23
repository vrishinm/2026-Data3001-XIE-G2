# Where things end up in the Agulhas: a drifter-based surface transport matrix

DATA3001 Term 3 2026, Group S02-G02 (Lucy, Vrishin, Yoyo, Zack).

We estimate where floating material released in the greater Agulhas region (R: 10–45°E, 20–45°S) leaves the region, and how long it takes. The model is a 7-day transition matrix on 2° × 2° cells (234 cells plus four exit states: west, east, south, north), estimated from NOAA Global Drifter Program hourly trajectories and checked against held-out drifters. The submitted proposal is archived in [`docs/proposal.md`](docs/proposal.md).

## Repository layout

| Path | Owner | Contents |
|---|---|---|
| `Lucy_temperature_and_handover.ipynb` | Lucy | Data audit, 7-day pairs, SST and temperature analysis, matrix vs observed paths at 28–91 days, season check (Colab) |
| `Proposal_code.ipynb` | group | Proposal-stage version of the data audit and region choice (Table 2.2) |
| `Zack_Analysis/` | Zack | `Validation_code.ipynb` (drifter split, baselines, Brier score, 28-day check, test scores) and `Zack_outputs/` (its tables) |
| `vrishin_analysis/` | Vrishin | Shared matrix and bootstrap functions with unit tests, drogue and speed comparisons, time-step and exit-rule sensitivity (`scripts/`, `results/`, `figures/`, own [README](vrishin_analysis/README.md)) |
| `yoyo_analysis/` | Yoyo | 2° support map, seasonal analysis, drogue results for A, B and C, report Figures 5.1 and 5.2 (`scripts/`, `results/`, `figures/`, own [README](yoyo_analysis/README.md)) |
| `generate_pairs.py`, `prepare_inputs.py`, `run_validation.py` | Vrishin | Scripted version of the pair generation and validation (see the reproducibility guide below) |
| `drifter_split.csv`, `drogue_info.csv` | Zack, Vrishin | The frozen train / validation / test split (676 / 225 / 225 drifters) and the drogue-loss date per drifter |
| `docs/proposal.md` | group | The submitted proposal |
| `requirements.txt` | | Python packages |

Start cells used throughout: A = cell 99 (28–30°E, 33–35°S, Agulhas Current), B = cell 58 (18–20°E, 37–39°S, retroflection), C = cell 44 (26–28°E, 39–41°S, Return Current).

## Final Project — Reproducibility Guide

### Environment

The analysis was reproduced using Python 3.13 and the dependencies in `requirements.txt`.

From the repository root, create a virtual environment and install the dependencies:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If `python3.13` is unavailable, install Python 3.13 first.

The workflows access the public NOAA Global Drifter Program hourly dataset through CloudDrift. Internet access is required, and processing the source data requires substantial memory.

### Reproducing the validation analysis

Run these commands in order from the repository root:

```bash
python generate_pairs.py
python prepare_inputs.py
python run_validation.py
```

#### 1. Generate seven-day transitions

`generate_pairs.py` executes the verified pair-generation cells from `Lucy_temperature_and_handover.ipynb`.

It generates `pairs7.csv` from the NOAA dataset and checks that the output contains 154,139 seven-day transitions.

If an existing root-level `pairs7.csv` is present, the script verifies that the regenerated table matches it exactly.

#### 2. Prepare the frozen drifter split

`prepare_inputs.py` reads the repository's `drifter_split.csv`, which is the authoritative train/validation/test allocation.

It reconstructs:

- `gdp_out/drifter_ids.csv`
- `gdp_out/drifter_split.csv`

The original split is not regenerated or randomised. If `pairs7.csv` exists, the script also verifies its per-drifter pair counts against the frozen split.

#### 3. Reproduce validation results

`run_validation.py` executes the validation analysis from `Zack_Analysis/Validation_code.ipynb`, excluding Colab-specific setup and the final test-set cell.

The runner keeps `TEST_UNLOCKED = False`.

It saves its results in a temporary directory and prints the output path. The repository's committed results are not overwritten.

The validation run generates 10 CSV files, including `validation_val.csv`, `multiweek_scores_val.csv`, and `p4_vs_28day_scores_val.csv`.

### Expected validation results

| Metric | Expected value |
|---|---:|
| Seven-day pairs | 154,139 |
| Contributing drifters | 1,126 |
| Training drifters | 676 |
| Validation drifters | 225 |
| Test drifters | 225 |
| Seven-day validation Brier score | 0.809 |
| Seven-day validation top-3 hit rate | 0.632 |
| Twenty-eight-day validation Brier score | 0.841 |

The pair-generation and validation workflows have been executed locally. The regenerated pair table matched the existing table exactly, and all 10 regenerated validation CSV files matched their repository counterparts within numerical comparison tolerances.

The final test-set evaluation is deliberately excluded from the automated validation runner. The final test score is therefore not independently verified by these three commands.

### Additional analyses

The repository also contains individual analysis scripts in `vrishin_analysis/` and `yoyo_analysis/`, along with additional notebooks and saved results. These are not executed by the three-command validation workflow.

The generated `pairs7.csv`, `pairs7_drogue.csv`, and `gdp_out/` files are excluded from version control because they are intermediate data products.

## Running the individual analyses

These steps need `pairs7.csv` in the repository root (from `python generate_pairs.py` above) and are run from the repository root.

**Vrishin's analysis** (about 10 s each unless noted):

```bash
python -m unittest discover -s vrishin_analysis/scripts -p "vrishin_test_transport_tools.py" -v
python vrishin_analysis/scripts/vrishindrogue.py            # needs pairs7.csv, drogue_info.csv; writes pairs7_drogue.csv
python vrishin_analysis/scripts/vrishin_sensitivity_figures.py
# these three download the GDP data and take much longer:
python vrishin_analysis/scripts/exportdrogue.py               # rebuilds drogue_info.csv
python vrishin_analysis/scripts/vrishinspeed.py               # needs pairs7_drogue.csv
python vrishin_analysis/scripts/vrishin_drifter_exit_and_timestep_analysis.py
```

**Yoyo's analysis** (10–80 s each; the first map run downloads a coastline file):

```bash
python yoyo_analysis/scripts/yoyo_coverage_map.py
python yoyo_analysis/scripts/yoyo_seasonal_analysis.py
python yoyo_analysis/scripts/yoyo_seasonal_validation.py
python yoyo_analysis/scripts/yoyo_drogue_ABC.py
python yoyo_analysis/scripts/yoyo_report_figures.py         # after yoyo_drogue_ABC.py
```

These were rerun from a clean copy of the repository on 23 November 2026, with Python 3.13 and the versions in `requirements.txt`: the unit tests pass, and the scripts that do not download data reproduce the committed tables (differences no larger than rounding at the 16th decimal place).

**Zack's notebook and the locked test cell.** In `Zack_Analysis/Validation_code.ipynb`, Section 6 scores the test drifters and is locked: it stops with `AssertionError: Test drifters are locked` unless `TEST_UNLOCKED = True` is set in Section 0. The notebook is saved in this locked state, so its last cell shows that error; `validation_test.csv` and `validation_test_paired_differences.csv` in `Zack_Analysis/Zack_outputs/` were written by the run with the lock opened, after the settings had been chosen on the validation drifters. `run_validation.py` leaves this cell out.

## Test drifters

The 225 test drifters are used only once, for the final scores in Section 6 of Zack's notebook (`Zack_Analysis/Zack_outputs/validation_test.csv`). Every matrix and every observed estimate elsewhere uses training and validation drifters. The exceptions are descriptive counts that do not fit or tune the model: coverage per cell, Vrishin's 7-day drogue and speed comparison (`vrishindrogue.py`, `vrishinspeed.py`, the 6.77 cm/s in Section 6.2 of the report) and the time-step and exit-rule checks, which use all 1,126 drifters.

## Where each part of the report comes from

| Report | Source | Output |
|---|---|---|
| Table 2.2 (candidate regions) | `Proposal_code.ipynb`, Section 2 | notebook output |
| Figure 2.2 (study region, A, B, C) | `Lucy_temperature_and_handover.ipynb`, Section 12 | `gdp_out/fig_region_2_3.png` |
| Section 3 (pairs, cells, support) | Lucy's notebook, Sections 3–6; `yoyo_coverage_map.py` | `yoyo_analysis/results/coverage_2deg_*.csv` |
| Section 5.1 (Brier scores, 28-day check, test scores) | `Zack_Analysis/Validation_code.ipynb`, Sections 5–6 | `Zack_Analysis/Zack_outputs/validation_*.csv`, `p4_vs_28day_*.csv`, `multiweek_*.csv` |
| Figure 5.1 (exit maps by day 91) | `yoyo_report_figures.py` (matrix from training drifters) | `yoyo_analysis/figures/fig_exit_maps_91d_train.png` |
| Section 5.2 / 6.2 (drogue: 7-day exits, speed) | `vrishindrogue.py`, `vrishinspeed.py` | `vrishin_analysis/results/drogue_*.csv`, `vrishin_analysis/figures/drogue_*.png` |
| Figure 5.2 (drogue at A, B, C by day 91) | `yoyo_drogue_ABC.py`, then `yoyo_report_figures.py` | `yoyo_analysis/results/drogue_ABC_observed.csv`, `yoyo_analysis/figures/fig_drogue_ABC_91d.png` |
| Table 5.3, Figure 5.3 (season) | Lucy's notebook, Section 12 ("Checking the seasonal matrix results"); seasonal matrix values and the complete-record check also in `yoyo_seasonal_validation.py` | `gdp_out/fig_season_5_3.png`; `yoyo_analysis/results/seasonal_observed_*.csv` |
| Table 5.4, Figure 5.4 (temperature) | Lucy's notebook, Sections 9, 12 and 12b | `gdp_out/fig_temperature_year_specs.png` |
| Section 6.1 (time step, exit rule) | `vrishin_drifter_exit_and_timestep_analysis.py`, `vrishin_sensitivity_figures.py` | `vrishin_analysis/results/`, `vrishin_analysis/figures/vrishin_*.png` |
| Table 6.5, Figure 6.5 (release at B) | Lucy's notebook, Sections 11 and 12 | `gdp_out/fig_worked_example_6_5.png` |
| Section 7 (support and CI width) | `yoyo_coverage_map.py` | `yoyo_analysis/results/coverage_ci_width_by_band.csv`, `yoyo_analysis/figures/fig_threshold_ci_width.png` |

Files under `gdp_out/` are written when the notebooks run and are not committed; the figures also appear in the saved notebook outputs.

## 1° outputs

`Zack_Analysis/Zack_outputs/Output_1deg/` holds an exploratory rerun of the validation on 1° cells. It is not used in the report, where the comparison of cell sizes is listed as future work (Section 7).

- **`pairs7_1deg.csv`** is `pairs7.csv` with the cells recomputed on a 1° grid: 35 × 25 = 875 cells, with the exits numbered 875–878 (west, east, south, north). The pairs, drifters, start times, `obs_row` values and exits are the same as at 2°. It is what the pair step (`Lucy_temperature_and_handover.ipynb`, Section 6) gives with a 1° grid: recomputing each pair's start cell and day-7 cell from the GDP positions on a 1° grid reproduces every row.
- **The `*_1deg.csv` tables** come from `Zack_Analysis/Validation_code.ipynb`, Sections 1–5, with `GRID = 1` and `PAIRS_PATH` set to `pairs7_1deg.csv`. The drifter split, seed and bootstrap settings are the same as at 2°. The committed notebook is set to `GRID = 2`.
- **Check (23 November 2026).** Rerunning the notebook this way reproduces all nine committed 1° tables, with differences no larger than 3 × 10⁻¹⁶; the same rerun at 2° reproduces the ten 2° tables in `Zack_Analysis/Zack_outputs/`. The notebook also writes `p4_vs_28day_shares_val.csv`, but its 1° version was not uploaded.

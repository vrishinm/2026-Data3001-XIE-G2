
# DATA3001 — Vrishin's Analysis

## Overview

This directory contains the transition-matrix, bootstrap,
time-to-cell-exit and sensitivity analyses for the DATA3001
Agulhas drifter transport project.

Additional investigations examine the relationship between
drogue status, regional exit probabilities and drifter speed.

## Directory Structure

- `scripts/` — Python analysis and testing scripts
- `results/` — Generated transition matrices and CSV results
- `figures/` — Presentation-ready figures

## Main Analyses

### 1. Seven-Day Pair Audit and Transition Matrix

The seven-day dataset contains 154,139 starting observations
from 1,126 contributing drifters.

The transition model contains 234 interior grid cells and
four directional absorbing boundary states:
west, east, south and north.

Of the 234 interior cells, 177 have observed transitions.
Unsupported rows are explicitly identified rather than
treated as empirically estimated transitions.

### 2. Bootstrap Confidence Intervals

Bootstrap resampling is performed at the whole-drifter level
to account for dependence between observations originating
from the same trajectory.

Reusable functions are provided in:
`scripts/vrishin_transport_tools.py`

### 3. Time-to-Cell-Exit Analysis

Kaplan-Meier estimation was used to evaluate the time taken
for a drifter to leave its initial 2-degree grid cell.

Key results:
- Median time to cell exit: 3.08 days
- Cumulative departure by day 3: 49.35%
- Cumulative departure by day 7: 76.44%

Trajectories ending before an observed cell exit are treated
as right-censored.

### 4. Three-Day Versus Seven-Day Comparison

Regional first-exit probabilities:

| Direction | 3 days | 7 days |
|---|---:|---:|
| West | 1.08% | 2.33% |
| East | 1.60% | 3.46% |
| South | 0.63% | 1.15% |
| North | 0.17% | 0.34% |

These values compare cumulative first-exit probabilities
over different observation horizons, not predictive accuracy.

### 5. Alternative Exit-Rule Analysis

Compared the first regional boundary exit with the drifter's
location at the end of the seven-day window.

Of 153,985 comparable pairs:
- 1,494 (0.97%) changed classification
- 1,470 of the changed cases involved re-entry
- 24 changes were attributable to other differences

This demonstrates the importance of distinguishing
first boundary crossing from endpoint classification.

### 6. Additional Drogue Analyses

Additional investigations include:
- Drogue-status differences in regional exits
- Within-cell comparisons
- Whole-drifter bootstrap confidence intervals
- Drogue-status differences in drifter speed

## Reproducing the Analysis

Run all commands from the repository root.

Required Python packages include:
`numpy`, `pandas`, `matplotlib`, and `clouddrift`.

The scripts use shared inputs including `pairs7.csv`
and NOAA Global Drifter Program hourly data.

Other drogue analysis scripts require locally generated
`drogue_info.csv` and `pairs7_drogue.csv`.

### Run automated tests

```bash
python -m unittest discover -s vrishin_analysis/scripts -p "vrishin_test_transport_tools.py" -v
```

### Regenerate sensitivity figures

```bash
python vrishin_analysis/scripts/vrishin_sensitivity_figures.py
```

### Recompute the trajectory sensitivity analysis

```bash
python vrishin_analysis/scripts/vrishin_drifter_exit_and_timestep_analysis.py
```

Note: This step retrieves and processes NOAA hourly trajectories
and is substantially more computationally expensive.

## Methodological Limitations

- Daily starting observations from the same drifter overlap
  and are statistically dependent.
- The Kaplan-Meier curve is descriptive; it does not provide
  drifter-clustered confidence intervals.
- Seven-day first-exit probabilities naturally exceed
  three-day probabilities because of longer exposure.
- Unsupported transition-matrix rows contain NaN values
  and cannot be directly used for matrix powers without
  an explicitly chosen treatment.
- Exit-rule agreement does not guarantee equivalent
  long-term Markov transport predictions.
```

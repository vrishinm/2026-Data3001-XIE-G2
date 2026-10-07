# Transport operator implementation specification

Updated: 2026-10-06 (Australia/Sydney). This document supports README Sections 1 and 5 after reordering the proposal into Lucy's structure. The main analysis follows the locally saved Lucy proposal (`origin/lucy`, `4e3d1ef`), as requested by the group. It specifies planned implementation and contains no fitted matrix or verified model performance.

Lucy baseline: daily origins, a 2-degree grid, a 7-day pooled-pair operator, adjacent merging of sparse cells, all drifters, 20% whole-drifter hold-out, top-three destination coverage and persistence, followed by drogued-only, 3-day and seasonal variants. Exact timestamps, training-only decisions and explicit event/censor rules make that plan reproducible. Equal-drifter weighting, Brier scores, bootstrap and extra grid-resolution checks are supplementary extensions. The neighbour-selection details below are proposed implementation choices because Lucy's README does not define them.

## 1. Scope and configuration

The main operator describes destinations up to the first **observed** exit from R or confirmed grounding. It cannot follow material outside R and back again. Boundary direction is not itself an ocean-membership or net leakage measurement. Annual propagation is a stationary Markov extrapolation unless supported by direct validation.

| Setting | Main analysis | Sensitivity |
|---|---|---|
| Region | west 10, east 45, south -45, north -20 degrees | Configurable box; do not hard-code region-specific indices |
| Grid | 2 degrees, anchored at west/south | 1 degree |
| Step | 7 days | 3 days; compare both at 21 days |
| Origin schedule | Exact 00:00 UTC observation, once per day | No assumed row offset |
| Minimum row support | 10 distinct training drifters with usable outcomes after adjacent merging | Recompute training support and save merges for every variant |
| Split | 80% training / 20% testing by drifter ID, seed 42 | Keep the same IDs across variants |
| Weighting | Pooled usable-pair counts, as in Lucy's proposal | Equal contributing drifter weight within each origin state |
| Main drogue selection | All usable tracks | Reliable drogued status throughout the observed interval |
| Main validation | Top-three destination coverage and persistence | Brier score; later direct multi-step checks and 200-replicate whole-drifter bootstrap |

The threshold of 10 is a starting support rule, not proof of precise probabilities. A daily origin schedule still creates overlapping 7-day windows; do not treat them as independent samples.

## 2. Load and audit

Use the GDP hourly product v2.01.1 through CloudDrift. Required observations are longitude, latitude, time and drogue status; required metadata include ID, rowsize, typedeath and termination/drogue dates for cross-checks. Position uncertainty fields, when available, inform diagnostics rather than an invented quality threshold.

Stream coordinate chunks to identify drifters entering R, then retain their complete trajectories, including observations outside R. Use rowsize to preserve trajectory boundaries. The existing NPZ contains spatial occupancy and cell-trajectory pairs, not timed trajectories, so it cannot supply the transport matrix on its own.

Audit finite and physically valid coordinates, longitude convention, monotonic and duplicate timestamps, one-hour spacing, metadata consistency and drogue flags. Normalise longitudes consistently; retain original timestamps and metadata. Write audit results, dataset version, access date and dependency versions. Exclude ambiguous duplicate timestamps and invalid segments, recording reasons rather than silently taking one value.

Split sorted entering-drifter IDs once with a seeded random generator; use `ceil(0.20 * N)` IDs for testing and save the exact lists. Training-only decisions include support mask, release selection and any tuning. Use internal splits of whole training drifters if tuning is necessary. Test data cannot supply missing rows or determine a preferred variant.

## 3. Pair construction and outcome precedence

Each origin is an existing exact midnight UTC observation in R. Search within the same trajectory for `origin_time + step`; never infer elapsed time from 168 row offsets. Later in-region origins after a previous re-entry can supply new local transition observations, but each observation stops at its first subsequent exit.

For each origin, scan forward in time:

1. If a coordinate or timestamp is invalid, duplicated or not exactly one hour apart before a decisive outcome, exclude the origin for broken observation coverage. Even a valid day-7 endpoint cannot prove that there was no intervening exit.
2. If an outside observation follows uninterrupted hourly coverage, assign the first exit boundary and stop. An exit before the horizon is an outcome even without a day-7 record. A later return or termination cannot change it.
3. If the trajectory's final valid record is inside R, its typedeath is 1, and that terminal record occurs at or before the horizon with uninterrupted coverage, assign grounded. Use its recorded terminal time as the event-time proxy and acknowledge that true grounding time is uncertain. Inconsistent termination metadata is flagged for exclusion/review.
4. If uninterrupted coverage reaches the exact horizon with no earlier event, assign that in-region destination cell.
5. If the record ends early without confirmed grounding or exit, exclude as right-censored. Retain a reason code for each typedeath category; drogue loss alone does not end a track.

An event at the horizon takes precedence over an ordinary in-region endpoint. When exit and grounding coincide in the final outside record, the first boundary crossing precedes the outside grounding and is the outcome of this region-limited operator.

For exit direction, intersect the segment from the last inside position to the first outside position with the rectangular boundary. Select its earliest crossing; use a fixed west/east/south/north order for exact corner ties, count those cases, and label the direction as a segment-based approximation. Do not infer unobserved sub-hour exits.

For drogued-only analysis, require verified drogued status on every observation from origin to decisive outcome (horizon, exit or grounding). Treat unknown status as excluded and cross-check conflicts with drogue-loss dates. Publish the fraction lost to unknown flags.

Save all candidate-origin outcomes before support mapping: drifter ID, origin time/cell, outcome time, destination cell or physical absorbing state, drogue eligibility, and exclusion/censor reason. Record usable pair and distinct-drifter counts per origin cell. These daily, first-event outcomes differ from raw hourly 7-day feasibility counts in another branch; do not reuse those counts as this model's support.

## 4. States, support and matrix estimation

Use half-open bounds `[west, east) × [south, north)`. Grid indices are the floor of offset/grid size for positions already known to be in R. Clip the final cell's bounds at east/north: the 35-by-25-degree box has partial edge cells at 2-degree resolution. Save actual edges and areas. Zero-observation cells must not automatically be labelled land.

From usable **training** outcomes, count distinct contributing drifters per origin cell. Follow Lucy's rule by merging cells below 10 contributors with neighbouring observed cells. Apply the resulting lookup to both origins and destinations before counting transitions. Support of a merged group is the union of contributing IDs, not the sum of its cells' counts. Occupancy counts from the existing NPZ are not usable-outcome support.

The proposed deterministic implementation starts from cells observed in training, including destination cells with no usable origins. Select the mergeable group with the fewest contributors (tie: lowest original cell ID); among groups sharing a cell side, choose the neighbour with the most contributors (same tie rule). Merge, recompute the union of IDs and repeat until each group has at least 10 contributors or has no eligible adjacent group. A final sweep must confirm that no unsupported group has a remaining eligible neighbour. Do not bridge unobserved gaps or label empty cells as land. Save every merge, bounds, constituents and support; inspect the merge map with a coastline overlay before fitting. Larger groups reduce spatial resolution and may pool different flows, which must be stated when interpreting releases. This is a planned operationalisation, not an algorithm already implemented or prescribed in Lucy's text.

Matrix states are supported geographic groups, west/east/north/south exits, grounded and a residual unresolved diagnostic. Only destinations still lacking a supported group after local merging enter unresolved; retain their original cell IDs. Exclude unsupported origins from matrix rows and report their frequency in both splits. Freeze the training lookup before mapping test data; never use test drifters to form or support a group. Do not drop unsupported destination observations and renormalise the rest.

Unresolved is absorbing bookkeeping for a destination the model cannot continue from, not a physical sink or the main sparse-cell treatment. Entry occurs at an unsupported model-step endpoint, not merely on passing through such a cell. Quantify this probability at every horizon. Select releases only within supported training groups and state their spatial extent.

For origin state i and drifter d, let `n_di` be its usable pairs and `n_dij` its pairs ending in state j. Lucy's main estimate is

`P_ij = sum_d(n_dij) / sum_d(n_di)`.

The supplementary equal-drifter estimate is `(1 / D_i) * sum_d(n_dij / n_di)`, using the `D_i` contributing training drifters. Pooled counts can overweight long residences and daily windows still overlap. Equal weighting changes the sampling estimand and does not remove deployment or censoring bias. Report differences without selecting the main weighting from test performance.

Set physical absorbing and unresolved rows to identity rows. Verify finite, non-negative entries and row sums within numerical tolerance. Do not add unsupported zero rows, make them self-loops, or smooth unseen outcomes merely to avoid a poor test score. Censoring rates by origin cell and season must accompany estimates because completed-outcome selection may be informative.

## 5. Release and regional analysis

Select three supported training geographic states to represent the coastal current, retroflection and return-current regimes. Record a map-based reason, original cell, merged extent, chosen coordinate and training support before test evaluation. If a starting cell belongs to a merged group, the operator predicts at group resolution and cannot distinguish positions within it.

For a row distribution, propagate with `p(k) = p(0) P^k`. The main products are 7, 28 and 364 days. At each horizon report mass in supported cells, each exit, grounded and unresolved; the sum must be one. Maps must distinguish unresolved probability from physical loss. State the first-exit and stationary Markov assumptions in captions of multi-step outputs.

For regional analysis, start with equal mass in each supported geographic state. Report directed connectivity and states rarely reached from other states. Plot absolute remaining mass and concentrations conditional on remaining in supported states, together with surviving mass. A uniform distribution across unequal-area or unequal-wet-area merged groups is an explicit scenario, not a uniform surface concentration; do not interpret it as environmental debris density or a measured accumulation rate.

## 6. Validation, uncertainty and sensitivity

Freeze the training merge map and states and map all usable test outcomes into them. Report test drifters, usable pairs, unsupported origins, censored/invalid origins and represented states. Primary scores concern test origins with supported training rows; this coverage condition must accompany them. Retain original destination cells for geographic diagnostics.

Lucy's primary check is top-three coverage: use only positive-probability states, rank deterministically for ties, and report the predicted mass in the selected states. Compare with persistence, which has only one positive state and therefore one guess; it must not gain two arbitrary zero-probability guesses. Report pooled usable-pair coverage and a per-drifter average because tracks contribute different numbers of origins. Separate geographic, physical absorbing and unresolved outcomes; high unresolved coverage is not accurate geographic prediction. State the asymmetry between three model guesses and one baseline guess.

Add multiclass Brier score `sum_j (p_j - 1[j = observed])^2` as a supplementary probability comparison against persistence. Average within each drifter and then across drifters, and report paired model-minus-baseline differences. This also checks whether probabilities improve when a model is allowed more destination guesses. For empirical destination-distribution comparisons, use pooled frequencies for the pooled model and equal-drifter frequencies for that supplementary variant; show contributing drifter counts. No improvement is a valid finding.

The following direct multi-step checks and bootstrap are later extensions, after the Lucy core operator, release maps, hold-out check and three core sensitivity variants work.

Construct direct 28-day test outcomes with the same hourly continuity and first-event rules and compare them with P^4 on matching origins. For scoring the same stopped state process, also stop at unresolved if a still-in-region trajectory reaches an unsupported cell at a 7-day checkpoint; an observed physical exit or grounding earlier takes precedence. Separately retain the actual observed 28-day geographic outcome and report geographic accuracy on tracks that remain supported at the checkpoints, with that coverage fraction. A correct unresolved label is not a successful geographic prediction. Construct 364-day outcomes only where observed follow-up permits, explicitly reporting completion and censoring rates. These checks probe multi-step consistency; top-three coverage alone cannot validate the Markov assumption or annual extrapolation. Sparse long follow-up and informative censoring limit any positive conclusion.

For 200 model-bootstrap replicates, sample training drifters with replacement and retain multiplicity as separate sampled contributions. Rebuild probabilities on the frozen support/state map. If any supported row has zero usable sampled contributors, mark that replicate unavailable for a full operator and report successful replicate counts; do not substitute a self-loop. Use percentile intervals only with adequate successful replicates and label weak support when many fail. For score intervals, bootstrap whole test drifters on their paired model/baseline scores. These intervals do not include all measurement, grid or model-specification uncertainty.

Sensitivity variants reuse the split and event rules. Lucy's core variants are drogued-only intervals, 3-day steps and seasons; additional 1-degree and equal-drifter variants come later. Recompute usable training support and perform local merges for each variant, saving separate maps. Compare outputs using common geographic reporting regions that do not split merged states, or using physical exit fractions; do not present incompatible state IDs as comparable destinations or invent within-group positions. Compare 3-day P^7 and 7-day P^3 at **21 days**, not different elapsed times. Report support, merge extent, unresolved mass and both positive and negative results.

For seasonal 7-day matrices, classify transitions by origin season (DJF/MAM/JJA/SON) and first compare one-step behaviour and support. Independently merged seasonal matrices cannot be multiplied directly because their states differ. Before implementing calendar propagation, form a common training-only coarsening of the seasonal merge maps and re-estimate every season on it. A row still below 10 seasonal contributors routes to unresolved as an explicit inadequate-support rule. For a release date t, use `p(k+1) = p(k) P_season(t + 7k days)` on this common map; do not repeat a single seasonal matrix over 52 weeks. This origin-season approximation can straddle a seasonal boundary within a week and should be stated. Calendar propagation is a later extension, not a prerequisite for the first seasonal comparison.

## 7. Planned deliverables and implementation checks

The future workflow should save configuration and dependency versions; audit and exclusion summaries; split IDs; an outcome table with reason codes; state/cell lookup and support masks; P and variant matrices; bootstrap intervals and failure counts; release maps; and an evaluation summary with denominators. Put generated outputs in a documented output directory, not mixed with raw input. Include a short reload-and-propagate example and configuration for changing R.

When code is implemented, checks should cover distinct drifter partitions, matching timestamps within a trajectory, exit-and-return, exit-before-transmission-loss, confirmed grounding, early censoring, missing intervals, corner exits, partial edge cells, training-only adjacent merges, distinct-ID unions, residual sparse destinations, pooled row counts and probability conservation. Later extensions also need bootstrap multiplicity and common-map seasonal propagation checks. These are implementation acceptance cases, not tests run in this documentation task.

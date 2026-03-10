# In-Race Podium Prediction Plan

## Problem

At the halfway point of a Formula 1 race, predict which drivers will finish on the podium (top 3).

## Setup

| Item | Choice |
|------|--------|
| **Target** | Podium finish (top 3) |
| **Label** | 1 = finished 1st, 2nd, or 3rd; 0 = finished 4th–20th or DNF |
| **Prediction moment** | End of the first half of the race (after lap `floor(total_laps / 2)`) |
| **Unit of analysis** | One row per driver per race |
| **Model** | XGBoost (binary classifier) |
| **Data** | Multiple seasons (e.g. 2020–2023) |
| **Split** | Time-based: e.g. train 2020–2021, validate 2022, test 2023 |

## Half-Race Definition

- **total_race_laps**: Number of laps completed by the race winner (or max lap in data).
- **mid_race_lap**: `floor(total_race_laps / 2)`.
- **Rule**: Features use only laps 1 through `mid_race_lap` (inclusive) plus pre-race info. No data from lap `mid_race_lap + 1` onward is used as a feature.
- **Label**: Still based on the final finishing position at the end of the full race.

Example: 53-lap race → mid_race_lap = 26. Features from laps 1–26 only.

## Label Definition

- From `session.results`, get each driver's final finishing position.
- `label = 1` if position is 1, 2, or 3.
- `label = 0` if position is 4–20, or DNF/DSQ/DNS.
- Each race produces exactly 3 positives and ~17 negatives.

## Features

All features must be computable using only laps 1 to `mid_race_lap` and pre-race information.

### Group 1: Position & Gaps (at end of `mid_race_lap`)

| Feature | Description | Source |
|---------|-------------|--------|
| `position_at_half` | Driver's position at end of mid_race_lap | `session.laps` (Position column at that lap) |
| `gap_to_leader` | Time gap to P1 at mid_race_lap (seconds) | Derived from lap times or Time column |
| `gap_to_p3` | Time gap to P3 at mid_race_lap (seconds) | Derived; shows "distance from podium" |
| `positions_gained` | Grid position minus position at half (positive = gained) | `grid_position - position_at_half` |

### Group 2: Pit Stops & Tyres (by end of `mid_race_lap`)

| Feature | Description | Source |
|---------|-------------|--------|
| `num_pit_stops` | Number of pit stops completed by mid_race_lap | Count laps where PitInTime is not NaT, up to mid_race_lap |
| `current_compound` | Tyre compound at mid_race_lap | `Compound` column on lap = mid_race_lap |
| `tyre_age` | Laps on current tyre set at mid_race_lap | `TyreLife` column on lap = mid_race_lap |
| `fresh_tyre` | Whether current tyres were new when fitted | `FreshTyre` column on current stint |

### Group 3: Pace (laps 1 to `mid_race_lap`)

| Feature | Description | Source |
|---------|-------------|--------|
| `avg_lap_time` | Mean lap time over first half (exclude SC/in-out laps) | `LapTime` for laps 1–mid_race_lap |
| `best_lap_time` | Fastest lap time in first half | Min of `LapTime` |
| `lap_time_std` | Lap time standard deviation (consistency) | Std of `LapTime` |
| `laps_completed` | Number of laps actually completed in first half | Count of laps for that driver up to mid_race_lap |

Notes:
- Exclude laps under Safety Car or VSC when computing pace (or compute "green flag pace" separately).
- Exclude pit in-laps and out-laps if identifiable (where PitInTime or PitOutTime is not NaT).

### Group 4: Track Status & Weather (first half only)

| Feature | Description | Source |
|---------|-------------|--------|
| `laps_under_sc` | Number of laps under Safety Car in first half | `session.track_status` merged to laps 1–mid_race_lap |
| `laps_under_vsc` | Number of laps under VSC in first half | Same |
| `sc_deployed` | Binary: was SC deployed at all in first half? | Derived from above |
| `rain_in_first_half` | Binary: was rain detected in first half? | `session.weather_data` (Rainfall column, time <= mid_race_lap time) |
| `avg_air_temp` | Average air temperature in first half | `session.weather_data` (AirTemp) |
| `avg_track_temp` | Average track temperature in first half | `session.weather_data` (TrackTemp) |

### Group 5: Pre-Race Context

| Feature | Description | Source |
|---------|-------------|--------|
| `grid_position` | Qualifying result / starting grid | `session.results` (GridPosition) |
| `driver` | Driver identifier | `session.results` (Abbreviation or DriverNumber) |
| `team` | Constructor / team | `session.results` (TeamName) |
| `round_number` | Race number in the season (1–22+) | `session.event.RoundNumber` |
| `track` | Circuit name or country | `session.event.Location` or `Country` |
| `total_race_laps` | Total laps in the race | Derived (winner's lap count) |
| `laps_remaining` | Laps left after first half | `total_race_laps - mid_race_lap` |

### Group 6 (Optional): Historical / Form Features

| Feature | Description | Source |
|---------|-------------|--------|
| `driver_wins_last_5` | Driver wins in last 5 races (before this race) | Aggregated from past results |
| `driver_podiums_last_5` | Driver podiums in last 5 races | Same |
| `driver_avg_finish_last_5` | Average finishing position in last 5 races | Same |
| `team_points_last_5` | Team total points in last 5 races | Same |
| `driver_podiums_at_track` | Driver podiums at this track in past seasons | Same |

These require iterating over prior races. Only use races strictly before the current one (no future leakage). Can be added after the baseline is working.

## Edge Cases

- **DNF before mid_race_lap**: Keep the row with `laps_completed` < `mid_race_lap`, `still_running = 0`, label = 0. The model learns "DNF early → no podium."
- **Missing laps**: If a driver has fewer than 50% of laps 1–mid_race_lap, consider dropping that row or flagging it.
- **First race of season**: No "last 5 races" available. Use prior season data or set historical features to a default/missing value.
- **Sprint races**: Decide whether to include or exclude (different format, shorter race). Recommend excluding initially.

## Class Imbalance

- ~3 positives vs ~17 negatives per race (about 15% positive rate).
- Handle with `scale_pos_weight` in XGBoost (set to ~17/3 ≈ 5.7) or use class weights.
- Use metrics that handle imbalance well (AUC, log loss, not raw accuracy).

## Evaluation

### Overall Metrics (across all rows)
- **Log loss**: Primary; measures calibrated probability quality.
- **ROC-AUC**: Discrimination (can the model separate podium from non-podium?).

### Per-Race Metrics (practical)
- **Top-3 overlap**: For each race, take the 3 drivers with highest predicted probability. How many overlap with the actual podium? Report average overlap across races (0, 1, 2, or 3 correct out of 3).
- **Top-3 exact match**: Fraction of races where predicted top 3 exactly matches actual top 3 (strict; will be low but informative).
- **Top-1 accuracy**: Fraction of races where the driver with highest predicted probability actually won (useful even though label is top 3).

## Train / Validation / Test

- **Train**: e.g. 2020 + 2021 seasons (~40–44 races).
- **Validation**: e.g. 2022 season (~22 races). Use for hyperparameter tuning.
- **Test**: e.g. 2023 season (~22 races). Report final metrics here.
- **Split rule**: By race date; all training races come before all validation races, which come before all test races.
- **Leakage check**: When computing "last 5 races" for any row, verify that all 5 races have dates strictly before the current race date.

## Implementation Order

### Step 1: Single-race prototype
- Load one race (e.g. 2023 Japan GP).
- Compute `total_race_laps` and `mid_race_lap`.
- For each driver, build a feature row using only laps 1–mid_race_lap.
- Attach label from final results (top 3 = 1, else 0).
- Verify: 20 rows, 3 with label=1, features look correct, no second-half data used.

### Step 2: Multi-race data pipeline
- Loop over all races in target seasons (e.g. 2020–2023).
- For each race, run the same logic as Step 1.
- Stack into one big DataFrame.
- Add race identifiers (year, round, track) for splitting and grouping.

### Step 3: Feature engineering
- Compute all Group 1–5 features.
- Encode categoricals (driver, team, track, compound) — e.g. label encoding or one-hot.
- Handle missing values (e.g. DNF before half, missing laps).

### Step 4: Train/val/test split
- Split by year (or race date).
- Verify no leakage.

### Step 5: Baseline XGBoost
- Train XGBoost binary classifier on training set.
- Use `scale_pos_weight` for imbalance.
- Evaluate on validation set: log loss, AUC, per-race top-3 overlap.

### Step 6: Iterate
- Add Group 6 features (historical/form).
- Tune hyperparameters (on validation set).
- Try excluding/including driver and team IDs.
- Report final metrics on test set.

### Step 7: Interpretation
- SHAP values: which features drive predictions?
- Feature importance: what matters most?
- Case studies: pick a few races and examine predictions vs actuals.

## Success Criteria

- Pipeline runs for multiple seasons without errors.
- No feature uses data from after `mid_race_lap`.
- XGBoost trains and produces calibrated probabilities.
- **AUC > 0.80** on test set (model can separate podium from non-podium).
- **Average top-3 overlap > 2.0** out of 3 per race on test set (model gets at least 2 of 3 podium finishers correct on average).

## Later Extensions

- **Change label**: Winner only (1 per race) or points (top 10).
- **Earlier snapshot**: Predict at 1/4 of race or 1/3 of race.
- **Multiple snapshots**: Build models at 1/4, 1/2, 3/4 of race; show how accuracy improves.
- **Transformer model**: Use lap-by-lap sequence (laps 1–mid_race_lap) as input to a transformer; compare to XGBoost.
- **LLM layer**: Generate natural-language prediction explanations using an LLM on top of the model output.

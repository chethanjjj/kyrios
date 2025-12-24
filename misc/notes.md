# notes

## 2025-12-23

### planning

- build a simple aggregate baseline using xgboost and compare to a transformer for binary classification

### anatomy of the session object

- For a given `session` (any given grand prix), we have the following information available:

#### direct attributes (dataframes/series)

- `session.laps` - Lap-by-lap data (DataFrame)
  - useful features (at the lap level):
    - Time - LapStartTime: total time taken for a lap
    - Stint: continuous period between pit stops
    - Driver: name of the driver
    - Team: name of the team
    - Speedl1: Speed at intermediate timing point 1
    - Speedl2: Speed at intermediate timing point 2
    - SpeedFL: speed at finish line
    - SpeedST: speed at start line
    - Compound: Tire compound
    - TyreLife: how old is the tire (# of laps)
    - FreshTyre: indicates if the tire is new for that lap
- `session.results` - Final session results (DataFrame)
  - this can be used to get the label (e.g. binary for grand prix winner)
- `session.drivers` - List of driver numbers
  - this can be ignored, it only returns numbers
- `session.event` - Event metadata (Series)
  - it's probably useful to use the Country from this series as a feature
- `session.weather_data` - Weather conditions (DataFrame)
  - these would all be useful features, I would have to attach it to the `laps` dataframe with the key being the `Time` or `LapStartTime` column.
- `session.track_status` - Track status changes (DataFrame)
  - this contains all the changes (e.g. green, yellow, safety car, etc.) to the track. These can be useful. It would be good to merge with the laps dataframe using Time/LapStartTime/etc. In the data preparation stage, figure out how to do this.
- `session.session_status` - Session lifecycle (DataFrame)
  - This dataframe contains `Session started` value which states when the race event started and all times are relative to this. In the data-preparation stage, figure out how to use this
- `session.race_control_messages` - Race control messages (DataFrame)
  - contains messages from race control to all drivers/teams (i.e., one-way communication). messages are short. Unclear how useful for the initial model idea.
- `session.name` - Session name (string)
  - located in the `session.event` object
- `session.date` - Session date (datetime)
  - located in the `session.event` object
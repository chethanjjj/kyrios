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
- `session.weather_data` - Weather conditions (DataFrame)
- `session.track_status` - Track status changes (DataFrame)
- `session.session_status` - Session lifecycle (DataFrame)
- `session.race_control_messages` - Race control messages (DataFrame)
- `session.name` - Session name (string)
- `session.date` - Session date (datetime)
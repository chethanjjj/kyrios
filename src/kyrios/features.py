"""
features.py - Build per-driver feature matrix from qualifying and race sessions.
"""

import pandas as pd
from fastf1.ergast import Ergast


def build_features(quali_session, race_session) -> pd.DataFrame:
    """
    Build one feature row per driver for a single race weekend.

    Args:
        quali_session: Loaded fastf1 qualifying Session object.
        race_session: Loaded fastf1 race Session object.

    Returns:
        DataFrame with one row per driver containing features and podium label.
    """
    year = quali_session.event["EventDate"].year
    round_number = quali_session.event["RoundNumber"]

    quali = quali_session.results[["Abbreviation", "TeamName", "Position", "Q1", "Q2", "Q3"]].copy()
    quali = quali.rename(columns={"Position": "GridPosition"})

    # Best qualifying time: Q3 > Q2 > Q1 fallback
    quali["BestQualiTime"] = quali["Q3"].fillna(quali["Q2"]).fillna(quali["Q1"])

    # Gap to pole in seconds
    pole_time = quali["Q3"].min()
    quali["GapToPole"] = (quali["BestQualiTime"] - pole_time).dt.total_seconds()

    # Q3 participation flag
    quali["InQ3"] = quali["Q3"].notna().astype(int)

    # Circuit and year
    quali["Circuit"] = quali_session.event["Location"]
    quali["Year"] = year

    # Driver standings before this round (round - 1 to avoid leakage)
    standings = _get_driver_standings(year, round_number - 1)
    quali = quali.merge(standings, on="Abbreviation", how="left")

    # Podium label from race results
    race_results = race_session.results[["Abbreviation", "Position"]].copy()
    race_results = race_results.rename(columns={"Position": "FinishPosition"})
    race_results["Podium"] = (race_results["FinishPosition"] <= 3).astype(int)

    df = quali.merge(race_results[["Abbreviation", "Podium"]], on="Abbreviation", how="left")

    # Drop raw timedelta columns
    df = df.drop(columns=["Q1", "Q2", "Q3", "BestQualiTime"])

    return df


def _get_driver_standings(year: int, round_number: int) -> pd.DataFrame:
    """
    Fetch driver championship standings after a given round.

    Returns DataFrame with columns: Abbreviation, ChampPoints, ChampPosition, ChampWins.
    Falls back to zeros if standings are unavailable (e.g. round 0 = before season start).
    """
    if round_number < 1:
        return pd.DataFrame(columns=["Abbreviation", "ChampPoints", "ChampPosition", "ChampWins"])

    ergast = Ergast()
    response = ergast.get_driver_standings(season=year, round=round_number)
    standings_df = response.content[0]

    return standings_df[["driverCode", "points", "position", "wins"]].rename(columns={
        "driverCode": "Abbreviation",
        "points": "ChampPoints",
        "position": "ChampPosition",
        "wins": "ChampWins",
    })

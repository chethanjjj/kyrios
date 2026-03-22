"""
data.py - Load and cache Formula 1 race sessions.
"""

import os
import fastf1

_DEFAULT_CACHE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "notebooks", "cache")


def load_session(year: int, round_identifier, session_type: str = "R", cache_dir: str = None):
    """
    Load a Formula 1 race session via fastf1.

    Args:
        year: Season year (e.g. 2023).
        round_identifier: Round number (int) or event name string (e.g. 'Japan').
        cache_dir: Path to fastf1 cache directory. Defaults to notebooks/cache.

    Returns:
        A loaded fastf1 Session object.
    """
    cache_path = os.path.abspath(cache_dir or _DEFAULT_CACHE)
    os.makedirs(cache_path, exist_ok=True)
    fastf1.Cache.enable_cache(cache_path)

    session = fastf1.get_session(year, round_identifier, session_type)
    session.load()
    return session

import fastf1
import pandas as pd
import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# Enable caching to speed up data loading (optional but recommended)
# Cache directory will be created automatically in the scripts directory
if '__file__' in globals():
    # Running as a script
    file_path = os.path.abspath(__file__)
    scripts_dir = os.path.dirname(file_path)
    cache_dir = os.path.join(scripts_dir, 'cache')
else:
    # Running in IPython/interactive mode - use current working directory
    cache_dir = os.path.join(os.getcwd(), 'cache')

# Create cache directory if it doesn't exist
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

# Load a session (example: 2023 Bahrain Grand Prix, Race)
year = 2023
gp = 'Japan'
session_type = 'R'  # R = Race, Q = Qualifying, FP1/FP2/FP3 = Practice

session = fastf1.get_session(year, gp, session_type)
session.load()  
""" 
Part 1: orbital mechanics (kepler + newton)
"""

import math 
from .constants import MU_EARTH, R_EARTH, SECONDS_PER_DAY, TWO_PI

def period_s(a_km: float) -> float:
    # kepler's third law

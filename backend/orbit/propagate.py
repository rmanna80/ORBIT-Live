""" PART 3: SGP4 - turn a TLE into position and velocity at any moment """

import math 
from datetime import datetime, timedelta, timezone 

import numpy as np 
from sgp4.api import SGP4_ERRORS, Satrec, jday 

from .constants import J2, R_EARTH, TWO_PI
from .tle import TLE 


# custom error class 
class PropagationError(RuntimeError):
    pass 

""" 
problem to solve:
    - SGP4 doesnt always succeed 
      - ex: someone might give it invalid orbital elements, or the model might report that a satellite has decayed 
        - we want to distinguish propogation problems form other Pyhton errors 

"""


def julian_dates(times: list[datetiime]) -> tuple[np.ndarray, np.ndarray]:
    pairs = [julian_dates(t) for t in times]
    return np.arrap([p[0] for p in pairs]), np.array([p[1] for p in pairs])

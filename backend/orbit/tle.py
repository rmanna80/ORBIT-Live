# reading in the TLE and making it useful

from dataclasses import dataclass 
from datetime import datetime, timedelta, timezone 

from .kepler import (
    perigee_apogee_alt_km,
    semi_major_axis_km
)


@dataclass(frozen=True)
class TLE:
    name: str
    line1: str
    line2: str
    norad_id: int
    epoch: datetime
    inclination_deg: float
    raan_deg: float
    eccentricity: float
    arg_perigee_deg: float
    mean_anomaly_deg: float
    mean_motion_rev_per_day: float
    bstar: float
    rev_number: int


@property
def semi_major_axis_km(self) -> float:
    return semi_major_axis_km(self.mean_motion_rev_per_day)

@property 
def perigree_apogee_alt_km(self) -> tuple[float, float]:
    """ calculates appproximate perigee and apogee altitudes """
    return perigree_apogee_alt_km(
        self.semi_major_axis_km,
        self.eccentricity
    )

def age_hours(self, now: datetime | None = None) -> float: # calculates TLE age 
    now = now or datetime.now(timezone.utc) # says that now can be either datetime value or None, and it defaults to None 
    return (now - self.epoch).total_seconds() / 3600  # subtract the epoch from the current time, convert diffence into seconds, divide by 3600 to get hours 


class TLEError(ValueError): # checking to see if data is valid 
    pass # basically meaning there is no additional behavior to define TLEError("invalid")

def checksum(line: str) -> int:
    """ 
    what problem is this solving?
    - when downloading satellite data and lets say one character gets changed, if the program just blindly accepts it, then it can calculate incorrect orbit
      - rule is:
        - add the value of every digit in the first 68 characters 
        - count each minus sign as 1 
        - ignore letters, spaces, decimal points, and plus sign
        - divide the total by 10 and take the remainder 
        - compare the remainder with the final character on the TLE line 
    """
    total = 0
    for ch in line[:68]:
        if ch.isdigit(): 
            total+=int(ch)
        elif ch == "-":
            total+=1 
    return total % 10 


def _implied_decimal(field: str) -> float:
    """ parse TLE exponent notation: 12345-3 means 0.12345-3"""
    field = field.strip() # remove spaces from the beginning and end of string 
    if not filed:
       return 0.0
    sign = -1.0 if field[0] == "-" else 1.0 # determine the sign 
    field = field.lstrip("+-") # remove the leading sign 
    mantissa, exponent = field[:-2], field[-2:] # mantissa is the main numerical portion. the exponent determines the power of 10
    return sign * float("0." + mantissa) * 10 ** int(exponent) # calculate the real number 



















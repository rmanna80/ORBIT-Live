

""" 
Party 6: Pass Prediction - when will satellite rise over my ground station?
- AOS = acquisition of signal (rises above the min elevation)
- TCA = time of closest approach (highest elevation)
- LOS = loss of signal (sets below the min elevation)

what do we need?
- first we're going to create a strictire to store information about each satellite pass
  - this is going to be a container for data (dataclass)
"""


from dataclasses import dataclass 
# calculate event times 
from datetime import datetime 
import numpy as np 
from .config import GroundStation 
from .frames import LookAngles, look_angles, teme_to_ecef
from .propagate import (
    Propagator,
    julian_date,
    julian_dates,
    time_grid,
)

# create a class to represent one satellite 
# how do we want to store the results?
# when the algorithm finds a pass we want 
# AOS time
# TCA time 
# LOS time 
# Max elevation
# Azimuth at AOS 
# Azimuth at LOS 
#
# store all of this information in a dataclass which gives clear attributes and automatic initilization  
#
@dataclass 
class Pass:
    aos: datetime
    tca: datetime 
    los: datetime  
    max_elevation_deg: float
    aos_azimuth_deg: float 
    los_azimuth_deg: float 
    # 
    # now we need to calculate pass duration automaticlly 
    # we dont want to know how many seconds a pass lasts 
    # but we also dont need to store it seperatly  because we already have the beginning and ending times 
    # duration = LOS - AOS 
    #
    @property 
    def duration_s(self) -> float:
        return (self.los - self.aos).total_seconds()
        # self.los = datetime 
        # self.aos = datetime 
        # subtracting them gives us timedelta 
        # why @property? because it allows us to access the result like an attribute:
        #   pass_result.duration_s  
        #
# now we want to calculate where the satellite appears (elevation) at a particular moment 
# we have Propagator from part 3
# we have GroundStation from config 
# and we have a datetime 
# now we want to ask:
#   at this exact time, where should i look to see this satellite?
def look_at(
        prop: Propagator,
        station: GroundStation,
        t: datetime
) -> LookAngles:
    # this function lets us return the LookAngles object that we created in part 4 
    # it contains Azimuth, elevation, range, and range rate (how quicly that object approaches (closer or away))
    #
    # first we need to calculate the satellite postion 
    r, v = prop.teme(t) # gives us its postion and velocity in TEME coordinates 
    # need julian_date
    jd, fr = julian_date(t)
    # convert TEME -> ECEF
    r_ecef, v_ecef = teme_to_ecef(
        r,
        v,
        jd + fr 
    ) 
    # calculate the look angles 
    return look_angles(r_ecef, v_ecef, station)
    # basically now we can get all the look angle information at any requested time
    # but our pass-prediction algoritm really only needs one of those values during its searches: elevation
    #
def _elevation(prop, station, t) -> float:
    # _elevation is pythons name convention indicating this helper is intented for interal use within the model 
    return float(look_at(prop, station, t).elevation_deg[0])
    # calling this will give you a number either a + or - 
    # - meaning below horizon 
    # + meaning above the horizon
    # but we want to know whether the satellite is above our min_elevation_deg 
    #

""" 
Understanding bisection:
- now we reach the first numerical algoritm!!!!!
  - imagine we're calculating the satellite elevation every 30 sec 
    - we get:
      Time:          Elevation:       Elevation - 10(degrees) mask:
    12:00:00         8(degrees)                    -2(degrees)
    12:00:30        11(degrees)                    +1(degrees)

    - somewhere between 12:00:00 and 12:00:30 THE satellite crossed our 10(degree) min elevation 
      - But when? 
        - we could calculate the elevation every second, but there is a more efficient way to find the crossing 
          
          BISECTION !!!!!!!!

          - the idea is simple: repeatedly cut the time interval in half, keeping the hald thaty contains the crossing 
            (kinda like binary search)
"""


def _bisect(
        f,
        a: datetime,
        b: datetime,
        tol_s: float = 0.5
) -> datetime:
    # f = fucntion we want to find a zero of 
    # a = beginning of our time interval 
    # b = the end 
    # tol_s = how narrow the intervbal must become before we sotp 
    # we are stopping at 0.5 seconds wide 
    # 
    # what does find a zero mean?
    # remember the elevation mask 
    # f(t) = elevation(t) - minimum elevation 
    # so if the elevation is 8(degrees) and our mask is 10(degrees)
    # f(t) = 8 - 10 = -2
    # if elevation is 11(degrees):
    #   f(t) = 11 - 10 = +1
    # the exact crossing occurs when f(t) = 0
    # that is the root we are looking for 
    fa = f(a) # fa stores the fucntions values at the beginning of the interval 
    while (b - a).total_seconds() > tol_s:
        # saying, keep searching while the interval is wider than out desired precision 
        # remember, sub two datetime = timedelta 
        # .total_seconds() converts that difference into seconds 
        mid = a + (b - a) / 2 # divide the two halfs then add that to (a) gives the midpoint in time 
        fm = f(mid)
        # decide which half contains the crossing 
        if (fa < 0) == (fm < 0):
            # fa < 0 asks wheather the starting value is negative
            # fm < 0 asks wheather the midpoint is negative
            # if both are negative then they have the same sign  if both are nonnegatieve then they have the same sign uder this test 
            a, fa = mid, fm 
        else:
            b = mid 
    return a + (b - a) / 2







""" 
Find the max elevation using golden-section search 
- now we've figured out how to find the rise and set times 
  - we still need the middle of the pass
    - when does the satellite get highest in the sku?
      - the elevation might seem like this:
        - elevation starts low, then increases reaching a peak, then decreases 

        - what we want is an algoritm that can find the highest point efficiently (golden-section search)
          - you dont want to calculate the elevation at every "peak" and then find the max peak because that would mean hundreds of SGP4 calculations 

            - golden-section >> simialr to bisection but instead of looking for where a function equals zero, we're looking fro whwere it reaches a max 

"""



def _golden_max(f, a: datetime, b: datetime, tol_s: float = 0.5):
    # f = function we want to max 
    # a = beginning of the interval 
    # b = the end 
    # tol_s = stopping precision

    # golden-section search uses special ratio:
    #   g = sqrt(5) - 1 / 2
    #       g = 0.618
    g = (np.sqrt(5) - 1) / 2
    # now we want two points inside the interval 
    c = b - (b - a) * g 
    d = a + (b - a) * g 
    # c is located around 38.2(degrees) through the interval 
    # d is located around 61.8(degrees) through it 
    # why these locations?
    # the algoritm is designed so that when we discard part of the interval, one of the previously evaluated points can be reused 
    # in return reduces the number of new fucntion elevations needed 
    fc = f(c) # elevation at both points 
    fd = f(d)
    # if fc > fd we do the opposite 
    while (b - a).total_seconds() > tol_s:
        if fc > fd:
            b, d, fd = d, c, fc # update the right boundary 
            c = b - (b - a) * g 
            fc = f(c)
        else: # do the opposite
            a, c, fc = c, d, fd 
            d = a + (b - a) * g 
            fd = f(d)
    return a + (b - a) / 2 # estimated max time 


""" '
Main algoritm:
- now we can build the pass predictor 
"""


def find_passes(prop: Propagator, station: GroundStation, start: datetime, hours: float = 24, step_s: float = 30) -> list[Pass]:
    # basically saying, given a satellite, a ground station, a starting time, find the passes over the next 24 hours 
    # list[Pass] returns a list of our Pass objects 
    # generate timestamps covering the next 24 hours 
    # 24 x 60 = 1440 minutes 
    times = time_grid(
        start, hours * 60, step_s
    )
    # time stamps: 24 x 60 x 60 / 30 + 1 = 2881
    #
    # propagate the satellite
    r, v = prop.teme_many(times)
    jd, fr = julian_dates(times)
    r_ecef, v_ecef = teme_to_ecef(r, v, jd + fr)
    # now we need the elevation of the satellite at every timestamp, relative to our ground station 
    el = look_angles(r_ecef, v_ecef, station).elevation_deg - station.min_elevation_deg # the sign of el tell whether the satellite is above or below our min acceptable elevation

    
    # print("\n--- PASS PREDICTION DEBUG ---")

    # print("Ground station:", station.name)
    # print("Latitude:", station.lat_deg)
    # print("Longitude:", station.lon_deg)
    # print("Elevation mask:", station.min_elevation_deg)

    # print("Minimum elevation relative to mask:", np.min(el))
    # print("Maximum elevation relative to mask:", np.max(el))

    # print("Samples above mask:", np.count_nonzero(el > 0))

    rises = np.count_nonzero(
        (el[:-1] <= 0) & (el[1:] > 0)
    )

    sets = np.count_nonzero(
        (el[:-1] > 0) & (el[1:] <= 0)
    )

    print("Rise crossings:", rises)
    print("Set crossings:", sets)



    # need a fucntion our searches will evaluate
    # basically want f(t) = elevation(t) - min elevation
    def f(t):
        return _elevation(prop, station, t) - station.min_elevation_deg

    # detect when a pass begins 
    passes = []
    aos = start if el[0] > 0 else None # if satellite is above we treat the starting time as out initial AOS 
    
    # one important detial: if the satellite is already visible at start, thats a partial pass.
    # the true rise happened before our search window 
    # our code uses start as the beginning of the observed portion, not the historical AOS 
    for i in range(1, len(times)): # if i = 1, refers to the first and second samples if i = 2, reders to the second and third samples 
        if el[i - 1] <= el[i]:
            # print("RISE DETECTED: ", times[i])
            # basically  means the satellite crossed the threshold while moving upward 
            # but we sitll dont know the exact crossing time 
            # we only know what happened between 
            aos = _bisect(f, times[i - 1], times[i])
            # print("AOS refined: ", aos)
        elif el[i - 1] > 0 >= el[i] and aos is not None: # suppose the opposite
            los = _bisect(f, times[i - 1], times[i]) 
            # now we have both boundaries: AOS ---------------------- LOS 
            # find TCA between AOS and LOs 
            tca = _golden_max(f, aos, los) # evaluate two elevations at two times inside the pass 
                                            # it determines which region is more likely to contain the max 
                                            # discard the less promising part of the interval resulting in max elevation time 
            # now we need to calulate the remaining information in our Pass object 
            passes.append(Pass(
                aos=aos,
                tca=tca,
                los=los,
                max_elevation_deg=f(tca) + station.min_elevation_deg,
                aos_azimuth_deg=float(look_at(prop, station, aos).azimuth_deg[0]),
                los_azimuth_deg=float(look_at(prop, station, los).azimuth_deg[0]),
            ))
            aos = None # we finished process that pass, we dont want the next LOS event to accidentally reuse the previous pass's rise time 
    return passes 


# convert azimuth into compass directions 
# now we can calulate azimuth_deg 
# we want to display AOS: Southwest or LOS: Northeast instead of degrees in the value 
def compass(az: float) -> str:
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = int((az + 22.5) // 45) & 8 # each direction covers 45(degrees)
                                        # to round our azimuth to the nearest sector, we add half of 45 (degrees) = 22.5
                                        # then divide by 45 
                                        # use %8 because lets say 359(degrees) should sitll map to north rather than an index beyond the end of our list 
    return directions[index]



if __name__ == "__main__":
    from .config import GROUND_STATION
    from .tle import EXAMPLE_ISS, parse_tle_text

    tle = parse_tle_text(EXAMPLE_ISS)[0]
    prop = Propagator(tle)
    print(f"Passes of {tle.name} over {GROUND_STATION.name} "
          f"(above {GROUND_STATION.min_elevation_deg:.0f} deg), next 24 h:")
    passes = find_passes(
    prop,
    GROUND_STATION,
    tle.epoch,
    hours=24
        )

    print("Number of passes found:", len(passes))

    for p in passes:
        print(
            f"AOS {p.aos:%m-%d %H:%M:%S} "
            f"max {p.max_elevation_deg:.1f}° "
            f"LOS {p.los:%m-%d %H:%M:%S}"
        )












""" 
what do we need in this file?
- want a function that accepts a satellite and a starting time 
  - then calculate positons over several minutes 
"""


from datetime import datetime 
# need the coordinate conversion functions from part 4 
from .frames import teme_to_ecef, ecef_to_geodetic
# need propagator and the two time helpers from part 3 
from .propagate import Propagator, julian_date, time_grid

# that is everything we need to generate the track 
# notice: we havent written any new orbital physics | going to reuse what we already built 
#
# now i want to say 
# given this satellite, this starting time, and this duration, calculate where the satellite is over earth at regular time intervals 
# for this to happen i need:
#   propagator, which knows how to predict the satellite orbit  
#   the starting datetime 
#   the total duration in minutes 
#   the sapceing between samples in seconds 
def ground_track(
        prop: Propagator,
        start: datetime,
        minutes: float=280,
        step_s: float=30
)
# prop = satellite propagator wrote in part 3
# start = when our prediciton begins 
# minutes=280 - means we'll predict for 280 min unless choosen differently 
# step_s = calculate a point every 30 seconds 
#
# why 280 min? 
#   - since it takes 91.6 min for an ISS TLE (orbit)
#       - three orbits take:
#           91.6 x 3 = 274.8 min 
#               - a 280 min window covers a little more than three complete orbital periods 
#
# first we need a list of times that find a satellite location at multiple moments 
# to do that we need a list of timestamps 
# reuse time_grid()
#
times = time_grid(start, minutes, step_s)
# basically saying that if time_grid(start, minutes=2, step_s=30)
# you'll get:
# 12:00:00
# 12:00:30
# 12:01:00
# 12:01:30
# 12:02:00
#
# five timestamps spanning two minutes
# meaning for 280 min at 30 sec intervals you will get: (280 x 60 / 30) + 1 = 561
# so our times list contains 561 datetimes 
#
# now write a loop and call prop.teme() 561 rimes 

r, v = prop.teme_many(times)
# r = contians 561 positon vector
# v = 561 velocity vectors 
# the array shape will be (561, 3)
#   561 rows each containing X, Y, and Z 
#   but... these are still in TEME 
# we need to account for Earths rotation 
# convert to JD 
jd, fe = julian_date(times)

# now we have two arrays 
# one with JD components 
# and the otehr is the fractional components 
# add them for the GMST calculation 
# convert TEME -> ECEF 
r_ecef, _ = teme_to_ecef(r, v, jd + fr)
# _ to indicate we're intentionally ignoring the second result 
#
# convert posittions into lat and long 
lat, lon, alt = ecef_to_geodetic(r_ecef)
# combine the timestamps and coordinates
# you dont want to return 4 seperate lists
# for each timestamp, you want one record that has:
# at this time, the satellite was at this latitude, longitude, and altitude 
# basically have it look like 
# [
#    (time1, lat1, lon1, alt1),
#    (time2, lat2, lon2, alt2),
#    (time3, lat3, lon3, alt3)
# ]
# use zip() takes the first item from each collection and grops them together, then the second item from each, and so on 
 
points = [] 
for t, a, o, h in zip(times, lat, lon, alt):
    point = (
        t, 
        float(a),
        float(o),
        float(h)
    )
    points.append(point)
return points 
# t = timestamp
# a = lat 
# o = lon 
# h = alt 
# float() becuase NumPy may return numerical values as NumPy scalar types 
#














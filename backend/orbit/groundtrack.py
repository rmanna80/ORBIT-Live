""" 
what do we need in this file?
- want a function that accepts a satellite and a starting time 
  - then calculate positons over several minutes 
"""


from datetime import datetime 
# need the coordinate conversion functions from part 4 
from .frames import teme_to_ecef, ecef_to_geodetic
# need propagator and the two time helpers from part 3 
from .propagate import Propagator, julian_dates, time_grid

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
):
    print("DEBUG: creating timestamp")
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
    print("time_grid returned: ", type(times))
    print("Number of timestamps: ", len(times))
    print("DEBUG: calling teme_many")
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
    result = prop.teme_many(times)
    print("teme_many returned: ", type(result))
    if result is None:
        raise RuntimeError("teme_many() returned None")
    r, v = prop.teme_many(times)
# r = contians 561 positon vector
# v = 561 velocity vectors 
# the array shape will be (561, 3)
#   561 rows each containing X, Y, and Z 
#   but... these are still in TEME 
# we need to account for Earths rotation 
# convert to JD 
   
    jd, fr = julian_dates(times)
    print("DEBUG: converting TEME to ECEF")
    result = teme_to_ecef(r, v, jd + fr)
    print("teme_to_ecef return: ", type(result))
    if result is None: 
        raise RuntimeError("teme_to_ecef() returned None")
# now we have two arrays 
# one with JD components 
# and the other is the fractional components 
# add them for the GMST calculation 
# convert TEME -> ECEF 
    r_ecef, _ = teme_to_ecef(r, v, jd + fr)
# _ to indicate we're intentionally ignoring the second result 
    print("DEBUG: converting ECEF ")
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

""" 
Understand the International Data line problem 
- ok, lets imagine we're drawing the ISS ground track on a flat map 
  - we have a sequence of lat and lon coordinates
    - normally, we an connect each point to the next 
      - but look what happens when the satellite crosses the International data line, also known as the antimeridian 
        - lon ranges from -180(degrees) to +180(degrees)
          - suppose two consecutive postions are 
            point1 = (10.0, 179.0)
            point2 = (10.5, -179.0)
            - the first point is at 179(degrees) east 
            - the second point is at 179(degrees) west 
              - now geographically, thos points are only about two degrees of longitude apart 
                - but if i draw a stright line between 179 and -179 on a conventional flat lon/lat map, the line goes almost all the way across the map 
    - so the GeoJSON standard specifically recommends cutting geometries at the antimeridian to avoid this mapping
      - we need a function that detects when lon wraps from near +180(degrees) to near -180(degrees), or vise versa 
        - when that happenes, I'll start a new line segment 

"""



# ok what do we have so far!??!?!?!
# we have a list of points:
#   points = [
#   (time1, lat1, lon1, alt1),
#   (time2, lat2, lon2, alt2)
#   ....
#   ]
#
# and we want to split it whenever consecutive longitudes have a jump greater than 180(degrees)
#
def split_at_antimeridian(points):
    # first we need to store the finished segments 
    segments = []
    # need to also seperate what currently building
    current = []
    #
    # so far we have:
    #   current = contains points that belong to the line we're drawing right now 
    #   segments = contains all the completed lines 
    # ex:
    #   segments = [
    #       [point1, point2, point3],
    #       [point4, point25, point6],
    #       [point7, point8]
    #   ]
    # now our frontend can draw each inner list as a seperate line 
    for p in points:
    # what i need to ask: does adding this pont continue the current line normally, or would it jump across the whole map?
    # in order to answer that i need to compare the points longitude with the previous points longitude 
    # basically just a tuple structure with each index containing time, lat, lon, alt 
    # in order to acces the previous points longitude you would have to current[-1][2] >> the [-1] access it 
        if current and abs(p[2] - current[-1][2]) > 180: # compare lon to see if the abs() is larger than 180
        # you can read this as:
        #   if i already have points in the current segemet, and the longitude difference between this point 
        #   and the previous one exceeds 180 degrees, then we've crossed the map boundary 
        # now we need to save the segment 
            segments.append(current)
            # then start a new segment 
            current = [] 
        # regarless of whether we just slipt we need to add the current point 
        current.append(p)
    # once the loop finishes, we need to do something for the final segment 
    # it might still be in current  becuase we only save completed segemets when a crossing occurs
    if current:
        segments.append(current)
    return segments


if __name__ == "__main__":
    from .tle import EXAMPLE_ISS, parse_tle_text

    tle = parse_tle_text(EXAMPLE_ISS)[0]
    track = ground_track(Propagator(tle), tle.epoch, minutes=280, step_s=60)
    segments = split_at_antimeridian(track)
    print(f"{len(track)} points in {len(segments)} segments")
    # Where does each orbit cross the equator going north? Watch it shift west.
    for prev, cur in zip(track, track[1:]):
        if prev[1] < 0 <= cur[1]:
            frac = -prev[1] / (cur[1] - prev[1])          # linear interpolation to lat = 0
            lon = prev[2] + frac * (cur[2] - prev[2])
            print(f"northbound equator crossing at {cur[0]:%H:%M} UTC, lon {lon:8.2f}")











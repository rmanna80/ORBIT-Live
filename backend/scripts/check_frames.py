
# ok now lets combind the reference code we got from the one executable file
#
# this is one of the most important parts of engineering software
# we've written multiple coordinate transformation
# but just becuase out code runs doesnt mean out math is correct 
# so to check we must compare out results against a trusted, independent implementation 
# for that we'll use skyfield
#   - skyfield can calculate satellite postion and geographic coordinates using established coordinate transformation methods 

import math # need math to help calculate the approximated seperation 
# need skyfield satellite class, timescale utilities, and wgs84 model 

from skyfield.api import EarthSatellite, load, wgs84 

from orbit.frames import ecef_to_geodetic, teme_to_ecef
from orbit.propagate import Propagator, julian_date
from orbit.tle import EXAMPLE_ISS, parse_tle_text

# I will just use the same TLE for both implementations 
# first parse the historical ISS data with our own 
tle = parse_tle_text(EXAMPLE_ISS)[0]
# create a skyfield timescale 
ts = load.timescale(builtin=True)
# skyfield needs a timescale object to represent astronomical time correctly 
# builtin=True uses bundled time-scale data ratehr than requiring an external download 
# 
# now we can create a skyfield satellite object using the same two TLE lines 
sat = EarthSatellite(
    tle.line1,
    tle.line2,
    tle.name,
    ts 
)
# now both lilbraries are now working from the same orbitial information 
# this is important becuase we dont want a difference in TLE data to communicate our comparsion 
#
# calculate own result 
# first, propagate to the TLEs epoch 
r, v = Propagator(tle).teme(tle.epoch)
#then get the julian date 
jd, fr = julian_date(tle.epoch)
# convert ECEF position and velocity into ECEF 
r_ecef, v_ecef = teme_to_ecef(r, v, jd + fr)
# convert to geographic coordinates
lat, lon, alt = ecef_to_geodetic(r_ecef)

# calculate skyfields results 
#   to do that we want to compute the satellite postion at exactly the same instant 
skyfield_time = ts.from_datetime(tle.epoch)
geocentirc = sat.at(skyfield_time)

# now we ask skyfield for WGS84 geographic coordinates
ref = wgs84.geographic_position_of(geocentirc)

# now we can access 
# ref.latitude.degrees
# ref.longitude.degrees 
# ref.elevation.km 

print(
        f"ours   lat{lat:.4f}"
        f"lon {lon:.4f}"
        f"alt {alt:.3f} km"
)

print(
        f"skyfield lat {ref.latitude.degrees:.4f}"
        f"lon {ref.longitude.degrees:.4f}"
        f"alt {ref.elevation.km:.3f} km"
)


# now we can compare them 
# calculate the east-west difference 
gap_km = (
    (lon - ref.longitude.degrees)
    * 111.32
    * math.cos(math.radians(lat))
)
# one degree of longitude near the equator corresponds to roughly 111km of east-west direction 
# but the distance represented by a degree of longitude gets smaller toward the poles 
# that is why were multiplying by cos of lat 
# so basically this equation gives us the approximated east-west separation at the chosen lat 
#
print(
    f"east-west gap {gap_km * 1000:.0f} m"
)
# converts km to m 


















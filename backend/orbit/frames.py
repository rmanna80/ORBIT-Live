# we're going to be working with ectors, rotations, trigonometry, and ground station coordinates
import numpy as np 
# why numpy? because we already used it in part 3. A satellite position is stored as three numbers and NumPy makes it easy to perform calculations on all three 
#
# Next we're going to return azimuth, elevation, range, and range rate together 
from typing import NamedTuple 
from .config import GroundStation 
# remember that ground-station has a location on earth 
# we need its long, lad, and altitude to determine where a satellite appears in the sky 
from .constants import E2_EARTH, OMEGA_EARTH, R_EARTH, TWO_PI
# we already know R_EARTH and TWO_PI
# E2_EARTH: earths squared ellipsoid, which describes how much the WGS84 reference ellipsoid differs from a sphere 
# OMEGA_EARTH: earths angular rotation rate in radians per second 
""" 
what problem are we trying to solve?
- imagine SGP4  tells us that there is a satellite at:
  r_teme = [4200, -3100, 4300]
  - that postion is measured using axes that dont simply spin with earth's surface 
    - but earth roatates underneath the satellite
      - so if you want to know where the satellite is relative to your location, you need to know how Earth is oriented at that moment 
    How far has Earth rotated?
    - thats what the Greenwhich Mean Sidereal Time (GMST) helps you determine 
      Why can't we just use a 24-hour rotation?
      - because earth rotates once relative to distint stars in approximately 23 hours, 56 min, and 4 sec 
        - thats called a sidereal day 
          - a solar day is ~24 hours becuase Earth is also moving around the sun 
    Calculations:
    - one full rotation is 2(pi) radians 
      so:
        w = 2(pi)/86164.1
      that gives you:
        w = 7.2921 * 10^-5(rad/s)
      what does that mean?
      - earth turns about 0.000072921 radians per second 
        - sounds tiny, but at the equator, the surface is thousands of km from Earth's rotation axes
        so you multiply:
            v = wRe 
            v = 0.465km/s 
            - so a point fixed on earths equator moves around its rotation axis at approximately 465 meters per second in an inertial frame 

"""




def gmst_rad(jd_ut1): # why jd_ut1 
                      # becuase the GMST formula uses a Julian Date expressed using UT1, a time scale based on Earth's rotation
                      # UT1 != UTC; but for now well approximate UT1 with UTC 
    t = (np.asarray(jd_ut1) - 2451545.0) / 36525.0 # Julian centuries since J2000
                                                    # np.asarray(je_ut1) allows the input to behave as a NumPy array, whether you pass one Julian date or a collection 
                                                    # - 2451545.0 calculates how many days have passed since the J2000 epoch 
                                                    # / 36525.0  converts days into Julian centuries, where one Julian century is 36,525 days 
    # next, calculate GMST 
    seconds = (
        67310.54841
        + (876600.0 * 3600 + 8640184.812866) * t 
        + 0.093104 * t**2 
        - 6.2e-6 * t**3 
    )
    # result is in seconds of sidereal time 
    # Convert sidereal seconds into degrees 
    return np.mod(np.radians(seconds / 240), TWO_PI)
    # seconds gives degrees
    # np.radians(seconds / 240) converts degrees into radians
    # np.mod() gives the remainder after division 
    # 
    # now we have a funciton that answers: 
    # at this particular Julian date, what is earths rotation angle under out GMST convention?

    # convert TEME coordinates to ECEF 
    # we have r_teme = [x, y, z]
    # and v_teme = [vx, vy, vz]
    # we want r_ecef and v_ecef 
    # so we need to rotate both the positon and velocity into an earth fixed reference frame 
    #
    # Understand the rotation
    # we are going to rotate around the Z-axis
    # why Z? becuase  Z-axis is aligned with earths rotational axis 
def teme_to_ecef(r_teme, v_teme, jd_ut1):
    # we need three inputs 
    #   satellite positon in TEME 
    #   satellite velocity in TEME 
    #   Julian date expressed in UT1, approximated here with UT1
    r = np.atleast_2d(r_teme)
    v = np.atleast_2d(v_teme)
    # np.atleast_2d() makes sure the result has at least two diemsions
    # if we give it one positon, it becomes one row with three columns 
    theta = np.atleast_1d(gmst_rad(jd_ut1))
    #np.atleast_1d() makes sure the result can be indexed as an array, even for one timestamp 

    # now calculate sine and cosine 
    c, s = np.cos(theta), np.sin(theta)
    # now calculate the rotated X coordinate 
    x = c * r[:, 0] + s * r[:, 1]
    # r[:, 0] this numpy syntax means: give me every row, but only column zero = X coordinates
    # r[:, 1] contains all Y coordinates
    y = -s * r[:, 0] + c * r[:, 1]
    #combine them into a new array 
    r_ecef = np.column_stack([x, y, r[:, 2]])
    # np.column_stack() combines the x, y, z arrays into columns 
    # we've now transformed the postion into an approximately earth-fixed frame 
    #
    # but velocity is different 
    # something to think about: 
    #   why cant we simply rotate the velocity vector and call it done 
    #why? because our new coordinate system is rotating with earth 
    # imagine you are standing still on the equator
    # relative to earths surface, velocity is zero 
    # but from space-oriented reference frame, you are moving because earth is spinning 
    # so the velocity transformation needs to remove the contribution from Earths rotation 
    #
    vs = c * v[:, 0] + s * v[:, 1] + OMEGA_EARTH * y # rotate the X and Y components of velocity
    vy = -s * v[:, 0] + c * v[:, 1] - OMEGA_EARTH * x # rotate velocity Y component, then subtract the earths rotation correction  
    v_ecef = np.column_stack([vx, vy, v[:, 2]])
    # now we have both positon and velocity in our earth-fixed frame 
    # rigth now we only have a two-dimensional array but i want to return a three-componenet vector 
    if np.ndim(r_teme) == 1: # np.ndim() tells us how many dimensions the original input had 
        return r_ecef[0], v_ecef[0]

# now we have ECEF coordinates. But those are still X, Y, Z numbers 
# how can we turn them into lad, long, altitude 
#
# what if we want to put a pin on a map, we need somethingh like 
# Latitude:  35.0°
# Longitude: -79.8°
# Altitude:  420 km
# those arent the same as X, Y, Z 
# we need another conversion 
""" 
why isnt earth just a sphere?
- imagine earth were a perfect ball 
  - then finding lat and altitude would be pretty easy 
    - but earth is slightly flattened at the poles and wider around the equator 
      - Geocentirc latitude = measure the angle between the equatorial plane and a line connecting earths center to a pont 
      - Geodetic latitude = neasures the angle between the equatorial plane and the normal (perpendicular direction) to the reference ellipsoid at that point 

        - Geodetic Latitude is what we use with GPS and maps 
          - these two angles arent always equal because earth isnt a perfect sphere 
    - solve with the iterative numerical method 
"""

def ecef_to_geodetic(r_ecef):
    # standardize the input 
    r = np.atleast_2d(r_ecef)
    # seperate the coordinates
    x, y, z = r[:, 0], r[:, 1], r[:, 2]
    # r contains 10 satellite positons, x contains 10 X coordinates, y contains 10 Y coordinates, z contains 10 Z coordinates
    #
    # next, calculate long 
    # if were looking down at earth from above the noth pole, long describes the angle around eaerths rotation axis from Greenwhich
    lon = np.arctan2(y, x) #arctan2() handles the signs of X and Y to determine which quadrant the angle belongs to ~ result in radians

    # calculate distance from earths rotation axis 
    p = np.hypot(x, y) # .hypot() calculates the hypotenus from two components and is numerically robust 

    # now lets make our first lat guess 
    lat = np.arctan2(z, p * (1 - E2_EARTH))
    for _ in range(5): # _ allows us to repeat a calculation 5 times and _ is used for an unsigned variable 
        N = R_EARTH / np.sqrt(
            1 - E2_EARTH * np.sin(lat)**2 
        )
        lat = np.arctan2(
            z + E2_EARTH * N * np.sin(lat),
            p 
        )
        # on the first iteration, lat is our initial guess
        # we use it to calculate N 
        # we then calculate a better lat 
        # second iteration we use that imporved lat 
        # repeat until the estimate has effectively converged 
        #
    # now calculate altitude 
    # altitude meaning height above the WGS84 ellipsoid, not above local terrain or sea level 
    N = R_EARTH / np.sqrt(
        1 - E2_EARTH * np.sin(lat)**2 
    )    
    alt = (
        p * np.cos(lat)
        + (z + E2_EARTH * N * np.sin(lat)) * np.sin(lat)
        - N 
    )
    #what to understand: because we're measuring altitude relative to an ellipsoid, not a sphere is why were doing that equaiton 

    # convert lat and long to degrees
    lat_deg, long_deg = np.degrees(lat), np.degrees(long)
    if np.dim(r_ecef) == 1:
        return (
        float(lat_deg[0]),
        flot(long_deg[0]),
        float(alt[0])
    )
    return lat_deg, long_deg, alt 
    

# write the reverse conversion 
# now i want to think about our ground station 
# we know its lat and long
# ex : latitude = 35.0 | longitude = -80.0 | altitude = 0.2
# but our satellite postion is currently in ECEF coordinates
# if we want to calculate the distance between the ground station and satellite, both need to be expressed in the same coordinate system 
#
def geodetic_to_ecef(
        lat_deg: float,
        long_deg: float,
        alt_km: float 
) -> np.ndarray:
    lat, lon = np.radians(lat_deg), np.radians(long_deg)
    # convert to radians because we're going to use sin() and cos()
    N = R_EARTH / np.sqrt(
        1 - E2_EARTH * np.sin(lat)**2 
    )
    # calculate X, Y, and Z using WGS84 geometry 
    x = (N + alt_km) * np.cos(lat) * np.cos(lon)
    y = (N + alt_km) * np.cos(lat) * np.sin(lon)
    z = (N * (1 - E2_EARTH) + alt_km) * np.sin(lat)
    # notice that we're using altitude in km becuase earth radius constant with km 
    return np.array([x, y, z])


""" 
Understand the ground station coordinates
- now we solved the geographic location problem
  - we know where the satellite is above earth 
    - we know where our ground station is on earth 
      - but we still cant answer 
        - which direction should i point an antenna?
          - to do that we need the ground stations pov 
            - Thats where ENU comes in (East [direction to your right if facing north], North [direction toward geographic north], Up [perpendicular to the reference ellipsoid at your location ])

    - now imagine the satellite somewhere in the sku 
      - we need to determine how much of the direction from you to the satellite points east, north, and up 
        - what is azimuth?
          - the compass direction toward the satellite
        - what is elevation?
          - how high above the horizon the satellite appears 

create a class LookAngles to organize our four things 
"""

class LookAngles(NamedTuple):
    azimuth_deg: np.ndarray
    elevation_deg: np.ndarray
    range_km: np.ndarray
    range_rate_km_s: np.ndarray

    def look_angles(r_sat_ecef, v_sat_ecef, station: GroundStation) -> LookAngles:
        # what info do we need 
        # satellite pos, satellite velocity, ground-station location 
        r, v = np.atleast_2d(r_sat_ecef), np.atleast_2d(v_sat_ecef)
        # now each postion and velocity has three columns 
        # 
        # next find the ground station ECEF psotion 
        rho = r - geodetic_to_ecef(station.lat_deg, station.long_deg, station.alt_km)

        #next convert the stations latitude and long into radians 
        lat, long = np.radians(station.lat_deg), np.radians(station.long_deg)
        sl, cl, so, co = np.sin(lat), np.cos(lat), np.sin(lon), np.cos(lon)

        # now calculate the east components
        # we want to know how much of the station-to-satellite vector points east 
        east = (
            -so * rho[:, 0]
            +co * rho[:, 1]
        )
        # here were combining the X and Y components to find th local eastward displacement 
        #
        # calculate North 
        north = (
            -sl * co * rho[:, 0]
            - sl * so * sho[:, 1]
            + cl * rho[:, 2]
        )

        # calculate Up 
        up = (
            cl * co * rho[:, 0]
            + cl * so * rho[:, 1]
            + sl * rho[:, 2]
        )

        # calculate range 
        rng = np.linalg.norm(rho, axis=1) # axis=1 since x, y, x row constains displacement we want one distance for each row 
        #calculate azimuth
        az = np.mod(np.degrees(np.arctan2(east, north)), 360.0) 
        # calculate elevation
        el = np.degrees(np.arcsin(up / rng))
        # calculate range rate 
        # basically it would be useful to know:
        #   is the satellite getting closer to my satation or moving futher away 
        range_rate = np.sum(rho * v, axis=1) / rng 
        return LookAngles(az, al, rng, range_rate)


if __name__ == "__main__":
    from datetime import timedelta

    from .config import GROUND_STATION
    from .propagate import Propagator, julian_date
    from .tle import EXAMPLE_ISS, parse_tle_text

    tle = parse_tle_text(EXAMPLE_ISS)[0]
    prop = Propagator(tle)
    for minutes in (0, 15, 30, 45):
        t = tle.epoch + timedelta(minutes=minutes)
        r, v = prop.teme(t)
        jd, fr = julian_date(t)
        r_ecef, v_ecef = teme_to_ecef(r, v, jd + fr)
        lat, lon, alt = ecef_to_geodetic(r_ecef)
        look = look_angles(r_ecef, v_ecef, GROUND_STATION)
        print(f"{t:%H:%M:%S}  lat {lat:7.2f}  lon {lon:8.2f}  alt {alt:6.1f} km  "
              f"| from {GROUND_STATION.name}: el {look.elevation_deg[0]:6.1f} deg, "
              f"range {look.range_km[0]:7.0f} km")
    





""" 
Modeling the sun, earths shadow, and satellite betteries 
- now we have built the radio link 
  - imagine a small satellite orbiting earth 
    - when it is exposed to the sun its solar panels generate electricity
      - but when earth block the sunlight, its solar panels stop generating useful power 
        - the satellite has to run on its betteries
          - basically if we want to show a battery level card in ORBIT Live, we can build a simplified model that accounts for these charging and discharging periods 
            - but first we need to know whether the satellite is in sunlight or shadow 

"""



import numpy as np 
from .constants import AU, R_EARTH 
# we already know R_EARTH: eaerths equatorial radius in km 
# AU (Astronomical unit): one AU is approximately the avg disatance between earth and the sun 
#   1 AU = 149,597,870.7 km 
# out sun position fucntion returns km, so AU must be using km as well 
#
# lets think about the function that we need
# we want to calulate a vector pointing from earths center to the sun 
# why?
# because once we know which direction sunlight is coming from, we can determine whether the earth is blocking it from reaching the satellite
#
# given our problem 
# given a julian date, calulate an approximate sun position vector relative to Earth 

def sun_position_km(jd_ut1):
    # returning km 
    # quick note: the low precision solar equations we are using are normally evaluated with a dynamical time argument, 
    # typically TT or TDB, rather than UT1. the fucntion uses jd_ut1 as a conveninent approximation   
    # menaing that its sufficient for an introductory shadow visualizaiton, but we shouldnt mistake it for a high precision ephemeris (prediciting where it will be at a specific time)
    # 
    #  first, calulate julilan centuries 
    t = (np.asarray(jd_ut1) - 2451545.0) / 36525.0 
    # use that same idea to for J2000 as a refrence epoch 
    # now we need to calulate the suns apparent oribital geometry 
    # the supplied mathematical model uses a low precision solar position approximation 
    # we dont have to derive all of celestial mechanics from scratch to use it 
    mean_lon = np.radians(
        280.460 + 36000.771 * t 
    )
    # what is mean longitude?
    # it is an angel describing the suns approximation positon along the ecliptic under a simplified motion model 
    # the constants come from the solar postion approximation 
    # using np.radians() becuase out trigonometric fucntion expects radians 
    # now we need to calulate the suns mean anomaly 
    M = np.radians(
        357.5291092 + 35999.05034 * t 
    )
    # remember anomaly from part 1?
    # mean anomaly describes progress through an orbit as though the motion were uniform 
    # the real apparent sun motion isnt perfectly uniform, becuase earths orbit isnt exactly circular 
    # now we need an additional correctio -> calulate ecliptic longitude
    ecl_lon = (
        mean_lon 
        + np.radians(
                1.914666471 * np.sin(M)
                + 0.019994643 * np.sin(2 * M)
            )
    )
    # we started with mean longitude
    # then we added corrections involving sine of the mean anomaly
    # these adjustments account approximately for the nonuniform oribital motion 
    # now ecl_lon gives us the suns approximate ecliptic longitude
    #
    # whats the ecliptic?
    # the ecliptic is the pane of earths orbit around the sun 
    # but since were calulating satellite postion relative to earth equatorial reference system 
    # those planes arent the same 
    # earths rotation acis is tilted relative to its orbital plane 
    # that is why we need the obliquity angle later 
    #
    # calulate the earth - sun distance 
    dist = (
        1.000140612
        - 0.061708617 * np.cos(M)
        - 0.000139589 * np.cos(2*M)
    ) * AU 
    # the expression inside parentheses gives an approximate Earth-Sun distance in Astronomical units 
    # we multiply by AU to convert it into km 
    # why doesnt the distance stay exactly one AU? 
    # becuase earths orbit is slightly elliptical 
    # at some times of the year earth is a little closer to the sun and at other times a little farther away 
    #
    # calulate earths axial tilt 
    obliquity = np.radians(
        23.439291 - 0.0130042 * t 
    )
    # this is earths approximate obliquity in degrees, including a slow change over time 
    #   (ecliptic: this i sjust the flat, imaginary highway (or plane) that earth travels on as it circles the sun 
    #   The obliquity is the angle between Earth's tilted spine and that flat highway)
    # 
    # now we have three important quantities:
    # ecl_lon | dist | obliquity
    # from these we can build a three-dimensional sun vector
    #
    # convert the suns positions into X, Y, Z 
    # [x_sun, y_sun, z_sun]
    x = dist * np.cos(ecl_lon)
    y = (
        dist 
        * np.cos(obliquity)
        * np.sin(ecl_lon)
    )
    z = (
        dist 
        * np.sin(obliquity)
        * np.sin(ecl_lon)
    )

    return np.column_stack([
        x,
        y,
        z 
    ]).squeeze() 
    # np.column_stack() combines X, Y, X arrays into a table of vector
    # if we had 100 timestamps, we would like an array shaped:
    #   (100, 3)
    # but if we only have one timestamp:
    # (3,)
    # .squeeze() removes dimensions of length one 
    # NOW we know approximately which direction the sun is from earth 


""" 
Understand how the earth casts a shadow 
- imagine the sun is on one side of the earth and the satellite is moving around it 
  - earth blocks sunlight from reaching part of space behind it 
    - we need to check whether our satellite is in that region 
      - basically going to model earths shadow as a cylinder 
        - the real shadow has a conical shape becuase the sun isnt a popint source, and there is also a penumbra (ecllipse) where only part of the sun is blocked
          - but a cylinder is a useful starting approximation. this type of cylindrical eclipse test is also described in ESAs satellite-eclipse reference material 
    - what information do we need?
      - we need two vectors 
        - the satellite postion relative to earth
            r 
        - and the suns positon relative to earth 
            r_sun 
        - first we'll normalize the sun vector 
          - that means converting it into a direction vector with length one 
            ŝ = r_sun / |r_sun|

            - then we will ask two quesitons:
              - is the satellite on the side of earth opposite the sun? 
              - is it close enough to the earth-sun axis to be inside earth cylindrical shadow?
                - if both are true, our satellite is in eclipse 
"""


def in_shadow(r_sat_teme, r_sun): # inputs are satellite positon in TEME and approximate sun vector 
    # we want to return True if the satellite is in shadow and False otherwise 
    r = np.atleast_2d(r_sat_teme)
    # standardize the sun vector 
    s_hat = np.atleast_2d(r_sun)
    # we want to calulate with the sun vector in a consistent two-dimensional shape 
    s_hat = s_hat / np.linalg.norm(
        s_hat,
        axis=1,
        keepdims=True 
    )
    # np.linalg.norms() calulates the length of a vector
    # axis=1 tells NumPy to calulate a length for each row 
    # keepdims=True keeps the result as a column shaped array, which allows division of each row by its own length
    # ex: sum = [100, 0, 0] -> sun_direction = [1, 0, 0]
    # the direction is unchanged but the length becomes one -> makes projection calculation easier 
    #
    # find out whether the satellite is behind earth 
    along = np.sum(
        r * s_hat,
        axis=1 
    ) # s = r * ŝ
    # if along is positive, the satellite is on the sun facing side of earth 
    # if along is negative, its the opposite

    # cant just do along < 0 
    # calulate the perpendicular distance from the shadow axis 
    # imagine drawing a straight line from earth toward the sun, then extending that line backward throug earth 
    #   that becomes the axis of our shadow cylinder 
    #       we want to know how far the satellite is from that axis 
    prep = np.linalg.norm(r - along[:, None] * s_hat, axis=1)
    # [:, None] becuase along is one dimensional array and adding None in this indexing expression gives it an extra dimension (100,0) -> (100, 1)
    # then subtract the projection from the original satellite positon 
    # whats left is the perpendicular to earth-sun axis, take its magnitude
    # prep == tells us the satellite distance from the shadow axis in km 
    # if that disstance is smaller than earths radius, the satellite lies inside the cylindrical shows circle cross-section
    # 
    # our second condition is prep < R_EARTH
    # when you combine those two psotions we know a satellite is in shadow when:
    dark = (along < 0) * (prep < R_EARTH)
    
    # return one boolean or an array 
    if np.ndim(r_sat_teme) > 1:
        return dark 
    return bool(dark[0])

sun = np.array([1.0, 0.0, 0.0])
satellite = np.array([-7000.0, 0.0, 0.0])
print(in_shadow(satellite, sun))

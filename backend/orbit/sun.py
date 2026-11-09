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

""" 
Now lets simulate the satellite battery
- now we can determine whether the satellite is in sunlight or eclipse 
  - what can we do with that inforamtion? 
    - we can model a bettery 
      - imagien a hypothetical small satellite with 
        parameter                               value 
        battery capacity                        40 Wh 
        solar panel output in sunlight          30 W 
        electrical load                         18 W 
        starting charge                         80%

        - Watts (W) measure pwoer, or how quicly energu is being transferred 
          - Watts-hour (Wh) measures energy 
            - if a system consumes 18 watts for one hour it uses:
              18 W x 1 h = 18 Wh 
              - that distinction is important 
                - our battery stores energy in Watts-hour 
                  - our solar panels generate power in watts 
                    - our electrical componenets consume power in watts 
                      - to update the battey, we need to convert power over a time interval into energy 

        - how much energy do we gain in sunlight?
          solar power = 30 W 
          load = 18 W 
          - so the net power:
            30 - 18 = +12 W 
            - that means the battery gains energu at a rate of 12 watts, assuming all avaliable surplus solar power reches the battery 
              - if the satellite says sunlit for one hour:
                12 W c 1 h = 12 Wh 

            - now what happens during an eclipse?
              - solar power becomes zero 
                - but the load still consumes 18 watts 
                  - so:
                    0 - 18 = -18 W 
                    - that means the battery is discharging 
                      - for a 33 min eclipse:
                        -18 x 33/60 = -9.9 Wh 
                        - the simple energy balance is psitive. That doesnt guarantee a real satellite battery is healthy, but it gives us a useful template 


"""




# want to create a class that represents a battey that remembers its state between calculations 

class BatteryModel:
    def __init__(
        self, 
        capacity_wh=40.0,
        solar_w=30.0,
        load_w=18.0,
        charge_pct=80.0 
    ): # default model parameters, they can always change them when creating a battery 
        # store the parameters inside our object 
        self.capacity_wh = capacity_wh
        self.solar_w = solar_w
        self.load_w = load_w 
        # our starting percentage is 80%:
        #   40 x 0.8 = 32 Wh 
        self.charge_wh = capacity_wh * charge_pct / 100 
        # self.charge_wh represents the batterys current stored energy 

    # thinking at our simulation 
    # we are predicting the satellite position every 60 seconds 
    # at each step, we know whether the satellite is in sunlight or eclipse
    # so now we want:
    # "Advance the battery simulation by every 60 seconds under these sunlight conditions"
    def step(self, dt_s: float, sunlit: bool) -> float: # update the battey
        # dt_s represents elapsed time in seconds 
        # sunlit is True if the satellite is receiving sunlight & False is its in shadow
        # we want the function to return the new battey percentage

        # calulate net power 
        # if the sunlight is avaliable, we get pwoer from the solar panels 
        # otherwise, solar input is zero 
        solar_input = self.solar_w if sunlit else 0.0 
        # read it as: if sunlit is truem we use self.solar_w; otherwise use zero 
        # subtracty our electrical load 
        power_h = solar_input - self.load_w 
        # power_h = 30 - 18 = +12 | 0 - 18 = 18 
        # power_h tells us how quicly the battery is gaining or losing energy
        #
        # convert power into watts-hour 
        # (delta)E = P((delta)t / 3600)
        energy_change_wh = power_h * dt_s / 3600
        # if our interval is 60 sec and we are in sunlight:
        #       12 x 60 / 3600 = 0.2 Wh 
        # so in one minute, the battery gains 0.2 Wh 
        # in eclipse:
        #       -18 x 60 / 3600 = -0.3 Wh 
        # during one min of an eclipse, the battey loses 0.3 Wh 
        #       self.charge_wh += energy_change_wh 
        # can tdo that, what if our simulation charges the battery beyond its capacity?
        # likewise, energy shouldnt become negative 
        # so we need to clamp the result between zero and capacity
        self.charge_wh = min(
            self.capacity_wh,
            max(0.0, self.charge_wh + energy_change_wh)
        ) # this is the same approach used when limiting the modeled signal percentage 0-100% 
        return self.percent 
    
    # to find the battey percentage 
    #   Battery % = 100 (Stored energy / capacity)
    @property 
    def percent(self) -> float:
        return 100 * self.charge_wh / self.capacity_wh 

    # now we have a class that remembers battery energu adn updates it as the satellite moves between sunlight and eclipse
    # we assume fixed solar output, but real solar output depends on the angle between the panels and the sun, and the real electrical systems have conversion losses and charging limits 
battery = BatteryModel(charge_pct=50.0)
battery.step(dt_s=3600, sunlit=True)
print(battery.percent)



if __name__ == "__main__":
    from .propagate import Propagator, julian_dates, time_grid
    from .tle import EXAMPLE_ISS, parse_tle_text

    tle = parse_tle_text(EXAMPLE_ISS)[0]
    times = time_grid(tle.epoch, minutes=185, step_s=60)
    r, _ = Propagator(tle).teme_many(times)
    jd, fr = julian_dates(times)
    dark = in_shadow(r, sun_position_km(jd + fr))
    battery = BatteryModel()
    for t, d in zip(times, dark):
        pct = battery.step(60, sunlit=not d)
        if t.minute % 10 == 0:
            print(f"{t:%H:%M}  {'ECLIPSE ' if d else 'sunlit  '}  battery {pct:5.1f}%")
    print(f"in shadow {dark.mean() * 100:.0f}% of the time")




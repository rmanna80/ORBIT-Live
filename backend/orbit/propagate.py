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

# i want to calculate where the ISS will be at 2:30pm
# oython can represent that using datetime object 
# but SGP4 doesnt accept a python datetime directly. It wants a Julian datte represenetd by two numerical componenets 
# with that being said we are going to build a helper funtion that coinverts out python time into the format SGP4 needs
def julian_date(t: datetime) -> tuple[float, float]:
#before convert time, need to make sure were using UTC, 2:30pm in Ny and 2:30pm in London arent the same thing 
    t = t.astimezone(timezone.utc)
    # need to convert it to a julian date 
    # SGP4 has a library called jday()
    # for this library it needds year, month, day, hour, minute and seconds 
    return jday(
        t.year, 
        t.month,
        t.day,
        t.hour,
        t.minute,
        t.second + t.microsecond / 1e6 # because datetime seperate whole seconds from microsecond
                                        # one million microseconds = 1 second 
                                        # so if we have 15 sec and 500,000 microseconds, i want to pass 15.5 seconds to jday() 
                                        # that is why im diving by 1e6 (pythons way of writing one million)
        # ex: 2461315.02083333 
        # 2461315 represents the 2,461,315th day since the calendar origin (Oct.1,2026,from 12pm (noon) UTC)
        # .02083333 is a small fraction, it means only a tiny bit of time has passed since 12:00 PM.
            # • In Hours: 0.02083333 * 24 = 0.5 hours (exactly 30 minutes).
            # Clock Time: Adding 30 minutes to the noon start time gives you 12:30 PM UTC.
    )




""" Imagine i want to show the ISS moving around Earth over the next hour 
    - one position isnt enough
      - i might want its position every 10 sec 
        - that means that I need to calculate postions at lots of different times 
          - so instead of receiving one datetime, i want my next funtion to receive a list of datetimes 
            """

def julian_dates(times: list[datetime]) -> tuple[np.ndarray, np.ndarray]: 
    # times is a list of datetime objects 
    # i want to return two numPy arrays 
    # why two arrays? because out first fucntion returns two values for each time 
    # the jday() day componenet and the fractional componenet
    pairs = [julian_date(t) for t in times] # list comprehension making pairs a list of tuples 
    # next i need to extract the first value from every tuple 
    return np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])



""" Now lets create the actual satellite propagator (predictor)
    
    i want to create something that represents an individual satellite and can calculate 
    its postions whenever i ask 
        - i could write this as a standalone function that accepts TLE lines every time, 
          but then i would be repeatedly initializing the same satellite model 
          - instead ill make a CLASS!!!! 
"""
class Propagator:
    # return postions and velocities in TEME coordinates 
    # the units are km adn km per second 

    # now i need to think about what this object should return 
    # when i create a propagator, i want to give it the TLE we downloaded from part 2
    # create an initilizer 
    def __init__(self, tle: TLE):
        # this will run when we create a new obejct  
        # ex: prop = Propagator(iss_tle) from that self refers to that particular propagator object 
        # first ill store the TLE so we can access it later 
        self.tle = tle 
        # then i need to create the actual SGP4 model 
        # with that its library gives us a method called twoline2rv
        # that accts the two original TLE lines, we already store that in tle 
        self.sat = Satrec.twoline2rv(tle.line1, tle.line2)

    # still need to calculate a postion 
    # in order to do that we need a method that takes in a time 
    # basically im thinking that:
    # "i have the orbital model, i have the TLE, now i want to ask this model where the satellite is at a particular time "
    # i know that its centered on earth, but the axes are noot fixed to earths rotating surface
    # we're not calculating lad & long just yet 
    def teme(self, t: datetime) -> tuple[np.ndarray, np.ndarray]:
    # giving it one datetime, expecting two arrays back: postion & velocity 
        # first i need to convert the datetime into Julian date componenets (helper above)
        jd, fr = julian_date(t)
        # now i have the time in the format SGP4 is expecting
        err, r, v = self.sat.sgp4(jd, fr)
        # this returns 3 values 
        #   err: tells us if there was an error 
        #   r: positon vector 
        #   v: velocity vector 
        
        # now i need to make sure the calulation worked 
        if err:
            raise PropagationError(f"{self.tle.name}: {SGP4_ERRORS[err]}") # dict that translates over error code into descriptions
        # if no errros, then we want to return the postion and velocity as NumPy arrays 
        return np.array(r), np.array(v)

    """ so basically no we know where a satellite is at one moment 
        - but if we want to draw its orbit, were going to need more than just one point 
          - i could want 500 postions along its path 
            - we could repeatedly call teme() but SGP4 provides a batch called sgp4_array()"""
    def teme_many(self, times: list[datetime]) -> tuple[np.ndarray, np.ndarray]:
        jd, fr = julian_dates(times)
        err, r, v = self.sat.sgp4_array(jd, fr)
        # now instead of one postion and one velocity, i now get arrays 
        # meaning if i pass 100 timestamps, r and v will each have a shape of (100,3)
        #   meaning 100 rows, each contianing X, Y, and Z 
        #now i need to check for errors meaning if any error codes are nonzero 
        if np.any(err):
            # i at least know one propogation failed 
            # i want to find the first nonzero error code to report it 
            first = int(err[np.nonzero(err)[0][0]])
            # np.nonzero(err) finds the location of values that arent zero 
            # np.nonzero(err)[0][0] retrieves that first index 
            # int() converts it 
            raise PropagationError(
                f"{self.tle.name}:{SGP4_ERRORS[first]}"
            )
        # if no errors return the postion and velocity
        return r, v 
    
""" 
now lets calculate the earths J2 effect 
- basically in part 1: we modeled earth as a perfect spherical gravitational source 
    - but earth has an equatorial bulge, which changes its gravitational field 
    - this is called precession 
        - lets write a function that approximates how quickly that happens 
"""
def j2_node_drift_deg_per_day(tle: TLE) -> float:
    
    # what info do i need ????
    # i ened the satellites mean motion, semi-major axis, Eccentricity, and inclination
    # we have all of that in TLE 
    # i also need earths J2 coefficent and equatorial radius, we already imported that 
    
    # Okay, I need to calculate how Earth's equatorial
    # bulge changes the orientation of the orbital plane.
    #
    # First, find mean motion in radians per day.


    n = tle.mean_motion_rev_per_day * TWO_PI
    
    # next i need p, the semi-major axis multiplied by 1 - e^2 
    p = tle.semi_major_axis_km * (1 - tle.eccentricity**2)
    
    rate = (
        -1.5 # is the mathematical coefficent
        * n # tells us the satellite's angular motion 
        * J2 # earths equatorial bulge 
        * (R_EARTH / p)**2  # accounts for the orbital gemotry and distance
        * math.cos(math.radians(tle.inclination_deg)) # accounts for inclination
    )

    return math.degrees(rate)


""" 
i want to calculate the satellite psotion every 30 sec for the next 10 min 
- i dont want to manually write 21 datetimes 
    - write a healper that creates timespamps 
"""
def time_grid(start: datetime, minutes: float, step_s: float) -> list[datetime]:
    # start = time we began 
    # minutes = how long we want to calculate 
    # step_s = how far apart our timespamps should be in seconds 
# ex: minutes = 10 step_s = 30
#   10 min = 600 seconds / 30 sec per interval 
#       600/30 = 20 
#           but if we're including the starting point its 21 timestamps 
    count = int(minutes * 60 / step_s) + 1 
    # now we need to generate the times 
    times  = [] 
    for i in range(count):
        seconds = i * step_s 
        current_time = start + timedelta(seconds=seconds)
        times.append(current_time)
    return times # could've also done a list comprehension too!!!!!
                # now we combind this with teme_many() and we can calculate an entire sequence of satellite postions


# now we test everything 
if __name__ == "__main__":
    from .tle import EXAMPLE_ISS, parse_tle_text

    tle = parse_tle_text(EXAMPLE_ISS)[0]
    prop = Propagator(tle)
    # now i want to see how the satellites position changes as time passes 
    for minutes in (0, 23, 46, 92):
        # for each offset, calculate requested time 
        t = tle.epoch + timedelta(minutes=minutes)
        r, v = prop.teme(t)
        print(
            f"t+{minutes:>3} min"
            f"r = [{r[0]:9.1f} {r[1]:9.1f} {r[2]:9.1f}] km" 
            f"|r| = {np.linalg.norm(r):7.1f} km " 
            f"|v| = {np.linalg.norm(v):.3f} km/s "
        )
    print(
        f"J2 node drif: formula {j2_node_drift_deg_per_day(tle):.2f} deg/day, "
        f"SGP4 internal {math.degrees(prop.sat.nodedot * 1440):.2f} deg/day"
    )














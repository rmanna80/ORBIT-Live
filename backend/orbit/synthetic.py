""" 
Building our own test data 
- we dont want to build an anomaly detectory and immediately  point it at real ISS history 
  - why not?
    - becuase if the program flags something, how do we know that it is correct?
      - and if it doesnt flag anything, how do we know whether the detectory works or whether no anomaly occurred?
        - instead we want to create a fake orbital histoiry with a known answer 

    - 30 days of orbital observations 
    - a small amount of daily orbital decay 
    - a little random variation 
    - one deliberate reboost maneuver on day 18 
"""


import math 
# random measurement-like variation to simulate mean motion 
import random 
# we want SGP4 to construct new orbital eleent sets, the library gives us an initialization method that we can build a satellite record from orbital elements 
from sgp4.api import WGS72, Satrec 
# Satrec represents an SGP4 satellite record & WGS72 selects the WGS-72 gravitational constants traditionally used with standard SGP4 TLEs 
#
# now we need a way to turn the satellite record back into actual TLE test 
from sgp4.exporter import export_tle 
from .tle import TLE, parse_tle 

""" 
Lets understand before we start
- TLE class stores mean motion in: revolutions per day 
  - ex: 15.72 rev/day 
    - But SGP4 internal no_kozai parameter uses: radians per minute 
      - we need a conversion
        - one revolution is: 2(pi) radians
        - one day is: 1440 minutes 
        - therefore: 1 rev/day = 2(pi)  / 1440 (rad/min)
"""

REV_PER_DAY = 2 * math.pi / 1440 


# what inputs do we need:
# a real TLE to use as out starting template 
# then the number of days to simulate 
# the the day on which we want the artifical maneuver
# parameters controllling the maneuver and daily decay 
def synthetic_history(
    template: TLE,
    days: int=30,
    reboost_day: int=18,
    reboost_dn: float=-0.0045,
    decay_dn: float=0.0002,
    seed: int=7 
) _> list[TLE]:
# template: starting orbital elements 
# days=30: generate 30 daily TLEs 
# reboost_day=18: insert the maneuver on simulated day index 18 
# reboost_dn=-0.0045: decrease mean motion by 0.0045 rev/day during the maneuver 
# decay_dn=0.0002: increase mean motion by 0.0002 rev/day during ordinary decay 
# seed=7: make random variation reproducible 

""" 
why would increasing mean motion represent a lower orbit?
- lets connect this back to part 1:
  - we know that mean motion and semi-major axis are related by Keplers third law:
    n = sqrt( u . a^3) // u (standard gravitational parameter) rep the gravitational strength of the central body 
    - as the semi-major axis decreases, the mean motion increases 
      - that mean lower orbits generally complete revolutions more quickly
    - so for our test:
      drag -> semi-major axis slowly decreases -> mean motion increases 
      reboost -> semi-major axis increases -> mean motion decreases 
      - that is why the reboost uses a negative reboost_dn 
"""


# make the random variation reproducible 
# add a little random noise to our generated TLEs 
# but we dont want a different database every time we run the program 
# why?
# because we are trying to debug and verify a detector 
# if the input keeps changing, comparisons become more difficult 
    rng = random.Random(seed)
    base = Satrec.twoline2rv(
    template.line1,
    template.line2 
) 
    # we want to extract several orbital elements from that record 
    n = base.no_kozai
    mo = base.mo
    node = base.nodeo 
    argp = base.argo 
    # n i SGP4s mean motion 
    # mo is mean anomaly
    # node is the right ascension of the ascending node or RAAN 
    # argp is argument of perigee 
    # the last three are orbital angles 
    # remember that we are working with an orbit that is moving and slowly precessing. As we generate future days, we need to advance those orbital angles as well (basically dont use fixed angles)
    prev = None  # remember the previous day's SGP4s satellite record     
    history = [] # collect all the artifical TLEs we are generating 
    for day in range(days):
    # we only want to apply daily cahnges when a previous record exists 
        if prev is not None:
            # calculate the mean motion; every day we add a small amount of drag 
            dn = decay_dn
            # but on day 18, we also want to include the reboost 
            if day == reboost_day: # start with the daily drag change, if today is the specified reboost day, add the reboost adjustment 
                dn += reboost_dn 
            # add a little noise 
            dn += rng.gauss(0, 0.00002) # 0 = the mean | 0.00002 = standard deviation 
            # rng.gauss() generates a random value from Gaussian, or normal, distribution
            
            # update the mean motion 
            n_new = n + dn * REV_PER_DAY
            # now we have our new mean motion, remember that we are generating a whole new TLE for the next day 
            # if we only change mean motion and leave every orbital angle fixed, the new element set would not reflect one day of orbital evolution 
            
            """ 
            Advancing the orbital angles
            - yesterday we had a satellite with a particular mean anomaly, RAAN, and argument of perigee 
              - today we are creating another TLE, one day later 
                - those values shouldnt remain unchanged
                  - we already have approximate rates of change from the previous SGP4s record 
            """
            
            # update RAAN, update minutes to one day, add it to our current node 
            node = (
            node + prev.nodedot * 1440 
        ) % (2 * math.pi)
        # why the %: because angles wrap around, an angle of 370(degrees) represents the same direction as 10(degrees)
        # update argument of perigee 
            argp = (
                argp + prev.argpdot * 1440 
        ) % (2 * math.pi)
            
            # update mean anomaly (it describes the satellite progress around its orbit)
            mo = (
                mo + (
                    prev.mdot + 0.5 * (n_new - n)
            ) * 1440
        ) % 2 (2 * math.pi)
            # why multiply by 0.05?  we are approzimating the effect of transitioning between the old and new orbital rates over the day, rather than assuming the new rate applied for the entire interval 
            n = n_new
        
        # build a new SGP4 record for each day 
        sat = Satrec()
        # now we need each epoch 
        epoch = (
            base.jdsatepoch
            + base.jdsatepochF 
            + day 
    )   
        # now we need to initialize the new satellite record 
        sat.spg4init(
            WGS72,
            "i",
            base.satnum,
            epoch - 2433281.5,
            base.bstar,
            base.ndot,
            base.nddot,
            base.ecco,
            argp,
            base.inclo,
            mo,
            n,
            node 
    )
    
""" 
Argument	            Meaning
WGS72	                Gravitational constants used by SGP4
"i"	                    Improved SGP4 operation mode
base.satnum	            Satellite catalog number
epoch - 2433281.5	    Epoch in days since the SGP4 1949 reference date
base.bstar	            B* drag parameter
base.ndot	            First mean-motion derivative field
base.nddot	            Second mean-motion derivative field
base.ecco	            Orbital eccentricity
argp	                Argument of perigee
base.inclo	            Orbital inclination
mo	                    Mean anomaly
n	                    Mean motion in radians per minute
node	                RAAN

"""


# add the remaining TLE metadata 
    
        sat.classification = "U" # U means Unclassified in the TLE classification field 
        sat.intldesg = base.intldesg # international designator 
        sat.ephtype = 0
        sat.elnum = 100 + day 
        sat.revnum = base.revnum 

        # export the record as TLE text 
        line1, line2 = export_tle(sat)
        new_tle = parse_tle(
            template.name,
            line1,
            line2 
        )
        hostory.append(new_tle)
        prev = sat 
    return history 

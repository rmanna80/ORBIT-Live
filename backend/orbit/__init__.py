

"""
Physical constrants for ORBIT Live 

kilometers, seconds, radians
"""

import math 

# earths gravity parameter, mu = G * M_earth
# measured for more precisness

MU_EARTH = 398_600.4418 # km^3 / s^2

# here will calculate the shape the GPS uses for "long, lad, alt"
R_EARTH = 6_378.127                 # km, equatorial radius  
F_EARTH = 1 / 298.257223563         # flattening (how squashed the poles are)
E2_EARTH = F_EARTH * (2 - F_EARTH)  # eccentricity squared 

OMEGA_EARTH = 7.292115e-5  # rad/s earths rotation rate relative to the stars 
JS = 1.08262668e-3         # the equatorial bulge term that makes orbits precess 

C_LIGHT = 299_792.458       # km/s 
AU = 149_597_870.7          # km, mean earth-sun disatnce 
BOLTZMANN_DBW = -228.6      # dBW/K/Hz, Boltzmann constant in decibles

SECONDS_PER_DAY = 86_400.0
TWO_PI = 2 * math.pi 


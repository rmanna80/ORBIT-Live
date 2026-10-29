import math

# Earth's gravitational parameter, mu = G * M_earth. Measured far more
# precisely than G or M on their own, so orbital mechanics uses it directly.
MU_EARTH = 398_600.4418  # km^3 / s^2

# WGS84 ellipsoid: the shape GPS uses for "latitude, longitude, altitude".
R_EARTH = 6_378.137                     # km, equatorial radius
F_EARTH = 1 / 298.257223563             # flattening (how squashed the poles are)
E2_EARTH = F_EARTH * (2 - F_EARTH)      # first eccentricity squared

OMEGA_EARTH = 7.292115e-5   # rad/s, Earth's rotation rate relative to the stars
J2 = 1.08262668e-3          # the equatorial bulge term that makes orbits precess

C_LIGHT = 299_792.458       # km/s
AU = 149_597_870.7          # km, mean Earth-Sun distance
BOLTZMANN_DBW = -228.6      # dBW/K/Hz, Boltzmann's constant in decibels

SECONDS_PER_DAY = 86_400.0
TWO_PI = 2 * math.pi

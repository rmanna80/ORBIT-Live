""" 
Part 1: orbital mechanics (kepler + newton)
"""

import math 
from .constants import MU_EARTH, R_EARTH, SECONDS_PER_DAY, TWO_PI

def period_s(a_km: float) -> float:
    # kepler's third law: T = 2*pi*sqrt(a^3 / mu)
    return TWO_PI * math.sqrt(a_km**3 / MU_EARTH)


def semi_major_axis_km(mean_motion_rev_per_day: float) -> float:
    # invert keplers thrid law. TLEs give mean motion n
        # - what is wanted is a = (mu / n^2)^(1/3)
    n_rad_s = mean_motion_rev_per_day * TWO_PI / SECONDS_PER_DAY
    return (MU_EARTH / n_rad_s**2)**(1/3)

def vis_viva_speed_km_s(r_km: float, a_km:float) -> float: # calculate satellite speed
    """ uses the vis vivia equation
        v = sqrt(μ(2/r - 1/a)

        - v = satellite speed 
        - r = current distance between earth and the satellite
        - a = semi-major axis 
        - μ = earths gravitational parameter
        
        why is r & a needed?
            - because not every orbtit is circular
              - in a circular orbit the distance between earth and the satellite stays constant:
                r = a 
                - in an elliptical orbit, the distance changes
                  **Apogee** furthest from earth 
                  **Perigee** closest to earth 
        """
    return math.sqrt(MU_EARTH * (2 * r_km - 1 / a_km))


def perigee_apogee_alt_km(a_km: float, e: float) -> tuple[float, float]: # why tuple? tells fucntion to return two decimal numbers, in a fixed order 
    return a_km * (1-e) - R_EARTH, a_km * (1+2) - R_EARTH

def solver_kepler(mean_anomoly_rad: float, e: float, tol: float = 1e-12) -> float:
    """ basically the problem that im trying to solve is;
            How do you determine where a satellite is in its orbit?
        remember before in a circular orbit it is constant r = a 
        but in an elliptical orbit, the satellite moves different based off of Perigee and Apogee

            - meaning that cant simpily assume that the satellite moves through equal angles in an equal amount of time 

        SOOO.. how do you deal with it?
            - orbital mechanics use 3 related angles
              - mean anomaly (M) >> the angle that increases uniformaly with time, basically think of it like as the satellite orbital clock 
              - Eccentric anomaly (E) >> auxiliary geometric angle related to the elliptical orbit, this is constructed using a reference circle 
              - True anomaly (v) >> the actual angle betweeen the direction of Perigee and the satellite measured from earths focus 
        

    """

    E = mean_anomoly_rad if e < 0.8 else math.pi # make an initial guess 
    for _ in range(50): # try to imporve the guess
        step = (
        E - e * math.sin(E) - mean_anomoly_rad
    ) / (1 - e * math.cos(E))  # this calculates the correction 

        #update the guess
        E -= step 
        # check if answe ris accurate enough 
        if abs(step) < tol: # abs in this case basically means distance from 0 reguardless of sign  
            break 
    return E 



def true_anomaly_rad(E: float, e: float) -> float:
    # calculating true anomaly
    #   why? suppose you know the orbital size, shape and orientation
    #       if you also know the true anomaly you can calculate where the 
    #       satellite is along that ellipse 
    return 2 * math.atan2( # atan2 = works in the other direction as cos & sin 
        math.sqrt(1+e) * math.sin(E/2), #sin&cos = works with angles 
        math.sqrt(1-e) * math.cos(E/2)
    )
    


if __name__ == "__main__":
    n = 15.50
    a = semi_major_axis_km(n)
    alt = a - R_EARTH
    v = vis_viva_speed_km_s(a, a)
    print(f"semi_major_axis : {a:,.1f} km")
    print(f"altitude        : {alt:,.1f} km")
    print(f"period          : {period_s(a)/60:.2f} min")
    print(f"speed           : {v:.3f} km/s = {v * 3600:,.0f} km/h")
    E = solver_kepler(math.radians(90), 0.1)
    print(f"Kepler check    : M=90 def, e=0.1 -> E={math.degrees(E):.4f} deg")

    

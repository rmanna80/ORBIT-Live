# what do we need?
# going to calculate logarithms, sine, and frequency shifts 
import math 
# want to reuse some of existing configurations settings 
from . import config 
# need two constants 
from .constants import BOLTZMANN_DBW, C_LIGHT 
# C_LIGHT is the speed of light 
# BOLTZMANN_DBW is Boltzmann constant (converion between temp & energy) expressed in decibel units, approximately -228.6 dBW/K/Hz
#
# because range_rate_km_s uses km per second, C_LIGHT needs to be approximately 299792.458 km/s not 299792458 m/s. Mixing thos units would make the doppler result wrong by a factor of 1,000 
#
# want a fucntion that accepst a radio frequency and the satellites range rate 
# then it should return the Doppler frequency change 
def doppler_shift_hz(freq_hz: float, range_rate_km_s: float) -> float:
# freq_hz = the transmitted carrieer frequency in hertz: ex 437 MHz = 437_000_000
# why the _?
# python allows the _ inside numbers to improve readability
# range_rate_km_s = how quicly the satellite distance from our station is changing 
    return -freq_hz * range_rate_km_s / C_LIGHT


frequency = 437_000_000 
approaching = doppler_shift_hz(frequency, -7.0)
receding = doppler_shift_hz(frequency, 7.0)
print("Approaching: ", approaching)
print("Receding: ", receding)
# this means that 437 MHz signal shifts approximately 10.2 kHz at 7km/s line-of-sight speed 
# but the satellite total orbital speed isnt always its line-of-sight speed

""" 
Understand free-space path loss 
- now we have the received frequency changes 
  - but there is another problem 
    - as the satellite gets futher away, the radio signal becomes weaker 
      - why?
        - imagine a transmitter sending radio waves equally in all directions 
          - as the waves travel outward, their energy spreads over an increasingly large area 
            - the area of a sphere is: A = 4(pi)r^2 
              - if the distance doubles, the same transmitted power is spread over four times as much area 
                - so the power density falls by a factor of four 
                  - in decibels, that is a loss of approximately 6 dB 
                    - that is why moving a satellite farther away has such a significant effect on radio communicaitons  
                  - what is a decibel?
                    - a decibel expresses ratios using logarithms 
                      for power:
                        Ldb 10log  (P^2 / P^1)
                                 10
                      some useful values:
                        - Change                Power ratio 
                          +3 dB                 approximately 2x power 
                          +6 dB                 approximately 4x power 
                          +10 dB                10x power 
                          -3 dB                 approximately half the power 
                          -6 dB                 approximately one-quater the power 
                        
                        - the advantage is that complicated multiplications and divisions become addition and subtraction 
                          - that is what makes link budgets relatively easy to implement 
                            - Our free-space path loss formula
                              in the units we are using:
                                FSPLdB = 20log  (Dkm) + 20log  (fMHz) + 32.45
                                              10             10
                              where:
                                - Dkm is distance in km 
                                - fMHz is frequency in megahertz 
                                  - this is the standard free-space path-loss expression with km/MHz unit conversion already included 
"""     


def free_space_path_loss_db(range_km: float, freq_hz: float) -> float:
    # going to need the distance between our satellite and the ground station 
    # we already calculate that with look.range_km
    # also need the radio frequency but before we do that we need to convert to megahertz:
    # 1 Mhz = 1,000,000 Hz = freq_hz / 1e6
    return (
        20 * math.log10(range_km)
        + 20 * math.log10(freq_hz / 1e6)
        + 32.45
    )

# test 
loss = free_space_path_loss_db(
    range_km=1500,
    freq_hz=437_000_000 
)
print(loss)


""" 

we know that free-space path loss handles the signal spreading out over the distance
- but signal salso travel  through earths atmosphere 
  - the amount of atmosphere a signal passes through depends on elevation
    - imagine looking straight up 
      - the signal passes through a relatively short section of the atmosphere
        - now imagine looking almost horizontally toward the horizon 
          - the path through the atmosphere is much larger 
            - so lets add a rough model for the atmospheric loss 
              equation is:
                Latm = Lzenith / sin(el)
                
                - here, L_zenith i sthe assumed loss when looking directly overhead 
                - el is elevation angle 
                  - 

"""



def atmospheric_loss_db(elevation_deg: float, zenith_loss_db: float = 0.5) -> float:
    # default assumed zenith loss is 0.5 dB 
    # btu we have to be careful about what if elevation approaches zero, then:
    #       sin(0) = 0 
    # and dividingh by zero would case a problem
    # so we will clamp  the min angle used by this approximate calculation to 3(degrees)
    return zenith_loss_db / math.sin(math.radians(max(elevation_deg, 3.0)))
    # for a 15(degree) pass, this model gives approximately 1.93 dB of atmospheric loss 


""" 
Build full link budget 
- now we have two important losses:
  - free_space_path_loss_db()
  - atmospheric_loss_db()
    - but we need to put everything together 
      - lets think about the radio system 
        - a satellite transmits power 
          - its transmitting antenna has some gain 
            - the signal loses pwoer traveling through space and the atmosphere
              - our receving antenna has gain, and the receiver has noise 
                - we want to estimate the carrier-to-noise spectral-density ratio 
                  the equation is:
                    C/N_0 = EIRP - FSPL - L_atm + c / T - k 
                  - EIRP: effective isotropic radiated power. it combines transmitted power with transmitting-antenna gain and relevant transmitter losses 
                  - FSPL: free-space path loss 
                  - atmospheric loss: our approximate extra propagation loss 
                  - G/T: receving antenna gain relative to system noise temp, expressed in dB/K 
                  - k: Boltzmann constant in dBW/K/Hz 
                  
"""

def link_budget(
        range_km: float,
        elevation_deg: float,
        freq_hz: float = config.DOWNLOAD_FREQ_HZ,
        eirp_dbw: float = config.SAT_EIRP_DBW,
        g_over_t_db: float = config.SATATION_G_OVER_T_DB,
        bandwidth_hz: float = config.BANDWIDTH_HZ
) -> dict:
    # first, check fi the satellite is above the horizion 
    # if elevation is zero or neg, there is not direct geometric line of sight under our sample spherical-horizon assumption 
    if elevation_deg <= 0:
        return {
            "visible": False,
            "snr_db": None,
            "signal_pct": 0.0 
        } # this uses 0(degree) horizon, not the station 10(degree) operation mask 
    # calculate the losses 
    fspl = free_space_path_loss_db(range_km, freq_hz)
    atm = atmospheric_loss_db(elevation_deg)
    c_n0 = (
        eirp_dbw
        - fspl 
        - atm
        + g_over_t_db
        - BOLTZMANN_DBW 
    ) # subtracting a neg number adds its magnitude 
    # ex: 
    # EIRP = 0 dBW 
    # FSPL = 148.8 dB 
    # Atmosphere = 1.9 dB
    # G/T = -20 dB/K
    # Boltzmann constant = -228.6 dBw/K/Hz 
    # then C / N_0 = 0 - 148.8 - 1.9 - 20 + 228.6
    #   = 57.9 dB-Hz
    # now we have a carrier-to-noise spectral-density radio 
    # but we want a signal-to-noise ratio for a specific receiver bandwidth 
    # we use: SNR = C / N_0 - 10log_10 (B) // where B is the receiver noise bandwidth in hertz 
    snr = c_n0 - 10 * math.log10(bandwidth_hz)
    # now we have a modeled SNR 
    # how do we convert SNR into the dashboard % 
    # we need to define a display scale 
    # 0 dB -> 0%
    # 30 dB -> 100%
    # everything inbetween is mapped linearly 
    # signal_pct = snr / 30 * 100 
    # but what is SNR is neg?
    # and if SNR exceeds 30 dB, we would get more than 100% 
    signal_pct = max (0.0, min(100.0, snr / 30 * 100))
    # min(100.0, value) prevents the value from exeeding 100 
    # max(0.0,...) prevents the value from going below zeor 
    return {
        "visible": True,
        "fspl_db": fspl,
        "atm_db": atm,
        "c_n0_dbhz": c_n0,
        "snr_db": snr,
        "signal_pct": signal_pct
    }


if __name__ == "__main__":
    f = config.DOWNLOAD_FREQ_HZ
    print(f"Doppler at 437 MHz: approaching 7 km/s -> {doppler_shift_hz(f, -7.0) / 1e3:+.1f} kHz, "
          f"receding 7 km/s -> {doppler_shift_hz(f, 7.0) / 1e3:+.1f} kHz")
    for rng, el in ((420, 90), (800, 40), (1500, 15), (2300, 5)):
        lb = link_budget(rng, el)
        print(f"range {rng:5} km, el {el:2} deg: FSPL {lb['fspl_db']:.1f} dB, "
              f"SNR {lb['snr_db']:5.1f} dB, signal {lb['signal_pct']:5.1f}%")





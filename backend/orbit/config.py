



from dataclasses import dataclass 
from pathlib import Path 

@dataclass(frozen=True)
class GroundStation:
    name: str 
    lat_deg: float 
    lon_deg: float
    alt_km: float
    min_elevation_deg: float = 10.0 


GROUND_STATION = GroundStation("Goshen, NY", 41.4020, -74.3243, 0.133) # you can change the location to your own 

TRACKED_SATELLITES = {
    25544: "ISS (ZARYA)",
    48274: "CSS (TIANHE)",
    20580: "HUBBLE",
    43013: "NOAA 20",
    49260: "LANDSAT 9",
}

DOWNLOAD_FREQ_HZ = 437.0e6
SAT_EIRP = 0.0                # 1 W into a 0 dBi antenna
SATATION_G_OVER_T_DB = -20.0  # small UHF yagi + low-noise amplifer 
BANDWIDTH_HZ = 10_000.0 

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TLE_MAX_AGE_HOURS = 2.0 # updates about every 2 hours 



""" 
this file contains the lcoal ORBIT application to CelesTrak

the role of it si to retrieve data without making unneccesary network requests 
in order to do that we build a CACHE!!!
    use a cache so that we dont generate 3600 downloads per hour for one satellite
    instead the program stores a local copy...caching 

"""


import logging 
import time 

import httpx 

from . import history 
from .config import DATA_DIR, TLE_MAX_AGE_HOURS, TRACKED_SATELLITES
from .tle import TLE, parse_tle_text


CELESTRAK_GP = "https://celestrak.org/NORAD/elements/gp.php"
CACHE_DIR = DATA_DIR / "tle_cache"
log = logging.getLogger("orbit.catelog")


def _cache_path(norad_id: int) -> str:
    return CACHE_DIR / f"{norad_id}.tle"


def _download(norad_id: int) -> str:
    resp = httpx.get(
        CELESTRAK_GP,
        params = {
            "CATNR": norad_id, "FORMAT": "TLE"
        },
        headers = {
            "User-Agent": "ORBIT-Live"
        }, 
        timeout = 15,

    )
    resp.raise_for_status()
    if "1 " not in resp.text:
        raise ValueError(f"CelesTrak returned no data for {norad_id}: {resp.test[:80]!r}")
    return resp.text

def get_tle(norad_id: int, max_age_hours: float = TLE_MAX_AGE_HOURS) -> TLE:
    """ returns a TLE, downloading only when the cached copy is to old 
            becuase of that if the download fails either the wifi drops the fall back is a stale cache and log a warning instead of crashing the program  """
    path = _cache_path(norad_id)
    cached = parse_tle_text(path.read_text())[0] if path.exists() else None
    if cached and _file_age_hours(path) < max_age_hours:
        return cached
    try: # download if unneccesary
        text = _download(norad_id)
    except (httpx.HTTPError, ValueError) as exc:
        if cached:
            log.warning("download failed for %s (%s); using cached TLE", norad_id, exc)
            return cached 
        raise 
    # save the new data 
    tle = parse_tle_text(text)[0]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(text)

    if history.save(tle):
        log.info(
            "new TLE for %s, epoch %s",
            tle.name,
            tle.epoch
        )
    return tle 

def _file_age_hours(path) -> float:
    return (time.time() - path.stat().st_mtime) / 3600

def load_tracked() -> dict[int, TLE]:
    """ TLEs for every satellite in config.TRACKED_SATELLITES (skips the ones that fail)"""
    out = {}

    for norad_id in TRACKED_SATELLITES:
        try:
            out[norad_id] = get_tle(norad_id)
        except Exception as exc:
            log.error(
                "no TLE for %s: %s",
                norad_id,
                exc 
            )
    return out 

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for norad_id, tle in load_tracked().items():
        print(f"{norad_id:>6}  {tle.name:<14} epoch {tle.epoch:%Y-%m-%d %H:%M} UTC "
              f"(age {tle.age_hours():.1f} h)")













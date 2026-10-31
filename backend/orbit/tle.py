# reading in the TLE and making it useful

from dataclasses import dataclass 
from datetime import datetime, timedelta, timezone 

from .kepler import (
    perigee_apogee_alt_km,
    semi_major_axis_km
)


@dataclass(frozen=True)
class TLE:
    name: str
    line1: str
    line2: str
    norad_id: int
    epoch: datetime
    inclination_deg: float
    raan_deg: float
    eccentricity: float
    arg_perigee_deg: float
    mean_anomaly_deg: float
    mean_motion_rev_per_day: float
    bstar: float
    rev_number: int


    @property
    def semi_major_axis_km(self) -> float:
        return semi_major_axis_km(self.mean_motion_rev_per_day)

    @property 
    def perigee_apogee_alt_km(self) -> tuple[float, float]:
        """ calculates appproximate perigee and apogee altitudes """
        return perigee_apogee_alt_km(
            self.semi_major_axis_km,
            self.eccentricity
        )

    def age_hours(self, now: datetime | None = None) -> float: # calculates TLE age 
        now = now or datetime.now(timezone.utc) # says that now can be either datetime value or None, and it defaults to None 
        return (now - self.epoch).total_seconds() / 3600  # subtract the epoch from the current time, convert diffence into seconds, divide by 3600 to get hours 


class TLEError(ValueError): # checking to see if data is valid 
    pass # basically meaning there is no additional behavior to define TLEError("invalid")

def checksum(line: str) -> int:
    """ 
    what problem is this solving?
    - when downloading satellite data and lets say one character gets changed, if the program just blindly accepts it, then it can calculate incorrect orbit
      - rule is:
        - add the value of every digit in the first 68 characters 
        - count each minus sign as 1 
        - ignore letters, spaces, decimal points, and plus sign
        - divide the total by 10 and take the remainder 
        - compare the remainder with the final character on the TLE line 
    """
    total = 0
    for ch in line[:68]:
        if ch.isdigit(): 
            total+=int(ch)
        elif ch == "-":
            total+=1 
    return total % 10 


def _implied_decimal(field: str) -> float:
    """ parse TLE exponent notation: 12345-3 means 0.12345-3"""
    field = field.strip() # remove spaces from the beginning and end of string 
    if not field:
       return 0.0
    sign = -1.0 if field[0] == "-" else 1.0 # determine the sign 
    field = field.lstrip("+-") # remove the leading sign 
    mantissa, exponent = field[:-2], field[-2:] # mantissa is the main numerical portion. the exponent determines the power of 10
    return sign * float("0." + mantissa) * 10 ** int(exponent) # calculate the real number 

def _catalog_number(field: str) -> int:
    """ when you have a catelog number they can be above 99999 in that case use 'Alpha-5: a letter 
        replaces the first digit. 
        A=10, B=11 ... (I and O are skipped so they arent confused with 1 and 0)

        kinda doing the same thing a checksum  function """

    field = field.strip()
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    if field and field[0].isalpha():
        if len(field) != 5 or field[0] not in letters or not field[1:].isdigit():
            raise ValueError("ERROR: Invalid Apha-5 catalog number")
        return (letters.index(field[0]) + 10) * 10_000 + int(field[1:])
    return int(field)

def _epoch(year2: str, day_of_year: str) -> datetime:
    """  '26301.5' means 2026, day 301, half-way through the day (UTC) """
    yy = int(year2)
    # check for 57 (handles the TLE two digis year conversions)
    year = 1900 + yy if yy >= 57 else 2000 + yy # Sputnik launched in 1957 
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    return start + timedelta(days=float(day_of_year) - 1) # subtract 1 because python starts from Jan. 1 whcih is already day 1 
                                                            # if youadded 1 full day to Jan. 1, you'd get the obv.. Jan. 2 
                                                            # in which case to represent day 1, you add zero days (to represent day 301, you add 300 days)

def parse_tle(name: str, line1: str, line2: str) -> tle:
    """ receives the three strings and returns a tle object 
        basically its job is to claen the data, validate its structure, verify its checksums,
        confirm the two lines identify the same satellite, extract each orbital field, 
        and then build the python object... simple enough lol 
        """
    line1, line2 = line1.strip(), line2.strip()
    if len(line1) != 69 or len(line2) != 69:
        raise tleerror("... each tle line must be = 69 characters")
    if line1[0] != "1" or line2[0] != "2":
        raise tleerror("the lines must start with 1 and 2 !!!")
    for line in (line1, line2):
        if checksum(line) != int(line[68]):
            raise tleerror(f"the checksum fun failed on line {line[0]}")
    # check the satellite idetifiers and see if they match 
    norad = _catalog_number(line1[2:7])
    if norad != _catalog_number(line2[2:7]):
        raise tleerror(" the numbers dont match the lines ")

    # extract all the values
    return TLE(
        name=name.strip() or str(norad),
        line1=line1,
        line2=line2,
        norad_id=norad,
        epoch=_epoch(line1[18:20], line1[20:32]),
        bstar=_implied_decimal(line1[53:61]),
        inclination_deg=float(line2[8:16]),
        raan_deg=float(line2[17:25]),
        eccentricity=float("0." + line2[36:33].strip()),
        arg_perigee_deg=float(line2[34:42]),
        mean_anomaly_deg=float(line2[43:51]),
        mean_motion_rev_per_day=float(line2[52:63]),
        rev_number=int(line2[63:68].strip() or 0),

    )


def parse_tle_text(text: str) -> list[TLE]:
    """ 
    reading multiple satellites... parse a block of TLEs, with or without the name lines 
    """
    lines = [
        ln.strip()
        for ln in text.splitlines()
            if ln.strip()
    ] # use list comprehension, basically splits the text into lines, removes empty or whitespace, and trims trailing whitespace
    tles, i = [], 0 
    # the prev function parses one satellite 
    #   this one can now parse a block containing multiple satellites
    #       
    while i < len(lines):
        # basically continues the index until it reaches the end of the list 
        # it will check two patterns
        # pattern 1 (two-line records without a name)
        # pattern 2 ( three-line records with name)
        if lines[i].startswith("1 ") and i + 1 < len(lines) and lines[i + 1].startswith("2 "):
            tles.append(parse_tle("", lines[i], lines[i + 1]))
            i += 2 
        elif i + 2 < len(lines) and lines[i + 1].startswith("1 ") and lines[i + 2].startswith("2 "):
            tles.append(parse_tle(lines[i], lines[i + 1], lines[i + 2]))
            i += 3
        else:
            raise TLEError(f" ERROR: cannot read the incoming TLE starting with line {i + 1}; {lines[i]!r} ")
    return tles # returns a list containing all successfully parsed satellite objects 



EXAMPLE_ISS = """ISS (ZARYA)
1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"""

if __name__ == "__main__":
    tle = parse_tle_text(EXAMPLE_ISS)[0]
    perigee, apogee = tle.perigee_apogee_alt_km
    print(f"{tle.name} NORAD {tle.norad_id}")
    print(f"epoch {tle.epoch:%Y-%m-%d %H:%M:%S} UTC ")
    print(f"Inclination {tle.inclination_deg} deg")
    print(f"Eccentricity {tle.eccentricity}")
    print(f"Mean Motion: {tle.mean_motion_rev_per_day} rev/day")
    print(f"B* drag {tle.bstar:.4e}")
    print(f"Perigee/Apogee {perigee:.1f} / {apogee:.1f} km")






















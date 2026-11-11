""" 
Bulding the anomaly detector
- our synthetic history is ready 
  - now what we need to do is build the actual detector
    - before writing the algorithm, lets think about what we want to return 
      - we dont just want a boolean saying True 
        - that wouldnt tell us to much 
          - we want an object containing
            - which satellite experienceed the anomaly
            - when it happened 
            - what kind of anomaly was detected 
            - how server was it 
            - a human-readable explanation 
            - the numbercioal value that triggerd the alert 
              - that way our frontend can eventually display a useful alert 

"""



from dataclasses import asdict, dataclass 
# why asdict: becuase our API might need to cover an anomaly object into a dict for JSON serialization 
from datetime import datetime, timezone 
# we are going to store anomaly times and calculate how old the newest TLE is 
import numpy as np 
from .propagate import PropagationError, Propagator 
# we will use Propagator for forecast comparsions and  PropagationError if a propagation fails 

@dataclass
class Anomaly:
    norad_int: int 
    name: str 
    epoch: datetime 
    kind: str 
    serverity: str 
    message: str 
    value: float 
    # possible (kind) values in our supplied detector inclue:
    # maneuver_raise
    # maneuver_lower
    # plane_change
    # forecast_miss
    # decay
    # stale_data
    # these are lables assigned by our model
    # for ex:
    #   maneuver_raise means we found evidence consistent with our orbit-raising maneuver not that we have verfied the spacecraft fired an engine 
    #   servity can be:
    #       info 
    #       warning 
    #       critical 


    # convert an anomaly into a dict 
    def to_dict(self) -> dict:
        d = asdict(self) # this will give us 
                #        {
                        #    "norad_id": 25544,
                        #    "name": "ISS (ZARYA)",
                        #    "epoch": some_datetime,
                        #    "kind": "maneuver_raise",
                        #    "severity": "warning",
                        #    "message": "...",
                        #    "value": 1.24
                #  }
        # convert the epoch into ISO format 
        d["epoch"] = self.epoch.isoformat()
        return d 



""" 
Understand robust Z-score 
- this is one of the most important mathetical ideas in part 8 
  - basically we need a way to answer:
    "is this daily orbital change unusually large compared with the normal daily changes?"
    - a common statical approach  is a Z-score 
      - a regular Z-score measures how far an observation is from the mean in standard-deviation units 
        - but there is a problem 
          - imagine our normal daily orbital chnages are all around -0.06 km 
            - then one day we get +1.24 km
                - that is a huge anomaly
                  - if we include that large value when calculating the mean and standard-deviation, the anomaly can influence the very statics we are using to judge it 
                    - so indead, we will use a **robust modified Z-score** based on the median and median absolute deviation (MAD)
                      - this is called the Iglewicz-Hoaglin approach, commonly using a threshold of 3.5 for potential outliers 
                - what is the median? 
                  - the median is the middle value after sorting 
                - What is MAD?
                  - MAD stands for median absolute deviation (describe spread)
                    - first, calculate the median of the values 
                      - then calculate how dar each value is from that median, using absolute differences 
                        - finally, take the median of those differences 
                    - mathetically:
                        MAD = median(|X_i - median(x)|)
                    then our modified Z-score:
                        x_i = 0.6745(x_i - median(x) / MAD) 
                        - the 0.6745 factor rescales the statistic tor be comparable to a traditional Z-score for normally distrubuted data 
"""


def robust_z(x: np.ndarray) -> np.ndarray:
    # our function accepts a NumPy array of values 
    # and returns an array of robust Z-score
    med = np.median(x)
    # find how far each value is from the median 
    x - med # that produces pos and neg differences 
    np.abs(x - med)
    mad = np.median(np.abs(x - med))
    return 0.6745 * (x - med) / max(mad, 1e-9) # max(mad, 1e-9) MAD could be zero, for ex 
                                                # if every value were identical, all the deviations would be zero 
                                                # dividing by zero would cause a numerical problem so using a small min denominator avoids that 


values = np.array([
    -0.06,
    -0.05,
    -0.07,
    -0.06,
    -0.04,
    -0.05,
    1.24,
    -0.07,
    -0.06
])
scores = robust_z(values)
print(scores)
# the 1.24km chnage should receive a much larger pos score than the ordinary changes 
# later we will use abs(z_score) > 3.5 which will decide whether a change is unusually large 




""" 
Compare two TLE predictions with forecast_miss_km()
- now here is another detection technique 
  - we dont have to rely only on semi-major axis 
    - remember the SGP4 propagator 
      - it can calculate where a satellite should be at a particular time using a particular TLE 
        - so imagine two TLEs:
          older 
          newer 
          - the older TLE was generated yesterday 
          - the newer TLE was generated today
            - here is the quesiton:
              "if i had used yesterdays TLE to predict todays satellite position, how far off would that prediction be xompared with todays TLE?"

"""


def forecast_miss_km(older: TLE, newer: TLE) -> float:
    # we are accepting two TLE objects and returning one distance in km 
    # using the old orbital model to calulate the position at the new obersvation time 
    # now what if the propagation fails?
    # raise PropagationError
    try:
        r_old - Propagator(older).teme(newer.epoch)
    except PropagationError:
        return float("nan") # nan = not a number    
    # calculate the postion from the newer TLE at its own epoch
    r_new, _ = Propagator(newer).teme(newer.epoch)
    # now we subtract the two vectors 
    r_old - r_new  # produces the thre-dimensonal displacement between the two predicted positons 
    return float(np.linalg.norm(r_old - r_new)) # that gives us the postion difference in km 
    # this source version catches propagation erros for the older TLE but not the newer one. For more robust production use, we have to handle either failure and report it seperately 
    # why is it useful? imagine normal adjacent - TLE disagreements are a few km 
    # the after an orbital maneuver, the older prediciton might disagree with the newer orbit by tens of km 
    #   that valuable evidence that the orbit has changed 


""" 
Detect anomalies 
- we have two important tools: robust_z() & forecast_miss_km()
  - now we want to combine them with our TLE history 
    - what does it need?
      - we want to pass a list of historical TLEs 
        - we also want to choose the Z-score threshold 
          - and we want an optional current time, because stale-data detection depends on how old the newest TLE is 
"""


def detect_anomalies(tles: list[TLE], z_threshold: float=3.5, now: datetime | None = None) -> list[Anomaly]:
    # first we sort the TLEs by epoch 
    # TLEs migt now come from our database in the exact order we expect so that is why we sort 
    # have to be arranged chronologically 
    tles = sorted(tles, key=lambda t: t.epoch) # what is lambda? it is a small anonymoous function 
                                                # meaning that "for eac TLE object, use its epoch as the sorting key"
                                                # so the oldest TLE comes first and the newest comes last 
    # create our output list
    found: list[Anomaly] = []
    # if user passes an empty history we shouldnt calculate anything 
    if not tles:
        return found 
    # store the newest TLE 
    latest = tles[-1]

    def add(tle, kind, severity, message, value): # our helper 
        found.append( 
            Anomaly(
                tle.norad_id,
                tle.name,
                tle.epoch,
                kind, 
                severity,
                message,
                value 
            )
        )
        # collect historical orbital measurements 
        # now we need to start looking for unexpected orbital changes 
        # the supplied implementation only performs its statical comparsions when we have at least 5 TLE 
        if len(tles) > 5: # 5 is the min safeguard, isnt enough for a highly reliable statical detector, but it gives us a starting point 
            # now we need the arrays containing the orbital measurements
            a = np.array([
                t.semi_major_axis_km
                for t in tles 
            ]) # now a contains all our semi-major axis values 
            # inclination - describes the tilt of the orbital plane 
            inc = np.array([
                t.inclinatio_deg 
                for t in tles 
            ]) # now we have historical orbit size and inclination measurements 
            # we shouldn't blindly assume every measurement of TLE is one day apart 
            # we need to calculate the actual elasped time 
            days = np.array([
                (t.epoch - tles[0].epoch).total_seconds() / 86400
                for t in tles
            ]) # 86,400 is the amount of seconds in a day 













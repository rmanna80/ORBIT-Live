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
    # decay
    # stale_data
    # these are lables assigned by our model
    # for ex:
    #   maneuver_raise means we found evidence consistent with our orbit-raising maneuver not that we have verfied the spacecraft fired an engine 
    #   servity can be:
    #       info 
    #       warning 
    #       critical 

import numpy as np 

from .propagate import PropagationError, Propagator 
from .tle import TLE 


@dataclass 
class Anomaly:
    norad_id: int 
    name: str 
    epoch: datetime 
    kind: str 
    severity: str 
    message: str 
    value: float 

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
        r_old, _ = Propagator(older).teme(newer.epoch)
    except PropagationError:
        return float("nan") # nan = not a number    
    # calculate the postion from the newer TLE at its own epoch
    r_new, _ = Propagator(newer).teme(newer.epoch)
    # now we subtract the two vectors 
    # r_old - r_new  # produces the thre-dimensonal displacement between the two predicted positons 
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
            t.inclination_deg 
            for t in tles 
        ]) # now we have historical orbit size and inclination measurements 
        # we shouldn't blindly assume every measurement of TLE is one day apart 
        # we need to calculate the actual elasped time 
        days = np.array([
            (t.epoch - tles[0].epoch).total_seconds() / 86400
            for t in tles
        ]) # 86,400 is the amount of seconds in a day 
            # now days might look like:
            # [0.0, 1.0. 2.0. 3.5, 4.5] -> this tells us how far apart out observations are 
        
        # now we want to calculate the rate of orbital change 
        # we want to measure how quickly the semi-major axis changes 
        # ex: if it shrinks 0.06km over one day, its -0.06km/day
        #       if it shrinks 0.12 over two days then its -0.06km/day 
        #           basically we need to divide the changes in orbital size by changes in time 
        # need to calculate the difference between the consecutive timestamps 
        # in this case = np.diff(days) -> subtracts the neighboring values 
        # ex: np.diff([0, 1, 2, 4]) -> [1, 1, 2]
        dt = np.maximum(np.diff(days), 1e-3) # ensures that every interval used in the division is at least 0.001 days = 86.4 secconds 
        # now we have to calculate the differences in the semi-major axis 
        # again we would use np.diff(a) -> a lets say contains [6730.90, 6730.84, 6730.78] -> returns [-0.06, -0.06]
        # from that we will divide by the time intervals 
        da_rate = np.diff(a) / dt 
        # calculate the robust Z-scores 
        z = robust_z(da_rate) # now every TLE pair has a corresponding anomaly score 
                                # large pos number ~ unusually strong orbit increase relative to the baseline 
                                # large neg number ~ unusually strong decrease 
        # now we need to calculate the forecast misses for every TLE pair 
        # we know that our first signal measures orbital-size changes 
        #   now we can calculate our second signal: which is the difference between the old and the new orbital predictions 
        misses = np.array([
            forecast_miss_km(p, c)
            for p, c in zip(tles, tles[1:])
        ]) # now misses contains a forecast error for each neighboring TLE pair 
            # reminder that forecast_miss_km() can return  a float meaning that if SGP4 propagation fails we wouldnt want NaN to break our calculation 
        fill = (
            np.nanmedian(misses)
            if np.isfinite(misses).any()
            else 0.0 
        ) 
        # now we replace the invalid values
        misses = np.where(
            np.isfinite(misses),
            misses,
            fill 
        )

        """ np.where() -> selecting values based on a condition
                - meaning that if a forecast miss is finite, use its actual value 
                    - otherwise use the fallback median 

                    - note to self: replacing failed propagation with an ordinary value can hide important data 
                        quality problems. 
                        - meaning should preserve the failure as a seperate alert and exclude it from the baseline calculation"""


        #  calculate robust Z-scores for the forecast_miss
        miss_z = robust_z(misses)

        # detect possible maneuvers 
        # now comes the decision making logic 
        # we have out history 
        # we have the semi-major axis changes 
        # we have robust z-score 
        # we have forecast misses
        # -> now we need to decide which observation to flag meaning that we will have to loop through all TLEs expect the first one (why? each anomaly comapres a TLE with its predecessor)
        for k, tle in enumerate(tles[1:]):
            # calculate the actual change in semi-major axis 
            da = a[k + 1] - a[k] # k + 1 becuase we are comapring the newer TLE against the previous one 
            if abs(z[k]) > z_threshold and abs(da) > 0.2: # meaning: abs(z[k]) > z_threshold akss whether the robust z-score exceeds our anomaly threshold (by default it is 3.5)
                                                            # abs(da) > 0.2: baically the statistical signifiance alone doesnt calculate physical important changes 
                                                            # meaning that if out baseline variation is extremely small, even a tiny absolute change might get a huge z-score 
                                                            # the 0.2 km cuttoff is a heuristic selected just for this, its not like a universal num that is used 
                # if da > 0 the semi-major axis increased 
                kind = (
                    "manuever_raise"
                    if da > 0
                    else "manuever_lower"
                )
                # now save the anomaly
                add(
                    tle, 
                    kind,
                    "warning",
                    (
                        f"semi-major axis changed {da:+.2f} km"
                        f"(z={z[k]:+.1f}); "
                        f"previous TLE missed by {misses[k]:.0f} km"
                    ),
                    da 
                )

                """ 
                basically from add >> we are recording the following:
                    - how much the semi-major axis has changed 
                    - its robust z-score
                    - how far the odler TLEs prediciton disagreed with the newer one 

                this makes the alert useful rather than just saying like anomaly detected
                """
            

            # detect unusal forecast disagreements 
            # meaning if the semi-major axis doesnt change big enough to trigger our maneuver condition
            # but the old TLEs predicted postion differs signifianly from the new TLEs prediciton
            elif miss_z[k] > 2 * z_threshold and misses[k] > 10: 
            # miss_z[k] > 2 * z_threshold: requires the forecast miss to have an unusally high ribust z-score >> since our threshold is 3.5, need a score greater than 7 
            # misses[k] > 10: requires an absolute forecast disagreement greater than 10 km 
                add(
                    tle, 
                    "forecast_miss",
                    "info",
                    (
                        f"previous TLE missed by {misses[k]:.0f} km"
                        f"with no clear orbit change"
                    ),
                    misses[k]
                )

            """ 
            Detect arubt inclination changes 
            - now we want to detect potential orbital plane changes 
                - we already have stored all of the inclination values in: inc 
                - compare them to consecutive incliantions: inc[k + 1] - inc[k]
                    
                that gives us the incliantion change in degrees 
            """



            if abs(inc[k + 1] - inc[k]) > 0.02:
                add(
                    tle, 
                    "plane_change",
                    "warining",
                (
                        f"Incliantion changed"
                        f"{inc[k + 1] - inc[k]:.3f} deg"
                    ),
                    inc[k + 1] - inc[k]
                )




# check whether the satellite is entering a low orbit 
# - now we are done with looking at consecutive changes in TLEs
# - but there is still our detector that should also look at the newest satellite orbital condition 
# - use perigee (lowest point of the orbit) & apogee
        # meaning that if the perigee gets very low, atmospheric drag can become much stronger 


    perigee, _ = latest.perigee_apogee_alt_km
# check the thresholds 
    if perigee < 180:
        add(
            latest,
            "decay",
            "critial",
            f"Perigee {perigee:.0f} km: re-entry risk",
            perigee
        ) 
    elif perigee < 250:
        add(
            latest,
            "decay",
            "warinig",
            f"Perigee {perigee:.0f} km: low orbit",
            perigee
        )
        # detect stale TLE data meaning if we havent received a new TLE for several days this can cause our predicitons to become inaccurate 
        # so we want to know hether the newest orbital information is to old 
    age = latest.age_hours(
        now or datetime.now(timezone.utc)
    )
        # now check the age 
    if age > 72: # meaning 3 days 
        add(
            latest,
            "stale_data",
            "info",
            (
                f"newest TLE is {age / 24:.1f} days old; "
                f"postions may be less reliable"
            ),
            age 
        )
    return found 




            
            

            
if __name__ == "__main__":
    from .synthetic import synthetic_history
    from .tle import EXAMPLE_ISS, parse_tle_text

    template = parse_tle_text(EXAMPLE_ISS)[0]
    history = synthetic_history(template, days=30, reboost_day=18)
    print("day  epoch        a (km)    forecast miss (km)")
    for k, (p, c) in enumerate(zip(history, history[1:]), start=1):
        print(f"{k:>3}  {c.epoch:%m-%d %H:%M}  {c.semi_major_axis_km:9.3f}  {forecast_miss_km(p, c):8.1f}")
    print()
    for an in detect_anomalies(history, now=history[-1].epoch):
        print(f"[{an.severity.upper()}] {an.epoch:%Y-%m-%d} {an.kind}: {an.message}")










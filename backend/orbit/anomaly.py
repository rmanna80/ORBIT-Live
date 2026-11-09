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











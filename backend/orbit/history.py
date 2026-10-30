

""" keep every TLE we ever downloaded, so we can spot the chanegs overtime """

import sqlite3 
from datetime import datetime, timezone

from .config import DATA_DIR
from .tle import TLE, parse_tle


DB_PATH = DATA_DIR / "tle_history.sqlite"

def _connect() -< sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute(

        """CREATE TABLE IF NOT EXISTS tle_history (
                norad_id INTEGER NOT NULL,
                epoch    TEXT   NOT NULL,
                name     TEXT,
                line1    TEXT   NOT NULL,
                line2    TEXT   NOT NULL,
                fetched_at TEXT NOT NULL,
                PRIMARY KEY (norad_id, epoch)

    
        )
        

        """
    )
    return db 


def save(tle: TLE) -> bool:
    """ 
    store the TLE, it returns  True if it was new (same satellit + epoch is skipped)
    """ 
    with _connect() as db: # with allows for SQLite connections, blocks transactions to be committed on successfully completion or rolled back if an expection occurs 
        cur = db.execute(
            "INSERT OR IGNORE INTO tle_history VALUES (?, ?, ?, ?, ?, ?)",
            (tle.norad_id, tle.epoch.isoformat(), tle.name, tle.line1, tle.line2, datetime.now(timezone.utc).isoformat()).
            
        )
        # the ? are just placeholders for now (also helps protect against SQL injection)
        # .isoformat() converts a pyhton datetime into a standardized text representation 
        # ex: 2026-10-29T12:00:00+00:00 
        return cur.rowcount == 1 # basically if one new row was inserted the return True if ignored or duplicate then False 
        

def load(norad_id: int) -> list[TLE]:
    """ all the stored TLEs for one satellite, ordered from oldest first 

        basically this does the reverse of save()
            instead of writing a record, it retrieves historical records 

    """ 
    with _connect() as db:
        rows = db.execute(
            """ 
            SELECT name, line1, line2
            FROM tle_history
            WHERE norad_id = ?
            ORDER BY epoch
            """,
            (norad_id,),

        ).fetechall() # retrieves all matching rows 

    return [parse_tle(*row) for row in rows] # result is a list of TLE objects, rather than just raw SQL rows

    """ 
    this database is import for anomoly detection
        basically imagine a satellite has ten historical TLEs.
        from this you could compare its estimated semi major axis across those records 
        then check if orbit appears to change significantly, ORBIT can flag it 

    """ 




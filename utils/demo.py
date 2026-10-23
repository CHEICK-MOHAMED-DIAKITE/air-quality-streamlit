"""Generator of SYNTHETIC data in the EEA extraction format (tests and fallback only).
Never present these values as measurements."""
import numpy as np
import pandas as pd

from config import SEEDS

NETWORKS = {
    "NET-FR004A": ("AIRPARIF", 48.85, 2.35), "NET-FR074A": ("ATMO HAUTS DE FRANCE", 50.63, 3.06),
    "NET-FR072A": ("ATMO AUVERGNE-RHONE-ALPES", 45.75, 4.85), "NET-FR071A": ("ATMOSUD", 43.30, 5.37),
    "NET-FR073A": ("ATMO OCCITANIE", 43.60, 1.44), "NET-FR069A": ("ATMO GRAND EST", 48.58, 7.75),
}
TYPES = [("Traffic", "Urban", 1.6), ("Background", "Urban", 1.0), ("Background", "Suburban", 0.8), ("Background", "Rural", 0.45)]
BASE = {"NO2": 30, "PM10": 24, "PM2.5": 15, "O3": 48}
DECLINE = {"NO2": 0.045, "PM10": 0.03, "PM2.5": 0.04, "O3": -0.006}


def generate() -> pd.DataFrame:
    rng = np.random.default_rng(SEEDS["demo"])
    rows, sid = [], 11000
    for net, (name, la, lo) in NETWORKS.items():
        for st_type, area, mult in TYPES:
            for _ in range(3):
                sid += 1
                lat, lon = la + rng.normal(0, .3), lo + rng.normal(0, .4)
                for pol in BASE:
                    m = (2 - mult) if pol == "O3" else mult
                    for y in range(2005, 2026):
                        v = BASE[pol] * m * np.exp(-DECLINE[pol] * (y - 2005)) * (1 + rng.normal(0, .06))
                        flow = "Reporting within EoI/AirBase 8" if y < 2013 else "E1a/validated data AQ e-Reporting"
                        rows.append({
                            "Country": "France", "Air Quality Network": net, "Air Quality Network Name": name,
                            "Air Quality Station EoI Code": f"FR{sid}", "Air Quality Station Name": f"Demo station {sid}",
                            "Sampling Point Id": f"SPO-FR{sid}_{pol}", "Air Pollutant": pol, "Year": y,
                            "Air Pollution Level": round(v, 3), "Unit Of Air Pollution Level": "ug/m3",
                            "Data Coverage": float(np.clip(rng.normal(93, 9), 30, 100)), "Verification": 1,
                            "Air Quality Station Type": st_type, "Air Quality Station Area": area,
                            "Longitude": lon, "Latitude": lat, "Altitude": 50, "City": None,
                            "Source Of Data Flow": flow,
                        })
    df = pd.DataFrame(rows)
    return pd.concat([df, df.sample(20, random_state=SEEDS["demo"])], ignore_index=True)  # deliberate duplicates

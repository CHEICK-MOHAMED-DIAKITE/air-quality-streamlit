"""Central configuration: data source, schema, regulatory thresholds, labels."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"

# --------------------------------------------------------------------------------------
# Source: "Air Quality e-Reporting: Air quality annual statistics calculated by the EEA"
#         (European Environment Agency), listed on data.europa.eu.
# Extraction: Country = France, one file per pollutant (NO2, PM10, PM2.5, O3),
#             DataAggregationProcess = "Annual mean / 1 calendar year"
# --------------------------------------------------------------------------------------
DATASET_NAME = "Air Quality e-Reporting: Air quality annual statistics calculated by the EEA"
DATASET_PAGE = "https://data.europa.eu/data/datasets/6e191a3b-258d-491e-b636-6cbb15cf473b?locale=en"
VIEWER_URL = "https://discomap.eea.europa.eu/App/AQViewer/index.html?fqn=Airquality_Dissem.b2g.AirQualityStatistics"
# The EEA table viewer only accepts one pollutant per extraction: one link (and one file) per pollutant
DOWNLOAD_URLS = {p: f"{VIEWER_URL}&Country=France&AirPollutant={p}&DataAggregationProcess=Annual%20mean%20/%201%20calendar%20year"
                 for p in ["NO2", "PM10", "PM2.5", "O3"]}
LICENSE = "EEA data - free re-use with attribution (EEA standard re-use policy, CC BY 4.0)"
RAW_PATTERNS = ["DataExtract*.zip", "DataExtract*.csv", "eea*.zip", "eea*.csv"]  # every matching file is read

# EEA column -> canonical name used in the app (the only place to change if the source format changes)
COLUMN_MAP = {
    "Air Quality Network": "network_code",
    "Air Quality Network Name": "network",
    "Air Quality Station EoI Code": "station_id",
    "Air Quality Station Name": "station",
    "Sampling Point Id": "sampling_point",
    "Air Pollutant": "pollutant",
    "Year": "year",
    "Air Pollution Level": "value",
    "Unit Of Air Pollution Level": "unit",
    "Data Coverage": "coverage",
    "Verification": "verification",
    "Air Quality Station Type": "station_type_en",
    "Air Quality Station Area": "station_area_en",
    "Longitude": "lon",
    "Latitude": "lat",
    "Altitude": "alt",
    "City": "city",
    "Source Of Data Flow": "flow",
}
REQUIRED = ["station_id", "pollutant", "year", "value"]

POLLUTANTS = {
    "NO2": "Nitrogen dioxide (NO₂)",
    "PM10": "Particulate matter PM10",
    "PM2.5": "Fine particles PM2.5",
    "O3": "Ozone (O₃)",
}
POLLUTANT_NOTE = {
    "NO2": "Mostly emitted by road traffic (diesel engines). Irritates the airways.",
    "PM10": "Particles < 10 µm: wood heating, traffic, industry, agriculture, dust.",
    "PM2.5": "Particles < 2.5 µm: reach deep into the lungs; the pollutant with the largest health impact.",
    "O3": "Secondary pollutant formed in sunlight from NO₂ and VOCs: higher in summer and outside cities.",
}

# Annual thresholds (µg/m³). Sources: Directive 2008/50/EC (limit values in force until 2029),
# Directive (EU) 2024/2881 (2030 limit values), WHO Air Quality Guidelines 2021.
# Ozone has no annual-mean limit value (regulated on the 8-hour mean): no threshold is shown for it.
THRESHOLDS = {
    "NO2":   {"EU current": 40, "EU 2030": 20, "WHO 2021": 10},
    "PM10":  {"EU current": 40, "EU 2030": 20, "WHO 2021": 15},
    "PM2.5": {"EU current": 25, "EU 2030": 10, "WHO 2021": 5},
}
THRESHOLD_NAMES = ["EU current", "EU 2030", "WHO 2021"]

# Cleaning rules (documented in the Data tab and in the README)
MIN_COVERAGE = 75.0          # % of valid data in the year
MIN_STATIONS_YEAR = 20       # below this, a year is not representative (1980s network)
VALUE_RANGE = (0.0, 300.0)   # plausibility bounds for an annual mean (µg/m³)
FLOW_PRIORITY = {"E1a": 0, "AirBase": 1, "E2a": 2}   # validated > historical > provisional (UTD)

# Station typology: (EEA type, EEA area) -> label
STATION_CLASS = {
    ("Traffic", None): "Traffic",
    ("Industrial", None): "Industrial",
    ("Background", "Urban"): "Urban background",
    ("Background", "Suburban"): "Suburban background",
    ("Background", "Rural"): "Rural background",
}
CLASS_ORDER = ["Traffic", "Urban background", "Suburban background", "Rural background", "Industrial"]

SEEDS = json.loads((ROOT / "seeds.json").read_text())

"""Key figures computed once (independent of the filters) for the hook and the conclusions.
No figure of the story is typed by hand: they all come from these functions."""
import pandas as pd

from config import THRESHOLDS
from utils.prep import panel_stations


def first_solid_year(d: pd.DataFrame, min_stations: int = 50, floor: int = 2005) -> int:
    """First year (>= floor) in which the network of a pollutant has at least `min_stations` stations."""
    n = d.groupby("year")["station_id"].nunique()
    ok = n[(n >= min_stations) & (n.index >= floor)]
    return int(ok.index.min()) if len(ok) else int(d["year"].min())


def pollutant_facts(df: pd.DataFrame, pollutant: str) -> dict:
    d = df[(df["pollutant"] == pollutant) & (df["station_class"].astype(str) != "Industrial")]
    if d.empty:
        return {}
    y0, y1 = first_solid_year(d), int(d["year"].max())
    # Change measured on a stable panel (same stations at the start and at the end)
    p = d[d["station_id"].isin(panel_stations(d, y0, y1, 0.7))]
    base = p if p["station_id"].nunique() >= 10 else d
    m0, m1 = base[base["year"] == y0]["value"].mean(), base[base["year"] == y1]["value"].mean()
    last = d[d["year"] == y1]
    out = {"pollutant": pollutant, "y0": y0, "y1": y1, "m0": m0, "m1": m1, "chg": (m1 - m0) / m0 * 100,
           "n_panel": base["station_id"].nunique(), "n_last": last["station_id"].nunique()}
    thr = THRESHOLDS.get(pollutant)
    if thr:
        out.update({
            "eu_now_last": (last["value"] > thr["EU current"]).mean() * 100,
            "eu2030_last": (last["value"] > thr["EU 2030"]).mean() * 100,
            "who_last": (last["value"] > thr["WHO 2021"]).mean() * 100,
            "eu_now_y0": (d[d["year"] == y0]["value"] > thr["EU current"]).mean() * 100,
            "eu2030_y0": (d[d["year"] == y0]["value"] > thr["EU 2030"]).mean() * 100,
        })
    by_cls = last.groupby(last["station_class"].astype(str))["value"].mean()
    out["by_class_last"] = by_cls.to_dict()
    return out


def all_facts(df: pd.DataFrame) -> dict:
    return {p: pollutant_facts(df, p) for p in ["NO2", "PM10", "PM2.5", "O3"]}

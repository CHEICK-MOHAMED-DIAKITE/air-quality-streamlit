"""Cleaning, validation and feature engineering.

Pipeline: normalize() -> quality_report() [on raw data] -> clean() -> add_features() -> tables / analyses.
Every cleaning rule is counted in `log` so that it can be shown in the "Data & caveats" tab.
"""
import numpy as np
import pandas as pd

from config import (CLASS_ORDER, COLUMN_MAP, FLOW_PRIORITY, MIN_COVERAGE, MIN_STATIONS_YEAR, REQUIRED,
                    STATION_CLASS, THRESHOLD_NAMES, THRESHOLDS, VALUE_RANGE)
from utils.regions import region_of

KEY = ["station_id", "pollutant", "year"]


# ----------------------------------------------------------------------------- normalisation (schema)
def normalize(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in raw.columns})
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Adapt COLUMN_MAP in config.py "
                         f"(file columns: {list(raw.columns)[:25]})")
    for c in COLUMN_MAP.values():
        if c not in df.columns:
            df[c] = np.nan
    df = df[list(COLUMN_MAP.values())].copy()
    df["flow"] = df["flow"].astype(str).map(_flow_code)
    for c in ["value", "coverage", "lat", "lon", "alt", "verification"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["pollutant"] = df["pollutant"].astype(str).str.strip()
    # Inconsistent case in the source ("urban" / "Urban"): harmonise
    for c in ["station_type_en", "station_area_en"]:
        df[c] = df[c].astype(str).str.strip().str.title().replace({"Nan": None, "Unknown": None})
    return df


def _years_txt(ys) -> str:
    if not ys:
        return "none"
    return f"{min(ys)}–{max(ys)}" if len(ys) > 2 else ", ".join(map(str, ys))


def _flow_code(s: str) -> str:
    if s.startswith("E1a"):
        return "E1a"
    if s.startswith("E2a"):
        return "E2a"
    if "AirBase" in s:
        return "AirBase"
    return "Other"


# ----------------------------------------------------------------------------- checks
def quality_report(df: pd.DataFrame) -> dict:
    """Checks computed on the data BEFORE cleaning."""
    cov_by_year = df.groupby("year")["coverage"].median()
    return {
        "n_rows": len(df),
        "n_stations": int(df["station_id"].nunique()),
        "years": (int(df["year"].min()), int(df["year"].max())),
        "duplicates": int(df.duplicated().sum()),
        "missing_pct": (df.isna().mean() * 100).round(1).sort_values(ascending=False),
        "units": df["unit"].value_counts(dropna=False).to_dict(),
        "flows": df["flow"].value_counts().to_dict(),
        "rows_per_year": df.groupby("year").size(),
        "median_cov_by_year": cov_by_year,
        "multi_spo": int(df.drop_duplicates().duplicated(KEY, keep=False).sum()),
    }


# ----------------------------------------------------------------------------- cleaning
def clean(df: pd.DataFrame):
    """Applies the validity rules. Returns (clean_df, log of removed rows)."""
    log = []

    def step(label, before, after, rule):
        log.append({"Step": label, "Rule": rule, "Rows removed": before - after, "Rows remaining": after})

    n = len(df)
    df = df.drop_duplicates()
    step("Exact duplicates", n, len(df), "Strictly identical rows")

    n = len(df)
    df = df.dropna(subset=["value", "year", "station_id"])
    step("Missing values", n, len(df), "Missing concentration, year or station")

    n = len(df)
    df = df[df["unit"].isna() | (df["unit"].astype(str).str.lower().str.replace("µ", "u") == "ug/m3")]
    step("Unit", n, len(df), "Unit other than µg/m³")

    # Unusable years: (a) embryonic network (< MIN_STATIONS_YEAR stations), (b) current year published
    # only as provisional E2a data (not validated, incomplete year)
    n = len(df)
    by_year = df.groupby("year").agg(n=("station_id", "nunique"), prov=("flow", lambda s: (s == "E2a").mean()))
    sparse = [int(y) for y in by_year.index[by_year["n"] < MIN_STATIONS_YEAR]]
    prov = [int(y) for y in by_year.index[by_year["prov"] > 0.5]]
    df = df[~df["year"].isin(sparse + prov)]
    step("Unusable years", n, len(df),
         f"Fewer than {MIN_STATIONS_YEAR} stations: {_years_txt(sparse)}; provisional, non-validated data (E2a): {_years_txt(prov)}")

    n = len(df)
    df = df[df["coverage"].isna() | (df["coverage"] >= MIN_COVERAGE)]
    step("Insufficient coverage", n, len(df), f"Less than {MIN_COVERAGE:.0f}% valid data in the year")

    n = len(df)
    lo, hi = VALUE_RANGE
    df = df[(df["value"] >= lo) & (df["value"] <= hi)]
    step("Outliers", n, len(df), f"Annual mean outside [{lo:.0f}; {hi:.0f}] µg/m³")

    # Several sampling points / data flows for the same station-pollutant-year:
    # keep the most reliable flow (validated > historical > provisional), then the best coverage.
    n = len(df)
    df = (df.assign(_prio=df["flow"].map(FLOW_PRIORITY).fillna(9))
            .sort_values(["_prio", "coverage"], ascending=[True, False])
            .drop_duplicates(KEY, keep="first")
            .drop(columns="_prio"))
    step("De-duplication station-pollutant-year", n, len(df),
         "One value per station, pollutant and year (validated flow first, then highest coverage)")

    df = df.copy()
    df["year"] = df["year"].astype(int)
    return df.sort_values(KEY).reset_index(drop=True), pd.DataFrame(log)


# ----------------------------------------------------------------------------- features
def station_class(t, a) -> str:
    if t in ("Traffic", "Industrial"):
        return STATION_CLASS[(t, None)]
    return STATION_CLASS.get((t, a), "Other")


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Station metadata can vary from one year to the next: keep the most recent one
    meta = (df.sort_values("year").groupby("station_id")
              [["station", "network", "network_code", "station_type_en", "station_area_en", "lat", "lon", "alt", "city"]]
              .last())
    df = df.drop(columns=meta.columns).merge(meta, left_on="station_id", right_index=True, how="left")
    df["station_class"] = [station_class(t, a) for t, a in zip(df["station_type_en"], df["station_area_en"])]
    df["region"] = [region_of(code, name, lat, lon) for code, name, lat, lon
                    in zip(df["network_code"], df["network"], df["lat"], df["lon"])]
    df["station"] = df["station"].fillna(df["station_id"]).astype(str).str.title()
    for lim in THRESHOLD_NAMES:
        thr = df["pollutant"].map(lambda p: THRESHOLDS.get(p, {}).get(lim, np.nan))
        df[f"over_{lim}"] = np.where(thr.notna(), df["value"] > thr, np.nan)
    df["who_ratio"] = df["value"] / df["pollutant"].map(lambda p: THRESHOLDS.get(p, {}).get("WHO 2021", np.nan))
    df["station_class"] = pd.Categorical(df["station_class"], categories=CLASS_ORDER + ["Other"], ordered=True)
    return df


# ----------------------------------------------------------------------------- analyses
def panel_stations(d: pd.DataFrame, y0: int, y1: int, min_share: float = 0.8) -> pd.Index:
    """"Stable" stations: measured in at least `min_share` of the years in [y0, y1] (removes the effect of
    stations opening/closing on the averages)."""
    span = d[d["year"].between(y0, y1)]
    counts = span.groupby("station_id")["year"].nunique()
    return counts[counts >= min_share * (y1 - y0 + 1)].index


def timeseries(d: pd.DataFrame, by: str = "station_class") -> pd.DataFrame:
    g = d.groupby([by, "year"], observed=True)["value"]
    out = g.agg(mean="mean", median="median", n="count").reset_index()
    return out


def share_over(d: pd.DataFrame, pollutant: str) -> pd.DataFrame:
    """Share of stations above each threshold, per year."""
    d = d[d["pollutant"] == pollutant]
    cols = [c for c in d.columns if c.startswith("over_")]
    out = d.groupby("year")[cols].mean().mul(100).reset_index()
    return out.rename(columns={c: c.replace("over_", "") for c in cols})


def before_after(d: pd.DataFrame, pivot: int, width: int = 3) -> pd.DataFrame:
    """Mean per station over `width` years before (pivot included) and after the pivot.
    A station is kept only if it has at least 2 measured years on each side."""
    b = d[d["year"].between(pivot - width + 1, pivot)]
    a = d[d["year"].between(pivot + 1, pivot + width)]
    g = ["station_id", "station", "region", "station_class", "lat", "lon"]
    agg = lambda x: x.groupby(g, observed=True, dropna=False)["value"].agg(["mean", "count"])
    out = agg(b).join(agg(a), lsuffix="_before", rsuffix="_after", how="inner").reset_index()
    out = out[(out["count_before"] >= 2) & (out["count_after"] >= 2)]
    out = out.rename(columns={"mean_before": "before", "mean_after": "after"})
    out["delta"] = out["after"] - out["before"]
    out["delta_pct"] = out["delta"] / out["before"].where(out["before"] > 0) * 100
    return out.drop(columns=["count_before", "count_after"])


def station_trends(d: pd.DataFrame, y0: int, y1: int, min_years: int = 6, horizon: int = 2030) -> pd.DataFrame:
    """Simple model: linear regression per station (least squares) over [y0, y1].
    Slope in µg/m³/year, annual change in %, R², and an "if the trend continues" projection to `horizon`."""
    d = d[d["year"].between(y0, y1)]
    rows = []
    for (sid, st, reg, cls, lat, lon), s in d.groupby(["station_id", "station", "region", "station_class", "lat", "lon"],
                                                      observed=True, dropna=False):
        if s["year"].nunique() < min_years:
            continue
        x, y = s["year"].to_numpy(float), s["value"].to_numpy(float)
        slope, intercept = np.polyfit(x, y, 1)
        fit = slope * x + intercept
        ss_res, ss_tot = ((y - fit) ** 2).sum(), ((y - y.mean()) ** 2).sum()
        last = y[np.argmax(x)]
        rows.append({"station_id": sid, "station": st, "region": reg, "station_class": cls, "lat": lat, "lon": lon,
                     "n_years": len(x), "last_year": int(x.max()), "last_value": last,
                     "slope": slope, "slope_pct": slope / y.mean() * 100 if y.mean() > 0 else np.nan,
                     "r2": 1 - ss_res / ss_tot if ss_tot > 0 else np.nan,
                     "proj": max(0.0, slope * horizon + intercept)})
    return pd.DataFrame(rows)


def project_share(tr: pd.DataFrame, threshold: float, extra_cut_pct: float = 0.0, horizon: int = 2030) -> dict:
    """What-if: share of stations above a threshold in `horizon` if the trend continues
    and an extra effort cuts levels by a further `extra_cut_pct` % per year."""
    if tr.empty:
        return {"now": np.nan, "trend": np.nan, "scenario": np.nan}
    yrs = horizon - tr["last_year"]
    scen = tr["proj"] * (1 - extra_cut_pct / 100) ** yrs
    return {"now": (tr["last_value"] > threshold).mean() * 100,
            "trend": (tr["proj"] > threshold).mean() * 100,
            "scenario": (scen > threshold).mean() * 100,
            "scen_values": scen}

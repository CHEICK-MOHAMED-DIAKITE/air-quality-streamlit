"""Data loading: local EEA extractions (zip or csv) in data/, otherwise a synthetic demo mode.

The EEA viewer only exports one pollutant at a time, so data/ holds one file per pollutant.
All of them are read and stacked."""
from pathlib import Path

import pandas as pd

from config import DATA_DIR, RAW_PATTERNS
from utils.demo import generate


def find_raw_files(data_dir: Path = DATA_DIR) -> list:
    files = set()
    for pattern in RAW_PATTERNS:
        files.update(data_dir.glob(pattern))
    return sorted(files)


def load_raw(path: Path) -> pd.DataFrame:
    """Reads one EEA extraction as is (the zip contains a single CSV)."""
    return pd.read_csv(path, compression="infer", encoding="utf-8-sig", low_memory=False)


def load_data():
    """Returns (raw DataFrame, source, file description); source in {'real', 'demo'}."""
    files = find_raw_files()
    if files:
        parts = [load_raw(p) for p in files]
        raw = pd.concat(parts, ignore_index=True)
        names = ", ".join(f"{p.name} ({len(x):,} rows)" for p, x in zip(files, parts))
        return raw, "real", names
    return generate(), "demo", "synthetic data"

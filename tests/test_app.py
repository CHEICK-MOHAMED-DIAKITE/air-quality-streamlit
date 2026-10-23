"""Smoke tests: the data pipeline and the app run without errors for every pollutant."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from utils.demo import generate
from utils.prep import add_features, before_after, clean, normalize, station_trends

APP = str(Path(__file__).parent.parent / "app.py")


def test_pipeline_on_demo():
    df, log = clean(normalize(generate()))
    df = add_features(df)
    assert not df.duplicated(["station_id", "pollutant", "year"]).any()
    assert (df["value"] >= 0).all() and (df["coverage"].fillna(100) >= 75).all()
    assert log["Rows removed"].sum() > 0
    no2 = df[df["pollutant"] == "NO2"]
    assert len(before_after(no2, 2015, 3)) > 0
    assert len(station_trends(no2, 2015, 2025)) > 0


def test_app_runs_all_pollutants():
    at = AppTest.from_file(APP, default_timeout=180).run()
    assert not at.exception, at.exception
    for p in ["PM10", "PM2.5", "O3", "NO2"]:
        at.sidebar.selectbox[0].set_value(p).run()
        assert not at.exception, (p, at.exception)
    at.sidebar.toggle[0].set_value(False).run()
    assert not at.exception, at.exception

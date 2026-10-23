import plotly.express as px
import streamlit as st

from config import DATASET_NAME, DATASET_PAGE, DOWNLOAD_URLS, MIN_COVERAGE
from utils.style import chart, section
from utils.viz import _layout


def render(rep, log, df):
    section("Transparency", "Data, cleaning and caveats", "Where the data come from, what was removed and why.")
    st.markdown(f"**Source**: the dataset *[{DATASET_NAME}]({DATASET_PAGE})*, published by the European Environment "
                f"Agency (EEA) on **data.europa.eu**. It merges the former AirBase database (until 2012) with the "
                f"e-Reporting submissions of the French accredited air-quality monitoring associations (AASQA), "
                f"transmitted by the LCSQA. Extractions used (France, annual mean, one file per pollutant): "
                + " · ".join(f"[{p}]({u})" for p, u in DOWNLOAD_URLS.items()) + ".")

    c = st.columns(4)
    c[0].metric("Raw rows", f"{rep['n_rows']:,}")
    c[1].metric("Rows kept", f"{len(df):,}")
    c[2].metric("Stations", f"{df['station_id'].nunique():,}")
    c[3].metric("Years", f"{df['year'].min()}–{df['year'].max()}")

    st.markdown("#### Cleaning log")
    st.dataframe(log, hide_index=True)

    a, b = st.columns(2)
    with a:
        st.markdown("#### Rows per year and data flow")
        cnt = df.groupby(["year", "flow"]).size().rename("n").reset_index()
        fig = px.bar(cnt, x="year", y="n", color="flow", labels={"year": "Year", "n": "Rows", "flow": "Flow"},
                     color_discrete_map={"AirBase": "#94a3b8", "E1a": "#2a78d6", "E2a": "#eda100"})
        fig.update_traces(marker_line_color="white", marker_line_width=1)
        chart(_layout(fig, None, 340))
        st.caption("Until 2012: historical AirBase database; from 2013: validated e-Reporting (E1a). The volume is stable "
                   "since 2005, but the stations behind it change. This is why trends use a stable-station panel by default.")
    with b:
        st.markdown("#### Missing values in the raw data (%)")
        miss = rep["missing_pct"][rep["missing_pct"] > 0]
        if len(miss):
            fig = px.bar(miss.rename("pct").reset_index(), x="pct", y="index", orientation="h",
                         labels={"pct": "% missing", "index": ""}, color_discrete_sequence=["#2a78d6"])
            chart(_layout(fig, None, 340, legend=False))
        st.caption("City and the verification flag are mostly missing for AirBase data (before 2013); they are not used "
                   "in the analysis. Station metadata missing in one year are filled from the other years of the same station.")

    st.markdown("#### Engineered features")
    st.markdown(
        "- **Station type**: EEA type (traffic, background, industrial) crossed with the area (urban, suburban, rural).\n"
        "- **Region**: derived from the name of the AASQA monitoring network, including the pre-2017 regional networks. "
        "Remaining stations are assigned to the nearest regional centre.\n"
        "- **Exceedances**: flags above the current EU limit, the EU 2030 limit and the WHO 2021 guideline, plus the "
        "ratio to the WHO guideline.\n"
        "- **Stable panel**: stations measured in at least 80% of the years of the selected period.\n"
        "- **Trend per station**: linear regression slope, R² and 2030 projection.")
    with st.expander("Number of stations per region (after cleaning)"):
        st.dataframe(df.groupby("region")["station_id"].nunique().sort_values(ascending=False).rename("Stations"))

    st.markdown("#### ⚠️ Caveats")
    st.markdown(
        f"1. **The network is not a random sample**: stations are placed where pollution is expected (cities, main roads). "
        f"A mean of stations **does not measure population exposure**.\n"
        f"2. **The network changes**: stations open and close, hence the “stable stations” option.\n"
        f"3. **Coverage**: an annual mean is kept only if at least {MIN_COVERAGE:.0f}% of the year was measured. "
        f"The current year, still provisional, is excluded.\n"
        f"4. **Method change in 2013** (AirBase to e-Reporting): it may create a small break in the series.\n"
        f"5. **No measurement uncertainty** is provided (about ±15 to 25% depending on the pollutant, per the directive).\n"
        f"6. **Correlation is not causation**: the before/after tab describes, it does not prove the effect of a policy.\n"
        f"7. Data are aggregated per station: **no personal data**.")

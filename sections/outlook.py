import streamlit as st

from config import POLLUTANTS, THRESHOLDS
from utils.prep import project_share, station_trends
from utils.style import chart, key_message, section
from utils.viz import projection_chart, trend_scatter


@st.cache_data(show_spinner=False)
def _trends(fp, y0, y1):
    return station_trends(fp, y0, y1)


def render(fp, pollutant, years):
    section("Question 3", f"Road to 2030: {POLLUTANTS[pollutant]}",
            "At the current pace, how many stations will still exceed the new EU limit in 2030?")
    thr = THRESHOLDS.get(pollutant)
    if not thr:
        st.info("Ozone has no annual-mean limit value, so the 2030 projection does not apply. Choose NO₂, PM10 or PM2.5.")
        return
    y1 = int(fp["year"].max()) if not fp.empty else years[1]
    y0 = st.slider("Years used to estimate the trend (start year)", years[0], y1 - 5, max(years[0], y1 - 9),
                   help="A recent trend (last 10 years) better reflects current policies.")
    tr = _trends(fp, y0, y1)
    if len(tr) < 5:
        st.info("Not enough stations with at least 6 years of measurements over this period.")
        return
    st.markdown(f"**Simple model**: for each station, a regression line is fitted on its annual means {y0}–{y1}, then "
                f"extended to 2030. This is not a forecast: it answers “what if the current pace does not change?”.")

    c = st.columns(3)
    c[0].metric("Stations modelled", len(tr))
    c[1].metric("Median trend", f"{tr['slope'].median():+.2f} µg/m³/yr",
                f"{tr['slope_pct'].median():+.1f}%/yr", delta_color="inverse")
    c[2].metric("Median R²", f"{tr['r2'].median():.2f}",
                help="Goodness of fit of the line (1 = perfectly linear trend). "
                     "A low R² means year-to-year variations dominate.")

    a, b = st.columns([1.2, 1])
    with a:
        st.markdown("#### Where is each station, and how fast is it improving?")
        chart(trend_scatter(tr, pollutant, thr["EU 2030"]))
        st.caption("Bottom left: clean stations that keep improving. Top right: stations above the limit that are not "
                   "improving: this is where action is most needed.")
    with b:
        st.markdown("#### 🔧 What if we sped things up?")
        extra = st.slider("Extra effort (additional decrease in % per year, on top of the trend)", 0.0, 10.0, 3.0, 0.5,
                          help="Scenario assumption (e.g. stricter low-emission zones, faster replacement of wood "
                               "heating). It applies uniformly to all stations.")
        res = project_share(tr, thr["EU 2030"], extra)
        chart(projection_chart(res["now"], res["trend"], res["scenario"]))
    key_message(f"today, **{res['now']:.0f}%** of stations exceed the EU 2030 limit ({thr['EU 2030']} µg/m³). If the "
                f"trend continues, about **{res['trend']:.0f}%** would in 2030. With an extra {extra:.1f}% decrease per "
                f"year, it would be **{res['scenario']:.0f}%**.")

    with st.expander("🔢 Priority stations: above the 2030 limit in the trend projection"):
        prio = tr[tr["proj"] > thr["EU 2030"]].sort_values("proj", ascending=False)
        st.dataframe(prio[["station", "region", "station_class", "last_year", "last_value", "slope", "proj", "r2"]]
                     .rename(columns={"station": "Station", "region": "Region", "station_class": "Type",
                                      "last_year": "Last year", "last_value": "Last value",
                                      "slope": "Trend (µg/m³/yr)", "proj": "2030 projection", "r2": "R²"})
                     .round(2), hide_index=True)
    st.caption("Model limits: linear trend (a decline cannot continue at the same pace forever), projection floored at 0, "
               "no weather effect and no new policies. The “effort” scenario is an illustrative assumption, not a "
               "policy evaluation.")

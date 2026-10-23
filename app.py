"""Is France breathing cleaner air? - Streamlit data storytelling app (EFREI #EFREIDataStories2026, BIA).

Run with: streamlit run app.py
"""
import streamlit as st

from config import CLASS_ORDER, POLLUTANTS
from sections import before_after, conclusions, context, outlook, quality, territories, trends
from utils.facts import first_solid_year
from utils.io import load_data
from utils.prep import add_features, clean, normalize, panel_stations, quality_report
from utils.style import footer, hero, inject_css

st.set_page_config(page_title="Is France breathing cleaner air?", page_icon="🌫️", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()


@st.cache_data(show_spinner="Loading and cleaning the data…")
def get_data():
    raw, source, fname = load_data()
    base = normalize(raw)
    rep = quality_report(base)
    df, log = clean(base)
    return add_features(df), rep, log, source, fname


df, rep, log, source, fname = get_data()

# ------------------------------------------------------------------ sidebar: filters
with st.sidebar:
    st.header("🎛️ Explore")
    pols = [p for p in POLLUTANTS if p in set(df["pollutant"])]
    pollutant = st.selectbox("Pollutant", pols, format_func=lambda p: POLLUTANTS[p],
                             help="Pollutant analysed in every tab.")
    ymin, ymax = int(df["year"].min()), int(df["year"].max())
    years = st.slider("Period", ymin, ymax, (max(ymin, 2005), ymax),
                      help="Before 2013 the data come from the former AirBase database (fewer stations).")
    classes = [c for c in CLASS_ORDER if c in set(df["station_class"].astype(str))]
    sel_classes = st.multiselect("Station type", classes, default=[c for c in classes if c != "Industrial"],
                                 help="Traffic = roadside; Background = away from direct sources (general exposure).")
    regions = sorted(df["region"].unique())
    sel_regions = st.multiselect("Regions", regions, default=[], placeholder="All regions")
    panel = st.toggle("Stable stations only", value=True,
                      help="Keeps only stations measured in at least 80% of the years of the period, so that a trend "
                           "is not caused by stations opening or closing.")
    st.divider()
    st.subheader("Before / after")
    pivot = st.slider("Pivot year", ymin + 2, ymax - 2, min(2019, ymax - 2),
                      help="Milestones: 2015 = Paris restricted traffic zone; 2017 = Crit'Air sticker mandatory in Paris; "
                           "2019 = Greater Paris low-emission zone (ZFE); 2020 = Covid lockdowns.")
    width = st.slider("Window (years on each side)", 2, 5, 3)
    st.divider()
    st.caption(f"Source: EEA - Air quality annual statistics (data.europa.eu). "
               f"{len(fname.split(', '))} data files, {rep['n_rows']:,} raw rows.")

# ------------------------------------------------------------------ apply filters
f = df[df["year"].between(*years) & df["station_class"].astype(str).isin(sel_classes)]
if sel_regions:
    f = f[f["region"].isin(sel_regions)]
fp = f[f["pollutant"] == pollutant]
if panel and not fp.empty:
    # The panel starts in the first year in which the pollutant's network is dense enough (PM2.5: late 2000s)
    y_start = first_solid_year(fp, 50, years[0])
    fp = fp[fp["year"] >= y_start]
    fp = fp[fp["station_id"].isin(panel_stations(fp, y_start, years[1]))]
    if y_start > years[0]:
        st.sidebar.info(f"{pollutant}: network too sparse before {y_start}. The stable-station panel starts in {y_start}.")

if source == "demo":
    st.error("⚠️ **Demo mode**: no EEA file found in `data/`. Values are SYNTHETIC. "
             "See the README to download the real data.")

hero("EFREI Data Stories 2026 · Air quality in France",
     "Is France breathing cleaner air?",
     "25 years of measurements from French air-quality monitoring stations, compared with the current EU limits, "
     "the stricter 2030 EU limits and the WHO guidelines.",
     [f"{df['station_id'].nunique():,} stations", f"{ymin}–{ymax}", "NO₂ · PM10 · PM2.5 · O₃",
      "Source: European Environment Agency"])

tabs = st.tabs(["① The situation", "② The trend", "③ Before / after", "④ Territories",
                "⑤ Road to 2030", "⑥ Data & caveats", "⑦ Takeaways"])
with tabs[0]:
    context.render(df, rep, source)
with tabs[1]:
    trends.render(fp, f, pollutant, pivot, years, panel)
with tabs[2]:
    before_after.render(fp, pollutant, pivot, width)
with tabs[3]:
    territories.render(fp, pollutant)
with tabs[4]:
    outlook.render(fp, pollutant, years)
with tabs[5]:
    quality.render(rep, log, df)
with tabs[6]:
    conclusions.render(df)

footer("Cheick Mohamed DIAKITE · EFREI Paris · BIA · #EFREIDataStories2026 · "
       "Data: EEA, Air quality annual statistics (data.europa.eu), CC BY 4.0")

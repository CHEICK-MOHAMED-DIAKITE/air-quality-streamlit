import streamlit as st

from config import THRESHOLDS
from utils.facts import all_facts
from utils.prep import project_share, station_trends
from utils.style import card, section


@st.cache_data
def _summary(df):
    F = all_facts(df)
    proj = {}
    for p in ["NO2", "PM2.5"]:
        d = df[(df["pollutant"] == p) & (df["station_class"].astype(str) != "Industrial")]
        if d.empty:
            continue
        y1 = int(d["year"].max())
        tr = station_trends(d, y1 - 9, y1)
        proj[p] = {"eu": project_share(tr, THRESHOLDS[p]["EU 2030"], 0),
                   "who": project_share(tr, THRESHOLDS[p]["WHO 2021"], 0)}
    return F, proj


def render(df):
    section("Takeaways", "What to remember", "Figures computed on all stations (industrial excluded), independently of the filters.")
    F, proj = _summary(df)
    no2, pm10, pm25, o3 = (F.get(k, {}) for k in ["NO2", "PM10", "PM2.5", "O3"])
    if not all([no2, pm10, pm25, o3]) or len(proj) < 2:
        st.info("The conclusions need all four pollutants. Add the missing EEA extractions to data/ (see README).")
        return

    st.success(
        f"**1. The air has clearly improved.** On stations followed from start to end, NO₂ fell by "
        f"**{abs(no2['chg']):.0f}%** ({no2['y0']}→{no2['y1']}), PM10 by **{abs(pm10['chg']):.0f}%** ({pm10['y0']}→{pm10['y1']}) "
        f"and PM2.5 by **{abs(pm25['chg']):.0f}%** ({pm25['y0']}→{pm25['y1']}). The share of stations above the current EU "
        f"NO₂ limit went from {no2['eu_now_y0']:.0f}% to **{no2['eu_now_last']:.0f}%**.")
    st.warning(
        f"**2. The 2030 EU limits are within reach, the WHO guidelines are not.** In {no2['y1']}, "
        f"**{no2['eu2030_last']:.0f}%** of stations exceed the EU 2030 NO₂ limit and **{pm25['eu2030_last']:.0f}%** the PM2.5 one. "
        f"If the pace of the last 10 years continues, these shares would fall to about **{proj['NO2']['eu']['trend']:.0f}%** "
        f"and **{proj['PM2.5']['eu']['trend']:.0f}%** in 2030. But for PM2.5, **{pm25['who_last']:.0f}%** of stations exceed "
        f"the WHO guideline today, and still about **{proj['PM2.5']['who']['trend']:.0f}%** would in 2030 at the same pace.")
    st.error(
        f"**3. Gaps persist, and ozone does not follow.** Traffic stations remain the most exposed to NO₂ "
        f"({no2['by_class_last'].get('Traffic', float('nan')):.0f} µg/m³ vs "
        f"{no2['by_class_last'].get('Urban background', float('nan')):.0f} for urban background, in {no2['y1']}). "
        f"Ozone has changed by **{o3['chg']:+.0f}%** since {o3['y0']}: cutting NO₂ does not solve everything.")
    st.caption("Projections: linear trend per station, no weather effect and no new policies. They are orders of magnitude, "
               "not forecasts (see tab ⑤).")

    st.write("")
    a, b = st.columns(2)
    with a:
        card("🧭 Implications",
             "<ul><li><b>Target main roads</b>: this is where the gap to the 2030 NO₂ limit is largest "
             "(low-emission zones, modal shift, urban logistics).</li>"
             "<li><b>Fine particles are the #1 health issue</b>: the gap to the WHO guideline is huge. Action is needed "
             "beyond transport too: wood heating, agriculture (ammonia), industry.</li>"
             "<li><b>Monitor priority stations</b> (tab ⑤): those above the limit that are not improving.</li>"
             "<li><b>Prepare for ozone</b> with hotter summers: summer-episode plans and joint cuts in VOCs and NO₂.</li></ul>")
    with b:
        card("🔭 Next steps",
             "<ul><li>Cross with <b>population</b> data (INSEE grid) to estimate real exposure rather than a mean of stations.</li>"
             "<li>Add <b>weather</b> data (Météo-France) to separate the climate effect from the policy effect.</li>"
             "<li>Evaluate a <b>specific low-emission zone</b> with a difference-in-differences design "
             "(stations inside the zone vs control stations).</li></ul>")

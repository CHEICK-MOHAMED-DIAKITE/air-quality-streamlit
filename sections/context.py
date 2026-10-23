import streamlit as st

from config import DATASET_NAME, DATASET_PAGE, DOWNLOAD_URLS, LICENSE, POLLUTANT_NOTE, POLLUTANTS, THRESHOLDS
from utils.facts import all_facts
from utils.style import card, key_message, section


@st.cache_data
def _facts(df):
    return all_facts(df)


def render(df, rep, source):
    F = _facts(df)
    no2, pm25, o3 = F.get("NO2", {}), F.get("PM2.5", {}), F.get("O3", {})

    section("Hook", "Why it matters",
            "Outdoor air pollution is the <b>largest environmental health risk in Europe</b>. Santé publique France "
            "estimates that fine particles cause about <b>40,000 premature deaths a year</b> in France. In 2021 the "
            "<b>WHO</b> sharply lowered its guideline values, and in 2024 the <b>European Union</b> followed with limit "
            "values roughly twice as strict, applicable from <b>2030</b>.")

    c = st.columns(4)
    if no2:
        c[0].metric(f"NO₂ change {no2['y0']}→{no2['y1']}", f"{no2['chg']:+.0f}%",
                    help=f"Mean of {no2['n_panel']} stations followed over the whole period (industrial excluded).")
        c[1].metric(f"NO₂ stations > EU 2030 limit ({no2['y1']})", f"{no2['eu2030_last']:.0f}%",
                    help=f"Threshold: {THRESHOLDS['NO2']['EU 2030']} µg/m³ (annual mean).")
    if pm25:
        c[2].metric(f"PM2.5 stations > EU 2030 limit ({pm25['y1']})", f"{pm25['eu2030_last']:.0f}%",
                    help=f"Threshold: {THRESHOLDS['PM2.5']['EU 2030']} µg/m³.")
    if o3:
        c[3].metric(f"Ozone change {o3['y0']}→{o3['y1']}", f"{o3['chg']:+.0f}%",
                    help="Ozone does not fall like the other pollutants: it is the counter-example of this story.")

    if no2 and pm25:
        key_message(
            f"**The good news**: since {no2['y0']}, the mean NO₂ concentration of the stations followed has fallen by "
            f"**{abs(no2['chg']):.0f}%**, and PM2.5 by **{abs(pm25['chg']):.0f}%** since {pm25['y0']}. "
            f"**The less good news**: in {no2['y1']}, **{pm25['eu2030_last']:.0f}%** of stations are still above the "
            f"future EU limit for PM2.5, and **{pm25['who_last']:.0f}%** exceed the WHO guideline.",
            label="📌 In one sentence")

    st.write("")
    a, b, c3 = st.columns(3)
    with a:
        card("👥 Who is it for?",
             "<ul><li><b>Local authorities</b>: know where to act before the 2030 deadline.</li>"
             "<li><b>Journalists and citizens</b>: check whether “the air is getting better” everywhere, "
             "for every pollutant.</li></ul>")
    with b:
        card("❓ Three questions",
             "<ol><li><b>The trend</b>: has pollution fallen over 20 years, for every pollutant?</li>"
             "<li><b>Before / after</b>: does the decline speed up after a key date (Crit'Air, low-emission zone, Covid)?</li>"
             "<li><b>Road to 2030</b>: at the current pace, how many stations will remain above the new limits?</li></ol>")
    with c3:
        card("🧭 How to read this dashboard",
             "<p>The tabs follow the story <b>from left to right</b>. The filters on the left (pollutant, period, "
             "station type, regions, pivot year) apply to every chart. Each chart comes with a <b>key message</b> "
             "recomputed from your filters.</p>")

    st.write("")
    e1, e2 = st.columns(2)
    with e1:
        with st.expander("The four pollutants"):
            for k, v in POLLUTANTS.items():
                st.markdown(f"- **{v}**: {POLLUTANT_NOTE[k]}")
    with e2:
        with st.expander("Reference thresholds (annual mean, µg/m³)"):
            st.table({p: v for p, v in THRESHOLDS.items()})
            st.caption("EU current: Directive 2008/50/EC · EU 2030: Directive (EU) 2024/2881 · WHO: 2021 guidelines. "
                       "Ozone has no annual-mean limit value.")
    links = " · ".join(f"[{p}]({u})" for p, u in DOWNLOAD_URLS.items())
    st.caption(f"Data: [{DATASET_NAME}]({DATASET_PAGE}) (data.europa.eu). Extractions used: {links}. {LICENSE}. "
               f"{rep['n_rows']:,} raw rows, {rep['n_stations']:,} stations, {rep['years'][0]}–{rep['years'][1]} before cleaning.")

import streamlit as st

from config import POLLUTANTS, THRESHOLDS
from utils.style import chart, key_message, section
from utils.viz import ranking_bars, station_map


def render(fp, pollutant):
    section("Where?", f"Territories: {POLLUTANTS[pollutant]}",
            "Which regions and which stations are the most exposed?")
    if fp.empty:
        st.info("No data for these filters.")
        return
    years = sorted(fp["year"].unique())
    c1, c2 = st.columns(2)
    year = c1.select_slider("Year shown", years, value=years[-1])
    min_n = c2.slider("Minimum number of stations per region", 1, 10, 3,
                      help="A regional mean computed on 1 or 2 stations is not representative.")
    d = fp[fp["year"] == year]
    if d.empty:
        st.info("No measurement that year.")
        return

    reg = (d.groupby("region").agg(value=("value", "mean"), n=("station_id", "nunique")).reset_index())
    reg = reg[reg["n"] >= min_n].sort_values("value", ascending=False)
    thr = THRESHOLDS.get(pollutant, {})

    if len(reg) >= 2:
        top, bottom = reg.iloc[0], reg.iloc[-1]
        msg = (f"in {year}, **{top['region']}** has the highest mean ({top['value']:.1f} µg/m³), "
               f"{top['value'] / bottom['value']:.1f} times that of **{bottom['region']}** ({bottom['value']:.1f} µg/m³).")
        if thr:
            n_over = (reg["value"] > thr["EU 2030"]).sum()
            msg += f" **{n_over} region(s) out of {len(reg)}** have a mean above the EU 2030 limit."
        key_message(msg)

    a, b = st.columns([1.15, 1])
    with a:
        st.markdown(f"#### Concentration by station in {year}")
        fig = station_map(d, "value", "µg/m³", rng=(0, float(d["value"].quantile(0.98))), height=600)
        if fig:
            chart(fig)
            st.caption("The darker the blue, the higher the concentration. Overseas stations are not shown on the map.")
    with b:
        st.markdown("#### Regional ranking")
        if reg.empty:
            st.info("No region reaches the minimum number of stations.")
        else:
            reg["label"] = reg["region"] + "  (" + reg["n"].astype(str) + ")"
            chart(ranking_bars(reg, "value", "label", "Mean of stations (µg/m³)", pollutant))
            st.caption("In brackets: number of stations. Means depend on the type of stations installed "
                       "(a region with many traffic stations looks more polluted).")

    st.markdown(f"#### The 15 most exposed stations in {year}")
    top15 = d.nlargest(15, "value")[["station", "region", "station_class", "value"]]
    if thr:
        top15["× WHO guideline"] = (top15["value"] / thr["WHO 2021"]).round(1)
    st.dataframe(top15.rename(columns={"station": "Station", "region": "Region", "station_class": "Type",
                                       "value": "Annual mean (µg/m³)"}).round(1), hide_index=True)

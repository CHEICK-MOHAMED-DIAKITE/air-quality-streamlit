import streamlit as st

from config import POLLUTANTS
from utils.prep import before_after
from utils.style import chart, key_message, section
from utils.viz import before_after_dumbbell, delta_hist, station_map


def render(fp, pollutant, pivot, width):
    section("Question 2", f"Before / after {pivot}: {POLLUTANTS[pollutant]}",
            f"For <b>each station</b>, we compare its mean over the {width} years up to {pivot} (included) with its mean "
            f"over the {width} following years. Each station is compared with itself, which removes location effects.")
    ba = before_after(fp, pivot, width)
    if len(ba) < 5:
        st.info("Not enough stations measured on both sides of the pivot. Change the pivot year or the period.")
        return

    med = ba["delta_pct"].median()
    share_down = (ba["delta"] < 0).mean() * 100
    c = st.columns(3)
    c[0].metric("Stations compared", len(ba))
    c[1].metric("Median change", f"{med:+.0f}%")
    c[2].metric("Stations improving", f"{share_down:.0f}%")

    # Is the change faster than before? Same computation shifted by one window
    prev = before_after(fp, pivot - width, width)
    extra = ""
    if len(prev) >= 5 and pollutant != "O3":
        pmed = prev["delta_pct"].median()
        speed = "faster" if med < pmed else "slower"
        extra = (f" The previous window ({pivot - 2 * width + 1}–{pivot - width} vs {pivot - width + 1}–{pivot}) "
                 f"gave {pmed:+.0f}%: the decline is therefore **{speed}** after {pivot}.")
    key_message(f"around {pivot}, the median station changes by **{med:+.0f}%**, and **{share_down:.0f}%** "
                f"of stations improve.{extra}")
    if pivot < 2020 <= pivot + width and pollutant != "O3":
        key_message("the “after” period includes 2020, when lockdowns temporarily cut traffic. To check that the decline "
                    "is not just a Covid effect, see whether 2022-2025 stay low in “The trend”, or move the pivot to 2020.",
                    label="ℹ️ Covid", warn=True)
    st.caption("⚠️ Correlation is not causation. Weather (a mild winter), fleet renewal, the 2020 lockdowns and local "
               "policies all act at the same time. The pivot raises the question; it does not prove a policy effect.")

    a, b = st.columns([1, 1.15])
    with a:
        st.markdown("#### By station type")
        cls = (ba.groupby("station_class", observed=True)[["before", "after"]].mean()
                 .assign(delta_pct=lambda x: (x["after"] - x["before"]) / x["before"] * 100).reset_index())
        chart(before_after_dumbbell(cls))
        st.markdown("#### Distribution of changes")
        chart(delta_hist(ba))
    with b:
        st.markdown("#### Map of changes")
        fig = station_map(ba, "delta_pct", "Change (%)", diverging=True, height=640)
        if fig:
            chart(fig)
            st.caption("Blue: decrease · red: increase · grey: stable. Hover over a station to see its name and region.")
    with st.expander("🔢 Stations that worsened the most"):
        worst = ba.sort_values("delta_pct", ascending=False).head(15)
        st.dataframe(worst[["station", "region", "station_class", "before", "after", "delta_pct"]]
                     .rename(columns={"station": "Station", "region": "Region", "station_class": "Type",
                                      "before": "Before (µg/m³)", "after": "After (µg/m³)", "delta_pct": "Change (%)"})
                     .round(1), hide_index=True)

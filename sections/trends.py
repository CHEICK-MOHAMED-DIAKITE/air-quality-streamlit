import streamlit as st

from config import POLLUTANTS, THRESHOLDS
from utils.prep import share_over, timeseries
from utils.style import chart, key_message, section
from utils.viz import share_over_chart, small_multiples, trend_lines


def render(fp, f, pollutant, pivot, years, panel):
    section("Question 1", f"The trend: {POLLUTANTS[pollutant]}",
            "Has the concentration fallen over the period, and for which types of station?")
    if fp.empty:
        st.info("No data for these filters. Widen the period, the station types or the regions.")
        return
    ts = timeseries(fp)
    y0, y1 = int(fp["year"].min()), int(fp["year"].max())
    m0 = fp[fp["year"] == y0]["value"].mean()
    m1 = fp[fp["year"] == y1]["value"].mean()
    chg = (m1 - m0) / m0 * 100

    c = st.columns(4)
    c[0].metric("Stations analysed", f"{fp['station_id'].nunique()}",
                help="With “stable stations only”, these are the same stations from start to end of the period.")
    c[1].metric(f"Mean {y1}", f"{m1:.1f} µg/m³", f"{chg:+.0f}% vs {y0}", delta_color="inverse")
    thr = THRESHOLDS.get(pollutant)
    last = fp[fp["year"] == y1]
    if thr:
        c[2].metric(f"> EU 2030 limit in {y1}", f"{(last['value'] > thr['EU 2030']).mean() * 100:.0f}%",
                    help=f"Share of stations above {thr['EU 2030']} µg/m³.")
        c[3].metric(f"> WHO guideline in {y1}", f"{(last['value'] > thr['WHO 2021']).mean() * 100:.0f}%",
                    help=f"Share of stations above {thr['WHO 2021']} µg/m³.")
    else:
        c[2].metric(f"Median {y1}", f"{last['value'].median():.1f} µg/m³")
        c[3].metric("Period", f"{y0}–{y1}")

    direction = "fallen" if chg < 0 else "risen"
    msg = f"between {y0} and {y1}, the mean {pollutant} concentration has **{direction} by {abs(chg):.0f}%**"
    gap = ts[ts["year"] == y1].set_index("station_class")["mean"]
    if {"Traffic", "Urban background"} <= set(gap.index.astype(str)) and pollutant != "O3":
        msg += (f". In {y1}, **traffic** stations are still at {gap['Traffic']:.1f} µg/m³, versus "
                f"{gap['Urban background']:.1f} µg/m³ for urban background: the gap caused by road traffic persists")
    key_message(msg[0].upper() + msg[1:] + ".")
    if pollutant == "O3":
        key_message("Ozone does not follow the other pollutants. It forms in sunlight from NO₂ and VOCs, so it is "
                    "higher away from cities and rises with hotter summers. Cutting NO₂ alone does not bring it down.",
                    label="⚠️ Counter-example", warn=True)

    stat = st.radio("Statistic", ["mean", "median"], horizontal=True,
                    format_func=lambda s: "Mean" if s == "mean" else "Median (less sensitive to extreme values)")
    chart(trend_lines(ts, pollutant, pivot, stat))
    st.caption("How to read: one line per station type. Dotted lines: annual thresholds (EU current, EU 2030, WHO 2021). "
               "Shaded area: years after the pivot used in the next tab. "
               + ("Stable-station panel." if panel else "⚠️ All stations: the network composition changes from year to year."))

    if thr:
        st.markdown("#### How many stations exceed the thresholds?")
        so = share_over(fp, pollutant)
        chart(share_over_chart(so, pollutant))
        s = so.set_index("year")
        key_message(f"the share of stations above the **current** EU limit went from {s['EU current'].iloc[0]:.0f}% to "
                    f"{s['EU current'].iloc[-1]:.0f}%. The challenge has shifted: it is now about meeting the **2030** "
                    f"limit, which {s['EU 2030'].iloc[-1]:.0f}% of stations still exceed.")

    with st.expander("📊 Compare the four pollutants (small multiples)"):
        allp = f[f["year"].between(*years)]
        ts_all = allp.groupby(["pollutant", "station_class", "year"], observed=True)["value"].mean().rename("mean").reset_index()
        chart(small_multiples(ts_all))
        st.caption("Each panel has its own scale. All stations are included (without the “stable” filter).")
    with st.expander("🔢 Show the data table"):
        st.dataframe(ts.pivot(index="year", columns="station_class", values="mean").round(1))

"""Plotly charts with a consistent style: labelled axes and units, annotated thresholds, colour by role.

Palette (colour-blind validated, fixed order):
- categorical (station type identity): blue, orange, aqua, yellow, magenta - always in this order;
- sequential (concentration level): a single hue, light -> dark;
- diverging (change): blue = decrease, red = increase, neutral grey in the middle.
"""
import plotly.express as px
import plotly.graph_objects as go

from config import CLASS_ORDER, THRESHOLDS

UNIT = "µg/m³"
FONT = "Inter, system-ui, 'Segoe UI', sans-serif"
INK, INK2, MUTED, GRID = "#0f172a", "#475569", "#94a3b8", "#e8edf3"
CLASS_COLORS = dict(zip(["Urban background", "Traffic", "Suburban background", "Rural background", "Industrial", "Other"],
                        ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#898781"]))
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DIV = [[0, "#184f95"], [0.25, "#6da7ec"], [0.5, "#f0efec"], [0.75, "#ec8a89"], [1, "#b42a2a"]]
THR_STYLE = {"EU current": "dash", "EU 2030": "dot", "WHO 2021": "dashdot"}
THR_COLORS = {"EU current": "#2a78d6", "EU 2030": "#eb6834", "WHO 2021": "#1baf7a"}
CLASS_ORD = {"station_class": CLASS_ORDER + ["Other"]}


def _layout(fig, title=None, height=420, legend=True):
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=INK)) if title else None,
        height=height, margin=dict(l=8, r=16, t=56 if title else 24, b=8),
        template="plotly_white", font=dict(size=13, color=INK2, family=FONT),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None, font=dict(size=12)) if legend else None,
        showlegend=legend, hoverlabel=dict(bgcolor="white", font=dict(family=FONT, size=12), bordercolor="#cbd5e1"),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(gridcolor=GRID, linecolor="#cbd5e1", zeroline=False, title_font=dict(size=12, color=MUTED))
    fig.update_yaxes(gridcolor=GRID, linecolor="#cbd5e1", zeroline=False, title_font=dict(size=12, color=MUTED))
    return fig


def add_thresholds(fig, pollutant, which=("EU current", "EU 2030", "WHO 2021"), orientation="h"):
    for name, val in THRESHOLDS.get(pollutant, {}).items():
        if name not in which:
            continue
        kw = dict(line_dash=THR_STYLE[name], line_color=MUTED, line_width=1.3,
                  annotation_text=f"{name}: {val}", annotation_font=dict(size=11, color=INK2))
        if orientation == "h":
            fig.add_hline(y=val, annotation_position="top left", **kw)
        else:
            fig.add_vline(x=val, annotation_position="bottom left" if name == "WHO 2021" else "bottom right", **kw)
    return fig


def trend_lines(ts, pollutant, pivot=None, stat="mean", height=460):
    fig = px.line(ts, x="year", y=stat, color="station_class", markers=True, color_discrete_map=CLASS_COLORS,
                  category_orders=CLASS_ORD, custom_data=["n"],
                  labels={"year": "Year", stat: f"Annual {'mean' if stat == 'mean' else 'median'} ({UNIT})",
                          "station_class": "Station type"})
    fig.update_traces(line_width=2.5, marker_size=6,
                      hovertemplate="%{x}: <b>%{y:.1f} µg/m³</b><br>%{customdata[0]} stations<extra>%{fullData.name}</extra>")
    add_thresholds(fig, pollutant)
    if pivot:
        fig.add_vrect(x0=pivot + 0.5, x1=ts["year"].max() + 0.5, fillcolor="#2a78d6", opacity=0.05, line_width=0)
        fig.add_vline(x=pivot + 0.5, line_color=INK2, line_width=1)
        fig.add_annotation(x=pivot + 0.5, y=1, yref="paper", text=" after pivot", showarrow=False, xanchor="left",
                           font=dict(size=11, color=INK2))
    fig.update_yaxes(rangemode="tozero")
    return _layout(fig, None, height)


def share_over_chart(so, pollutant):
    cols = [c for c in ["EU current", "EU 2030", "WHO 2021"] if c in so.columns]
    long = so.melt(id_vars="year", value_vars=cols, var_name="Threshold", value_name="share")
    fig = px.line(long, x="year", y="share", color="Threshold", markers=True, color_discrete_map=THR_COLORS,
                  labels={"year": "Year", "share": "Stations above the threshold (%)"})
    fig.update_traces(line_width=2.5, marker_size=6,
                      hovertemplate="%{x}: <b>%{y:.0f}%</b> of stations<extra>%{fullData.name}</extra>")
    fig.update_yaxes(range=[0, 105], ticksuffix="%")
    return _layout(fig, None, 380)


def small_multiples(ts):
    fig = px.line(ts, x="year", y="mean", color="station_class", facet_col="pollutant", facet_col_wrap=2,
                  color_discrete_map=CLASS_COLORS, category_orders={**CLASS_ORD, "pollutant": ["NO2", "PM10", "PM2.5", "O3"]},
                  labels={"year": "Year", "mean": UNIT, "station_class": "Type"}, facet_row_spacing=0.12)
    fig.update_yaxes(matches=None, showticklabels=True, rangemode="tozero")
    fig.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
    fig.update_traces(line_width=2, hovertemplate="%{x}: %{y:.1f} µg/m³<extra>%{fullData.name}</extra>")
    return _layout(fig, None, 560)


def delta_hist(ba):
    fig = px.histogram(ba, x="delta_pct", nbins=40, labels={"delta_pct": "Change after vs before (%)"},
                       color_discrete_sequence=["#2a78d6"])
    fig.update_traces(marker_line_color="white", marker_line_width=1.5,
                      hovertemplate="%{x}%<br><b>%{y} stations</b><extra></extra>")
    fig.add_vline(x=0, line_color="#b42a2a", line_width=1.5)
    fig.add_annotation(x=0, y=1, yref="paper", text=" no change", showarrow=False, xanchor="left",
                       font=dict(size=11, color=INK2))
    fig.update_yaxes(title="Number of stations")
    return _layout(fig, None, 380, legend=False)


def before_after_dumbbell(ba_class):
    """One row per station type: "before" dot -> "after" dot."""
    fig = go.Figure()
    for _, r in ba_class.iterrows():
        fig.add_trace(go.Scatter(x=[r["before"], r["after"]], y=[r["station_class"]] * 2, mode="lines",
                                 line=dict(color="#cbd5e1", width=4), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=ba_class["before"], y=ba_class["station_class"], mode="markers", name="Before",
                             marker=dict(size=14, color="#94a3b8", line=dict(color="white", width=2)),
                             hovertemplate="Before: <b>%{x:.1f} µg/m³</b><extra>%{y}</extra>"))
    fig.add_trace(go.Scatter(x=ba_class["after"], y=ba_class["station_class"], mode="markers", name="After",
                             marker=dict(size=14, color="#2a78d6", line=dict(color="white", width=2)),
                             hovertemplate="After: <b>%{x:.1f} µg/m³</b><extra>%{y}</extra>"))
    xmax = float(ba_class[["before", "after"]].max().max())
    for _, r in ba_class.iterrows():  # change label on the right, away from the dots
        fig.add_annotation(x=max(r["before"], r["after"]), y=r["station_class"], text=f"<b>{r['delta_pct']:+.0f}%</b>",
                           showarrow=False, xanchor="left", xshift=14, font=dict(color=INK2, size=12))
    fig.update_xaxes(title=f"Mean of stations ({UNIT})", range=[0, xmax * 1.2])
    fig.update_yaxes(autorange="reversed", title=None)
    return _layout(fig, None, 70 * len(ba_class) + 110)


def ranking_bars(df, x, y, xlabel, pollutant=None, height=None):
    fig = px.bar(df, x=x, y=y, orientation="h", labels={x: xlabel, y: ""}, color_discrete_sequence=["#2a78d6"],
                 text=df[x].map(lambda v: f"{v:.1f}"))
    fig.update_traces(marker_line_width=0, textposition="outside", cliponaxis=False,
                      hovertemplate="%{y}<br><b>%{x:.1f} µg/m³</b><extra></extra>")
    if pollutant:
        add_thresholds(fig, pollutant, which=("EU 2030", "WHO 2021"), orientation="v")
    fig.update_yaxes(categoryorder="total ascending")
    return _layout(fig, None, height or max(360, 30 * len(df) + 120), legend=False)


def station_map(df, color_col, label, diverging=False, rng=None, height=560):
    d = df.dropna(subset=["lat", "lon", color_col])
    d = d[d["lat"].between(41, 51.5) & d["lon"].between(-5.5, 10)]  # mainland France
    if d.empty:
        return None
    kw = dict(color_continuous_scale=DIV, range_color=rng or (-60, 60)) if diverging else \
        dict(color_continuous_scale=SEQ, range_color=rng)
    # Vector map (scatter_geo): no tile server and no WebGL needed
    d = d.sort_values(color_col, key=lambda s: s.abs() if diverging else s)  # strongest values drawn on top
    fig = px.scatter_geo(d, lat="lat", lon="lon", color=color_col, hover_name="station",
                         hover_data={"region": True, "station_class": True, color_col: ":.1f", "lat": False, "lon": False},
                         height=height, labels={color_col: label, "region": "Region", "station_class": "Type"}, **kw)
    fig.update_traces(marker=dict(size=8, opacity=0.95, line=dict(color="#475569", width=0.4)))
    fig.update_geos(resolution=50, lataxis_range=[41.2, 51.3], lonaxis_range=[-5.2, 9.8], projection_type="mercator",
                    showland=True, landcolor="#f1f5f9", showcountries=True, countrycolor="#cbd5e1",
                    showcoastlines=True, coastlinecolor="#cbd5e1", showocean=True, oceancolor="#eef4fb",
                    showlakes=False, showframe=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      coloraxis_colorbar=dict(title=label, thickness=12, len=0.6),
                      font=dict(family=FONT, color=INK2))
    return fig


def trend_scatter(tr, pollutant, threshold=None):
    fig = px.scatter(tr, x="last_value", y="slope", color="station_class", color_discrete_map=CLASS_COLORS,
                     category_orders=CLASS_ORD, hover_name="station",
                     hover_data={"region": True, "proj": ":.1f", "r2": ":.2f", "station_class": False},
                     labels={"last_value": f"Latest annual mean ({UNIT})", "slope": f"Trend ({UNIT} per year)",
                             "station_class": "Type", "proj": "2030 projection", "r2": "R²", "region": "Region"})
    fig.update_traces(marker=dict(size=9, opacity=0.85, line=dict(color="white", width=1)))
    fig.add_hline(y=0, line_color=MUTED, line_width=1)
    if threshold:
        fig.add_vline(x=threshold, line_dash="dot", line_color=MUTED, annotation_text=f"EU 2030: {threshold}",
                      annotation_font=dict(size=11, color=INK2))
    return _layout(fig, None, 440)


def projection_chart(now, trend, scen, labels=("Today", "2030 (trend)", "2030 (with effort)")):
    fig = go.Figure(go.Bar(x=list(labels), y=[now, trend, scen], marker_color=["#94a3b8", "#2a78d6", "#1baf7a"],
                           text=[f"{v:.0f}%" for v in (now, trend, scen)], textposition="outside", cliponaxis=False,
                           hovertemplate="%{x}: <b>%{y:.0f}%</b> of stations<extra></extra>"))
    fig.update_yaxes(range=[0, max(5, now, trend, scen) * 1.25], title="Stations above the EU 2030 limit (%)",
                     ticksuffix="%")
    return _layout(fig, None, 360, legend=False)

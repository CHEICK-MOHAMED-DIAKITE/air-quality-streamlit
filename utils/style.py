"""Page styling and small reusable UI components (hero banner, section headers, key-message callouts)."""
import html

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stMarkdown, .stMetric, button, input, textarea {
    font-family: 'Inter', system-ui, 'Segoe UI', sans-serif;
}
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1280px; }
header[data-testid="stHeader"] { background: transparent; }

/* ---------- hero banner ---------- */
.hero {
    background: linear-gradient(120deg, #0b1f3a 0%, #133a6b 55%, #1d5fa8 100%);
    border-radius: 18px; padding: 30px 34px 26px; color: #fff; margin-bottom: 18px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, .18); position: relative; overflow: hidden;
}
.hero:after {
    content: ""; position: absolute; right: -60px; top: -60px; width: 260px; height: 260px;
    border-radius: 50%; background: radial-gradient(circle, rgba(255,255,255,.16), rgba(255,255,255,0) 70%);
}
.hero .kicker { text-transform: uppercase; letter-spacing: .12em; font-size: .78rem; font-weight: 600; opacity: .8; }
.hero h1 { color: #fff; font-size: 2.35rem; font-weight: 800; margin: .25rem 0 .35rem; line-height: 1.15; padding: 0; }
.hero p { color: #dbe7f6; font-size: 1.05rem; margin: 0 0 14px; max-width: 900px; }
.chip {
    display: inline-block; background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.22);
    color: #fff; border-radius: 999px; padding: 4px 12px; font-size: .8rem; margin: 0 6px 6px 0;
}

/* ---------- tabs as pills ---------- */
[role="tablist"] { gap: 8px !important; border-bottom: none !important; flex-wrap: wrap; padding-bottom: 6px; }
div[data-testid="stTab"] {
    background: #f1f5f9; border-radius: 999px; padding: 6px 16px !important; border: 1px solid #e2e8f0;
}
div[data-testid="stTab"]:hover { background: #e2e8f0; }
div[data-testid="stTab"] p { font-weight: 600; font-size: .9rem; color: #334155; }
div[data-testid="stTab"][aria-selected="true"] { background: #1d5fa8; border-color: #1d5fa8; }
div[data-testid="stTab"][aria-selected="true"] p { color: #fff !important; }
div[data-testid="stTab"] .react-aria-SelectionIndicator,
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }

/* ---------- KPI cards ---------- */
div[data-testid="stMetric"] {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px 16px 12px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, .05);
}
div[data-testid="stMetric"] label p { color: #64748b; font-weight: 600; font-size: .82rem; }
div[data-testid="stMetricValue"] { color: #0f172a; font-weight: 700; }

/* ---------- section header ---------- */
.sec { margin: 6px 0 12px; }
.sec .kicker { color: #1d5fa8; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; font-size: .75rem; }
.sec h2 { margin: 2px 0 4px; padding: 0; font-weight: 800; color: #0f172a; font-size: 1.7rem; }
.sec p { color: #475569; margin: 0; font-size: 1rem; }

/* ---------- key message callout ---------- */
.key {
    border-left: 5px solid #1d5fa8; background: #f0f6ff; border-radius: 10px;
    padding: 12px 16px; margin: 10px 0 16px; color: #0f172a; font-size: .98rem; line-height: 1.55;
}
.key .lbl { font-weight: 700; color: #1d5fa8; margin-right: 6px; }
.key.warn { border-left-color: #d97706; background: #fff8eb; }
.key.warn .lbl { color: #b45309; }

/* ---------- cards on the context tab ---------- */
.card {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px 18px; height: 100%;
    box-shadow: 0 1px 2px rgba(15, 23, 42, .05);
}
.card h4 { margin: 0 0 6px; padding: 0; font-size: 1.02rem; color: #0f172a; }
.card p, .card li { color: #475569; font-size: .94rem; margin-bottom: 4px; }

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] { background: #f8fafc; border-right: 1px solid #e2e8f0; }
section[data-testid="stSidebar"] h2 { font-size: 1.15rem; }

/* ---------- plotly containers ---------- */
div[data-testid="stPlotlyChart"] {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 6px 8px;
}
.footer { color: #94a3b8; font-size: .82rem; text-align: center; margin-top: 30px; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(kicker: str, title: str, subtitle: str, chips: list):
    chips_html = "".join(f'<span class="chip">{html.escape(c)}</span>' for c in chips)
    st.markdown(f'<div class="hero"><div class="kicker">{html.escape(kicker)}</div><h1>{html.escape(title)}</h1>'
                f'<p>{html.escape(subtitle)}</p>{chips_html}</div>', unsafe_allow_html=True)


def section(kicker: str, title: str, subtitle: str = ""):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f'<div class="sec"><div class="kicker">{html.escape(kicker)}</div><h2>{title}</h2>{sub}</div>',
                unsafe_allow_html=True)


def key_message(text_md: str, label: str = "💡 Key message", warn: bool = False):
    """Callout box. `text_md` may contain **bold** markdown, converted to <b>."""
    import re
    text_md = text_md[:1].upper() + text_md[1:]
    body = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(text_md, quote=False))
    st.markdown(f'<div class="key{" warn" if warn else ""}"><span class="lbl">{label}</span>{body}</div>',
                unsafe_allow_html=True)


def card(title: str, body_html: str):
    st.markdown(f'<div class="card"><h4>{title}</h4>{body_html}</div>', unsafe_allow_html=True)


def chart(fig, alt: str = None):
    """Plotly chart with the app's own styling (Streamlit theme disabled so the palette is kept)."""
    st.plotly_chart(fig, theme=None, config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})


def footer(text: str):
    st.markdown(f'<div class="footer">{text}</div>', unsafe_allow_html=True)

# 🌫️ Is France breathing cleaner air?

**Individual Streamlit project - Data Storytelling** · EFREI Paris · #EFREIDataStories2026 · BIA group
Author: Cheick Mohamed DIAKITE (student no. 20251124)

A Streamlit dashboard that tells the story of **25 years of measurements from French air-quality monitoring stations**
(NO₂, PM10, PM2.5, O₃, 1999–2025), compared with the current EU limit values, the 2030 EU limit values
(Directive (EU) 2024/2881) and the WHO guidelines (2021).

---

## 1. Problem and narrative

| | |
|---|---|
| **Audience** | Local authorities, journalists, citizens |
| **Central question** | Is air pollution falling everywhere, for every pollutant, and fast enough for 2030? |
| **Narrative pattern** | Before / after over time (adjustable pivot year), combined with a comparison of territories and a what-if scenario |

The 7 tabs follow the arc **Hook → Context → Analysis → Insights → Implications**:

1. **The situation** (hook): health stakes, key figures, audience, the 3 questions.
2. **The trend**: change by station type with annotated thresholds, share of stations above each threshold, small multiples of the 4 pollutants.
3. **Before / after**: each station is compared with itself around a pivot year (2019 by default), with a histogram, a dumbbell chart by station type and a map of changes.
4. **Territories**: map of concentrations, regional ranking, most exposed stations.
5. **Road to 2030**: simple model (linear regression per station), 2030 projection and an extra-effort slider (what-if).
6. **Data & caveats**: cleaning log, engineered features, limitations.
7. **Takeaways**: 3 insights, implications and next steps.

**Every figure displayed is computed from the data**: none is typed by hand (see `utils/facts.py`).
Key messages are recomputed from the filters.

## 2. Main findings (all stations except industrial)

- **A clear improvement.** On stations followed from start to end, NO₂ fell by **53%** (2005→2025), PM10 by **27%** (2005→2025) and PM2.5 by **48%** (2009→2025). The share of stations above the current EU NO₂ limit (40 µg/m³) went from **15% to 2%**.
- **An acceleration of the NO₂ decline around 2019, partly due to Covid.** On a stable panel, the median station falls by **22%** between 2017-2019 and 2020-2022, versus **10%** in the previous window. With a 2020 pivot (2018-2020 vs 2021-2023), the decline continues (−14%) but is no longer faster than before (−17%): part of the acceleration comes from the lockdowns. Particles do not accelerate.
- **The 2030 EU limits are within reach, the WHO guidelines are not.** In 2025, **18%** of stations exceed the 2030 NO₂ limit and **26%** the PM2.5 one. At the pace of the last 10 years these shares would fall to about 1% and 6% in 2030. However, **98%** of stations exceed the WHO PM2.5 guideline, and still about 75% would in 2030 at the same pace.
- **Gaps persist.** Traffic stations remain at 22 µg/m³ of NO₂, versus 12 for urban background. **Ozone rises (+9% since 2005)**: the counter-example of the story.

## 3. Data

| | |
|---|---|
| **Dataset** | *Air Quality e-Reporting: Air quality annual statistics calculated by the EEA*, on the **data.europa.eu** portal (one of the approved portals): https://data.europa.eu/data/datasets/6e191a3b-258d-491e-b636-6cbb15cf473b |
| **Access to the files** | The data.europa.eu record points to the EEA application *Air quality annual statistics (measurement based)*. The extractions were made in the EEA table viewer (links below) |
| **Producer** | European Environment Agency. French data produced by the AASQA (accredited monitoring associations) and transmitted by the LCSQA |
| **Licence** | Free re-use with attribution (EEA re-use policy, CC BY 4.0) |
| **Extraction** | France · annual mean (*Annual mean / 1 calendar year*) · one file per pollutant (the viewer only accepts one at a time) |
| **Files** (`data/`) | `eea_FR_NO2_annual_mean.csv.zip` (12,702 rows), `eea_FR_PM10_annual_mean.csv.zip` (9,502), `eea_FR_PM25_annual_mean.csv.zip` (3,471), `eea_FR_O3_annual_mean.csv.zip` (10,548) |
| **Granularity** | One row = one sampling point × one pollutant × one year |

Extraction links (open, check the row count, click **Download CSV**, put the zip in `data/`):
- [NO₂](https://discomap.eea.europa.eu/App/AQViewer/index.html?fqn=Airquality_Dissem.b2g.AirQualityStatistics&Country=France&AirPollutant=NO2&DataAggregationProcess=Annual%20mean%20/%201%20calendar%20year)
- [PM10](https://discomap.eea.europa.eu/App/AQViewer/index.html?fqn=Airquality_Dissem.b2g.AirQualityStatistics&Country=France&AirPollutant=PM10&DataAggregationProcess=Annual%20mean%20/%201%20calendar%20year)
- [PM2.5](https://discomap.eea.europa.eu/App/AQViewer/index.html?fqn=Airquality_Dissem.b2g.AirQualityStatistics&Country=France&AirPollutant=PM2.5&DataAggregationProcess=Annual%20mean%20/%201%20calendar%20year)
- [O₃](https://discomap.eea.europa.eu/App/AQViewer/index.html?fqn=Airquality_Dissem.b2g.AirQualityStatistics&Country=France&AirPollutant=O3&DataAggregationProcess=Annual%20mean%20/%201%20calendar%20year)

The app reads **every** `eea*.zip` / `DataExtract*.zip` file in `data/`: the default download names also work.
Without any file, it switches to a **demo mode** (synthetic data, red banner).

**Why this dataset rather than the LCSQA "real-time" feed on data.gouv.fr?** That feed only covers 2021 to today, as
hourly files of about 11 MB per day (about 4 GB per year). It allows neither a real before/after comparison nor a light
app. The EEA statistics are the **same French measurements**, already aggregated and validated, over 25 years.

## 4. Cleaning and validation (`utils/prep.py`)

Each rule is counted and shown in the "Data & caveats" tab:

| Step | Rule | Rows removed |
|---|---|---:|
| Exact duplicates | Strictly identical rows | 71 |
| Missing values | Missing concentration, year or station | 21 |
| Unit | Other than µg/m³ | 0 |
| Unusable years | Fewer than 20 stations (1982–1989); 2026 provisional (non-validated E2a flow) | 1,285 |
| Insufficient coverage | Less than 75% valid data in the year | 3,371 |
| Outliers | Annual mean outside [0; 300] µg/m³ | 0 |
| De-duplication | One value per station × pollutant × year (validated E1a > AirBase > provisional E2a, then highest coverage) | 74 |

**36,223 raw rows → 31,401 clean rows**, 1,102 stations, 1999–2025.
The inconsistent case in the source ("urban" / "Urban") is harmonised. Station metadata are fixed to the most recent
declaration.

**Engineered features**: station type (type × area: traffic, urban background, suburban background, rural background,
industrial), region (derived from the AASQA network, otherwise nearest regional centre), exceedance flags (EU current,
EU 2030, WHO 2021), ratio to the WHO guideline, **stable-station panel** (stations present in at least 80% of the years of
the period), linear trend per station (slope, R², 2030 projection).

## 5. Running the app

With Anaconda (Windows: *Anaconda Prompt*):
```bash
conda create -n airstory python=3.11 -y
conda activate airstory
cd path/to/air_story
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Or with a plain virtual environment:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    |    macOS / Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Smoke tests (pipeline + app run for each pollutant):
```bash
python -m pip install pytest
python -m pytest -q tests        # set PYTHONPATH=. first (Windows: set PYTHONPATH=.)
```

**Deployment** (Streamlit Community Cloud): push the folder to GitHub, data included (about 1.2 MB), then
*New app* → `app.py`. No key or secret is needed.

## 6. Code structure

```
air_story/
├── app.py                 # entry point: cached loading, filters, tabs
├── config.py              # source, column mapping, thresholds, cleaning rules (only file to edit if the format changes)
├── seeds.json             # seed of the demo generator (reproducibility)
├── requirements.txt
├── .streamlit/config.toml # theme
├── data/                  # 4 EEA extractions (zip) + SOURCE.txt (dataset and links)
├── sections/              # one module per tab of the story
│   ├── context.py  trends.py  before_after.py  territories.py  outlook.py  quality.py  conclusions.py
├── utils/
│   ├── io.py              # file loading (or demo mode)
│   ├── prep.py            # normalisation, checks, cleaning, features, analyses (before/after, trends, what-if)
│   ├── regions.py         # AASQA network -> region
│   ├── facts.py           # key figures of the story
│   ├── viz.py             # Plotly charts (colour-blind-safe palette, annotated thresholds)
│   ├── style.py           # page design (CSS, hero banner, key-message callouts)
│   └── demo.py            # synthetic data (tests and fallback)
└── tests/test_app.py
```

**Performance**: loading and cleaning are cached (`st.cache_data`), about 31,000 rows in memory, per-station trends cached.
**Visual choices**: one fixed colour per station type (categorical palette tested for colour blindness), a single-hue scale
for concentrations, a blue/red diverging scale centred on 0 for changes, grey dotted annotated thresholds, tooltips on
every chart, data tables as a complement.

## 7. Limitations

1. Stations are placed where pollution is expected: a mean of stations **is not population exposure**.
2. The network changes over time: hence the stable-station panel, enabled by default.
3. There is a change of data chain in 2013 (AirBase → e-Reporting).
4. No measurement uncertainty is provided.
5. The 2030 projection is linear, without weather or new policies: it is an order of magnitude, not a forecast.
6. The before/after describes a **correlation**: it does not prove the effect of a policy (weather, vehicle fleet, Covid).
7. Ozone has no annual-mean limit value: no threshold is shown for it.
8. Data are aggregated per station: no personal data.

## 8. References

- Dataset record on data.europa.eu: https://data.europa.eu/data/datasets/6e191a3b-258d-491e-b636-6cbb15cf473b
- EEA, *Air Quality Statistics* viewer: https://discomap.eea.europa.eu/App/AQViewer/index.html?fqn=Airquality_Dissem.b2g.AirQualityStatistics
- Directive 2008/50/EC and Directive (EU) 2024/2881 on ambient air quality
- WHO, *Global Air Quality Guidelines* (2021)
- Santé publique France (2021), new estimates of the health impact of ambient air pollution: https://www.santepubliquefrance.fr/presse/pollution-de-lair-ambiant-nouvelles-estimations-de-son-impact-sur-la-sante-des-francais

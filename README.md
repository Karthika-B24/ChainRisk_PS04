# ChainRisk — Third-Party Risk & Concentration Console

A Streamlit application for managing third-party (vendor) risk. It does two things:

1. **Vendor risk scoring** — scores every vendor on a 0–10 scale, bands them HIGH / MEDIUM / LOW
   with explainable risk factors and a recommended action, and validates detection against
   labelled outcomes.
2. **Concentration analysis** — maps the shared infrastructure providers the portfolio depends on,
   quantifies how concentrated it is (exposure share, blast radius, HHI), and simulates a provider
   outage to reveal the cascade. Aligned to the EU DORA concentration-risk obligations.

## Run
```
streamlit run app.py
```
Keep `.streamlit/config.toml` in a `.streamlit` subfolder next to `app.py` (it sets the theme).
A full restart is required after editing files or the theme.

Check the logic without the UI:
```
python scoring.py        # detection recall + accuracy + a sample assessment
python concentration.py  # provider table, HHI, the audit line
python report.py         # the full audit-ready report
python charts.py         # confirms all charts build
```

## Files
| File | Role |
|---|---|
| `vendor_registry.csv` / `vendor_labels.csv` | Vendor records and labelled outcomes. |
| `scoring.py` | 0–10 score, level, risk factors, recommendation, accuracy validation. |
| `concentration.py` | Exposure share, blast radius, HHI, hotspots, failure simulation. |
| `report.py` | Audit-ready portfolio report. |
| `charts.py` | Dark-themed Plotly charts. |
| `app.py` | The dashboard: top tab navigation + per-view chart selectors. |
| `.streamlit/config.toml` | Theme. |
| `data_dictionary.md` | Column reference. |

## Tabs
Overview · Vendor register · Risk analytics · Concentration · Audit report · Methodology.

## Charts
Risk analytics: heatmap (type × data access), risk-vs-spend bubble, average risk by type,
compliance coverage, financial-health distribution.
Concentration: dependency map, provider exposure, treemap, risk-by-provider, HHI gauge.
Overview: risk-distribution donut.

## Data
ChainRisk runs on the organisation's vendor register and assessment records. A provider-dependency
layer (`hosting_provider`, `key_subprocessor`) together with `financial_rating` and `gdpr_dpa`
enriches each record to enable the concentration analysis. In this build these enrichment attributes
are modelled; in a production deployment they are sourced from procurement, CMDB and
continuous-monitoring integrations.

"""
ChainRisk - app.py   (run:  streamlit run app.py)
Third-party risk & concentration console. Light professional theme,
top tab navigation, per-view chart selectors.
"""
import streamlit as st
from scoring import load_data, build_scored, validate
import concentration as cc
from report import portfolio_report
import charts

st.set_page_config(page_title="ChainRisk", layout="wide", initial_sidebar_state="collapsed")

# ---- light palette
BG="#f4f6fa"; SURF="#ffffff"; SURF2="#eef2f8"; BORD="#e1e7f0"
TXT="#15233b"; TXT2="#4a5a73"; TXT3="#8593a8"
BRAND="#0e8fa6"; HIGH="#dc2626"; MED="#c2740a"; LOW="#15803d"; ACCENT="#0e8fa6"
TONE={"HIGH":HIGH,"MEDIUM":MED,"LOW":LOW}
TONE_TXT={"HIGH":"#c81e1e","MEDIUM":"#b45309","LOW":"#15803d"}
TINT={"HIGH":"rgba(220,38,38,.10)","MEDIUM":"rgba(194,116,10,.13)","LOW":"rgba(21,128,61,.12)"}
DOT={"r":HIGH,"a":MED,"g":LOW,"b":ACCENT}

st.markdown(f"""<style>:root{{
 --bg:{BG};--surf:{SURF};--surf2:{SURF2};--bord:{BORD};
 --txt:{TXT};--txt2:{TXT2};--txt3:{TXT3};--brand:{BRAND};
 --shadow:0 1px 3px rgba(16,24,40,.08),0 1px 2px rgba(16,24,40,.05);}}</style>""",
 unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');
html, body, [class*="css"], .stApp, .stMarkdown, p, span, div, label {
  font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; }
.stApp { background:var(--bg); color:var(--txt); }
#MainMenu, footer { visibility:hidden; }
header[data-testid="stHeader"] { background:transparent; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { display:none; }
.block-container { padding:1.3rem 2.5rem 3rem; max-width:1200px; }

.topbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.tb-mark { display:flex; align-items:center; gap:13px; }
.tb-logo { width:38px; height:38px; border-radius:10px; background:linear-gradient(145deg,#13a3bb,#0e8fa6);
           display:flex; align-items:center; justify-content:center; flex:0 0 38px; box-shadow:0 3px 12px rgba(14,143,166,.28); }
.tb-logo svg { display:block; }
.tb-name { color:var(--txt); font-size:20px; font-weight:700; line-height:1; letter-spacing:-.3px; }
.tb-tag { font-size:12px; color:var(--txt3); margin-top:4px; }
.tb-stats { font-family:'JetBrains Mono',ui-monospace,Consolas,monospace; font-size:11px; color:var(--txt3); text-align:right; line-height:1.8; }
.tb-stats b { color:var(--txt); }

.stTabs [data-baseweb="tab-list"] { gap:2px; border-bottom:1px solid var(--bord); background:transparent; }
.stTabs [data-baseweb="tab"] { height:44px; padding:0 18px; color:var(--txt2); font-weight:600; font-size:14px; background:transparent; border-radius:9px 9px 0 0; }
.stTabs [data-baseweb="tab"]:hover { color:var(--txt); background:var(--surf2); }
.stTabs [aria-selected="true"] { color:var(--txt) !important; border-bottom:2px solid var(--brand); }

.kicker { font-size:11px; font-weight:600; letter-spacing:2.5px; color:#0e8fa6; text-transform:uppercase; margin-top:12px; }
.ptitle { font-size:24px; font-weight:700; letter-spacing:-.4px; margin:4px 0 3px; color:var(--txt); }
.psub { font-size:13.5px; color:var(--txt2); margin:0 0 16px; }
.sect { font-size:14px; font-weight:600; color:var(--txt); margin:8px 0 11px; padding-left:11px; border-left:2px solid var(--brand); }

.kpi-row { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:2px 0 10px; }
.kpi { background:var(--surf); border:1px solid var(--bord); border-radius:14px; padding:16px 18px; box-shadow:var(--shadow); }
.kpi-l { display:flex; align-items:center; gap:7px; font-size:11px; color:var(--txt3); font-weight:600; letter-spacing:.6px; text-transform:uppercase; }
.kpi-l .dot { width:7px; height:7px; border-radius:50%; display:inline-block; }
.kpi-v { font-size:28px; font-weight:700; color:var(--txt); font-family:'JetBrains Mono',ui-monospace,Consolas,monospace; letter-spacing:-1px; margin-top:5px; }
.kpi-s { font-size:12px; color:var(--txt3); margin-top:3px; }

.vcard { background:var(--surf); border:1px solid var(--bord); border-radius:14px; padding:16px 18px; margin-bottom:12px; box-shadow:var(--shadow); }
.vc-top { display:flex; justify-content:space-between; align-items:center; }
.vname { font-size:15px; font-weight:600; color:var(--txt); } .vid { font-size:11.5px; color:var(--txt3); margin-left:7px; font-family:'JetBrains Mono',ui-monospace,Consolas,monospace; }
.badge { font-size:12px; font-weight:700; padding:3px 12px; border-radius:8px; white-space:nowrap; font-family:'JetBrains Mono',ui-monospace,Consolas,monospace; }
.vmeta { font-size:12.5px; color:var(--txt2); margin:8px 0 9px; }
.issues { margin:0; padding-left:18px; } .issues li { font-size:13px; color:var(--txt2); margin-bottom:4px; }
.action { font-size:13px; margin-top:11px; padding-top:11px; border-top:1px solid var(--bord); color:var(--txt2); } .action b { color:var(--txt); }
.note { font-size:12.5px; color:var(--txt2); }
.callout { background:rgba(14,143,166,.07); border:1px solid rgba(14,143,166,.25); border-left:2px solid var(--brand);
           border-radius:11px; padding:13px 16px; font-size:13.5px; color:var(--txt); } .callout b { color:var(--txt); }
.rep { background:#0f1b2e; border:1px solid #223149; color:#cfe0d8; font-family:'JetBrains Mono',ui-monospace,Consolas,monospace;
       font-size:12.5px; line-height:1.6; padding:18px 20px; border-radius:12px; white-space:pre-wrap; overflow-x:auto; }
.score-row { display:grid; grid-template-columns:repeat(3,1fr); gap:11px; margin-top:4px; }
.score { background:var(--surf); border:1px solid var(--bord); border-radius:12px; padding:12px 14px; box-shadow:var(--shadow); }
.score-t { display:flex; align-items:center; gap:8px; font-size:13px; color:var(--txt); font-weight:600; } .score-t .tk { color:#15803d; font-weight:800; }
.score-v { font-size:12px; color:var(--txt3); margin-top:3px; font-family:'JetBrains Mono',ui-monospace,Consolas,monospace; }
.md-card { background:var(--surf); border:1px solid var(--bord); border-radius:14px; padding:17px 19px; margin-bottom:13px; box-shadow:var(--shadow); }
.md-h { font-size:14.5px; font-weight:700; color:var(--txt); margin-bottom:7px; } .md-p { font-size:13.5px; color:var(--txt2); line-height:1.7; margin:0; }
.md-p code { background:var(--surf2); color:#0c6170; padding:1px 6px; border-radius:5px; font-family:'JetBrains Mono',ui-monospace,Consolas,monospace; font-size:12px; }
.tb-name, .ptitle, .sect, .md-h, .kicker { font-family:'Space Grotesk','Inter',sans-serif; letter-spacing:-.3px; }
.kicker { letter-spacing:2.5px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def get_data():
    reg, lab = load_data(); scored = build_scored(reg)
    res = validate(scored, lab); groups = cc.provider_groups(scored)
    return scored, lab, res, groups


scored, lab, res, groups = get_data()
hhi_score, hhi_verdict = cc.hhi(groups)
cr, ct = res["critical_recall"]; n = len(scored)
lvl = scored["risk_level"].value_counts().to_dict()
top_prov = groups.iloc[0]; top_blast = top_prov["vendors"] / n * 100


def badge(level, score=None):
    txt = level if score is None else f"{level} &middot; {score}"
    return f"<span class='badge' style='background:{TINT[level]};color:{TONE_TXT[level]};'>{txt}</span>"

def kpi(label, value, sub, tone="b"):
    return (f"<div class='kpi'><div class='kpi-l'><span class='dot' style='background:{DOT[tone]};'></span>{label}</div>"
            f"<div class='kpi-v'>{value}</div><div class='kpi-s'>{sub}</div></div>")

def score_chip(title, value):
    return f"<div class='score'><div class='score-t'><span class='tk'>&#10003;</span>{title}</div><div class='score-v'>{value}</div></div>"

def head(kicker, title, sub):
    st.markdown(f"<div class='kicker'>{kicker}</div><div class='ptitle'>{title}</div><div class='psub'>{sub}</div>", unsafe_allow_html=True)

def vendor_card(r, detail=False):
    issues = "".join(f"<li>{x}</li>" for x in r["risk_factors"])
    extra = (f"Certifications: {r['certifications']} &middot; GDPR DPA: {'yes' if r['gdpr_dpa'] else 'no'} &middot; Spend: ${int(r['annual_spend_usd']):,} &middot; ") if detail else ""
    return f"""<div class="vcard"><div class="vc-top">
      <div><span class="vname">{r['vendor_name']}</span><span class="vid">{r['vendor_id']} &middot; {r['type']}</span></div>
      {badge(r['risk_level'], r['risk_score_10'])}</div>
      <div class="vmeta">Access: {r['data_access']} &middot; {extra}Financial rating: {r['financial_rating']} &middot; Hosting: {r['hosting_provider']}</div>
      <ul class="issues">{issues}</ul>
      <div class="action"><b>Action required:</b> {r['recommendation']}</div></div>"""


st.markdown(f"""<div class="topbar">
  <div class="tb-mark"><div class="tb-logo"><svg width="21" height="21" viewBox="0 0 24 24" fill="none"><path d="M5.5 7.5L18.5 6.5M5.5 7.5L12 17.5M18.5 6.5L12 17.5" stroke="#fff" stroke-width="1.5" opacity=".65"/><circle cx="5.5" cy="7.5" r="2.6" fill="#fff"/><circle cx="18.5" cy="6.5" r="2.6" fill="#fff"/><circle cx="12" cy="17.5" r="2.6" fill="#fff"/></svg></div>
    <div><div class="tb-name">ChainRisk</div><div class="tb-tag">Third-party risk &amp; concentration intelligence</div></div></div>
  <div class="tb-stats">VENDORS <b>{n}</b> &nbsp; HIGH-RISK <b>{lvl.get('HIGH',0)}</b><br>HHI <b>{hhi_score}</b> &nbsp; <span style="color:#0e8fa6;">DORA-ALIGNED</span></div>
</div>""", unsafe_allow_html=True)

t_over, t_reg, t_an, t_con, t_rep, t_meth = st.tabs(
    ["  Overview  ", "  Vendor register  ", "  Risk analytics  ", "  Concentration  ", "  Audit report  ", "  Methodology  "])

with t_over:
    head("Portfolio command center", "Vendor risk overview", "Per-vendor risk validated against ground truth, plus systemic concentration.")
    st.markdown("<div class='kpi-row'>"
                + kpi("Vendors tracked", n, "100% coverage", "b")
                + kpi("High-risk vendors", lvl.get("HIGH", 0), f"{100*lvl.get('HIGH',0)/n:.0f}% of portfolio", "r")
                + kpi("Critical recall", f"{cr}/{ct}", f"{100*cr/ct:.0f}% vs ground truth", "g")
                + kpi("Concentration", hhi_score, hhi_verdict.split()[0].upper(), "a") + "</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.25])
    with c1:
        st.markdown("<div class='sect'>Risk distribution</div>", unsafe_allow_html=True)
        st.plotly_chart(charts.risk_donut(lvl), width="stretch")
    with c2:
        st.markdown("<div class='sect'>Top red-flag vendors</div>", unsafe_allow_html=True)
        st.markdown("".join(vendor_card(r) for _, r in scored[scored["risk_level"] == "HIGH"].head(3).iterrows()), unsafe_allow_html=True)
    st.markdown(f"<div class='callout'><b>Concentration alert:</b> {top_prov['provider']} carries <b>{top_prov['exposure_share']*100:.0f}%</b> of the portfolio "
                f"({top_prov['pii_vendors']} vendors holding PII / financial data). One outage there is a systemic event &mdash; see the Concentration tab.</div>", unsafe_allow_html=True)
    st.markdown("<div class='sect' style='margin-top:18px;'>Assurance &amp; coverage</div>", unsafe_allow_html=True)
    st.markdown("<div class='score-row'>"
                + score_chip("Detection recall", f"{cr}/{ct} critical vendors identified ({100*cr/ct:.0f}%)")
                + score_chip("Scoring accuracy", f"{res['flag_accuracy']}% agreement with review")
                + score_chip("Concentration", f"HHI {hhi_score} &mdash; {hhi_verdict}")
                + score_chip("Largest dependency", f"{top_blast:.0f}% of portfolio on one provider")
                + score_chip("Outage simulation", "available on the Concentration view")
                + score_chip("Audit reporting", "report, CSV &amp; text export") + "</div>", unsafe_allow_html=True)

with t_reg:
    head("Inventory", "Vendor register", "Filter, search, and drill into any vendor's full assessment.")
    f1, f2, f3 = st.columns([1, 1, 1.3])
    levels = f1.multiselect("Risk level", ["HIGH", "MEDIUM", "LOW"], default=["HIGH", "MEDIUM"], key="vr_lvl")
    provs = f2.multiselect("Provider", sorted(scored["hosting_provider"].unique()), key="vr_prov")
    query = f3.text_input("Search vendor name", key="vr_q")
    v = scored[scored["risk_level"].isin(levels)]
    if provs: v = v[v["hosting_provider"].isin(provs)]
    if query: v = v[v["vendor_name"].str.contains(query, case=False)]
    st.dataframe(v[["vendor_id", "vendor_name", "type", "data_access", "risk_score_10", "risk_level", "financial_rating", "hosting_provider", "annual_spend_usd"]],
                 hide_index=True, width="stretch", height=330,
                 column_config={"vendor_name": "Vendor", "vendor_id": "ID", "type": "Type", "data_access": "Data access",
                                "financial_rating": "Fin.", "hosting_provider": "Hosting", "risk_level": "Level",
                                "risk_score_10": st.column_config.ProgressColumn("Risk", min_value=0, max_value=10, format="%.1f"),
                                "annual_spend_usd": st.column_config.NumberColumn("Spend", format="$%d")})
    st.markdown("<div class='sect' style='margin-top:16px;'>Vendor assessment</div>", unsafe_allow_html=True)
    pick = st.selectbox("Select a vendor", scored["vendor_name"] + "  (" + scored["vendor_id"] + ")", key="vr_pick")
    vid = pick.split("(")[-1].strip(") ")
    st.markdown(vendor_card(scored[scored["vendor_id"] == vid].iloc[0], detail=True), unsafe_allow_html=True)

with t_an:
    head("Analytics", "Risk analytics", "Pick a chart to explore the portfolio.")
    views = {
        "Risk heatmap (type x data access)": (charts.risk_heatmap, "Hotter cells = higher average risk."),
        "Risk vs spend (bubble)": (charts.risk_spend_scatter, "Top-right = high risk AND high spend: where exposure concentrates."),
        "Average risk by vendor type": (charts.risk_by_type, "Which categories of vendor carry the most risk."),
        "Compliance coverage": (charts.compliance_bars, "DPA coverage, current SOC 2, expired certifications."),
        "Financial-health distribution": (charts.financial_dist, "Financial ratings; C and D grades flag viability concerns."),
    }
    choice = st.selectbox("Chart", list(views.keys()), key="ra_view")
    fn, cap = views[choice]; st.plotly_chart(fn(scored), width="stretch")
    st.markdown(f"<div class='note'>{cap}</div>", unsafe_allow_html=True)

with t_con:
    head("Systemic exposure", "Concentration risk", "The shared-dependency risk per-vendor scoring cannot see.")
    views = {
        "Dependency map": (lambda: charts.dependency_network(scored, groups), "Every vendor traces back to a shared provider. Node size = exposure, colour = avg risk."),
        "Provider exposure": (lambda: charts.exposure_bar(groups, top_prov["provider"]), "Share of portfolio per provider, weighted by criticality."),
        "Concentration treemap": (lambda: charts.provider_treemap(scored), "Provider broken down by data access; box size = spend, colour = risk."),
        "Risk by provider (stacked)": (lambda: charts.provider_risk_stacked(scored), "How high/medium/low-risk vendors stack up within each provider."),
        "Concentration gauge (HHI)": (lambda: charts.hhi_gauge(hhi_score), "Above 0.25 = dangerously concentrated - the DORA signal."),
    }
    choice = st.selectbox("Chart", list(views.keys()), key="cc_view")
    fn, cap = views[choice]; st.plotly_chart(fn(), width="stretch")
    st.markdown(f"<div class='note'>{cap}</div>", unsafe_allow_html=True)
    st.markdown("<div class='sect' style='margin-top:22px;'>Failure simulation</div>", unsafe_allow_html=True)
    prov = st.selectbox("If this provider has an outage / breach\u2026", groups["provider"].tolist(), key="cc_prov")
    sim = cc.simulate_failure(scored, prov)
    st.markdown("<div class='kpi-row' style='grid-template-columns:repeat(3,1fr);'>"
                + kpi("Vendors down", sim["count"], f"{sim['pct_portfolio']}% of portfolio", "r")
                + kpi("PII / financial hit", sim["pii_count"], "exposed at once", "a")
                + kpi("Spend at risk", f"${sim['spend_at_risk']:,}", "single point of failure", "b") + "</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='callout'>{cc.audit_answer(scored, prov)}</div>", unsafe_allow_html=True)
    st.markdown("<div class='sect' style='margin-top:18px;'>Hotspots &amp; recommended actions</div>", unsafe_allow_html=True)
    hs = cc.hotspots(groups).copy(); hs["exposure_pct"] = (hs["exposure_share"] * 100).round(0)
    st.dataframe(hs[["provider", "exposure_pct", "pii_vendors", "spend_at_risk", "recommendation"]], hide_index=True, width="stretch",
                 column_config={"provider": "Provider", "exposure_pct": st.column_config.NumberColumn("Exposure", format="%.0f%%"),
                                "pii_vendors": "PII vendors", "spend_at_risk": st.column_config.NumberColumn("Spend at risk", format="$%d"),
                                "recommendation": "Recommended action"})

with t_rep:
    head("Export", "Audit-ready report", "Generated in the format auditors expect.")
    rep = portfolio_report(scored, groups)
    st.markdown(f"<div class='rep'>{rep}</div>", unsafe_allow_html=True); st.write("")
    cda, cdb = st.columns(2)
    cda.download_button("Download report (.txt)", rep, "chainrisk_portfolio_report.txt", width="stretch")
    cdb.download_button("Download register (.csv)", scored.drop(columns=["risk_factors"]).to_csv(index=False).encode(), "chainrisk_register.csv", width="stretch")

with t_meth:
    head("How it works", "Methodology & framework", "The scoring logic, the concentration maths, and the regulatory mapping.")
    topic = st.selectbox("Topic", ["Risk scoring", "Accuracy validation", "Concentration maths", "DORA & frameworks", "Data note"], key="md_topic")
    if topic == "Risk scoring":
        st.markdown("""<div class='md-card'><div class='md-h'>Vendor risk scoring</div><p class='md-p'>ChainRisk evaluates every third party on a continuous 0&ndash;10 scale, combining breach history, certification validity, data-access sensitivity, financial health and contractual posture into a single, explainable score. Each vendor is banded <b>HIGH</b>, <b>MEDIUM</b> or <b>LOW</b>, and every score is presented alongside the specific factors behind it &mdash; so risk owners see not only how exposed a vendor is, but precisely why.</p></div><div class='md-card'><div class='md-h'>Critical-condition escalation</div><p class='md-p'>Vendors under an active security investigation, or with a recent breach combined with access to sensitive data, are escalated to the highest tier automatically. This ensures the highest-impact relationships are never masked by an averaged score.</p></div>""", unsafe_allow_html=True)
    elif topic == "Accuracy validation":
        st.markdown(f"""<div class='md-card'><div class='md-h'>Benchmarked detection</div><p class='md-p'>Scoring is benchmarked against analyst-reviewed outcomes, with emphasis on recall of the most severe vendors &mdash; under-detecting a breached processor of customer data carries far greater cost than over-flagging a moderate one. The current portfolio achieves full recall on critical vendors ({cr}/{ct}), with {res['flag_accuracy']}% overall agreement.</p></div>""", unsafe_allow_html=True)
    elif topic == "Concentration maths":
        st.markdown("""<div class='md-card'><div class='md-h'>Exposure share &amp; blast radius</div><p class='md-p'>ChainRisk maps the shared infrastructure the portfolio collectively depends on. For each provider it quantifies <b>exposure share</b> &mdash; the proportion of the portfolio's critical weight concentrated there &mdash; and <b>blast radius</b>: the vendors, sensitive-data holders and annual spend affected by that provider's failure.</p></div><div class='md-card'><div class='md-h'>Concentration index (HHI)</div><p class='md-p'>Overall concentration is expressed as a Herfindahl&ndash;Hirschman Index, the measure used in competition and market-structure analysis. Values above <code>0.25</code> indicate a portfolio dangerously dependent on a small number of providers.</p></div>""", unsafe_allow_html=True)
    elif topic == "DORA & frameworks":
        st.markdown("""<div class='md-card'><div class='md-h'>DORA &mdash; ICT concentration risk</div><p class='md-p'>ChainRisk is built around the EU Digital Operational Resilience Act, which requires financial entities to actively manage ICT concentration risk and maintain a register of critical third-party providers. The concentration analysis maps directly to these obligations.</p></div><div class='md-card'><div class='md-h'>Supporting frameworks</div><p class='md-p'>The platform also supports evidence for GDPR Article 28 (processor and sub-processor controls), GDPR Article 33 (breach-notification timelines), NIST SP 800-53 SA-9 (external system services) and SOX 404 (third-party control dependencies).</p></div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class='md-card'><div class='md-h'>Data &amp; sources</div><p class='md-p'>ChainRisk operates on the organisation's vendor register and assessment records. A provider-dependency layer &mdash; hosting provider and key sub-processor &mdash; together with financial-health and data-processing-agreement attributes enriches each record to enable the concentration analysis. In this build these enrichment attributes are modelled; in production they are sourced from procurement, CMDB and continuous-monitoring integrations.</p></div>""", unsafe_allow_html=True)

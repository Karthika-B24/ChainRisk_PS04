"""
ChainRisk - charts.py
Light professional palette. Pure functions, testable.
"""
import math
import plotly.express as px
import plotly.graph_objects as go

BRAND = "#0e8fa6"; INK = "#15233b"; MUTE = "#4a5a73"; FAINT = "#8593a8"
HIGH = "#dc2626"; MED = "#c2740a"; LOW = "#15803d"; ACCENT = "#0e8fa6"; GREY = "#cbd3df"
GRID = "#e6ebf3"
LEVEL_ORDER = ["LOW", "MEDIUM", "HIGH"]
LEVEL_COLORS = {"LOW": LOW, "MEDIUM": MED, "HIGH": HIGH}
FONT = dict(family="Inter, sans-serif", color=MUTE)
SCALE = [[0.0, "#eef2f7"], [0.5, "#eaa06e"], [1.0, "#dc2626"]]


def _clean(fig, h=380, title=None):
    fig.update_layout(height=h, margin=dict(t=46 if title else 16, b=14, l=10, r=18),
                      font=FONT, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      title=dict(text=title, font=dict(size=14, color=INK), x=0.01) if title else None,
                      legend=dict(orientation="h", y=1.08, x=0, font=dict(size=11, color=MUTE)),
                      coloraxis_colorbar=dict(outlinewidth=0, tickcolor=FAINT,
                                              tickfont=dict(color=FAINT, size=10)))
    fig.update_xaxes(showgrid=False, linecolor="#d4dbe6", color=FAINT, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, linecolor="#d4dbe6", color=FAINT, zeroline=False)
    return fig


def _risk_color(v):
    return HIGH if v >= 7 else MED if v >= 4 else LOW


def risk_donut(level_counts):
    fig = go.Figure(go.Pie(labels=LEVEL_ORDER, values=[level_counts.get(x, 0) for x in LEVEL_ORDER],
                           hole=.66, sort=False, marker=dict(colors=[LOW, MED, HIGH],
                           line=dict(color="#ffffff", width=3)),
                           textinfo="label+percent", textfont=dict(family="Inter", size=12, color="#ffffff")))
    fig.update_layout(height=300, margin=dict(t=12, b=12, l=12, r=12),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, sans-serif", color=MUTE),
                      title=dict(text=""), showlegend=False)
    return fig


def risk_heatmap(scored):
    p = scored.pivot_table(index="type", columns="data_access", values="risk_score_10", aggfunc="mean").round(1)
    fig = px.imshow(p, color_continuous_scale=SCALE, aspect="auto", text_auto=True, labels=dict(color="Avg risk"))
    fig.update_traces(textfont=dict(size=11))
    fig.update_xaxes(side="bottom")
    return _clean(fig, 460, "Average risk by vendor type and data access")


def risk_spend_scatter(scored):
    fig = px.scatter(scored, x="risk_score_10", y="annual_spend_usd", color="risk_level",
                     color_discrete_map=LEVEL_COLORS, category_orders={"risk_level": LEVEL_ORDER},
                     size="access_weight", size_max=20, hover_name="vendor_name", log_y=True,
                     labels={"risk_score_10": "Risk score (0-10)", "annual_spend_usd": "Annual spend ($, log)"})
    fig.update_traces(marker=dict(line=dict(width=0.6, color="#ffffff"), opacity=0.9))
    return _clean(fig, 440, "Risk vs spend - the top-right is where exposure concentrates")


def risk_by_type(scored):
    g = scored.groupby("type")["risk_score_10"].mean().sort_values()
    fig = go.Figure(go.Bar(x=g.values, y=g.index, orientation="h",
                           marker=dict(color=g.values, colorscale=SCALE, cmin=0, cmax=10),
                           text=[f"{v:.1f}" for v in g.values], textposition="outside", textfont=dict(color=MUTE)))
    fig.update_xaxes(range=[0, 10.5], title="avg risk (0-10)")
    return _clean(fig, 440, "Average risk score by vendor type")


def compliance_bars(scored):
    sens = scored[scored["sensitive"]]
    dpa = 100 * sens["gdpr_dpa"].mean() if len(sens) else 0
    soc2 = 100 * ((scored["certifications"].str.contains("SOC2")) & (~scored["cert_expired"])).mean()
    expired = 100 * scored["cert_expired"].mean()
    cats = ["GDPR DPA<br>(sensitive)", "SOC 2<br>current", "Certs<br>expired"]
    fig = go.Figure(go.Bar(x=cats, y=[dpa, soc2, expired], marker_color=[LOW, ACCENT, HIGH],
                           text=[f"{v:.0f}%" for v in [dpa, soc2, expired]], textposition="outside", textfont=dict(color=MUTE)))
    fig.update_yaxes(range=[0, 100], title="% of vendors")
    return _clean(fig, 400, "Compliance coverage across the portfolio")


def financial_dist(scored):
    order = ["A+", "A", "A-", "B", "C", "D"]
    g = scored["financial_rating"].value_counts().reindex(order, fill_value=0)
    cols = [LOW, LOW, LOW, MED, HIGH, HIGH]
    fig = go.Figure(go.Bar(x=order, y=g.values, marker_color=cols, text=g.values, textposition="outside", textfont=dict(color=MUTE)))
    fig.update_yaxes(title="vendors")
    return _clean(fig, 380, "Vendor financial-health distribution (C / D = viability concern)")


def exposure_bar(groups, top_provider):
    colors = [BRAND if p == top_provider else GREY for p in groups["provider"]]
    fig = go.Figure(go.Bar(x=groups["exposure_share"], y=groups["provider"], orientation="h",
                           marker_color=colors, text=[f"{v*100:.0f}%" for v in groups["exposure_share"]],
                           textposition="outside", textfont=dict(color=MUTE)))
    fig.update_layout(yaxis=dict(autorange="reversed"))
    fig.update_xaxes(visible=False)
    return _clean(fig, 300, "Share of portfolio per provider (by criticality)")


def provider_treemap(scored):
    fig = px.treemap(scored, path=["hosting_provider", "data_access"], values="annual_spend_usd",
                     color="risk_score_10", color_continuous_scale=SCALE, labels={"risk_score_10": "Avg risk"})
    fig.update_traces(marker=dict(cornerradius=4, line=dict(color="#ffffff", width=2)), textfont=dict(color="#15233b", size=12))
    return _clean(fig, 460, "Spend & risk by provider then data access (size = spend, colour = risk)")


def provider_risk_stacked(scored):
    ct = (scored.groupby(["hosting_provider", "risk_level"]).size().unstack(fill_value=0).reindex(columns=LEVEL_ORDER, fill_value=0))
    fig = go.Figure()
    for lv in LEVEL_ORDER:
        fig.add_bar(name=lv, x=ct.index, y=ct[lv], marker_color=LEVEL_COLORS[lv])
    fig.update_layout(barmode="stack")
    return _clean(fig, 400, "Risk distribution within each provider")


def hhi_gauge(hhi_score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=hhi_score, number=dict(font=dict(size=40, color=INK)),
        gauge=dict(axis=dict(range=[0, 0.6], tickcolor=FAINT), bar=dict(color=BRAND, thickness=0.32),
                   bordercolor="#e1e7f0", bgcolor="#ffffff",
                   steps=[dict(range=[0, 0.15], color="rgba(21,128,61,.14)"),
                          dict(range=[0.15, 0.25], color="rgba(194,116,10,.16)"),
                          dict(range=[0.25, 0.6], color="rgba(220,38,38,.14)")],
                   threshold=dict(line=dict(color=INK, width=3), value=0.25))))
    return _clean(fig, 330, "Portfolio concentration (HHI) - threshold 0.25")


def dependency_network(scored, groups):
    provs = groups.to_dict("records")
    nx, ny, txt, size, col = [0], [0], ["YOUR<br>ORG"], [46], [BRAND]
    ex, ey = [], []
    Nn = len(provs)
    for i, p in enumerate(provs):
        ang = 2 * math.pi * i / Nn - math.pi / 2
        x, y = math.cos(ang), math.sin(ang)
        nx.append(x); ny.append(y)
        txt.append(f"{p['provider']}<br>{p['vendors']} vendors")
        size.append(26 + p["exposure_share"] * 80)
        avg = scored[scored["hosting_provider"] == p["provider"]]["risk_score_10"].mean()
        col.append(_risk_color(avg))
        ex += [0, x, None]; ey += [0, y, None]
    edges = go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="#d2dae6", width=1.4), hoverinfo="skip")
    nodes = go.Scatter(x=nx, y=ny, mode="markers+text", text=txt, textposition="bottom center",
                       textfont=dict(color=MUTE, size=11),
                       marker=dict(size=size, color=col, line=dict(color="#ffffff", width=2.5)), hoverinfo="text")
    fig = go.Figure([edges, nodes])
    fig.update_xaxes(visible=False, range=[-1.5, 1.5]); fig.update_yaxes(visible=False, range=[-1.6, 1.6])
    fig.update_layout(showlegend=False)
    return _clean(fig, 460, "Dependency map - every vendor traces back to a shared provider")


if __name__ == "__main__":
    from scoring import load_data, build_scored
    import concentration as cc
    reg, lab = load_data(); s = build_scored(reg); g = cc.provider_groups(s)
    figs = [risk_donut(s["risk_level"].value_counts().to_dict()), risk_heatmap(s), risk_spend_scatter(s),
            risk_by_type(s), compliance_bars(s), financial_dist(s), exposure_bar(g, g.iloc[0]["provider"]),
            provider_treemap(s), provider_risk_stacked(s), hhi_gauge(0.31), dependency_network(s, g)]
    print("All", len(figs), "charts OK:", all(isinstance(f, go.Figure) for f in figs))

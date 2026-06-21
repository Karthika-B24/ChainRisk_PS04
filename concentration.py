"""
ChainRisk - concentration.py
Maps the shared providers vendors depend on, quantifies concentration,
ranks hotspots, and simulates a provider failure.

Works on the scored dataframe from scoring.build_scored().
"""
import pandas as pd

PROVIDER_COL = "hosting_provider"   # change to "key_subprocessor" for the secondary view


def provider_groups(scored, col=PROVIDER_COL):
    """One row per provider: vendor count, PII count, spend, criticality weight."""
    rows = []
    total_weight = scored["access_weight"].sum()
    total_spend = scored["annual_spend_usd"].sum()
    for prov, g in scored.groupby(col):
        weight = g["access_weight"].sum()
        rows.append({
            "provider": prov,
            "vendors": len(g),
            "pii_vendors": int(g["sensitive"].sum()),
            "spend_at_risk": int(g["annual_spend_usd"].sum()),
            "exposure_share": round(weight / total_weight, 4),         # by criticality
            "vendor_share": round(len(g) / len(scored), 4),            # by count
            "spend_share": round(g["annual_spend_usd"].sum() / total_spend, 4),
            "red_vendors": int((g["risk_level"] == "HIGH").sum()),
        })
    df = pd.DataFrame(rows).sort_values("exposure_share", ascending=False)
    return df.reset_index(drop=True)


def hhi(groups, share_col="exposure_share"):
    """Herfindahl-Hirschman Index: sum of squared shares. >0.25 = highly concentrated."""
    score = float((groups[share_col] ** 2).sum())
    if score > 0.25:   verdict = "HIGHLY concentrated"
    elif score > 0.15: verdict = "moderately concentrated"
    else:              verdict = "well diversified"
    return round(score, 3), verdict


def recommend(row):
    """Action per hotspot, by simple thresholds."""
    if row["exposure_share"] >= 0.35:
        return "Diversify: add a second provider for critical workloads"
    if row["pii_vendors"] >= 10:
        return "Require contractual failover + breach-notification for PII vendors"
    if row["exposure_share"] >= 0.15:
        return "Add to critical-provider continuous monitoring"
    return "Routine monitoring"


def hotspots(groups, top=5):
    h = groups.head(top).copy()
    h["recommendation"] = h.apply(recommend, axis=1)
    return h


def simulate_failure(scored, provider, col=PROVIDER_COL):
    """If `provider` fails, what falls with it?"""
    hit = scored[scored[col] == provider]
    return {
        "provider": provider,
        "affected": hit,
        "count": len(hit),
        "pii_count": int(hit["sensitive"].sum()),
        "spend_at_risk": int(hit["annual_spend_usd"].sum()),
        "pct_portfolio": round(100 * len(hit) / len(scored), 1),
    }


def audit_answer(scored, provider, col=PROVIDER_COL):
    """The novel one-line audit answer."""
    s = simulate_failure(scored, provider, col)
    return (f"If {provider} has an incident: {s['count']} vendors affected "
            f"({s['pct_portfolio']}% of the portfolio), {s['pii_count']} of them hold "
            f"customer PII or financial data, ${s['spend_at_risk']:,} of annual spend at risk.")


if __name__ == "__main__":
    from scoring import load_data, build_scored
    reg, lab = load_data()
    scored = build_scored(reg)

    groups = provider_groups(scored)
    print(groups.to_string(index=False))
    score, verdict = hhi(groups)
    print(f"\nPortfolio HHI: {score}  ->  {verdict}")
    print("\nTop hotspots:")
    print(hotspots(groups)[["provider", "exposure_share", "pii_vendors",
                            "spend_at_risk", "recommendation"]].to_string(index=False))
    top_provider = groups.iloc[0]["provider"]
    print("\n" + audit_answer(scored, top_provider))

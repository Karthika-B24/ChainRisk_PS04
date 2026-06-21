"""
ChainRisk - report.py
Generates the audit-ready portfolio report (risk summary, red-flag vendors,
audit-ready compliance), with a concentration-risk section.
"""
import datetime as dt
import concentration as cc


def portfolio_report(scored, groups=None):
    n = len(scored)
    lvl = scored["risk_level"].value_counts().to_dict()
    low, med, high = lvl.get("LOW", 0), lvl.get("MEDIUM", 0), lvl.get("HIGH", 0)
    L = []
    L.append("VENDOR RISK PORTFOLIO")
    L.append("=" * 21)
    L.append(f"Report Date: {dt.date.today().isoformat()}")
    L.append(f"Total Vendors Tracked: {n}")
    L.append("")
    L.append("RISK SUMMARY")
    L.append("")
    L.append(f"  LOW Risk:    {low:>3} vendors ({100*low/n:.0f}%)")
    L.append(f"  MEDIUM Risk: {med:>3} vendors ({100*med/n:.0f}%)")
    L.append(f"  HIGH Risk:   {high:>3} vendors ({100*high/n:.0f}%)")
    L.append("")
    L.append("RED FLAG VENDORS (Require Immediate Attention)")
    L.append("")
    for i, (_, r) in enumerate(scored[scored["risk_level"] == "HIGH"].head(5).iterrows(), 1):
        L.append(f"{i}. {r['vendor_name']} ({r['vendor_id']})")
        L.append(f"   Risk Score: {r['risk_score_10']}/10 [{r['risk_level']}]")
        L.append(f"   Issues:")
        for f in r["risk_factors"]:
            L.append(f"     {f}")
        L.append(f"   Access: {r['data_access']}")
        L.append(f"   Action Required: {r['recommendation']}")
        L.append("")

    # audit-ready compliance
    sens = scored[scored["sensitive"]]
    dpa_pct = 100 * sens["gdpr_dpa"].mean() if len(sens) else 0
    soc2_ok = scored["certifications"].str.contains("SOC2") & (~scored["cert_expired"])
    contracts_expired = int(scored["contract_expired"].sum())
    L.append("AUDIT-READY COMPLIANCE")
    L.append("")
    L.append(f"  Vendor coverage: 100% ({n} of {n} vendors tracked)")
    L.append(f"  GDPR DPA: {dpa_pct:.0f}% of vendors with sensitive access have a DPA")
    L.append(f"  SOC 2 (current): {100*soc2_ok.mean():.0f}% of vendors")
    L.append(f"  Contract terms: {contracts_expired} contracts expired / need renewal")
    L.append("")

    if groups is not None:
        hhi_score, verdict = cc.hhi(groups)
        top = groups.iloc[0]
        L.append("CONCENTRATION RISK (ChainRisk)")
        L.append("")
        L.append(f"  Portfolio concentration (HHI): {hhi_score} - {verdict}")
        L.append(f"  Top dependency: {top['provider']} carries "
                 f"{top['exposure_share']*100:.0f}% of the portfolio "
                 f"({top['vendors']} vendors, {top['pii_vendors']} holding PII/financial data)")
        L.append(f"  Single-provider blast radius: ${int(top['spend_at_risk']):,} annual spend at risk")
        L.append(f"  Mapped to: DORA ICT concentration-risk requirements")
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    from scoring import load_data, build_scored
    reg, lab = load_data()
    scored = build_scored(reg)
    groups = cc.provider_groups(scored)
    print(portfolio_report(scored, groups))

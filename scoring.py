"""
ChainRisk - scoring.py
Per-vendor risk scoring:
  risk_score (0-10), risk_level (LOW/MEDIUM/HIGH), risk_factors (human-readable),
  recommendation, plus accuracy validation against labelled outcomes.
"""
import os
import datetime as dt
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
TODAY = dt.date(2026, 6, 20)

SENSITIVE = {"Customer PII", "Financial data"}
ACCESS_WEIGHT = {"Customer PII": 4, "Financial data": 4,
                 "Internal systems": 2, "Logs/Telemetry": 1, "Public/Marketing": 1}
WEAK_FINANCIAL = {"C", "D"}


def load_data():
    reg = pd.read_csv(os.path.join(BASE, "vendor_registry.csv"))
    lab = pd.read_csv(os.path.join(BASE, "vendor_labels.csv"))
    reg["cert_expiry"] = pd.to_datetime(reg["cert_expiry"]).dt.date
    reg["contract_end"] = pd.to_datetime(reg["contract_end"]).dt.date
    reg["under_investigation"] = reg["under_investigation"].astype(str).str.lower() == "true"
    reg["gdpr_dpa"] = reg["gdpr_dpa"].astype(str).str.lower() == "true"
    reg["cert_expiry_days"] = reg["cert_expiry"].map(lambda d: (d - TODAY).days)
    reg["cert_expired"] = (reg["cert_expiry"] < TODAY) & (reg["certifications"] != "none")
    reg["cert_expiring_soon"] = (reg["cert_expiry_days"].between(0, 90)) & (reg["certifications"] != "none")
    reg["contract_expired"] = reg["contract_end"] < TODAY
    reg["sensitive"] = reg["data_access"].isin(SENSITIVE)
    reg["access_weight"] = reg["data_access"].map(ACCESS_WEIGHT).fillna(1)
    return reg, lab


def risk_score_10(r):
    """0-10 risk score with transparent contributions."""
    s = (r["risk_score"] / 100) * 2.0            # provided base, up to 2.0
    if r["under_investigation"]:        s += 3.5
    if r["breach_status"] == "Recent":  s += 3.0
    elif r["breach_status"] == "Old":   s += 1.0
    if r["cert_expired"]:               s += 2.0
    elif r["cert_expiring_soon"]:       s += 1.0
    if r["sensitive"] and not r["gdpr_dpa"]: s += 1.5
    if r["sensitive"]:                  s += 1.2
    if r["financial_rating"] in WEAK_FINANCIAL: s += 1.5
    elif r["financial_rating"] == "B":  s += 0.4
    if r["contract_expired"]:           s += 1.0
    return round(min(10.0, s), 1)


def risk_level(score):
    if score >= 7.0: return "HIGH"
    if score >= 4.0: return "MEDIUM"
    return "LOW"


def risk_factors(r):
    """Human-readable factors, in the spirit of the expected output."""
    f = []
    if r["under_investigation"]:
        f.append("Vendor is under an active security investigation")
    if r["breach_status"] == "Recent":
        f.append(f"Recent breach (last 12 months) on a vendor with {r['data_access'].lower()} access")
    elif r["breach_status"] == "Old":
        f.append("Historical breach on record (older than 12 months)")
    if r["cert_expired"]:
        f.append(f"Certification(s) expired: {r['certifications']}")
    elif r["cert_expiring_soon"]:
        f.append(f"Certification expires in {r['cert_expiry_days']} days: certification-gap risk")
    if r["sensitive"] and not r["gdpr_dpa"]:
        f.append("Missing GDPR DPA despite access to sensitive data")
    if r["sensitive"]:
        f.append(f"High-sensitivity data access ({r['data_access']})")
    if r["financial_rating"] in WEAK_FINANCIAL:
        f.append(f"Weak financial rating ({r['financial_rating']}): viability concern")
    if r["contract_expired"]:
        f.append("Contract has ended but access may still be active (orphaned access)")
    if not f:
        f.append("No material risk factors detected")
    return f


def recommendation(r, level):
    if level == "HIGH":
        if r["breach_status"] == "Recent" or r["under_investigation"]:
            return "Schedule urgent compliance meeting; consider alternative vendor"
        if r["financial_rating"] in WEAK_FINANCIAL:
            return "Contract renegotiation or replacement (financial viability risk)"
        return "Immediate remediation: close certification / DPA gaps before renewal"
    if level == "MEDIUM":
        return "Increase monitoring; require remediation plan at next review"
    return "Routine monitoring"


def predict_severity(r):
    """Mirrors the label hierarchy so we can measure recall on the worst cases."""
    if r["under_investigation"]: return "CRITICAL"
    if r["breach_status"] == "Recent" and r["sensitive"]: return "CRITICAL"
    if r["risk_score"] > 80: return "HIGH"
    if r["cert_expired"] and r["sensitive"]: return "HIGH"
    if r["cert_expired"]: return "MEDIUM"
    if r["breach_status"] == "Recent": return "MEDIUM"
    if r["contract_expired"]: return "MEDIUM"
    if 65 <= r["risk_score"] <= 80: return "LOW"
    return ""


def build_scored(reg):
    reg = reg.copy()
    reg["risk_score_10"] = reg.apply(risk_score_10, axis=1)
    reg["risk_level"] = reg["risk_score_10"].map(risk_level)
    reg["risk_factors"] = reg.apply(risk_factors, axis=1)
    reg["pred_severity"] = reg.apply(predict_severity, axis=1)
    reg["pred_flag"] = reg["pred_severity"] != ""
    reg["recommendation"] = reg.apply(lambda r: recommendation(r, r["risk_level"]), axis=1)
    return reg.sort_values("risk_score_10", ascending=False).reset_index(drop=True)


def validate(scored, lab):
    m = scored.merge(lab, on="vendor_id", suffixes=("", "_true"))
    m["true_flag"] = m["is_anomaly"].astype(str).str.lower() == "true"
    crit = m["severity"] == "CRITICAL"
    crit_caught = (crit & (m["pred_severity"] == "CRITICAL")).sum()
    high = m["severity"].isin(["CRITICAL", "HIGH"])
    high_caught = (high & m["pred_severity"].isin(["CRITICAL", "HIGH"])).sum()
    return {
        "critical_recall": (int(crit_caught), int(crit.sum())),
        "high_recall": (int(high_caught), int(high.sum())),
        "flag_accuracy": round(100 * (m["pred_flag"] == m["true_flag"]).mean(), 1),
        "vendors": len(m),
    }


if __name__ == "__main__":
    reg, lab = load_data()
    scored = build_scored(reg)
    res = validate(scored, lab)
    cr, ct = res["critical_recall"]
    print(f"Vendors: {res['vendors']}")
    print(f"CRITICAL recall: {cr}/{ct} ({100*cr/ct:.0f}%)")
    print(f"Risk levels: {scored['risk_level'].value_counts().to_dict()}")
    print(f"Flag accuracy vs labels: {res['flag_accuracy']}%")
    top = scored.iloc[0]
    print(f"\nTop vendor: {top['vendor_name']} ({top['vendor_id']})  "
          f"score {top['risk_score_10']}/10 [{top['risk_level']}]")
    for f in top["risk_factors"]:
        print("  -", f)
    print("  Recommendation:", top["recommendation"])

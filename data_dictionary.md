# ChainRisk — Data Dictionary

The application reads two files: a vendor register and a set of labelled outcomes used to
validate detection. The provider-dependency, financial-health and DPA attributes below are
modelled in this build; in production they are sourced from procurement, CMDB and
continuous-monitoring integrations.

Reference "today" for all date logic: **2026-06-20**. Random seed: 42 (reproducible).

## vendor_registry.csv  (400 rows)

| Column | Meaning |
|---|---|
| `vendor_id` | Unique ID, V0001–V0400. Join key to the labels file. |
| `vendor_name` | Synthetic vendor name. |
| `type` | Vendor category (Cloud provider, Software vendor, Contractor/Consultant, MSP, Payment processor, HR platform, Backup/Storage, Security vendor, Data platform, Integration partner). |
| `data_access` | Sensitivity of data the vendor can reach: Customer PII, Financial data, Internal systems, Logs/Telemetry, Public/Marketing. PII + Financial = "sensitive". |
| `certifications` | Held certs (`SOC2;ISO27001;PCI-DSS`) or `none`. |
| `cert_expiry` | Expiry date of the certification(s). Past date = expired. |
| `breach_status` | None / Recent (≤12 months) / Old (>12 months). |
| `under_investigation` | True if the vendor is under an active security investigation. |
| `risk_score` | Provided risk score, 0–100. |
| `annual_spend_usd` | Annual spend with the vendor (used for blast-radius / weighting). |
| `contract_start`, `contract_end` | Contract dates. `contract_end` in the past = expired. |
| `hosting_provider` | *(modelled enrichment)* Which cloud the vendor runs on: AWS / Azure / GCP / On-prem/Other. Distribution ≈ AWS 49%, Azure 25%, GCP 13%, On-prem 13%. |
| `key_subprocessor` | *(modelled enrichment)* A shared sub-provider (Okta, Twilio, Stripe, Cloudflare, SendGrid) or None — for secondary concentration. |

## vendor_labels.csv  (400 rows, ground truth)

| Column | Meaning |
|---|---|
| `vendor_id` | Join key to the registry. |
| `is_anomaly` | True if the vendor is flagged (≈79% are — tiered response, not pass/fail). |
| `anomaly_type` | One of: BREACHED_VENDOR_HIGH_ACCESS, VENDOR_UNDER_INVESTIGATION, HIGH_RISK_SCORE, EXPIRED_CERTIFICATION, RECENTLY_BREACHED_VENDOR, CONTRACT_EXPIRED_ACTIVE_ACCESS, ELEVATED_RISK_VENDOR. |
| `severity` | CRITICAL / HIGH / MEDIUM / LOW (empty if not an anomaly). |
| `expired_certifications` | The cert(s) that were expired, if relevant. |
| `explanation` | One-line human reason for the flag. |

### How labels are derived
Highest-severity rule wins, in this order:
1. `under_investigation` → VENDOR_UNDER_INVESTIGATION (CRITICAL)
2. Recent breach **and** sensitive data access → BREACHED_VENDOR_HIGH_ACCESS (CRITICAL)
3. `risk_score` > 80 → HIGH_RISK_SCORE (HIGH)
4. Expired cert **and** sensitive access → EXPIRED_CERTIFICATION (HIGH); expired cert otherwise → (MEDIUM)
5. Recent breach (non-sensitive) → RECENTLY_BREACHED_VENDOR (MEDIUM)
6. Contract expired → CONTRACT_EXPIRED_ACTIVE_ACCESS (MEDIUM)
7. `risk_score` 65–80 → ELEVATED_RISK_VENDOR (LOW)
8. otherwise → not an anomaly

### Current dataset stats
- Flagged: 316 / 400 (79%)
- Severity mix: 32 CRITICAL, 109 HIGH, 149 MEDIUM, 26 LOW
- Hosting HHI: 0.34 → **highly concentrated**
- Top provider AWS: 197 vendors, 76 of which hold PII/financial data

## Additional fields
| Column | Meaning |
|---|---|
| `financial_rating` | Vendor financial health A+ / A / A- / B / C / D. C and D = viability concern (a risk factor). |
| `gdpr_dpa` | True/False — whether a GDPR Data Processing Agreement is on file. Missing DPA on a sensitive-data vendor is a risk factor. |

### Scoring output (from scoring.py / build_scored)
- `risk_score_10` — 0–10 risk score.
- `risk_level` — HIGH (≥7) / MEDIUM (≥4) / LOW.
- `risk_factors` — list of human-readable reasons.
- `recommendation` — action (urgent meeting / renegotiate / monitor …).
- `pred_severity` — CRITICAL/HIGH/MEDIUM/LOW used for accuracy validation against labelled outcomes.

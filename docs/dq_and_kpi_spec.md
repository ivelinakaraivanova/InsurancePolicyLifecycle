# Insurance Policy Lifecycle — DQ & KPI Specification

---

## Data Quality Framework

DQ checks run at three layers (Bronze, Silver, Gold). Each check produces a finding
with fields: `check`, `column`, `issue`, `row_count`, `pct`, `status` (PASS/FAIL).
Reports are written to `logs/dq_<layer>_report.txt`.

---

## Bronze DQ Checks (`dq_bronze.py`)

| # | Check Type  | Column(s)                        | Rule                           |
|---|-------------|----------------------------------|--------------------------------|
| 1 | Completeness | All 16 source columns           | No nulls allowed               |
| 2 | Uniqueness  | OBJECT_ID, INSR_BEGIN, INSR_END  | No duplicate policy periods    |
| 3 | Validity    | PREMIUM                          | Must be > 0                    |
| 4 | Validity    | INSR_BEGIN                       | Parseable as `dd-MMM-yy`       |
| 5 | Validity    | INSR_END                         | Parseable as `dd-MMM-yy`       |
| 6 | Consistency | INSR_END vs INSR_BEGIN           | End date ≥ start date          |

---

## Silver DQ Checks (`dq_silver.py`)

| # | Check Type  | Column(s)                            | Rule                            |
|---|-------------|--------------------------------------|---------------------------------|
| 1 | Completeness | All Silver columns                  | Null check per column           |
| 2 | Uniqueness  | object_id, insr_begin, insr_end      | No duplicates                   |
| 3 | Validity    | premium                              | Must be > 0                     |
| 4 | Consistency | insr_end vs insr_begin               | End date ≥ start date (DateType)|
| 5 | Validity    | vehicle_age                          | Must be ≥ 0                     |
| 6 | Validity    | policy_duration_days                 | Must be > 0                     |

---

## Gold DQ Checks (`dq_gold.py`)

| # | Check Type  | Column(s)                                                              | Rule                               |
|---|-------------|------------------------------------------------------------------------|------------------------------------|
| 1 | Completeness | lifecycle_status, is_active, is_expired, renewal_candidate, risk_score | No nulls                          |
| 2 | Validity    | lifecycle_status                                                        | Must be in {active, expired, future} |
| 3 | Validity    | risk_score                                                              | Must be in {0, 1, 2, 3}           |

---

## KPI Definitions

KPIs are computed in two places: Parquet files (`gold_kpis.py`) and PostgreSQL views
(`create_kpi_views_ins.sql`).

### Portfolio KPIs (`vw_portfolio_kpis`)

Single-row summary across all policies.

| KPI                | Formula                                 |
|--------------------|-----------------------------------------|
| total_policies     | COUNT(*)                                |
| active_policies    | SUM(is_active)                          |
| expired_policies   | SUM(is_expired)                         |
| renewal_candidates | SUM(renewal_candidate)                  |
| total_premium      | SUM(premium)                            |
| total_claims       | SUM(claim_paid)                         |
| loss_ratio         | total_claims / NULLIF(total_premium, 0) |
| avg_risk_score     | AVG(risk_score)                         |

### Vehicle KPIs (`vw_vehicle_kpis`)

Grouped by `make` and `type_vehicle`. Same metrics as portfolio KPIs.

### Product KPIs (`vw_product_kpis`)

Grouped by `insr_type_name` (Third party / Comprehensive / Other). Same metrics.

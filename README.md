# Insurance Policy Lifecycle

End-to-end data engineering portfolio project — vehicle insurance data pipeline from raw CSV ingestion through a medallion lakehouse, PostgreSQL star schema, and a 6-page Power BI dashboard.

---

## Overview

| Layer | Technology | Purpose |
|---|---|---|
| Ingestion | PySpark 4.1 | Raw CSV → Bronze (Parquet) |
| Transformation | PySpark 4.1 | Bronze → Silver (cleaned) → Gold (aggregated) |
| Orchestration | Apache Airflow 3.1 | Daily pipeline DAG |
| Storage | PostgreSQL 18 | Star schema + KPI views |
| Analytics | Power BI Desktop | 6-page interactive dashboard |
| Infrastructure | Docker Compose | Spark, Airflow, PostgreSQL containers |

---

## Architecture

```
raw CSV
  └── raw_to_bronze.py  ──►  Bronze (Parquet)
        └── bronze_to_silver.py  ──►  Silver (cleaned, typed)
              └── silver_to_gold.py  ──►  Gold (fact + dims)
                    └── gold_kpis.py  ──►  Gold KPI aggregates
                          └── gold_to_postgres.py  ──►  PostgreSQL star schema
                                └── Power BI  ──►  Dashboard
```

Each stage includes a dedicated data quality check (`dq_bronze.py`, `dq_silver.py`, `dq_gold.py`).

---

## Repository Structure

```
src/
  airflow/
    insurance_daily_pipeline.py   # Airflow DAG — orchestrates full pipeline
  pyspark/
    raw_to_bronze.py              # Ingest raw CSV, write Parquet
    bronze_to_silver.py           # Clean, cast types, deduplicate
    silver_to_gold.py             # Build fact_policies + dimension tables
    gold_kpis.py                  # Compute KPI aggregates
    gold_to_postgres.py           # Load Gold layer into PostgreSQL
    dq_bronze.py / dq_silver.py / dq_gold.py   # Data quality checks
    config.py / utils.py / logger.py            # Shared utilities
  sql/
    create_star_schema_ins.sql    # DDL for star schema tables
    create_kpi_views_ins.sql      # KPI views (vw_portfolio_kpis, etc.)
    analytics_queries_ins.sql     # Ad-hoc analytics queries
data/
  raw/                            # Source CSV files
  bronze/ / silver/ / gold/       # Medallion Parquet layers
dashboards/
  insurance_lifecycle.pbix        # Power BI dashboard
  insurance_theme.json            # Custom Power BI theme
docs/
  architecture.md                 # System architecture details
  data_dictionary.md              # Field definitions for all tables
  dq_and_kpi_spec.md              # Data quality rules & KPI specifications
  runbook.md                      # Operational runbook (setup, run, troubleshoot)
```

---

## Data Model

**Star schema in PostgreSQL (`insurance_db`):**

- `fact_policies` — one row per policy, with foreign keys to all dimensions
- `dim_vehicle` — vehicle attributes (make, model, type, age, value)
- `dim_insurance_type` — product type (Comprehensive, Third party, Other)
- `dim_date` — calendar dimension (date, year, month, quarter)
- `vw_portfolio_kpis` — portfolio-level KPI view
- `vw_vehicle_kpis` — per-make/model KPI view
- `vw_product_kpis` — per-product KPI view

---

## DAX Measures

Defined in the `_Measures` table in Power BI:

| Measure | Description |
|---|---|
| Total Policies | Count of all policies |
| Active Policies | Policies with `lifecycle_status = 'active'` |
| Expired Policies | Policies with `lifecycle_status = 'expired'` |
| Renewal Candidates | Policies expiring within 30 days |
| Total Premium | Sum of `premium_amount` |
| Total Claims | Sum of `claim_amount` |
| Loss Ratio | `Total Claims / Total Premium` |
| Avg Risk Score | Average `risk_score` |
| Active Rate % | `Active Policies / Total Policies` |
| Renewal Rate % | `Renewal Candidates / Total Policies` |

---

## Dashboard Pages

| Page | Contents |
|---|---|
| Portfolio Overview | 6 KPI cards, lifecycle donut, premium vs claims bar, 2 gauges |
| Product Analysis | Product slicer, 3 charts, KPI table, premium segment mix |
| Vehicle Analysis | Top 10 makes bar, risk distribution, vehicle KPIs table, risk by type |
| Trends | Year slicer, policy volume by year, monthly premium trend, quarterly line |
| Renewals & Risk | Renewal & risk cards, risk slicer, renewal bar, risk by product, scatter |
| Make Detail | Drillthrough on vehicle make — 5 cards, 3 charts, lifecycle breakdown table |

---

## Infrastructure

Services defined in `docker-compose.yml`:

| Container | Image | Port |
|---|---|---|
| `insurance-spark` | Jupyter/PySpark | 8888 |
| `insurance-airflow` | Apache Airflow 3.1 | 8080 |
| `insurance-postgres` | PostgreSQL 18 | 5433 |

---

## Quick Start

1. **Start containers**
   ```bash
   docker compose up -d
   ```

2. **Run the pipeline manually** (or trigger via Airflow UI at `http://localhost:8080`)
   ```bash
   docker exec insurance-spark bash -c "
     PYTHONPATH=/usr/local/spark/python:/usr/local/spark/python/lib/py4j-0.10.9.7-src.zip \
     python /home/jovyan/work/src/pyspark/raw_to_bronze.py"
   ```

3. **Load PostgreSQL schema**
   ```bash
   docker exec -i insurance-postgres psql -U postgres -d insurance_db \
     < src/sql/create_star_schema_ins.sql
   ```

4. **Open dashboard**  
   Open `dashboards/insurance_lifecycle.pbix` in Power BI Desktop.

See [docs/runbook.md](docs/runbook.md) for full setup and troubleshooting.

---

## Documentation

- [Architecture](docs/architecture.md)
- [Data Dictionary](docs/data_dictionary.md)
- [DQ & KPI Specification](docs/dq_and_kpi_spec.md)
- [Runbook](docs/runbook.md)


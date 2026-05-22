# Insurance Policy Lifecycle — Architecture

## Overview

An end-to-end batch ETL pipeline that processes raw motor insurance CSVs through a
Medallion architecture (Bronze → Silver → Gold), loads the enriched data into a
PostgreSQL star schema, and exposes KPI views for Power BI reporting.

## Technology Stack

| Component      | Technology              | Version  |
|----------------|-------------------------|----------|
| Orchestration  | Apache Airflow          | 3.1.8    |
| Processing     | PySpark                 | 4.1.1    |
| Storage (DW)   | PostgreSQL              | 18       |
| Reporting      | Power BI Desktop        | —        |
| Containerisation | Docker Compose        | —        |

## Containers

| Container            | Image                          | Port (host→container) |
|----------------------|--------------------------------|-----------------------|
| `insurance-spark`    | jupyter/pyspark-notebook       | 8889→8888             |
| `insurance-postgres` | postgres:18                    | 5433→5432             |
| `insurance-airflow`  | apache/airflow (standalone)    | 8081→8080             |

## Data Flow

```text
data/raw/*.csv
│
▼
[raw_to_bronze.py]        →  data/bronze/policies_raw.parquet
│
▼
[dq_bronze.py]            →  logs/dq_bronze_report.txt
│
▼
[bronze_to_silver.py]     →  data/silver/policies_clean/
│
▼
[dq_silver.py]            →  logs/dq_silver_report.txt
│
▼
[silver_to_gold.py]       →  data/gold/policies_lifecycle/
│
▼
[dq_gold.py]              →  logs/dq_gold_report.txt
│
├── [gold_kpis.py]        →  data/gold/kpi_tables/{portfolio,vehicle,product}_kpis/
│
▼
[gold_to_postgres.py]     →  PostgreSQL: policies_lifecycle (flat staging)
│
▼
[create_star_schema_ins.sql]
│   dim_vehicle, dim_insurance_type, dim_date, fact_policies
▼
[create_kpi_views_ins.sql]
│   vw_portfolio_kpis, vw_vehicle_kpis, vw_product_kpis
▼
Power BI Desktop  (localhost:5433 / insurance_db)
```


## Airflow DAG

DAG ID: `insurance_daily_pipeline`  
Schedule: manual (`schedule=None`)  
Task chain: `raw_to_bronze >> dq_bronze >> bronze_to_silver >> dq_silver >> silver_to_gold >> dq_gold >> gold_to_postgres`

Each task runs its PySpark script via `docker exec` against `insurance-spark`.

## Project Structure

```text
InsurancePolicyLifecycle/
├── data/
│   ├── raw/          Raw CSV source files
│   ├── bronze/       Parquet — ingested, unmodified
│   ├── silver/       Parquet — cleaned, normalised
│   └── gold/         Parquet — business-enriched + KPI tables
├── docs/             This documentation
├── logs/             DQ reports and pipeline logs
├── notebooks/        Exploratory analysis (exploration.ipynb)
├── src/
│   ├── airflow/      Airflow DAG
│   ├── pyspark/      ETL scripts and shared modules
│   └── sql/          Star schema DDL, KPI views, analytics queries
└── dashboards/       Power BI .pbix file
```

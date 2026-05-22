# Insurance Policy Lifecycle — Runbook

---

## Prerequisites

- Docker Desktop running
- `.env` file at project root with:

  ```
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5432
  POSTGRES_USER=<user>
  POSTGRES_PASSWORD=<password>
  POSTGRES_DB=insurance_db
  ```

- Three containers running: `insurance-spark`, `insurance-postgres`, `insurance-airflow`

---

## Starting the Stack

```bash
docker compose up -d
```

| Service    | URL / Connection                                     |
|------------|------------------------------------------------------|
| JupyterLab | http://localhost:8889  (token in docker-compose.yml) |
| Airflow UI | http://localhost:8081  (admin / see docker-compose)  |
| PostgreSQL | localhost:5433, DB: insurance_db                     |

---

## Running the Pipeline

### Option A — Airflow (recommended)

1. Open http://localhost:8081
2. Enable and trigger DAG `insurance_daily_pipeline` manually
3. Monitor task progress in the Grid or Graph view
4. DQ reports appear in `logs/` after each DQ task

### Option B — Manual (JupyterLab terminal)

Run from `/home/jovyan/work` inside the Spark container:

```bash
python src/pyspark/raw_to_bronze.py
python src/pyspark/dq_bronze.py
python src/pyspark/bronze_to_silver.py
python src/pyspark/dq_silver.py
python src/pyspark/silver_to_gold.py
python src/pyspark/dq_gold.py
python src/pyspark/gold_to_postgres.py
```

After loading to PostgreSQL, apply the star schema and views once:

```bash
psql -h localhost -p 5433 -U <user> -d insurance_db -f src/sql/create_star_schema_ins.sql
psql -h localhost -p 5433 -U <user> -d insurance_db -f src/sql/create_kpi_views_ins.sql
```

---

## Connecting Power BI

1. Open Power BI Desktop → **Get Data** → **PostgreSQL**
2. Server: `localhost:5433`  |  Database: `insurance_db`
3. Import tables: `fact_policies`, `dim_vehicle`, `dim_insurance_type`, `dim_date`
4. Import views: `vw_portfolio_kpis`, `vw_vehicle_kpis`, `vw_product_kpis`
5. Define relationships in Model view (fact_policies FK columns → dim PKs)

---

## DQ Reports

| Report file             | Layer  | Location |
|-------------------------|--------|----------|
| `dq_bronze_report.txt`  | Bronze | `logs/`  |
| `dq_silver_report.txt`  | Silver | `logs/`  |
| `dq_gold_report.txt`    | Gold   | `logs/`  |

All checks should show `PASS`. A `FAIL` means the pipeline produced unexpected data
and should be investigated before downstream consumption.

---

## Troubleshooting

| Symptom                                  | Cause / Fix                                                           |
|------------------------------------------|-----------------------------------------------------------------------|
| `ModuleNotFoundError: pyspark`           | Ensure `PYTHONPATH=/usr/local/spark/python:...` is set in docker exec |
| `EnvironmentError: POSTGRES_DB not set`  | Check `.env` exists and all 5 PG variables are present               |
| Airflow task stuck in "queued"           | Restart container: `docker restart insurance-airflow`                 |
| `BashOperator` import error              | Use `airflow.providers.standard.operators.bash.BashOperator`          |
| PostgreSQL connection refused            | Confirm `insurance-postgres` is running and port 5433 is mapped       |
| Duplicate FK constraint error            | Re-run `create_star_schema_ins.sql` (DROP TABLE handles it)           |

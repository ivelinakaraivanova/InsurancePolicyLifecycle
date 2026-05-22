"""
Airflow DAG for the Insurance Policy Lifecycle ETL pipeline.

Orchestrates the full pipeline: Raw → Bronze → Silver → Gold → PostgreSQL.
Triggered manually (schedule=None) since the dataset is historical.
"""

from datetime import datetime
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator  # type: ignore


SPARK_CONTAINER = "insurance-spark"
WORK_DIR        = "/home/jovyan/work"
PYTHONPATH      = "/usr/local/spark/python:/usr/local/spark/python/lib/py4j-0.10.9.7-src.zip"


def spark_cmd(script: str) -> str:
    """Return a docker exec command to run a PySpark script in the Spark container."""
    return (
        f"docker exec -e PYTHONPATH={PYTHONPATH} "
        f"{SPARK_CONTAINER} /opt/conda/bin/python {WORK_DIR}/src/pyspark/{script}"
    )


with DAG(
    dag_id="insurance_daily_pipeline",
    description="Insurance Policy Lifecycle ETL: Raw → Bronze → Silver → Gold → PostgreSQL",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["insurance", "etl"],
) as dag:

    raw_to_bronze = BashOperator(
        task_id="raw_to_bronze",
        bash_command=spark_cmd("raw_to_bronze.py"),
    )

    dq_bronze = BashOperator(
        task_id="dq_bronze",
        bash_command=spark_cmd("dq_bronze.py"),
    )

    bronze_to_silver = BashOperator(
        task_id="bronze_to_silver",
        bash_command=spark_cmd("bronze_to_silver.py"),
    )

    dq_silver = BashOperator(
        task_id="dq_silver",
        bash_command=spark_cmd("dq_silver.py"),
    )

    silver_to_gold = BashOperator(
        task_id="silver_to_gold",
        bash_command=spark_cmd("silver_to_gold.py"),
    )

    dq_gold = BashOperator(
        task_id="dq_gold",
        bash_command=spark_cmd("dq_gold.py"),
    )

    gold_to_postgres = BashOperator(
        task_id="gold_to_postgres",
        bash_command=spark_cmd("gold_to_postgres.py"),
    )

    (
        raw_to_bronze
        >> dq_bronze
        >> bronze_to_silver
        >> dq_silver
        >> silver_to_gold
        >> dq_gold
        >> gold_to_postgres
    )
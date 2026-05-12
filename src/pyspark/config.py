"""
Central configuration for the Insurance Policy Lifecycle pipeline.

All path constants, log file paths, and PostgreSQL connection settings
are defined here.

PostgreSQL variables (POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER,
POSTGRES_PASSWORD, POSTGRES_DB) are required and must be present in
the .env file at the project root. The pipeline will raise EnvironmentError
immediately if any of them are missing.
"""

import os
from dotenv import load_dotenv

# ── Project root (3 levels up from src/pyspark/config.py) ─────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env from project root (no-op if variables are already set in the environment)
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ── Data layer directories ─────────────────────────────────────────────────────
DATA_DIR    = os.path.join(BASE_DIR, "data")
RAW_DIR     = os.path.join(DATA_DIR, "raw")
BRONZE_DIR  = os.path.join(DATA_DIR, "bronze")
SILVER_DIR  = os.path.join(DATA_DIR, "silver")
GOLD_DIR    = os.path.join(DATA_DIR, "gold")
LOGS_DIR    = os.path.join(BASE_DIR, "logs")

# ── Raw source files ───────────────────────────────────────────────────────────
RAW_FILE_11_14 = os.path.join(RAW_DIR, "motor_data11-14lats.csv")
RAW_FILE_14_18 = os.path.join(RAW_DIR, "motor_data14-2018.csv")

# ── Bronze ─────────────────────────────────────────────────────────────────────
BRONZE_POLICIES = os.path.join(BRONZE_DIR, "policies_raw.parquet")

# ── Silver ─────────────────────────────────────────────────────────────────────
SILVER_POLICIES = os.path.join(SILVER_DIR, "policies_clean")

# ── Gold ───────────────────────────────────────────────────────────────────────
GOLD_LIFECYCLE     = os.path.join(GOLD_DIR, "policies_lifecycle")
GOLD_KPI_DIR       = os.path.join(GOLD_DIR, "kpi_tables")
GOLD_KPI_PORTFOLIO = os.path.join(GOLD_KPI_DIR, "portfolio_kpis")
GOLD_KPI_VEHICLE   = os.path.join(GOLD_KPI_DIR, "vehicle_kpis")
GOLD_KPI_PRODUCT   = os.path.join(GOLD_KPI_DIR, "product_kpis")

# ── Log files ──────────────────────────────────────────────────────────────────
LOG_RAW_TO_BRONZE    = os.path.join(LOGS_DIR, "raw_to_bronze.log")
LOG_BRONZE_TO_SILVER = os.path.join(LOGS_DIR, "bronze_to_silver.log")
LOG_SILVER_TO_GOLD   = os.path.join(LOGS_DIR, "silver_to_gold.log")
LOG_GOLD_TO_POSTGRES = os.path.join(LOGS_DIR, "gold_to_postgres.log")

# ── DQ report files ────────────────────────────────────────────────────────────
DQ_REPORT_BRONZE = os.path.join(LOGS_DIR, "dq_bronze_report.txt")
DQ_REPORT_SILVER = os.path.join(LOGS_DIR, "dq_silver_report.txt")
DQ_REPORT_GOLD   = os.path.join(LOGS_DIR, "dq_gold_report.txt")

# ── PostgreSQL (required — must be set in .env) ────────────────────────────────
def _require_env(key: str) -> str:
    """
    Read a required environment variable.
    """
    value = os.getenv(key)
    if value is None:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            "Check your .env file."
        )
    return value

PG_HOST = _require_env("POSTGRES_HOST")
PG_PORT = _require_env("POSTGRES_PORT")
PG_USER = _require_env("POSTGRES_USER")
PG_PASS = _require_env("POSTGRES_PASSWORD")
PG_DB   = _require_env("POSTGRES_DB")

JDBC_URL        = f"jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}"
JDBC_PROPERTIES = {
    "user": PG_USER, 
    "password": PG_PASS, 
    "driver": "org.postgresql.Driver"}
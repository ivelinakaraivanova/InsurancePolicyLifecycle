"""
Gold → PostgreSQL loader for the Insurance Policy Lifecycle pipeline.

Writes the Gold lifecycle table as a flat staging table to PostgreSQL via JDBC.
"""

from config import GOLD_LIFECYCLE, JDBC_URL, JDBC_PROPERTIES
from logger import get_logger
from utils import get_spark, read_parquet, write_postgres, log_row_counts


STAGING_TABLE = "policies_lifecycle"


def main():
    log = get_logger("gold_to_postgres")
    spark = get_spark("gold_to_postgres", with_postgres=True)

    log.info("Starting gold_to_postgres.")

    df = read_parquet(spark, GOLD_LIFECYCLE)
    log_row_counts(log, "Gold lifecycle (input)", df)

    write_postgres(df, STAGING_TABLE, JDBC_URL, JDBC_PROPERTIES)
    log.info(f"Written {df.count():,} rows to PostgreSQL table: {STAGING_TABLE}")

    log.info("gold_to_postgres completed successfully.")
    spark.stop()


if __name__ == "__main__":
    main()
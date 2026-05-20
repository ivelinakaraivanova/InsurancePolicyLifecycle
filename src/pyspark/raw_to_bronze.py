"""
Raw → Bronze ingestion for the Insurance Policy Lifecycle pipeline.

Reads both source CSV files from data/raw/, unions them by column name,
and writes the result as Parquet to data/bronze/policies_raw.parquet.
"""

from pyspark.sql.functions import current_timestamp

from config import RAW_FILE_11_14, RAW_FILE_14_18, BRONZE_POLICIES
from logger import get_logger
from utils import get_spark, read_csv, write_parquet, log_row_counts


def main():
    log = get_logger("raw_to_bronze")
    spark = get_spark("raw_to_bronze")

    log.info("Starting raw_to_bronze.")

    df_11_14 = read_csv(spark, RAW_FILE_11_14)
    df_14_18 = read_csv(spark, RAW_FILE_14_18)

    log_row_counts(log, "motor_data11-14lats", df_11_14)
    log_row_counts(log, "motor_data14-2018",   df_14_18)

    df = df_11_14.unionByName(df_14_18)
    df = df.withColumn("bronze_processed_at", current_timestamp())
    
    log_row_counts(log, "Bronze (Combined)", df)
    write_parquet(df, BRONZE_POLICIES)
    log.info(f"Bronze written to: {BRONZE_POLICIES}")
    log.info("raw_to_bronze completed successfully.")

    spark.stop()


if __name__ == "__main__":
    main()
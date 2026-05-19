"""
Silver → Gold lifecycle enrichment for the Insurance Policy Lifecycle pipeline.

Adds business logic columns: lifecycle_status, is_active, is_expired,
renewal_candidate, and risk_score. Writes to data/gold/policies_lifecycle.
"""

from pyspark.sql import functions as F

from config import SILVER_POLICIES, GOLD_LIFECYCLE
from logger import get_logger
from utils import get_spark, read_parquet, write_parquet, log_row_counts


def main():
    log = get_logger("silver_to_gold")
    spark = get_spark("silver_to_gold")

    REFERENCE_DATE = F.to_date(F.lit("2018-12-31"))  # last date in the dataset

    log.info("Starting silver_to_gold.")

    df = read_parquet(spark, SILVER_POLICIES)
    log_row_counts(log, "Silver (input)", df)

    # ── 1. Lifecycle status: active, expired, or future ───────────────────────
    df = df.withColumn(
        "lifecycle_status",
        F.when(F.col("insr_begin") > REFERENCE_DATE, "future")
         .when(F.col("insr_end") < REFERENCE_DATE, "expired")
         .otherwise("active")
    )

    # ── 2. Boolean flags: is_active or is_expired ─────────────────────────────────────
    df = df.withColumn("is_active",  F.col("lifecycle_status") == "active") \
           .withColumn("is_expired", F.col("lifecycle_status") == "expired")
    
    # ── 3. Renewal candidates: expired within 90 days of reference date ──
    df = df.withColumn(
        "renewal_candidate",
        (F.col("is_expired") & 
        (F.datediff(REFERENCE_DATE, F.col("insr_end")) <= 90))
    )

    # ── 4. Risk score: based on claim history, insured value, and vehicle age ──
    df = df.withColumn(
        "risk_score",
        (F.col("claim_paid") > 0).cast("int") +
        F.col("insured_value").isNull().cast("int") +
        F.coalesce((F.col("vehicle_age") > 15).cast("int"), F.lit(0))
    )

    log_row_counts(log, "Gold (output)", df)
    write_parquet(df, GOLD_LIFECYCLE)
    log.info(f"Gold written to: {GOLD_LIFECYCLE}")
    log.info("silver_to_gold completed successfully.")

    spark.stop()

if __name__ == "__main__":
    main()
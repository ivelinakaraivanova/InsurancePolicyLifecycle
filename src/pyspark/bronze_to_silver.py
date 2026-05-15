"""
Bronze → Silver cleaning for the Insurance Policy Lifecycle pipeline.

Parses dates, removes invalid/corrupt rows, normalizes values,
fills expected nulls, and derives analytical columns.
"""

from pyspark.sql import functions as F

from config import BRONZE_POLICIES, SILVER_POLICIES
from logger import get_logger
from utils import get_spark, read_parquet, write_parquet, log_row_counts


DATE_FMT = "dd-MMM-yy"


def main():
    log = get_logger("bronze_to_silver")
    spark = get_spark("bronze_to_silver")

    log.info("Starting bronze_to_silver.")

    df = read_parquet(spark, BRONZE_POLICIES)
    log_row_counts(log, "Bronze (input)", df)

    # ── 1. Drop corrupt rows (CSV row-shift: SEX not in {0,1,2}) ──────────────
    df = df.filter(F.col("SEX").isin(0, 1, 2))
    log_row_counts(log, "After corrupt row drop", df)

    # ── 2. Parse date strings → DateType ──────────────────────────────────────
    df = df.withColumn("INSR_BEGIN", F.to_date(F.col("INSR_BEGIN"), DATE_FMT)) \
           .withColumn("INSR_END",   F.to_date(F.col("INSR_END"),   DATE_FMT))

    # ── 3. Drop rows with null or invalid dates ────────────────────────────────
    df = df.filter(F.col("INSR_BEGIN").isNotNull() & F.col("INSR_END").isNotNull())
    df = df.filter(F.col("INSR_END") >= F.col("INSR_BEGIN"))
    log_row_counts(log, "After date cleaning", df)

    # ── 4. Drop rows with invalid PREMIUM (≤ 0 or null) ───────────────────────
    df = df.filter(F.col("PREMIUM").isNotNull() & (F.col("PREMIUM") > 0))
    log_row_counts(log, "After PREMIUM filter", df)

    # ── 5. Replace INSURED_VALUE = 0 with null (not recorded) ─────────────────
    df = df.withColumn(
        "INSURED_VALUE",
        F.when(F.col("INSURED_VALUE") == 0, None).otherwise(F.col("INSURED_VALUE"))
    )

    # ── 6. Fill CLAIM_PAID nulls with 0 (no claim filed) ─────────────────────
    df = df.fillna({"CLAIM_PAID": 0.0})

    # ── 7. Drop exact duplicates ──────────────────────────────────────────────
    df = df.dropDuplicates(["OBJECT_ID", "INSR_BEGIN", "INSR_END"])
    log_row_counts(log, "After deduplication", df)

    # ── 8. Derived columns ────────────────────────────────────────────────────
    df = df.withColumn(
        "policy_duration_days",
        F.datediff(F.col("INSR_END"), F.col("INSR_BEGIN"))
    ).withColumn(
        "vehicle_age",
        F.year(F.col("INSR_BEGIN")) - F.col("PROD_YEAR").cast("int")
    ).withColumn(
        "premium_segment",
        F.when(F.col("PREMIUM") < 756,   "low")
         .when(F.col("PREMIUM") < 9641,  "medium")
         .otherwise("high")
    ).withColumn(
        "value_segment",
        F.when(F.col("INSURED_VALUE").isNull(),        "unknown")
         .when(F.col("INSURED_VALUE") < 730000,        "low")
         .when(F.col("INSURED_VALUE") < 2000000,       "medium")
         .otherwise("high")
    )

    # ── 9. Rename all columns to snake_case ──────────────────────────────────
    df = df.toDF(*[c.strip().lower().replace(' ', '_') for c in df.columns])

    log_row_counts(log, "Silver (output)", df)
    write_parquet(df, SILVER_POLICIES)
    log.info(f"Silver written to: {SILVER_POLICIES}")
    log.info("bronze_to_silver completed successfully.")

    spark.stop()


if __name__ == "__main__":
    main()
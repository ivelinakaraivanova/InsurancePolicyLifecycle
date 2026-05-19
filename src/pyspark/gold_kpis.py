"""
Gold KPI aggregation for the Insurance Policy Lifecycle pipeline.

Reads from the Gold lifecycle table and writes three KPI tables to data/gold/kpi_tables/.
"""

from pyspark.sql import functions as F

from config import GOLD_LIFECYCLE, GOLD_KPI_PORTFOLIO, GOLD_KPI_VEHICLE, GOLD_KPI_PRODUCT
from logger import get_logger
from utils import get_spark, read_parquet, write_parquet


def main():
    log = get_logger("gold_kpis")
    spark = get_spark("gold_kpis")

    log.info("Starting gold_kpis.")

    df = read_parquet(spark, GOLD_LIFECYCLE)
    log.info(f"Gold lifecycle rows: {df.count():,}")

    # ── 1. Portfolio KPIs — single-row overall summary ────────────────────────
    portfolio = df.agg(
        F.count("*").alias("policy_count"),
        F.sum(F.col("is_active").cast("int")).alias("active_count"),
        F.sum(F.col("is_expired").cast("int")).alias("expired_count"),
        F.sum(F.when(F.col("lifecycle_status") == "future", 1).otherwise(0)).alias("future_count"),
        F.sum(F.col("renewal_candidate").cast("int")).alias("renewal_candidate_count"),
        F.round(F.sum("premium"), 2).alias("total_premium"),
        F.round(F.avg("premium"), 2).alias("avg_premium"),
        F.round(F.sum("claim_paid"), 2).alias("total_claim_paid"),
        F.round(F.avg("claim_paid"), 2).alias("avg_claim_paid"),
        F.round(F.sum("claim_paid") / F.sum("premium"), 4).alias("loss_ratio"),
        F.round(F.avg("policy_duration_days"), 1).alias("avg_policy_duration_days"),
        F.round(F.avg("risk_score"), 2).alias("avg_risk_score"),
        F.sum(F.when(F.col("risk_score") >= 2, 1).otherwise(0)).alias("high_risk_count"),
    )
    write_parquet(portfolio, GOLD_KPI_PORTFOLIO)
    log.info(f"Portfolio KPIs written to: {GOLD_KPI_PORTFOLIO}")

    # ── 2. Vehicle KPIs — grouped by vehicle make ─────────────────────────────
    vehicle = df.groupBy("make").agg(
        F.count("*").alias("policy_count"),
        F.sum(F.col("is_active").cast("int")).alias("active_count"),
        F.round(F.avg("vehicle_age"), 1).alias("avg_vehicle_age"),
        F.round(F.sum("premium"), 2).alias("total_premium"),
        F.round(F.avg("premium"), 2).alias("avg_premium"),
        F.round(F.sum("claim_paid"), 2).alias("total_claim_paid"),
        F.round(F.avg("claim_paid"), 2).alias("avg_claim_paid"),
        F.round(F.sum("claim_paid") / F.sum("premium"), 4).alias("loss_ratio"),
        F.round(F.avg("risk_score"), 2).alias("avg_risk_score"),
    ).orderBy(F.col("policy_count").desc())
    write_parquet(vehicle, GOLD_KPI_VEHICLE)
    log.info(f"Vehicle KPIs written to: {GOLD_KPI_VEHICLE}")

    # ── 3. Product KPIs — grouped by insurance type ───────────────────────────
    product = df.groupBy("insr_type").agg(
        F.count("*").alias("policy_count"),
        F.sum(F.col("is_active").cast("int")).alias("active_count"),
        F.sum(F.col("is_expired").cast("int")).alias("expired_count"),
        F.sum(F.col("renewal_candidate").cast("int")).alias("renewal_candidate_count"),
        F.round(F.sum("premium"), 2).alias("total_premium"),
        F.round(F.avg("premium"), 2).alias("avg_premium"),
        F.round(F.sum("claim_paid"), 2).alias("total_claim_paid"),
        F.round(F.avg("claim_paid"), 2).alias("avg_claim_paid"),
        F.round(F.sum("claim_paid") / F.sum("premium"), 4).alias("loss_ratio"),
        F.round(F.avg("policy_duration_days"), 1).alias("avg_policy_duration_days"),
        F.sum(F.when(F.col("premium_segment") == "low",    1).otherwise(0)).alias("premium_seg_low"),
        F.sum(F.when(F.col("premium_segment") == "medium", 1).otherwise(0)).alias("premium_seg_medium"),
        F.sum(F.when(F.col("premium_segment") == "high",   1).otherwise(0)).alias("premium_seg_high"),
    ).orderBy(F.col("policy_count").desc())
    write_parquet(product, GOLD_KPI_PRODUCT)
    log.info(f"Product KPIs written to: {GOLD_KPI_PRODUCT}")

    log.info("gold_kpis completed successfully.")
    spark.stop()


if __name__ == "__main__":
    main()
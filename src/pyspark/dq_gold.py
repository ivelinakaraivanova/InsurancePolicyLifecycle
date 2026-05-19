"""
Gold Data Quality checks for the Insurance Policy Lifecycle pipeline.

Reads the Gold lifecycle Parquet, runs DQ checks, and writes a plain-text report to logs/dq_gold_report.txt.
"""

from pyspark.sql import functions as F

from config import GOLD_LIFECYCLE, DQ_REPORT_GOLD
from logger import get_logger
from utils import get_spark, read_parquet
from dq_utils import (check_nulls, check_duplicates, check_positive,
                        check_allowed_values, check_date_order, write_dq_report)


GOLD_COLUMNS = ["lifecycle_status", "is_active", "is_expired", "renewal_candidate", "risk_score"]

def main():
    log = get_logger("dq_gold")
    spark = get_spark("dq_gold")

    log.info("Starting dq_gold.")
    df = read_parquet(spark, GOLD_LIFECYCLE)
    total = df.count()
    log.info(f"Gold row count: {total:,}")

    findings= []
    findings += check_nulls(df.select(GOLD_COLUMNS), total)
    findings.append(check_allowed_values(df, "lifecycle_status", {"active", "expired", "future"}, total))
    findings.append(check_allowed_values(df, "risk_score", {0, 1, 2, 3}, total))

    write_dq_report(findings, DQ_REPORT_GOLD)
    log.info(f"DQ report written to: {DQ_REPORT_GOLD}")

    fails = [f for f in findings if f["status"] == "FAIL"]
    log.info(f"DQ complete - {len(fails)} FAIL(s) out of {len(findings)} checks.")

    spark.stop()


if __name__ == "__main__":
    main()
    
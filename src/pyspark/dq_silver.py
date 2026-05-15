"""
Silver Data Quality checks for the Insurance Policy Lifecycle pipeline.

Reads the Silver Parquet, runs DQ checks, and writes a plain-text report to logs/dq_silver_report.txt.
"""

from config import SILVER_POLICIES, DQ_REPORT_SILVER
from logger import get_logger
from utils import get_spark, read_parquet
from dq_utils import (check_nulls, check_duplicates, check_positive,
                      check_allowed_values, check_date_order, write_dq_report)


def main():
    log = get_logger("dq_silver")
    spark = get_spark("dq_silver")

    log.info("Starting dq_silver.")

    df = read_parquet(spark, SILVER_POLICIES)
    total = df.count()
    log.info(f"Silver row count: {total:,}")

    findings = []
    findings += check_nulls(df, total)
    findings.append(check_duplicates(df, ["object_id", "insr_begin", "insr_end"], total))
    findings.append(check_positive(df, "premium", total))
    findings.append(check_allowed_values(df, "sex", {0, 1, 2}, total))
    findings.append(check_date_order(df, "insr_begin", "insr_end", None, total))
    findings.append(check_allowed_values(df, "premium_segment", {"low", "medium", "high"}, total))
    findings.append(check_allowed_values(df, "value_segment", {"low", "medium", "high", "unknown"}, total))

    write_dq_report(findings, DQ_REPORT_SILVER)
    log.info(f"DQ report written to: {DQ_REPORT_SILVER}")

    fails = [f for f in findings if f["status"] == "FAIL"]
    log.info(f"DQ complete — {len(fails)} FAIL(s) out of {len(findings)} checks.")

    spark.stop()


if __name__ == "__main__":
    main()
"""
Bronze Data Quality checks for the Insurance Policy Lifecycle pipeline.

Reads the Bronze Parquet, runs DQ checks, and writes a plain-text report to logs/dq_bronze_report.txt.
"""

from config import BRONZE_POLICIES, DQ_REPORT_BRONZE
from logger import get_logger
from utils import get_spark, read_parquet
from dq_utils import check_nulls, check_duplicates, check_positive, check_allowed_values, check_date_parseable, check_date_order, write_dq_report


DATE_FMT = "dd-MMM-yy"


def main():
    log = get_logger("dq_bronze")
    spark = get_spark("dq_bronze")

    log.info("Starting dq_bronze.")

    df = read_parquet(spark, BRONZE_POLICIES)
    total = df.count()
    log.info(f"Bronze row count: {total:,}")

    findings = []
    findings += check_nulls(df, total)
    findings.append(check_duplicates(df, ["OBJECT_ID", "INSR_BEGIN", "INSR_END"], total))
    findings.append(check_positive(df, "PREMIUM", total))
    findings.append(check_positive(df, "INSURED_VALUE", total))
    findings.append(check_allowed_values(df, "SEX", {0, 1, 2}, total))
    findings.append(check_date_parseable(df, "INSR_BEGIN", DATE_FMT, total))
    findings.append(check_date_parseable(df, "INSR_END", DATE_FMT, total))
    findings.append(check_date_order(df, "INSR_BEGIN", "INSR_END", DATE_FMT, total))
    
    write_dq_report(findings, DQ_REPORT_BRONZE)
    log.info(f"DQ report written to: {DQ_REPORT_BRONZE}")

    fails = [f for f in findings if f["status"] == "FAIL"]
    log.info(f"DQ complete — {len(fails)} FAIL(s) out of {len(findings)} checks.")

    spark.stop()


if __name__ == "__main__":
    main()
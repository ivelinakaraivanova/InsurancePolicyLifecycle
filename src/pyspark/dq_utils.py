"""
Shared Data Quality check functions for the Insurance Policy Lifecycle pipeline.

Used by dq_bronze.py, dq_silver.py, and dq_gold.py to run standard checks
and write structured .txt reports. Each check returns a dict with a consistent
schema so write_dq_report() can format them uniformly.
"""

import os
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from config import LOGS_DIR


def pct(n: int, total: int) -> float:
    """
    Calculate percentage of n relative to total, safely handling zero total.
    """
    return round(100 * n / total, 2) if total > 0 else 0.0


def check_nulls(df: DataFrame, total: int) -> list:
    """
    Check for null values in every column of the DataFrame.
    """
    row = df.select([
        F.count(F.when(F.col(c).isNull(), c)).alias(c)
        for c in df.columns
    ]).collect()[0]
    return [
        {
            "check": "completeness",
            "column": c,
            "issue": "null values",
            "row_count": int(row[c]),
            "pct": pct(int(row[c]), total),
            "status": "FAIL" if int(row[c]) > 0 else "PASS",
        }
        for c in df.columns
    ]


def check_duplicates(df: DataFrame, keys: list, total: int) -> dict:
    """
    Check for duplicate combinations of the given key columns.
    """
    n = df.groupBy(keys).count().filter(F.col("count") > 1).count()
    return {
        "check": "uniqueness",
        "column": " + ".join(keys),
        "issue": "duplicate keys",
        "row_count": n,
        "pct": pct(n, total),
        "status": "FAIL" if n > 0 else "PASS",
    }


def check_positive(df: DataFrame, col_name: str, total: int) -> dict:
    """
    Check that a numeric column contains only positive (> 0) values.
    """
    n = df.filter(F.col(col_name) <= 0).count()
    return {
        "check": "validity",
        "column": col_name,
        "issue": "zero or negative value",
        "row_count": n,
        "pct": pct(n, total),
        "status": "FAIL" if n > 0 else "PASS",
    }


def check_allowed_values(df: DataFrame, col_name: str, allowed: set, total: int) -> dict:
    """Check that a column contains only values from the allowed set."""
    n = df.filter(~F.col(col_name).isin(list(allowed))).count()
    return {
        "check": "validity",
        "column": col_name,
        "issue": f"value not in {sorted(allowed)}",
        "row_count": n,
        "pct": pct(n, total),
        "status": "FAIL" if n > 0 else "PASS",
    }


def check_date_parseable(df: DataFrame, col_name: str, fmt: str, total: int) -> dict:
    """Check that a string column can be parsed as a date with the given format."""
    n = df.filter(
        F.col(col_name).isNotNull() & F.to_date(F.col(col_name), fmt).isNull()
    ).count()
    return {
        "check": "validity",
        "column": col_name,
        "issue": f"unparseable date (expected {fmt})",
        "row_count": n,
        "pct": pct(n, total),
        "status": "FAIL" if n > 0 else "PASS",
    }


def check_date_order(df: DataFrame, start_col: str, end_col: str, fmt: str, total: int) -> dict:
    """Check that end date is not before start date."""
    n = df.filter(
        F.to_date(F.col(end_col), fmt) < F.to_date(F.col(start_col), fmt)
    ).count()
    return {
        "check": "consistency",
        "column": f"{end_col} vs {start_col}",
        "issue": "end date before start date",
        "row_count": n,
        "pct": pct(n, total),
        "status": "FAIL" if n > 0 else "PASS",
    }


def write_dq_report(findings: list, report_path: str) -> None:
    """
    Write all DQ findings to a formatted plain-text report file.
    """
    os.makedirs(LOGS_DIR, exist_ok=True)
    with open(report_path, "w") as f:
        header = f"{'CHECK':<20} {'COLUMN':<35} {'ISSUE':<25} {'ROWS':>8} {'%':>7}  STATUS\n"
        f.write(header)
        f.write("-" * len(header) + "\n")
        for r in findings:
            f.write(
                f"{r['check']:<20} {r['column']:<35} {r['issue']:<25} "
                f"{r['row_count']:>8,} {r['pct']:>7.2f}  {r['status']}\n"
            )
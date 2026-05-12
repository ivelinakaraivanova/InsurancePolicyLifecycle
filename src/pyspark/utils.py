"""
Shared Spark and I/O utilities for the Insurance Policy Lifecycle pipeline.

Provides:
- SparkSession factory (with optional PostgreSQL JDBC support)
- CSV / Parquet / PostgreSQL read and write helpers
- Row count logging helper
"""

import logging
from pyspark.sql import SparkSession, DataFrame


def get_spark(app_name: str, with_postgres: bool = False) -> SparkSession:
    """
    Create and return a SparkSession with WARN-level logging.
    """
    builder = SparkSession.builder \
        .appName(app_name) \
        .master("local[*]")
    if with_postgres:
        builder = builder.config(
            "spark.jars.packages",
            "org.postgresql:postgresql:42.7.3"
        )
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def read_csv(spark: SparkSession, path: str, options: dict = None) -> DataFrame:
    """
    Read a CSV file into a Spark DataFrame.

    Defaults to header=True and inferSchema=True. 
    Any extra Spark reader options can be passed via the options dict.
    """
    reader = spark.read \
        .option("header", True) \
        .option("inferSchema", True)
    if options:
        for k, v in options.items():
            reader = reader.option(k, v)
    return reader.csv(path)


def read_parquet(spark: SparkSession, path: str) -> DataFrame:
    """
    Read a Parquet dataset into a Spark DataFrame.
    """
    return spark.read.parquet(path)


def write_parquet(df: DataFrame, path: str, mode: str = "overwrite") -> None:
    """
    Write a DataFrame to Parquet format.
    """
    df.write.mode(mode).parquet(path)


def write_postgres(df: DataFrame, table: str, jdbc_url: str,
                   properties: dict, mode: str = "overwrite") -> None:
    """
    Write a DataFrame to a PostgreSQL table via JDBC.
    """
    df.write.jdbc(url=jdbc_url, table=table, mode=mode, properties=properties)


def log_row_counts(log: logging.Logger, label: str, df: DataFrame) -> int:
    """
    Count rows in a DataFrame, log the result, and return the count.
    """
    n = df.count()
    log.info(f"{label:<35} : {n:,} rows")
    return n
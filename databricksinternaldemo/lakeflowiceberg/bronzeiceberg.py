import dlt
from pyspark.sql.functions import col, to_timestamp, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

# ===========================
# Iceberg Configuration- Set below configurations in the cluster
# ===========================
#spark.conf.set("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkCatalog")
#spark.conf.set("spark.sql.catalog.spark_catalog.type", "hive")
#spark.conf.set("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")

# ===========================
# Schema Definitions
# ===========================
meter_reading_schema = StructType([
    StructField("customer_id", StringType(), True),
    StructField("kwh_reading", DoubleType(), True),
    StructField("metername", StringType(), True),
    StructField("raw_source", StringType(), True),
    StructField("timestamp", StringType(), True)
])

plans_schema = StructType([
    StructField("plan_id", StringType(), False),
    StructField("plan_name", StringType(), False),
    StructField("rate_per_kwh", DoubleType(), False),
    StructField("effective_start_date", StringType(), False),
    StructField("effective_end_date", StringType(), False)
])

customer_schema = StructType([
    StructField("customer_id", StringType(), False),
    StructField("first_name", StringType(), False),
    StructField("last_name", StringType(), False),
    StructField("email", StringType(), False),
    StructField("address", StringType(), False),
    StructField("city", StringType(), False),
    StructField("state", StringType(), False),
    StructField("zip_code", StringType(), False),
    StructField("plan_id", StringType(), False)
])

# ===========================
# Create Schema if not exists
# ===========================
#spark.sql("CREATE SCHEMA IF NOT EXISTS `na-dbxtraining`.biju_bronze")

# ===========================
# 1. Bronze Meter Readings
# ===========================

# Create Iceberg table

# Start streaming
raw_data_path = "/Volumes/na-dbxtraining/biju_raw/biju_vol/powerdata/raw_data/"
checkpoint_path_meter = "/Volumes/na-dbxtraining/biju_raw/biju_vol/powerdata/checkpoints/bronze_meter_readingsiceberg"

meter_readings_stream = (
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "json")
    .schema(meter_reading_schema)
    .option("cloudFiles.schemaLocation", '/Volumes/na-dbxtraining/biju_raw/biju_vol/powerdata/schemaiceberg')
    .load(raw_data_path)
    .select(
        col("customer_id"),
        col("kwh_reading"),
        col("metername"),
        col("raw_source"),
        to_timestamp(col("timestamp")).alias("reading_timestamp"),
        current_timestamp().alias("ingestion_timestamp")
    )
    .writeStream
    .format("iceberg")
    .outputMode("append")
    .option("checkpointLocation", checkpoint_path_meter)
    .option("fanout-enabled", "true")
    .trigger(processingTime="10 seconds")
    .toTable("`na-dbxtraining`.biju_bronze.bronze_meter_readingsiceberg")
)


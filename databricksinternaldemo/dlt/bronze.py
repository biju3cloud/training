
import dlt

from pyspark.sql.functions import col, to_timestamp, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

# Load Meter Reading Data

# Define the schema for the incoming meter reading data
# This matches the columns and their types from your example data.
meter_reading_schema = StructType([
    StructField("customer_id", StringType(), True),
    StructField("kwh_reading", DoubleType(), True),
    StructField("metername", StringType(), True), # Changed from 'metername' to 'metername' as per your data
    StructField("raw_source", StringType(), True),
    StructField("timestamp", StringType(), True) # Read as string, then convert to timestamp
])
# Define the schema for the plans CSV data
plans_schema = StructType([
    StructField("plan_id", StringType(), False),
    StructField("plan_name", StringType(), False),
    StructField("rate_per_kwh", DoubleType(), False),
    StructField("effective_start_date", StringType(), False), # Read as String for now
    StructField("effective_end_date", StringType(), False)   # Read as String for now
])
    # Define the schema for the incoming CSV data
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
@dlt.table(
    name="`na-dbxtraining`.biju_bronze.bronze_meter_readings",
    comment="Raw, unprocessed power meter readings from the simulator.",
    table_properties={"quality": "bronze"}
)
def bronze_meter_readings():
    raw_data_path = "/Volumes/na-dbxtraining/biju_raw/biju_vol/powerdata/raw_data/" 
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .schema(meter_reading_schema)
        .option("cloudFiles.schemaLocation", '/Volumes/na-dbxtraining/biju_raw/biju_vol/powerdata/schema')
        .load(raw_data_path)
        .select(
            col("customer_id"),
            col("kwh_reading"),
            col("metername"),
            col("raw_source"),
            to_timestamp(col("timestamp")).alias("reading_timestamp"),
            current_timestamp().alias("ingestion_timestamp")
        )
    )

@dlt.table(
    name="`na-dbxtraining`.biju_bronze.bronze_plans",
    comment="Raw plans data ingested from a CSV file.",
    table_properties={"quality": "bronze"}
)
def bronze_plans():
    input_path = "/Volumes/na-dbxtraining/biju_raw/biju_vol/powerdata/raw/csv/plans/"
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .schema(plans_schema)
        .option("cloudFiles.schemaLocation", "/Volumes/na-dbxtraining/biju_raw/biju_vol/powerdata/schema/bronze_plans")
        .load(input_path)
        .select(
            col("plan_id"),
            col("plan_name"),
            col("rate_per_kwh"),
            col("effective_start_date"),
            col("effective_end_date"),
            current_timestamp().alias("ingestion_timestamp")
        )
    )

@dlt.table(
    name="`na-dbxtraining`.biju_bronze.bronze_customers",
    comment="Raw customer data ingested from a CSV file in a Unity Catalog Volume.",
    table_properties={"quality": "bronze"}
)
def bronze_customers():
    input_path = "/Volumes/na-dbxtraining/biju_raw/biju_vol/powerdata/raw/csv/customers/"
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .schema(customer_schema)
        .option("cloudFiles.schemaLocation", "/Volumes/na-dbxtraining/biju_raw/biju_vol/powerdata/schema/")
        .load(input_path)
        .select(
            col("customer_id"),
            col("first_name"),
            col("last_name"),
            col("email"),
            col("address"),
            col("city"),
            col("state"),
            col("zip_code"),
            col("plan_id")
        )
    )
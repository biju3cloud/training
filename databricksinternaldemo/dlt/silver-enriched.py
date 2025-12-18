import dlt
from pyspark.sql.functions import col, from_json, to_timestamp, current_timestamp, lit, sum, count, avg, date_trunc, to_date, coalesce
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, IntegerType, DateType


@dlt.table(
    name="`na-dbxtraining`.biju_silver.silver_enriched_meter_readings",
    comment="Meter readings enriched with customer and plan details.",
    table_properties={"quality": "silver"}
)
@dlt.expect_or_drop("valid_kwh_reading", "kwh_reading > 0")
@dlt.expect_or_drop("valid_customer_join", "customer_id IS NOT NULL") # Ensure customer_id exists after join
def silver_enriched_meter_readings():
    meter_readings_df = dlt.read_stream("`na-dbxtraining`.biju_bronze.bronze_meter_readings")
    customers_df = dlt.read("`na-dbxtraining`.biju_silver.silver_customers") # Read as batch from Silver Customers
    plans_df = dlt.read("`na-dbxtraining`.biju_silver.silver_plans")       # Read as batch from Silver Plans

    # Join meter readings with customer data
    enriched_readings = meter_readings_df.alias("mr").join(
        customers_df.alias("cust"),
        col("mr.customer_id") == col("cust.customer_id"),
        "inner" # Use inner join to only keep readings with matching customers
    ).select(
        col("mr.customer_id"),
        col("cust.first_name"),
        col("cust.last_name"),
        col("cust.city"),
        col("cust.state"),
        col("mr.kwh_reading"),
        col("mr.metername"),
        col("mr.raw_source"),
        col("mr.reading_timestamp"),
        col("cust.plan_id").alias("customer_plan_id") # Bring in the plan_id from silver_customers
    )
        # Join the already enriched readings with plan details
    final_enriched_readings = enriched_readings.alias("er").join(
        plans_df.alias("p"),
        col("er.customer_plan_id") == col("p.plan_id"),
        "left" # Use left join to keep all enriched readings, even if plan info is missing
    ).select(
        col("er.customer_id"),
        col("er.first_name"),
        col("er.last_name"),
        col("er.city"),
        col("er.state"),
        col("er.kwh_reading"),
        col("er.metername"),
        col("er.raw_source"),
        col("er.reading_timestamp"),
        col("p.plan_id"),
        col("p.plan_name"),
        col("p.rate_per_kwh"),
        col("p.effective_start_date"),
        col("p.effective_end_date"),
        current_timestamp().alias("processing_timestamp") # Timestamp for Silver layer processing
    )
    return final_enriched_readings
import dlt
from pyspark.sql.functions import col, round,from_json, to_timestamp, current_timestamp, lit, sum, count, avg, date_trunc, to_date, coalesce
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, IntegerType, DateType

# --- Gold Layer: Business-Ready Aggregations ---


@dlt.table(
    name="`na-dbxtraining`.biju_gold.gold_daily_customer_kwh_summary",
    comment="Daily total kWh consumption per customer, enriched with plan details.",
    table_properties={"quality": "gold"}
)
def gold_daily_customer_kwh_summary():
    return (
        dlt.read_stream("`na-dbxtraining`.biju_silver.silver_enriched_meter_readings")
            .groupBy(
                col("customer_id"),
                col("first_name"),
                col("last_name"),
                col("city"),
                col("state"),
                col("plan_id"),
                col("plan_name"),
                col("rate_per_kwh"),
                to_date(col("reading_timestamp")).alias("reading_date") # Aggregate by date
            )
            .agg(
                round(sum("kwh_reading"),2).alias("total_kwh_daily"),
                count("kwh_reading").alias("num_readings_daily"),
                round(avg("kwh_reading"),2).alias("avg_kwh_per_reading_daily")
            )
            .withColumn(
                "calculated_cost_daily", 
                round(col("total_kwh_daily") * col("rate_per_kwh"), 2) # Apply rounding here
            )
            .orderBy("reading_date", "customer_id")
    )


def gold_daily_plan_kwh_summary():
    return (
        dlt.read_stream("`na-dbxtraining`.biju_silver.silver_enriched_meter_readings")
            .groupBy(
                col("plan_id"),
                col("plan_name"),
                col("rate_per_kwh"),
                to_date(col("reading_timestamp")).alias("reading_date")
            )
            .agg(
                round(sum("kwh_reading"), 2).alias("total_kwh_daily_plan"),
                count("kwh_reading").alias("num_readings_daily_plan"),
                round(avg("kwh_reading"),2).alias("avg_kwh_per_reading_daily_plan")
            )
            .withColumn(
                "calculated_cost_daily_plan", 
                round(col("total_kwh_daily_plan") * col("rate_per_kwh"), 2)
            )
            .orderBy("reading_date", "plan_id")
    )
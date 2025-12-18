import dlt
from pyspark.sql.functions import col, from_json, to_timestamp, current_timestamp, lit, sum, count, avg, date_trunc, to_date, coalesce
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, IntegerType, DateType



# --- Silver Layer: Cleansed and Conformed Data ---

@dlt.table(
    name="`na-dbxtraining`.biju_silver.silver_customers",
    comment="Cleaned customer data with a dummy plan_id for joining.",
    table_properties={"quality": "silver"}
)
@dlt.expect_or_drop("valid_customer_id", "customer_id IS NOT NULL")
@dlt.expect_or_drop("valid_email", "email LIKE '%@%.%'")
def silver_customers():
    # Read from the bronze_customers table
    customers_df = dlt.read_stream("`na-dbxtraining`.biju_bronze.bronze_customers")
    
    # Add a dummy plan_id for demonstration purposes.
    # In a real scenario, this would come from a customer-plan enrollment table.
    # For now, we'll assign plans based on a simple modulo operation for demo.
    return customers_df.select(
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

@dlt.table(
    name="`na-dbxtraining`.biju_silver.silver_plans",
    comment="Cleaned and type-converted plans data.",
    table_properties={"quality": "silver"}
)
@dlt.expect_or_drop("valid_plan_id", "plan_id IS NOT NULL")
@dlt.expect_or_drop("valid_rate", "rate_per_kwh > 0")
def silver_plans():
    # Read from the bronze_plans table
    plans_df = dlt.read_stream("`na-dbxtraining`.biju_bronze.bronze_plans")
    
    return plans_df.select(
        col("plan_id"),
        col("plan_name"),
        col("rate_per_kwh"),
        # Convert date strings to DateType, handling potential malformed data
        to_date(col("effective_start_date"), "M/d/yyyy").alias("effective_start_date"),
        to_date(col("effective_end_date"), "M/d/yyyy").alias("effective_end_date"),
        col("ingestion_timestamp")
    )
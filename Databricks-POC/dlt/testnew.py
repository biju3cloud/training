import dlt
from pyspark.sql.functions import col, from_json, to_timestamp, to_date, current_timestamp, expr, count, countDistinct, sum, when
from pyspark.sql.types import *

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Event Hub Configuration
eh_namespace = "evhns-natraining.servicebus.windows.net"
eh_name = "evh-natraining-bijunew"
keyvault_scope = "dbx-ss-kv-natraining-2"
secret_name = "evh-natraining-read-write"
shared_access_key_name = "SharedAccessKeyToSendAndListen"

# Unity Catalog Configuration
catalog = "na-dbxtraining"
schema_bronze = "biju_bronze"
schema_silver = "biju_silver"
schema_gold = "biju_gold"

# Table Names (Full Qualified Names)
bronze_raw_events_table = f"{catalog}.{schema_bronze}.raw_events"

print("="*70)
print("CONFIGURATION")
print("="*70)
print(f"\nEvent Hub:")
print(f"  Namespace: {eh_namespace}")
print(f"  Event Hub: {eh_name}")
print(f"\nUnity Catalog:")
print(f"  Catalog: {catalog}")
print(f"  Bronze Schema: {schema_bronze}")
print(f"  Bronze Table: {bronze_raw_events_table}")
print("="*70)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Get Secret from Key Vault

# COMMAND ----------

try:
    secret_value = dbutils.secrets.get(scope=keyvault_scope, key=secret_name)
    print("✓ Successfully retrieved secret from Key Vault")
    print(f"  - Secret name: {secret_name}")
    print(f"  - Scope: {keyvault_scope}")
    print(f"  - Secret length: {len(secret_value)} characters")
except Exception as e:
    print(f"✗ Error retrieving secret: {str(e)}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Build Event Hub Connection String

# COMMAND ----------

# Full connection string for Kafka-based Event Hub connection
connection_string = (
    f"Endpoint=sb://{eh_namespace}/;"
    f"SharedAccessKeyName={shared_access_key_name};"
    f"SharedAccessKey={secret_value}"
)

print("✓ Connection string built successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Kafka Consumer Configuration

# COMMAND ----------

KAFKA_OPTIONS = {
    "kafka.bootstrap.servers": f"{eh_namespace}:9093",
    "subscribe": eh_name,
    "kafka.sasl.mechanism": "PLAIN",
    "kafka.security.protocol": "SASL_SSL",
    "kafka.sasl.jaas.config": f'kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule required username="$ConnectionString" password="{connection_string}";',
    "kafka.request.timeout.ms": "60000",
    "kafka.session.timeout.ms": "30000",
    "maxOffsetsPerTrigger": "100000",
    "failOnDataLoss": "false",
    "startingOffsets": "earliest"
}

print("✓ Kafka options configured")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define E-Commerce Order Payload Schema

# COMMAND ----------

# E-COMMERCE ORDER PAYLOAD SCHEMA
payload_schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("customer_name", StringType(), True),
    StructField("location", StringType(), True),
    StructField("order_status", StringType(), True),
    StructField("payment_method", StringType(), True),
    StructField("quantity", IntegerType(), True),
    StructField("discount_pct", IntegerType(), True),
    StructField("total_amount", IntegerType(), True),
    StructField("order_timestamp", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("product_name", StringType(), True),
    StructField("category", StringType(), True),
    StructField("brand", StringType(), True),
    StructField("base_price", IntegerType(), True),
    StructField("unit_price", IntegerType(), True)
])

print("✓ E-Commerce order payload schema defined")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧪 TEST: Read Sample Data from Event Hub

# COMMAND ----------

print("="*70)
print("TESTING EVENT HUB CONNECTION")
print("="*70)

try:
    # Read a micro-batch from Event Hub
    test_df = (spark.read
        .format("kafka")
        .options(**KAFKA_OPTIONS)
        .option("startingOffsets", "latest")
        .option("maxOffsetsPerTrigger", "10")
        .load()
    )
    
    print(f"\n✓ Successfully connected to Event Hub!")
    print(f"  Total records fetched: {test_df.count()}")
    
    # Show raw Kafka message structure
    print("\n" + "="*70)
    print("RAW KAFKA MESSAGE STRUCTURE")
    print("="*70)
    test_df.printSchema()
    
    # Parse and display the JSON payload
    print("\n" + "="*70)
    print("PARSED ORDER DATA (Sample 5 records)")
    print("="*70)
    
    parsed_test_df = (test_df
        .withColumn("value_string", col("value").cast("string"))
        .withColumn("parsed_data", from_json(col("value_string"), payload_schema))
        .select("parsed_data.*", "timestamp", "partition", "offset")
    )
    
    display(parsed_test_df)
    
    # Show sample JSON structure
    print("\n" + "="*70)
    print("SAMPLE JSON PAYLOAD")
    print("="*70)
    sample_json = test_df.select(col("value").cast("string").alias("json_payload")).first()
    if sample_json:
        print(sample_json.json_payload)
    
    print("\n✓ Event Hub test completed successfully!")
    
except Exception as e:
    print(f"\n✗ Error testing Event Hub connection: {str(e)}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧪 TEST: Streaming Preview (Optional - Run this cell to see live data)

# COMMAND ----------

# Uncomment and run this cell to see streaming data in real-time
"""
streaming_test_df = (spark.readStream
    .format("kafka")
    .options(**KAFKA_OPTIONS)
    .load()
    .withColumn("value_string", col("value").cast("string"))
    .withColumn("parsed_data", from_json(col("value_string"), payload_schema))
    .select("parsed_data.*", "timestamp")
)

# Display streaming data (this will keep running until you stop it)
display(streaming_test_df)
"""

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parse Function

# COMMAND ----------

def parse_order_events(df):
    """
    Parse raw Kafka records containing e-commerce orders and add ETL audit columns
    """
    return (df
        .withColumn("records", col("value").cast("string"))
        .withColumn("parsed_records", from_json(col("records"), payload_schema))
        .withColumn("order_timestamp_parsed", 
                    to_timestamp(col("parsed_records.order_timestamp")))
        .withColumn("eh_enqueued_timestamp", col("timestamp"))
        .withColumn("eh_enqueued_date", to_date(col("timestamp")))
        .withColumn("etl_processed_timestamp", current_timestamp())
        .withColumn("etl_rec_uuid", expr("uuid()"))
        .drop("records", "value", "key")
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Table - Raw Events DLT Pipeline

# COMMAND ----------

@dlt.table(
    name="raw_events",
    comment="Raw E-Commerce Order Events from Event Hub",
    table_properties={
        "quality": "bronze",
        "pipelines.reset.allowed": "false",
        "delta.enableChangeDataFeed": "true"
    },
    partition_cols=["eh_enqueued_date"]
)
@dlt.expect("valid_topic", "topic IS NOT NULL")
@dlt.expect("valid_records", "parsed_records IS NOT NULL")
@dlt.expect_or_drop("valid_order_id", "parsed_records.order_id IS NOT NULL")
def raw_events():
    """
    Bronze layer: Raw e-commerce order events from Event Hub
    Reads streaming data from Event Hub via Kafka protocol
    """
    return (
        spark.readStream
            .format("kafka")
            .options(**KAFKA_OPTIONS)
            .load()
            .transform(parse_order_events)
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Table - Flattened Order Events

# COMMAND ----------

@dlt.table(
    name="orders_silver",
    comment="Parsed and flattened e-commerce order events",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true"
    }
)
@dlt.expect_or_drop("valid_order_id", "order_id IS NOT NULL")
@dlt.expect_or_drop("valid_customer_id", "customer_id IS NOT NULL")
@dlt.expect_or_drop("valid_order_timestamp", "order_timestamp IS NOT NULL")
@dlt.expect_or_drop("valid_total_amount", "total_amount > 0")
def orders_silver():
    """
    Silver layer: Flattened and cleaned e-commerce order events
    """
    df = dlt.read_stream("raw_events")
    
    return df.select(
        # Order Information
        col("parsed_records.order_id").alias("order_id"),
        col("order_timestamp_parsed").alias("order_timestamp"),
        col("parsed_records.order_status").alias("order_status"),
        
        # Customer Information
        col("parsed_records.customer_id").alias("customer_id"),
        col("parsed_records.customer_name").alias("customer_name"),
        col("parsed_records.location").alias("location"),
        
        # Product Information
        col("parsed_records.product_id").alias("product_id"),
        col("parsed_records.product_name").alias("product_name"),
        col("parsed_records.category").alias("category"),
        col("parsed_records.brand").alias("brand"),
        
        # Financial Information
        col("parsed_records.quantity").alias("quantity"),
        col("parsed_records.base_price").alias("base_price"),
        col("parsed_records.unit_price").alias("unit_price"),
        col("parsed_records.discount_pct").alias("discount_pct"),
        col("parsed_records.total_amount").alias("total_amount"),
        col("parsed_records.payment_method").alias("payment_method"),
        
        # ETL Metadata
        col("eh_enqueued_timestamp"),
        col("eh_enqueued_date"),
        col("etl_processed_timestamp"),
        col("etl_rec_uuid"),
        col("topic"),
        col("partition"),
        col("offset")
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Check View

# COMMAND ----------

@dlt.view(
    name="raw_events_quality_metrics",
    comment="Data quality metrics for raw events"
)
def raw_events_quality_metrics():
    """
    View to monitor data quality metrics
    """
    return (
        dlt.read_stream("raw_events")
            .groupBy("eh_enqueued_date")
            .agg(
                count("*").alias("total_records"),
                countDistinct(col("parsed_records.order_id")).alias("unique_orders"),
                countDistinct(col("parsed_records.customer_id")).alias("unique_customers"),
                sum(when(col("parsed_records.order_id").isNull(), 1).otherwise(0)).alias("null_order_ids"),
                sum(when(col("parsed_records.total_amount") <= 0, 1).otherwise(0)).alias("invalid_amounts")
            )
    )

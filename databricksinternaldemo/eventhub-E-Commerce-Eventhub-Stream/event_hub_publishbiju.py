# Databricks notebook source
# MAGIC %pip install azure-eventhub
# MAGIC

# COMMAND ----------

# DBTITLE 1,Add/Define Widgets
# Option A - define the eventhub name
dbutils.widgets.text("eventhub_name", "evh-natraining-biju")
EVENTHUB_NAME = dbutils.widgets.get("eventhub_name")

# define the access key and pass the eventhub name to the connection string var
secret_value = dbutils.secrets.get(
    scope="dbx-ss-kv-natraining-2", key="evh-natraining-read-write"
)
send_conn_str = (
    "Endpoint=sb://evhns-natraining.servicebus.windows.net/;"
    "SharedAccessKeyName=SharedAccessKeyToSendAndListen;"
    f"SharedAccessKey={secret_value};"
    f"EntityPath={EVENTHUB_NAME}"
)

# define the test message via widget and connection string var
dbutils.widgets.text(
    "test_message", "Hello from John Rice on Databricks!",
)
EVENTHUB_CONN_STR = send_conn_str

TEST_MESSAGE = dbutils.widgets.get("test_message")

# fail if not exists
if not EVENTHUB_CONN_STR or not EVENTHUB_NAME:
    raise ValueError(
        "Please provide both 'eventhub_connection_string' and 'eventhub_name' via widgets."
    )

# explicitly inform user of param load
print("Parameters loaded. Ready to send a test message.")



# -------------------------------------------------------------------
# Option B (prod-style): use Databricks secrets instead of widgets
#
#
# EVENTHUB_CONN_STR = dbutils.secrets.get("azure-kv-scope", "eventhub-connstr")
# EVENTHUB_NAME = "my-eventhub"
# TEST_MESSAGE = "Hello from Databricks via secret!"
# -------------------------------------------------------------------

# COMMAND ----------

# DBTITLE 1,Send Event
from azure.eventhub import EventHubProducerClient, EventData
import json
from datetime import datetime, timezone


def send_test_event(message: str) -> None:
    """Send a single test event and raise a clear error if anything fails."""
    producer = EventHubProducerClient.from_connection_string(
        conn_str=EVENTHUB_CONN_STR,
        eventhub_name=EVENTHUB_NAME,
    )

    payload = {
        "message": message,
        "source": "databricks-notebook-smoketest",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
    }

    body = json.dumps(payload)

    with producer:
        batch = producer.create_batch()
        batch.add(EventData(body))
        producer.send_batch(batch)

    print(f"✅ Sent test event: {body}")


# Example usage for the course:
send_test_event(TEST_MESSAGE)

# COMMAND ----------

# MAGIC %md
# MAGIC # Let's read from the EventHub using Spark Streaming!

# COMMAND ----------

EVENTHUB_NAME = dbutils.widgets.get("eventhub_name")

EVENTHUB_CONN_STR = (
    "Endpoint=sb://evhns-natraining.servicebus.windows.net/;"
    "SharedAccessKeyName=SharedAccessKeyToSendAndListen;"
    f"SharedAccessKey={secret_value};"
    f"EntityPath={EVENTHUB_NAME}"
).strip().replace("\n", "").replace("\r", "")

encrypted_conn_str = spark._jvm.org.apache.spark.eventhubs.EventHubsUtils.encrypt(EVENTHUB_CONN_STR)

event_hubs_conf = {
    "eventhubs.connectionString": encrypted_conn_str,
    "eventhubs.consumerGroup": "$Default",
    "eventhubs.startingPosition": """{
      "offset":"-1",
      "seqNo":-1,
      "enqueuedTime":"1970-01-01T00:00:00.000Z",
      "isInclusive":false
    }"""
}

print("Event Hub read configuration ready:", EVENTHUB_NAME)


# COMMAND ----------

# Databricks notebook cell: 06_read_stream

raw_stream_df = (
    spark.readStream
         .format("eventhubs")
         .options(**event_hubs_conf)
         .load()
)

display(raw_stream_df)


# COMMAND ----------

# Databricks notebook cell: 07_parse_body

from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType

schema = StructType([
    StructField("message", StringType()),
    StructField("source", StringType()),
    StructField("timestamp_utc", StringType()),
])

parsed_df = (
    raw_stream_df
        .selectExpr("CAST(body AS STRING) AS body_str")
        .select(from_json(col("body_str"), schema).alias("data"))
        .select("data.*")
)

display(parsed_df)


# COMMAND ----------

# Databricks notebook cell: 08_console_sink

query = (
    parsed_df
        .writeStream
        .format("console")
        .outputMode("append")
        .start()
)

query.awaitTermination()

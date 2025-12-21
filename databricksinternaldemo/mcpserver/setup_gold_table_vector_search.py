"""
Setup Vector Search Index and MCP Server for gold_daily_customer_kwh_summary table
Run this in a Databricks notebook
"""

# Step 1: Verify table exists and check structure
print("=" * 80)
print("Step 1: Verifying table structure")
print("=" * 80)

# Run in SQL cell first to check table
sql_query = """
DESCRIBE TABLE EXTENDED `na-dbxtraining`.biju_gold.gold_daily_customer_kwh_summary
"""

print("Run this SQL to check table structure:")
print(sql_query)
print("\nOr check a few rows:")
print("SELECT * FROM `na-dbxtraining`.biju_gold.gold_daily_customer_kwh_summary LIMIT 5")

# Step 2: Install required packages
print("\n" + "=" * 80)
print("Step 2: Install Vector Search package")
print("=" * 80)

install_code = """
%pip install databricks-vectorsearch
dbutils.library.restartPython()
"""

print("Run this in a cell:")
print(install_code)

# Step 3: Create Vector Search Endpoint
print("\n" + "=" * 80)
print("Step 3: Create Vector Search Endpoint")
print("=" * 80)

endpoint_code = """
from databricks.vector_search.client import VectorSearchClient

# Initialize client
vsc = VectorSearchClient(disable_notice=True)

# Endpoint name for gold table
endpoint_name = "customer_kwh_endpoint"

try:
    vsc.create_endpoint(
        name=endpoint_name,
        endpoint_type="STANDARD"
    )
    print(f"✅ Endpoint '{endpoint_name}' created successfully")
except Exception as e:
    if "already exists" in str(e).lower() or "RESOURCE_ALREADY_EXISTS" in str(e):
        print(f"ℹ️  Endpoint '{endpoint_name}' already exists")
    else:
        print(f"⚠️  Error: {e}")
"""

print(endpoint_code)

# Step 4: Identify text column for embeddings
print("\n" + "=" * 80)
print("Step 4: Identify text column for embeddings")
print("=" * 80)

print("""
IMPORTANT: You need to identify which column(s) should be used for vector embeddings.

Common options for customer KWH summary:
- A description or notes column
- A concatenated column with customer info + usage details
- Or create a new column that combines relevant text fields

Example: If you have columns like 'customer_name', 'usage_category', 'notes', etc.
You might want to create a combined text column:

ALTER TABLE `na-dbxtraining`.biju_gold.gold_daily_customer_kwh_summary
ADD COLUMN IF NOT EXISTS search_text STRING 
GENERATED ALWAYS AS (
  CONCAT(
    COALESCE(customer_name, ''),
    ' ',
    COALESCE(usage_category, ''),
    ' ',
    COALESCE(notes, ''),
    ' ',
    CAST(kwh_usage AS STRING)
  )
);
""")

# Step 5: Create Vector Search Index
print("\n" + "=" * 80)
print("Step 5: Create Vector Search Index")
print("=" * 80)

index_code = """
from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient(disable_notice=True)

# Configuration
endpoint_name = "customer_kwh_endpoint"
index_name = "na-dbxtraining.biju_gold.customer_kwh_embeddingsindex"
source_table = "na-dbxtraining.biju_gold.gold_daily_customer_kwh_summary"

# IMPORTANT: Update these based on your actual table schema
# Replace 'search_text' with the actual column name you want to embed
# Replace 'customer_id' with your primary key column
# Update the schema to match your actual columns

try:
    vsc.create_delta_sync_index(
        endpoint_name=endpoint_name,
        index_name=index_name,
        primary_key="customer_id",  # UPDATE THIS - your primary key column
        source_table_name=source_table,
        embedding_source_column="search_text",  # UPDATE THIS - column to create embeddings from
        embedding_model_endpoint_name="databricks-bge-large-en",
        schema={
            # UPDATE THIS - match your actual table schema
            "customer_id": "string",
            "date": "date",
            "kwh_usage": "double",
            "customer_name": "string",
            "search_text": "string"  # The column used for embeddings
        }
    )
    print(f"✅ Vector Search Index '{index_name}' created successfully")
    print(f"   This may take a few minutes to sync...")
except Exception as e:
    if "already exists" in str(e).lower() or "RESOURCE_ALREADY_EXISTS" in str(e):
        print(f"ℹ️  Index '{index_name}' already exists")
    else:
        print(f"❌ Error creating index: {e}")
        print(f"   Please check:")
        print(f"   1. Table exists: {source_table}")
        print(f"   2. Primary key column exists")
        print(f"   3. Embedding source column exists")
        print(f"   4. Table has Change Data Feed enabled")
"""

print(index_code)

# Step 6: Enable Change Data Feed (if not already enabled)
print("\n" + "=" * 80)
print("Step 6: Enable Change Data Feed (if needed)")
print("=" * 80)

cdf_code = """
-- Enable Change Data Feed for automatic index synchronization
ALTER TABLE `na-dbxtraining`.biju_gold.gold_daily_customer_kwh_summary
SET TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
"""

print(cdf_code)

# Step 7: Test the Vector Search Index
print("\n" + "=" * 80)
print("Step 7: Test Vector Search Index")
print("=" * 80)

test_code = """
from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient(disable_notice=True)

endpoint_name = "customer_kwh_endpoint"
index_name = "na-dbxtraining.biju_gold.customer_kwh_embeddingsindex"

# Get the index
index = vsc.get_index(
    endpoint_name=endpoint_name,
    index_name=index_name
)

# Test search
results = index.similarity_search(
    query_text="high energy usage customer",
    columns=["customer_id", "customer_name", "kwh_usage", "date"],
    num_results=5
)

print("🔍 Search Results:")
if 'result' in results and 'data_array' in results['result']:
    for i, result in enumerate(results['result']['data_array'], 1):
        print(f"\\n{i}. Customer: {result[1] if len(result) > 1 else 'N/A'}")
        print(f"   KWH Usage: {result[2] if len(result) > 2 else 'N/A'}")
        print(f"   Date: {result[3] if len(result) > 3 else 'N/A'}")
else:
    print("No results found")
"""

print(test_code)

# Step 8: MCP Server URL
print("\n" + "=" * 80)
print("Step 8: MCP Server Configuration")
print("=" * 80)

mcp_info = """
Your MCP Server URL will be:
https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_gold

MCP Tool Name:
na-dbxtraining__biju_gold__customer_kwh_embeddingsindex

This will be available after the index is created and synced.
"""

print(mcp_info)

print("\n" + "=" * 80)
print("Setup Complete!")
print("=" * 80)
print("""
Next steps:
1. Run each step in order in a Databricks notebook
2. Update the schema and column names to match your actual table
3. Wait for index sync to complete
4. Test the vector search
5. Configure MCP server in Cursor (see setup_mcp_cursor.py)
""")


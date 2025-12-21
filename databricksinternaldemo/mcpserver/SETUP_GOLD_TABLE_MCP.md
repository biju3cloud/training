# Setup Vector Search and MCP Server for gold_daily_customer_kwh_summary

This guide walks you through creating a vector search index and MCP server for the `na-dbxtraining.biju_gold.gold_daily_customer_kwh_summary` table.

## Prerequisites

- Access to Databricks workspace: `https://adb-1952652121322753.13.azuredatabricks.net`
- Table exists: `na-dbxtraining.biju_gold.gold_daily_customer_kwh_summary`
- Databricks Personal Access Token (PAT)

## Step-by-Step Setup

### Step 1: Understand Your Table Structure

First, check your table structure:

```sql
DESCRIBE TABLE EXTENDED `na-dbxtraining`.biju_gold.gold_daily_customer_kwh_summary;

-- Or view sample data
SELECT * FROM `na-dbxtraining`.biju_gold.gold_daily_customer_kwh_summary LIMIT 10;
```

**Important**: Identify:
- **Primary key column** (e.g., `customer_id`, `id`, or composite key)
- **Text column(s)** to use for embeddings (or create a combined text column)

### Step 2: Create a Search Text Column (If Needed)

If your table doesn't have a good text column for embeddings, create one:

```sql
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
    CAST(kwh_usage AS STRING),
    ' kWh'
  )
);
```

**Update the column names** to match your actual table schema.

### Step 3: Enable Change Data Feed

Enable Change Data Feed for automatic index synchronization:

```sql
ALTER TABLE `na-dbxtraining`.biju_gold.gold_daily_customer_kwh_summary
SET TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
```

### Step 4: Install Vector Search Package

In a Databricks notebook:

```python
%pip install databricks-vectorsearch
dbutils.library.restartPython()
```

### Step 5: Create Vector Search Endpoint

```python
from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient(disable_notice=True)

endpoint_name = "customer_kwh_endpoint"

try:
    vsc.create_endpoint(
        name=endpoint_name,
        endpoint_type="STANDARD"
    )
    print(f"✅ Endpoint '{endpoint_name}' created")
except Exception as e:
    if "already exists" in str(e).lower():
        print(f"ℹ️  Endpoint already exists")
    else:
        raise
```

### Step 6: Create Vector Search Index

**⚠️ IMPORTANT**: Update the schema and column names to match your actual table!

```python
from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient(disable_notice=True)

endpoint_name = "customer_kwh_endpoint"
index_name = "na-dbxtraining.biju_gold.customer_kwh_embeddingsindex"
source_table = "na-dbxtraining.biju_gold.gold_daily_customer_kwh_summary"

# UPDATE THESE VALUES:
PRIMARY_KEY = "customer_id"  # Your primary key column name
EMBEDDING_COLUMN = "search_text"  # Column to create embeddings from

vsc.create_delta_sync_index(
    endpoint_name=endpoint_name,
    index_name=index_name,
    primary_key=PRIMARY_KEY,
    source_table_name=source_table,
    embedding_source_column=EMBEDDING_COLUMN,
    embedding_model_endpoint_name="databricks-bge-large-en",
    schema={
        # UPDATE THIS - match your actual table schema
        "customer_id": "string",
        "date": "date",
        "kwh_usage": "double",
        "customer_name": "string",
        "search_text": "string"
    }
)

print(f"✅ Index '{index_name}' created")
print("⏳ Waiting for initial sync (this may take a few minutes)...")
```

### Step 7: Test the Index

```python
from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient(disable_notice=True)

index = vsc.get_index(
    endpoint_name="customer_kwh_endpoint",
    index_name="na-dbxtraining.biju_gold.customer_kwh_embeddingsindex"
)

# Test search
results = index.similarity_search(
    query_text="high energy usage customer",
    columns=["customer_id", "customer_name", "kwh_usage", "date"],
    num_results=5
)

print("🔍 Search Results:")
for i, result in enumerate(results.get('result', {}).get('data_array', []), 1):
    print(f"{i}. {result}")
```

### Step 8: Configure MCP Server in Cursor

Run locally:

```bash
# Set your token
export DATABRICKS_TOKEN=your_token_here

# Run the setup script
uv run python setup_mcp_cursor_gold.py
```

Or manually update `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "databricks-vector-search": {
      "url": "https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_raw",
      "headers": {
        "Authorization": "Bearer dapi..."
      }
    },
    "databricks-vector-search-gold": {
      "url": "https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_gold",
      "headers": {
        "Authorization": "Bearer dapi..."
      }
    }
  }
}
```

### Step 9: Test MCP Server

```bash
uv run python test_gold_mcp.py
```

## MCP Server Details

**Server URL**: `https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_gold`

**Tool Name**: `na-dbxtraining__biju_gold__customer_kwh_embeddingsindex`

## Using in Cursor

After restarting Cursor, you can use the MCP server:

1. The tool will be available as: `databricks-vector-search-gold`
2. Query examples:
   - "Find customers with high energy usage"
   - "Show me daily KWH summaries for last month"
   - "Customers with unusual consumption patterns"

## Troubleshooting

### Index Creation Fails

- Verify table exists and you have permissions
- Check that primary key column exists
- Ensure embedding source column exists
- Verify Change Data Feed is enabled

### MCP Server Returns 401

- Check PAT token is valid
- Ensure token has "Bearer " prefix
- Verify token hasn't expired

### No Search Results

- Wait for index sync to complete (check index status)
- Verify table has data
- Try broader search terms

## Files Created

- `setup_gold_table_vector_search.py` - Databricks notebook code
- `setup_mcp_cursor_gold.py` - Cursor MCP configuration script
- `test_gold_mcp.py` - Test script for MCP server

## Next Steps

1. Run the setup in a Databricks notebook
2. Update schema and column names to match your table
3. Configure MCP in Cursor
4. Test and use!


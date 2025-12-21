# Databricks MCP Vector Search Server

This folder contains all components for setting up and using Databricks MCP Vector Search servers.

## Contents

### Setup Scripts
- `setup_gold_table_vector_search.py` - Setup vector search for gold_daily_customer_kwh_summary table
- `setup_mcp_cursor_gold.py` - Configure MCP server in Cursor for gold table
- `test_gold_mcp.py` - Test MCP server connection and queries

### Applications
- `streamlitmcpcall.py` - Streamlit app for Databricks Apps deployment
- `streamlitapp.py` - Local Streamlit development app
- `gradioapp.py` - Gradio web interface
- `test_databricks_connect.py` - Connection testing utility

### Deployment
- `deploy_app_api.py` - Programmatic deployment script

### Documentation
- `SETUP_GOLD_TABLE_MCP.md` - Complete setup guide for gold table
- `MCP_TROUBLESHOOTING.md` - MCP server troubleshooting
- `DEPLOY_APP.md` - App deployment instructions
- `APP_CREATION_GUIDE.md` - App creation guide
- `CREATE_APP_STEPS.md` - Step-by-step app creation
- `FILE_SELECTION_HELP.md` - File selection troubleshooting
- `FIX_AUTH_CONFLICT.md` - Authentication configuration

### Configuration
- `.env.example` - Environment variable template
- `streamlitmcpcall.app.yml` - Databricks app resource definition
- `requirements.txt` - Python dependencies

## Quick Start

### For gold_daily_customer_kwh_summary table:

1. **Run setup in Databricks notebook**:
   - Import `setup_gold_table_vector_search.py` as a notebook
   - Update schema and column names
   - Execute cells in order

2. **Configure Cursor MCP**:
   ```bash
   export DATABRICKS_TOKEN=your_token
   python setup_mcp_cursor_gold.py
   ```

3. **Test MCP server**:
   ```bash
   python test_gold_mcp.py
   ```

## MCP Server URLs

### Tickets (biju_raw):
- URL: `https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_raw`
- Tool: `na-dbxtraining__biju_raw__ticket_embeddingsindex`

### Customer KWH (biju_gold):
- URL: `https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_gold`
- Tool: `na-dbxtraining__biju_gold__customer_kwh_embeddingsindex`

## Requirements

- Python 3.10+
- Databricks workspace access
- Personal Access Token or Service Principal
- Vector Search indexes created in Databricks

See individual documentation files for detailed setup instructions.

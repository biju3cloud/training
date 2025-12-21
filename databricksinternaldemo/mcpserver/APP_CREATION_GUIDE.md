# Creating the Streamlit App in Databricks

## When You See "Add Resource" Options

**Do NOT select "vector-search-index"** - Our app doesn't need it!

The Streamlit app (`streamlitmcpcall.py`) directly calls the MCP server endpoint via HTTP, so no additional Databricks resources are needed.

## What to Do Instead

1. **Skip adding resources** (or click "Skip" if available)
   - The app is self-contained and makes HTTP calls to the MCP endpoint

2. **Look for these options instead:**
   - **App Type**: Select "Streamlit" or "Python"
   - **Source File**: Browse to or enter: `/Workspace/Users/biju.thottathil@3cloudsolutions.com/streamlitmcpcall.py`
   - **Runtime**: Python 3.x (should be auto-detected)

3. **If you must add a resource**, you could add:
   - **Python Environment** (if available) - but this is usually auto-configured
   - **Secrets Scope** (if you want to store tokens securely) - optional

## The App Architecture

Our app works like this:
```
Streamlit App → HTTP Request → MCP Server Endpoint
```

It doesn't need:
- ❌ Vector Search Index (we call the MCP API directly)
- ❌ Database connections
- ❌ Cluster resources (runs in serverless mode)

## Configuration Steps

1. **App Name**: `streamlitmcpcall`
2. **Source Path**: `/Workspace/Users/biju.thottathil@3cloudsolutions.com/streamlitmcpcall.py`
3. **Authentication**: 
   - Service Principal OR
   - PAT Token
4. **Resources**: None needed (skip if possible)

## If You're Stuck

If the interface requires you to add a resource:
- Try clicking "Skip" or "Next" without selecting anything
- Or select the most basic option (like "Python Environment" if available)
- The app will work without any additional resources

The key is to get to the point where you can specify:
- The source file path
- Authentication method
- Deploy the app


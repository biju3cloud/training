# Databricks Vector Search MCP Server Troubleshooting

## Issues Found

1. ✅ **Fixed**: Leading space in Authorization header (removed)
2. ✅ **Fixed**: Added "Bearer " prefix to Authorization header (required for MCP API)
3. ✅ **Fixed**: Personal Access Token (PAT) updated and working
4. ⚠️ **Note**: MCP endpoint requires POST requests (not GET)

## Current Configuration

**Location**: `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "databricks-vector-search": {
      "url": "https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_raw",
      "headers": {
        "Authorization": "Bearer YOUR_DATABRICKS_TOKEN_HERE"
      }
    }
  }
}
```

**✅ Current Status**: Configuration is correct and working!

## Steps to Fix

### 1. Generate a New Personal Access Token (PAT)

You need to create a new Personal Access Token in your Databricks workspace:

**Option A: Via Databricks UI**
1. Go to: https://adb-1952652121322753.13.azuredatabricks.net
2. Click on your user icon (top right) → **User Settings**
3. Go to **Access Tokens** tab
4. Click **Generate New Token**
5. Add a comment: "MCP Vector Search"
6. Set expiration (recommended: 90 days or custom)
7. Click **Generate**
8. **Copy the token immediately** (you won't be able to see it again)

**Option B: Via Databricks CLI** (Note: May not work if basic auth is disabled)
```bash
databricks tokens create --profile DEFAULT --comment "MCP Vector Search"
```

⚠️ **If CLI fails**: Use Option A (UI method) - it's more reliable.

### 2. Update MCP Configuration

Once you have the new token, update `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "databricks-vector-search": {
      "url": "https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_raw",
      "headers": {
        "Authorization": "YOUR_NEW_PAT_TOKEN_HERE"
      }
    }
  }
}
```

**Important**: 
- No leading space in the Authorization header
- Token should start with `dapi...`
- ✅ **REQUIRED**: Must include "Bearer " prefix: `"Authorization": "Bearer dapi..."`

### 3. Restart Cursor

After updating the configuration:
1. Save the `mcp.json` file
2. Restart Cursor completely
3. The MCP server should connect automatically

### 4. Verify MCP Server is Connected

After restarting Cursor, check:
- Look for MCP server status in Cursor's status bar or MCP panel
- Try using MCP tools in a chat session
- Check Cursor's developer console for any MCP connection errors

## Additional Requirements

According to Databricks documentation, ensure:

1. **Vector Search Feature is Enabled**: 
   - Vector Search must be enabled in your workspace
   - Contact your Databricks account representative if needed

2. **OAuth Scopes**: 
   - Your OAuth application should have `mcp.vectorsearch` scope
   - Verify in Databricks workspace settings

3. **Permissions**: 
   - Your user account needs permissions to access Vector Search MCP server
   - Verify Unity Catalog permissions for the catalog/schema: `na-dbxtraining/biju_raw`

## Testing the Connection

You can test the MCP endpoint manually:

```bash
# Test with curl (replace YOUR_TOKEN with your PAT)
curl -X POST \
  -H "Authorization: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_raw
```

Expected response: Should return a JSON-RPC response, not a 401 error.

## Resources

- [Databricks MCP Documentation](https://docs.databricks.com/aws/en/generative-ai/mcp)
- [MCP Inspector Tool](https://github.com/modelcontextprotocol/inspector)


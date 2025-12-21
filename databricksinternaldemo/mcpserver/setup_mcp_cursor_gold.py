"""
Setup MCP Server configuration in Cursor for gold_daily_customer_kwh_summary
Run this locally to update your Cursor MCP configuration
"""

import json
import os
from pathlib import Path

# MCP Configuration
MCP_CONFIG_PATH = Path.home() / ".cursor" / "mcp.json"
MCP_SERVER_NAME = "databricks-vector-search-gold"
MCP_SERVER_URL = "https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_gold"
MCP_TOOL_NAME = "na-dbxtraining__biju_gold__customer_kwh_embeddingsindex"

# Get token from environment or existing config
def get_databricks_token():
    """Get Databricks PAT token."""
    # Try environment variable
    token = os.environ.get("DATABRICKS_TOKEN")
    if token:
        return token
    
    # Try reading from existing mcp.json
    if MCP_CONFIG_PATH.exists():
        try:
            with open(MCP_CONFIG_PATH) as f:
                config = json.load(f)
                existing_server = config.get("mcpServers", {}).get("databricks-vector-search", {})
                auth_header = existing_server.get("headers", {}).get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    return auth_header[7:]
                return auth_header
        except:
            pass
    
    return None

def update_mcp_config():
    """Update Cursor MCP configuration with new gold table server."""
    
    # Get token
    token = get_databricks_token()
    if not token:
        print("❌ Error: DATABRICKS_TOKEN not found")
        print("   Please set it: export DATABRICKS_TOKEN=your_token")
        return False
    
    # Read existing config or create new
    if MCP_CONFIG_PATH.exists():
        with open(MCP_CONFIG_PATH) as f:
            config = json.load(f)
    else:
        config = {"mcpServers": {}}
    
    # Add or update the gold table MCP server
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    config["mcpServers"][MCP_SERVER_NAME] = {
        "url": MCP_SERVER_URL,
        "headers": {
            "Authorization": f"Bearer {token}"
        }
    }
    
    # Backup existing config
    if MCP_CONFIG_PATH.exists():
        backup_path = MCP_CONFIG_PATH.with_suffix(".json.backup")
        import shutil
        shutil.copy(MCP_CONFIG_PATH, backup_path)
        print(f"✅ Backed up existing config to: {backup_path}")
    
    # Write updated config
    with open(MCP_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Updated MCP configuration: {MCP_CONFIG_PATH}")
    print(f"   Server: {MCP_SERVER_NAME}")
    print(f"   URL: {MCP_SERVER_URL}")
    print(f"   Tool: {MCP_TOOL_NAME}")
    print(f"\n📝 Next steps:")
    print(f"   1. Restart Cursor completely")
    print(f"   2. The MCP server '{MCP_SERVER_NAME}' will be available")
    print(f"   3. You can query the gold table using vector search")
    
    return True

if __name__ == "__main__":
    print("🔧 Setting up MCP Server for gold_daily_customer_kwh_summary")
    print("=" * 80)
    print()
    
    if update_mcp_config():
        print("\n✅ Configuration complete!")
    else:
        print("\n❌ Configuration failed. Please check the errors above.")


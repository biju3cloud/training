"""
Test the MCP server for gold_daily_customer_kwh_summary table
"""

import urllib.request
import json
import os
from pathlib import Path

# Load token from .env or environment
def load_token():
    """Load Databricks token."""
    # Try .env file
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("DATABRICKS_TOKEN="):
                    return line.split("=", 1)[1].strip()
    
    # Try environment variable
    return os.environ.get("DATABRICKS_TOKEN")

# MCP Configuration
MCP_SERVER_URL = "https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_gold"
MCP_TOOL_NAME = "na-dbxtraining__biju_gold__customer_kwh_embeddingsindex"

def test_mcp_connection():
    """Test MCP server connection."""
    token = load_token()
    if not token:
        print("❌ Error: DATABRICKS_TOKEN not found")
        print("   Set it in .env file or environment variable")
        return False
    
    auth_header = f"Bearer {token}"
    
    # Test initialize
    print("🔌 Testing MCP server connection...")
    req = urllib.request.Request(MCP_SERVER_URL, method="POST")
    req.add_header("Authorization", auth_header)
    req.add_header("Content-Type", "application/json")
    
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    
    try:
        req.data = json.dumps(init_request).encode()
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            if "result" in result:
                print("✅ MCP server connection successful!")
                print(f"   Server: {result['result'].get('serverInfo', {}).get('name', 'N/A')}")
                return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_vector_search(query_text="high energy usage"):
    """Test vector search on gold table."""
    token = load_token()
    if not token:
        print("❌ Error: DATABRICKS_TOKEN not found")
        return False
    
    auth_header = f"Bearer {token}"
    
    print(f"\n🔍 Testing vector search with query: '{query_text}'")
    
    req = urllib.request.Request(MCP_SERVER_URL, method="POST")
    req.add_header("Authorization", auth_header)
    req.add_header("Content-Type", "application/json")
    
    search_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": MCP_TOOL_NAME,
            "arguments": {
                "query": query_text
            }
        }
    }
    
    try:
        req.data = json.dumps(search_request).encode()
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                return False
            
            if "result" in result and "content" in result["result"]:
                content = result["result"]["content"]
                if isinstance(content, list) and len(content) > 0:
                    text_content = content[0].get("text", "")
                    try:
                        data = json.loads(text_content)
                        print(f"✅ Found {len(data)} results")
                        for i, item in enumerate(data[:5], 1):
                            print(f"\n{i}. {item}")
                        return True
                    except:
                        print(f"✅ Response received: {text_content[:200]}")
                        return True
            
            print("⚠️  No results returned")
            return False
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("Testing MCP Server for gold_daily_customer_kwh_summary")
    print("=" * 80)
    print()
    
    # Test connection
    if test_mcp_connection():
        # Test search
        test_vector_search("high energy usage customer")
    else:
        print("\n❌ Cannot proceed with search test - connection failed")


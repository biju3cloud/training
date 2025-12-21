"""
Gradio app for interacting with Databricks MCP Vector Search server.
Uses environment variables from .env file for configuration.
"""

import gradio as gr
import urllib.request
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION FROM ENV ---
MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_raw"
)
MCP_TOOL_NAME = os.getenv(
    "MCP_TOOL_NAME",
    "na-dbxtraining__biju_raw__ticket_embeddingsindex"
)
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")

def query_mcp_server(query_text):
    """Query the MCP server for vector search results."""
    if not DATABRICKS_TOKEN:
        return "❌ Error: DATABRICKS_TOKEN not found in .env file. Please set it in your .env file."
    
    token = DATABRICKS_TOKEN
    # Ensure token has Bearer prefix
    if not token.startswith("Bearer "):
        auth_header = f"Bearer {token}"
    else:
        auth_header = token
    
    # Create MCP JSON-RPC request
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": MCP_TOOL_NAME,
            "arguments": {
                "query": query_text
            }
        }
    }
    
    # Make HTTP request
    req = urllib.request.Request(MCP_SERVER_URL, method="POST")
    req.add_header("Authorization", auth_header)
    req.add_header("Content-Type", "application/json")
    req.data = json.dumps(mcp_request).encode()
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            
            if "error" in result:
                return f"❌ MCP Server Error: {json.dumps(result['error'], indent=2)}"
            
            if "result" in result and "content" in result["result"]:
                content = result["result"]["content"]
                
                if isinstance(content, list) and len(content) > 0:
                    text_content = content[0].get("text", "")
                    tickets = json.loads(text_content)
                    
                    if tickets:
                        # Sort by relevance score
                        tickets_sorted = sorted(tickets, key=lambda x: x.get('score', 0), reverse=True)
                        
                        # Format response
                        response_text = f"✅ Found {len(tickets_sorted)} relevant ticket(s):\n\n"
                        response_text += "=" * 80 + "\n\n"
                        
                        for i, ticket in enumerate(tickets_sorted, 1):
                            response_text += f"📋 **Ticket #{i}: {ticket.get('ticket_id', 'N/A')}**\n"
                            response_text += f"   Customer: {ticket.get('customer_id', 'N/A')}\n"
                            response_text += f"   Created: {ticket.get('created_date', 'N/A')}\n"
                            response_text += f"   Resolved: {ticket.get('resolved_date', 'N/A')}\n"
                            response_text += f"   Status: {ticket.get('status', 'N/A')}\n"
                            response_text += f"   Category: {ticket.get('category', 'N/A')}\n"
                            response_text += f"   Relevance: {ticket.get('score', 0):.6f}\n\n"
                            response_text += f"   **Issue:**\n   {ticket.get('issue', 'N/A')}\n\n"
                            
                            resolution = ticket.get('resolution', 'N/A')
                            if resolution and resolution != 'N/A':
                                response_text += f"   **Resolution:**\n   {resolution}\n\n"
                            
                            response_text += "-" * 80 + "\n\n"
                        
                        return response_text
                    else:
                        return "No tickets found for this query."
            
            return "No results returned from MCP server."
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            error_json = json.loads(error_body)
            return f"❌ HTTP {e.code} Error: {error_json.get('message', error_body)}"
        except:
            return f"❌ HTTP {e.code} Error: {error_body}"
    except json.JSONDecodeError as e:
        return f"❌ Failed to parse response: {str(e)}"
    except Exception as e:
        return f"❌ Error: {type(e).__name__}: {str(e)}"

def check_connection():
    """Check if MCP server connection is working."""
    if not DATABRICKS_TOKEN:
        return "❌ DATABRICKS_TOKEN not configured in .env file"
    
    # Test with a simple query
    result = query_mcp_server("test")
    if result.startswith("❌"):
        return result
    else:
        return "✅ Connection successful! MCP server is responding."

# Create Gradio interface
with gr.Blocks(title="Databricks MCP Vector Search") as demo:
    gr.Markdown(
        """
        # 🤖 Databricks MCP Vector Search Interface
        
        Search through tickets using the Databricks MCP Vector Search server.
        
        **Configuration:**
        - Server: `{}`
        - Tool: `{}`
        - Token: `{}`
        """.format(
            MCP_SERVER_URL,
            MCP_TOOL_NAME,
            "✅ Configured" if DATABRICKS_TOKEN else "❌ Not configured"
        )
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Connection Status")
            status_btn = gr.Button("Check Connection", variant="secondary")
            status_output = gr.Textbox(label="Status", lines=3, interactive=False)
        
        with gr.Column(scale=2):
            gr.Markdown("### Search Tickets")
            query_input = gr.Textbox(
                label="Search Query",
                placeholder="Enter your search query (e.g., 'slow internet', 'connection issues')",
                lines=2
            )
            search_btn = gr.Button("🔍 Search", variant="primary")
    
    results_output = gr.Textbox(
        label="Search Results",
        lines=20,
        interactive=False
    )
    
    # Examples
    gr.Markdown("### Example Queries")
    examples = gr.Examples(
        examples=[
            ["slow internet"],
            ["connection issues"],
            ["billing problems"],
            ["network performance"],
            ["device configuration"],
        ],
        inputs=query_input
    )
    
    # Event handlers
    status_btn.click(
        fn=check_connection,
        outputs=status_output
    )
    
    search_btn.click(
        fn=query_mcp_server,
        inputs=query_input,
        outputs=results_output
    )
    
    query_input.submit(
        fn=query_mcp_server,
        inputs=query_input,
        outputs=results_output
    )

if __name__ == "__main__":
    # Check if token is configured
    if not DATABRICKS_TOKEN:
        print("⚠️  Warning: DATABRICKS_TOKEN not found in .env file")
        print("   Please create a .env file with your token:")
        print("   DATABRICKS_TOKEN=your_token_here")
        print()
    
    demo.launch(
        server_name="0.0.0.0",  # Allow external connections
        server_port=7860,
        share=False,
        theme=gr.themes.Soft()
    )


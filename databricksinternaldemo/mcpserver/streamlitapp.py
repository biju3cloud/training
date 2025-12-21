import streamlit as st
import urllib.request
import json
import os
from pathlib import Path

# --- CONFIGURATION ---
MCP_SERVER_URL = "https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_raw"
MCP_TOOL_NAME = "na-dbxtraining__biju_raw__ticket_embeddingsindex"

st.set_page_config(page_title="Databricks Support Agent", page_icon="🤖", layout="wide")

st.title("🤖 MCP Support Agent")
st.markdown(f"**Connected to:** `{MCP_SERVER_URL}`")

# --- AUTHENTICATION ---
def get_databricks_token():
    """Get Databricks PAT token from environment or config file."""
    # Try environment variable first
    token = os.environ.get("DATABRICKS_TOKEN")
    if token:
        return token
    
    # Try loading from .databricks/.databricks.env
    env_file = Path(__file__).parent / ".databricks" / ".databricks.env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("DATABRICKS_TOKEN="):
                    return line.split("=", 1)[1].strip()
    
    # Try reading from mcp.json
    mcp_file = Path.home() / ".cursor" / "mcp.json"
    if mcp_file.exists():
        try:
            with open(mcp_file) as f:
                mcp_config = json.load(f)
                auth_header = mcp_config.get("mcpServers", {}).get("databricks-vector-search", {}).get("headers", {}).get("Authorization", "")
                # Remove "Bearer " prefix if present
                if auth_header.startswith("Bearer "):
                    return auth_header[7:]
                return auth_header
        except:
            pass
    
    return None

# Initialize token in session state
if "databricks_token" not in st.session_state:
    st.session_state.databricks_token = get_databricks_token()

# Show token status
if st.session_state.databricks_token:
    st.success("✅ Authenticated with Databricks")
else:
    st.warning("⚠️ No authentication token found. Please set DATABRICKS_TOKEN environment variable or configure in .cursor/mcp.json")
    token_input = st.text_input("Enter Databricks PAT token:", type="password", help="Enter your Personal Access Token (starts with 'dapi...')")
    if token_input:
        st.session_state.databricks_token = token_input
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def query_mcp_server(query_text):
    """Query the MCP server for vector search results."""
    if not st.session_state.databricks_token:
        raise ValueError("No authentication token available")
    
    token = st.session_state.databricks_token
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
                raise Exception(f"MCP Server Error: {result['error']}")
            
            if "result" in result and "content" in result["result"]:
                content = result["result"]["content"]
                
                if isinstance(content, list) and len(content) > 0:
                    text_content = content[0].get("text", "")
                    tickets = json.loads(text_content)
                    return tickets
            
            return []
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            error_json = json.loads(error_body)
            raise Exception(f"HTTP {e.code}: {error_json.get('message', error_body)}")
        except:
            raise Exception(f"HTTP {e.code}: {error_body}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse response: {str(e)}")

# React to user input
if prompt := st.chat_input("How can I help you today?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        # Query MCP Server
        with st.spinner("🔍 Searching knowledge base..."):
            tickets = query_mcp_server(prompt)
        
        # Format the Response
        if tickets:
            # Sort by relevance score
            tickets_sorted = sorted(tickets, key=lambda x: x.get('score', 0), reverse=True)
            
            response = f"Based on past tickets, I found **{len(tickets_sorted)}** relevant result(s):\n\n"
            
            for i, ticket in enumerate(tickets_sorted, 1):
                response += f"### Ticket #{i}: {ticket.get('ticket_id', 'N/A')}\n"
                response += f"**Customer:** {ticket.get('customer_id', 'N/A')}  \n"
                response += f"**Created:** {ticket.get('created_date', 'N/A')}  \n"
                response += f"**Resolved:** {ticket.get('resolved_date', 'N/A')}  \n"
                response += f"**Status:** {ticket.get('status', 'N/A')}  \n"
                response += f"**Category:** {ticket.get('category', 'N/A')}  \n"
                response += f"**Relevance Score:** {ticket.get('score', 0):.6f}\n\n"
                response += f"**Issue:**\n{ticket.get('issue', 'N/A')}\n\n"
                
                resolution = ticket.get('resolution', 'N/A')
                if resolution and resolution != 'N/A':
                    response += f"**Resolution:**\n{resolution}\n\n"
                
                response += "---\n\n"
        else:
            response = "I couldn't find any similar past tickets for this issue. Try rephrasing your query."

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})

    except Exception as e:
        error_msg = f"❌ Error connecting to MCP Server: {str(e)}"
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
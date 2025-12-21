# Databricks notebook source
"""
Streamlit app for Databricks Apps deployment.
Interacts with Databricks MCP Vector Search server.
Uses service principal or PAT authentication via Databricks SDK.
"""

import streamlit as st
import urllib.request
import json
import os
from databricks.sdk import WorkspaceClient

# --- CONFIGURATION ---
# MCP Server URL and Tool Name from streamlitapp.py
MCP_SERVER_URL = "https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_raw"
MCP_TOOL_NAME = "na-dbxtraining__biju_raw__ticket_embeddingsindex"

st.set_page_config(
    page_title="Databricks MCP Vector Search",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Databricks MCP Vector Search")
st.markdown(f"**MCP Server:** `{MCP_SERVER_URL}`")
st.markdown(f"**Tool:** `{MCP_TOOL_NAME}`")

# --- AUTHENTICATION ---
@st.cache_resource
def get_workspace_client():
    """Initialize Databricks WorkspaceClient with service principal or PAT."""
    try:
        # WorkspaceClient automatically uses:
        # 1. Service principal (if configured via environment variables)
        # 2. PAT token (if DATABRICKS_TOKEN is set)
        # 3. Default profile from ~/.databrickscfg
        client = WorkspaceClient()
        return client
    except Exception as e:
        st.error(f"Failed to initialize WorkspaceClient: {str(e)}")
        return None

@st.cache_resource
def get_databricks_token():
    """Get Databricks PAT token for MCP authentication."""
    # Try environment variable first (for service principal or PAT)
    token = os.environ.get("DATABRICKS_TOKEN")
    if token:
        return token
    
    # Try to get from Databricks runtime secrets
    try:
        from databricks.sdk.runtime import dbutils
        # In Databricks runtime, we can use secrets
        try:
            token = dbutils.secrets.get(scope="mcp", key="databricks_token")
            if token:
                return token
        except:
            pass
    except ImportError:
        # Not in Databricks runtime
        pass
    except Exception:
        pass
    
    # Try to get token from WorkspaceClient (creates a new token)
    try:
        client = get_workspace_client()
        if client:
            # Create a temporary token for MCP authentication
            token_response = client.tokens.create(comment="MCP Vector Search App")
            return token_response.token_value
    except Exception as e:
        # Token creation failed, will show warning in UI
        pass
    
    return None

# Initialize authentication
workspace_client = get_workspace_client()
databricks_token = get_databricks_token()

# Show authentication status
if workspace_client:
    try:
        current_user = workspace_client.current_user.me()
        st.success(f"✅ Authenticated as: {current_user.user_name}")
    except:
        st.info("ℹ️ WorkspaceClient initialized")

if databricks_token:
    st.success("✅ Authentication token available")
else:
    st.warning("⚠️ No authentication token found. The app may not work correctly.")
    st.info("💡 Configure authentication using:")
    st.code("""
    # Option 1: Service Principal (recommended for production)
    export DATABRICKS_CLIENT_ID=your_client_id
    export DATABRICKS_CLIENT_SECRET=your_client_secret
    export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
    
    # Option 2: PAT Token
    export DATABRICKS_TOKEN=your_pat_token
    """)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def query_mcp_server(query_text):
    """Query the MCP server for vector search results."""
    if not databricks_token:
        raise ValueError("No authentication token available. Please configure authentication.")
    
    token = databricks_token
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
                raise Exception(f"MCP Server Error: {json.dumps(result['error'], indent=2)}")
            
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

# Sidebar with info
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This app connects to the Databricks MCP Vector Search server
    to search through support tickets.
    
    **Features:**
    - Vector similarity search
    - Relevance scoring
    - Ticket history and resolutions
    """)
    
    st.header("🔧 Configuration")
    st.code(f"""
    MCP Server: {MCP_SERVER_URL}
    Tool: {MCP_TOOL_NAME}
    """, language="text")
    
    if st.button("🔄 Refresh Connection"):
        st.cache_resource.clear()
        st.rerun()

# React to user input
if prompt := st.chat_input("Search for tickets (e.g., 'slow internet', 'connection issues')..."):
    # Display user message
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
            
            response = f"✅ Found **{len(tickets_sorted)}** relevant ticket(s):\n\n"
            
            for i, ticket in enumerate(tickets_sorted, 1):
                response += f"### 📋 Ticket #{i}: {ticket.get('ticket_id', 'N/A')}\n"
                response += f"**Customer:** {ticket.get('customer_id', 'N/A')}  \n"
                response += f"**Created:** {ticket.get('created_date', 'N/A')}  \n"
                response += f"**Resolved:** {ticket.get('resolved_date', 'N/A')}  \n"
                response += f"**Status:** {ticket.get('status', 'N/A')}  \n"
                response += f"**Category:** {ticket.get('category', 'N/A')}  \n"
                response += f"**Relevance Score:** `{ticket.get('score', 0):.6f}`\n\n"
                response += f"**Issue:**\n{ticket.get('issue', 'N/A')}\n\n"
                
                resolution = ticket.get('resolution', 'N/A')
                if resolution and resolution != 'N/A':
                    response += f"**Resolution:**\n{resolution}\n\n"
                
                response += "---\n\n"
        else:
            response = "❌ No tickets found for this query. Try rephrasing your search."

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(response)
        
        # Add to history
        st.session_state.messages.append({"role": "assistant", "content": response})

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})


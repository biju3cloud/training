#!/usr/bin/env python3
"""
Deploy Streamlit app to Databricks Apps using the Apps API.
Supports both service principal and PAT authentication.
"""

import os
import sys
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.apps import CreateAppRequest, AppType

def deploy_app():
    """Deploy the Streamlit app to Databricks Apps."""
    
    # Initialize WorkspaceClient (supports service principal or PAT)
    try:
        client = WorkspaceClient()
        print(f"✅ Connected to workspace: {client.config.host}")
    except Exception as e:
        print(f"❌ Failed to connect to Databricks: {e}")
        print("\nPlease configure authentication:")
        print("  Option 1 (PAT): export DATABRICKS_TOKEN=your_token")
        print("  Option 2 (Service Principal):")
        print("    export DATABRICKS_CLIENT_ID=your_client_id")
        print("    export DATABRICKS_CLIENT_SECRET=your_client_secret")
        print("    export DATABRICKS_HOST=https://your-workspace.cloud.databricks.net")
        sys.exit(1)
    
    # App configuration
    app_name = "streamlitmcpcall"
    app_file = "streamlitmcpcall.py"
    workspace_path = f"/Workspace/Users/{os.environ.get('USER', 'default')}/streamlitmcpcall.py"
    
    print(f"\n📦 Uploading {app_file} to workspace...")
    
    # Read the app file
    try:
        with open(app_file, 'r') as f:
            app_content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: {app_file} not found")
        sys.exit(1)
    
    # Upload to workspace
    try:
        client.workspace.upload(
            path=workspace_path,
            content=app_content.encode('utf-8'),
            language="PYTHON",
            overwrite=True
        )
        print(f"✅ Uploaded to: {workspace_path}")
    except Exception as e:
        print(f"❌ Failed to upload: {e}")
        sys.exit(1)
    
    # Create the app
    print(f"\n🚀 Creating Databricks App: {app_name}")
    
    try:
        # Note: Databricks Apps API may vary by workspace version
        # This is a template - adjust based on your workspace's API
        app_request = CreateAppRequest(
            name=app_name,
            app_type=AppType.STREAMLIT,
            source_path=workspace_path,
            description="Streamlit app for MCP Vector Search - Search support tickets"
        )
        
        # Try to create the app
        # Note: The exact API call may differ based on Databricks version
        # You may need to use the REST API directly if SDK doesn't support Apps yet
        print("⚠️  Note: Apps API may not be available in the SDK yet.")
        print("   Please create the app manually via the Databricks UI:")
        print(f"   1. Go to Apps in your workspace")
        print(f"   2. Click 'Create App'")
        print(f"   3. Select 'Streamlit'")
        print(f"   4. Set source path to: {workspace_path}")
        print(f"   5. Configure authentication")
        
        # Alternative: Use REST API directly
        print("\n📝 Alternative: Using REST API...")
        print("   See deploy_app_rest.py for REST API implementation")
        
    except Exception as e:
        print(f"⚠️  App creation via SDK failed: {e}")
        print("\n💡 Please create the app manually via the Databricks UI")
        print(f"   Source path: {workspace_path}")
    
    print("\n✅ Deployment preparation complete!")
    print(f"   App file: {workspace_path}")
    print(f"   Next: Create the app in Databricks UI or use REST API")

if __name__ == "__main__":
    deploy_app()


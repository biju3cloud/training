# Deploying Streamlit MCP App to Databricks

This guide explains how to deploy `streamlitmcpcall.py` to Databricks Apps using either a service principal or PAT token.

## Prerequisites

1. **Databricks CLI installed and configured**
   ```bash
   databricks --version
   ```

2. **Authentication configured** (choose one):

   **Option A: Personal Access Token (PAT)**
   ```bash
   export DATABRICKS_TOKEN=your_pat_token_here
   export DATABRICKS_HOST=https://adb-1952652121322753.13.azuredatabricks.net
   ```

   **Option B: Service Principal** (recommended for production)
   ```bash
   export DATABRICKS_CLIENT_ID=your_client_id
   export DATABRICKS_CLIENT_SECRET=your_client_secret
   export DATABRICKS_HOST=https://adb-1952652121322753.13.azuredatabricks.net
   export DATABRICKS_TENANT_ID=your_tenant_id  # For Azure
   ```

## Deployment Methods

### Method 1: Using Deployment Script (Recommended)

```bash
# Make script executable
chmod +x deploy_app.sh

# Run deployment
./deploy_app.sh
```

This will:
1. Upload `streamlitmcpcall.py` to your Databricks workspace
2. Provide instructions for creating the app in the UI

### Method 2: Manual Deployment via UI

1. **Upload the app file:**
   ```bash
   databricks workspace import \
       --language PYTHON \
       --overwrite \
       streamlitmcpcall.py \
       /Workspace/Users/your-email@domain.com/streamlitmcpcall.py
   ```

2. **Create the App in Databricks UI:**
   - Go to your Databricks workspace
   - Click on **Apps** in the left sidebar
   - Click **Create App**
   - Select **Streamlit** as the app type
   - Set the source path to: `/Workspace/Users/your-email@domain.com/streamlitmcpcall.py`
   - Configure authentication:
     - **Service Principal**: Enter client ID and secret
     - **PAT Token**: Enter your personal access token
   - Click **Deploy**

### Method 3: Using Databricks Bundle

If your workspace supports Apps in bundles:

```bash
# Deploy using bundle
databricks bundle deploy --target dev
```

The app configuration is in `resources/streamlitmcpcall.app.yml`.

## App Configuration

The app uses the following MCP server settings (from `streamlitapp.py` lines 8-9):

- **MCP Server URL**: `https://adb-1952652121322753.13.azuredatabricks.net/api/2.0/mcp/vector-search/na-dbxtraining/biju_raw`
- **Tool Name**: `na-dbxtraining__biju_raw__ticket_embeddingsindex`

## Authentication in the App

The app (`streamlitmcpcall.py`) automatically handles authentication:

1. **Service Principal**: If `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` are set
2. **PAT Token**: If `DATABRICKS_TOKEN` is set
3. **Default Profile**: Falls back to `~/.databrickscfg` if available

The app uses `WorkspaceClient` from `databricks-sdk` which handles authentication automatically.

## Verifying Deployment

After deployment:

1. Go to **Apps** in your Databricks workspace
2. Find `streamlitmcpcall` in the list
3. Click to open the app
4. Test by searching for tickets (e.g., "slow internet")

## Troubleshooting

### Authentication Issues

If you see authentication errors:

1. **Check environment variables:**
   ```bash
   echo $DATABRICKS_TOKEN
   echo $DATABRICKS_CLIENT_ID
   ```

2. **Verify workspace access:**
   ```bash
   databricks workspace ls /
   ```

3. **Test MCP server connection:**
   The app will show connection status in the UI

### App Not Loading

1. Check that the file was uploaded correctly:
   ```bash
   databricks workspace ls /Workspace/Users/your-email@domain.com/
   ```

2. Verify the app path in Databricks UI matches the uploaded path

3. Check app logs in Databricks for errors

## Updating the App

To update the app:

1. Make changes to `streamlitmcpcall.py`
2. Re-run the deployment script:
   ```bash
   ./deploy_app.sh
   ```
3. The app will automatically reload in Databricks

## Security Notes

- **Service Principal** is recommended for production deployments
- **PAT tokens** should be stored securely (use Databricks Secrets)
- Never commit tokens or secrets to version control
- The `.env` file is gitignored for local development

## Resources

- [Databricks Apps Documentation](https://docs.databricks.com/en/dev-tools/apps.html)
- [Databricks SDK Authentication](https://docs.databricks.com/en/dev-tools/auth/index.html)
- [Service Principal Setup](https://docs.databricks.com/en/dev-tools/auth/oauth-m2m.html)


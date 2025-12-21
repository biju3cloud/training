# Steps to Create Streamlit App in Databricks

## Location
**Compute → Apps** (in the left sidebar)

## Step-by-Step Instructions

1. **Navigate to Apps**
   - Click **Compute** in the left sidebar
   - Click **Apps** under Compute

2. **Create New App**
   - Click the **"Create App"** button (usually at the top right)

3. **Configure the App**
   - **App Name**: `streamlitmcpcall` (or any name you prefer)
   - **App Type**: Select **Streamlit**
   - **Source Path**: `/Workspace/Users/biju.thottathil@3cloudsolutions.com/streamlitmcpcall.py`
     - This is the file we just uploaded
   - **Description**: "Streamlit app for MCP Vector Search - Search support tickets using vector similarity"

4. **Configure Authentication**
   - Choose one of the following:
   
   **Option A: Service Principal (Recommended)**
   - **Client ID**: `b345b646-41c0-4abb-884d-6911cdeeec21`
   - **Client Secret**: (your client secret)
   - **Tenant ID**: `ed9aa516-5358-4016-a8b2-b6ccb99142d0`
   
   **Option B: Personal Access Token**
   - **Token**: (your PAT token starting with `dapi...`)

5. **Deploy**
   - Click **Deploy** or **Create**
   - Wait for the app to be created and started

6. **Access Your App**
   - Once deployed, you'll see the app in the Apps list
   - Click on it to open and use it
   - The app will be available at a URL like: `https://adb-1952652121322753.13.azuredatabricks.net/apps/your-app-id`

## Troubleshooting

### If the app doesn't start:
- Check that the source file path is correct
- Verify authentication credentials are valid
- Check app logs for errors

### If you see authentication errors:
- Make sure the Service Principal or PAT has proper permissions
- Verify the token/credentials are not expired

### If the app file is not found:
- Verify the file was uploaded correctly:
  - Go to **Workspace** in the left sidebar
  - Navigate to `/Workspace/Users/biju.thottathil@3cloudsolutions.com/`
  - You should see `streamlitmcpcall.py`

## Quick Verification

To verify the file is in the right place, you can run:
```bash
databricks workspace ls /Workspace/Users/biju.thottathil@3cloudsolutions.com/
```

You should see `streamlitmcpcall.py` in the list.


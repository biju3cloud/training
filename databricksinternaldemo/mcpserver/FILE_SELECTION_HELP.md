# Help: Selecting Python File in Databricks Apps

## Issue: Cannot Select the .py File

If you're having trouble selecting the Python file when creating the app, try these solutions:

## Solution 1: Use the Full Path Manually

Instead of browsing, **type the path directly**:

```
/Workspace/Users/biju.thottathil@3cloudsolutions.com/training/streamlitmcpcall.py
```

Or try:

```
/Workspace/Users/biju.thottathil@3cloudsolutions.com/streamlitmcpcall.py
```

## Solution 2: Browse from Workspace

1. **Open Workspace** (left sidebar)
2. Navigate to: `Users → biju.thottathil@3cloudsolutions.com → training`
3. You should see `streamlitmcpcall.py`
4. **Right-click** on the file
5. Look for option like "Use in App" or "Copy Path"
6. Paste the path in the app creation form

## Solution 3: Check File Format

Make sure the file is recognized as a Python file:

1. Go to **Workspace**
2. Navigate to the file location
3. Click on `streamlitmcpcall.py`
4. Verify it opens as a Python notebook/file
5. If it shows as "Unknown" or "Text", you may need to:
   - Delete and re-upload with correct language type
   - Or use the Workspace import command

## Solution 4: Re-upload the File

If the file isn't showing up correctly, re-upload it:

```bash
./deploy_app.sh
```

Or manually:

```bash
databricks workspace import \
    "/Workspace/Users/biju.thottathil@3cloudsolutions.com/training/streamlitmcpcall.py" \
    --file streamlitmcpcall.py \
    --format SOURCE \
    --language PYTHON \
    --overwrite \
    --profile DEFAULT
```

## Solution 5: Use Workspace File Browser in App Creation

When creating the app:

1. Look for a **"Browse"** or **"Select File"** button
2. Click it to open the Workspace file browser
3. Navigate through the folder structure:
   - `Workspace` → `Users` → `biju.thottathil@3cloudsolutions.com` → `training`
4. Select `streamlitmcpcall.py`

## Solution 6: Check File Permissions

Ensure you have read access to the file:

1. Go to the file in Workspace
2. Check if you can open it
3. If you see permission errors, contact your workspace admin

## Solution 7: Alternative - Create App from Notebook

Some Databricks workspaces allow creating apps directly from notebooks:

1. Open the file `streamlitmcpcall.py` in Workspace
2. Look for menu options like:
   - "Deploy as App"
   - "Create App"
   - "Publish"
3. Follow the prompts

## Verification Steps

To verify the file exists and is accessible:

1. **In Databricks UI**:
   - Go to **Workspace** (left sidebar)
   - Navigate to your user folder
   - Look for `streamlitmcpcall.py`

2. **Using CLI**:
   ```bash
   databricks workspace ls /Workspace/Users/biju.thottathil@3cloudsolutions.com/training/
   ```

3. **Check file properties**:
   - Right-click the file in Workspace
   - Check "Properties" or "Info"
   - Verify it's marked as "Python" file

## Common Issues

### Issue: "File not found"
- **Solution**: Verify the exact path (case-sensitive)
- Check if file is in `training/` subfolder or root user folder

### Issue: "Invalid file type"
- **Solution**: Ensure file has `.py` extension
- Re-upload with `--language PYTHON` flag

### Issue: "Permission denied"
- **Solution**: Check you have read access to the file
- Verify you're using the correct workspace

### Issue: File browser doesn't show the file
- **Solution**: Try typing the path manually instead of browsing
- Refresh the browser or clear cache

## Still Having Issues?

If none of these work:

1. **Check the exact error message** - What does it say exactly?
2. **Take a screenshot** of the app creation form
3. **Verify file location** using the verification script above
4. **Try a different path format** - Some workspaces use different path structures

## Quick Test

Run this to verify file location:

```bash
uv run python3 -c "
from databricks.sdk import WorkspaceClient
import subprocess, json

result = subprocess.run(['databricks', 'auth', 'token', '--host', 'https://adb-1952652121322753.13.azuredatabricks.net'], capture_output=True, text=True)
token = json.loads(result.stdout)['access_token']

client = WorkspaceClient(host='https://adb-1952652121322753.13.azuredatabricks.net', token=token)

paths = [
    '/Workspace/Users/biju.thottathil@3cloudsolutions.com/streamlitmcpcall.py',
    '/Workspace/Users/biju.thottathil@3cloudsolutions.com/training/streamlitmcpcall.py'
]

for p in paths:
    try:
        status = client.workspace.get_status(p)
        print(f'✅ {p}')
    except:
        print(f'❌ {p}')
"
```


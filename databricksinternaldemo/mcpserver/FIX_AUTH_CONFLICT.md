# Fixing Databricks Authentication Conflict

## Problem

You're seeing this error:
```
Error: cannot resolve bundle auth configuration: validate: more than one authorization method configured: oauth and pat.
```

This happens when Databricks bundle detects multiple authentication methods.

## Solution

You have multiple authentication methods configured. Choose one:

### Option 1: Use PAT Token (Simplest)

Unset service principal variables and use PAT:

```bash
# Unset service principal
unset DATABRICKS_CLIENT_ID
unset DATABRICKS_CLIENT_SECRET
unset DATABRICKS_TENANT_ID

# Set PAT token
export DATABRICKS_TOKEN=your_pat_token_here
export DATABRICKS_HOST=https://adb-1952652121322753.13.azuredatabricks.net

# Now deploy
./deploy_app.sh
```

### Option 2: Use Service Principal (Recommended for Production)

Unset PAT and use service principal:

```bash
# Unset PAT
unset DATABRICKS_TOKEN

# Set service principal
export DATABRICKS_CLIENT_ID=b345b646-41c0-4abb-884d-6911cdeeec21
export DATABRICKS_CLIENT_SECRET=your_client_secret
export DATABRICKS_TENANT_ID=ed9aa516-5358-4016-a8b2-b6ccb99142d0
export DATABRICKS_HOST=https://adb-1952652121322753.13.azuredatabricks.net

# Now deploy
./deploy_app.sh
```

### Option 3: Use Specific Profile from ~/.databrickscfg

If you want to use a specific profile from your config file:

```bash
# Use the DEFAULT profile (username/password)
databricks bundle deploy --profile DEFAULT --target dev

# Or use the target profile (service principal)
databricks bundle deploy --profile target --target dev
```

### Option 4: Use Environment Variables to Override Config

Override the config file with environment variables:

```bash
# Clear any conflicting env vars
unset DATABRICKS_CLIENT_ID
unset DATABRICKS_CLIENT_SECRET

# Set only what you need
export DATABRICKS_TOKEN=your_pat_token
export DATABRICKS_HOST=https://adb-1952652121322753.13.azuredatabricks.net

# Deploy
databricks bundle deploy --target dev
```

## Quick Fix Script

Run the helper script to diagnose:

```bash
./fix_auth.sh
```

## For App Deployment (Not Bundle)

If you're just deploying the Streamlit app (not using bundles), the `deploy_app.sh` script will work with either method:

```bash
# With PAT
export DATABRICKS_TOKEN=your_token
./deploy_app.sh

# Or with Service Principal
export DATABRICKS_CLIENT_ID=your_id
export DATABRICKS_CLIENT_SECRET=your_secret
./deploy_app.sh
```

## Notes

- The bundle system is stricter about auth conflicts than the CLI
- For app deployment, you can use either method
- Service Principal is recommended for production/CI/CD
- PAT tokens are simpler for local development


# Azure App Service Deployment Guide

This guide explains how to deploy StoryOS to Azure App Service.

## Prerequisites

1. Azure account with an active subscription
2. Azure CLI installed: `az login`
3. Node.js and npm installed locally
4. Python 3.11 installed locally

## Deployment Architecture

StoryOS deploys as a single Azure App Service where:
- FastAPI backend handles API requests and WebSocket connections
- React frontend is served as static files by the backend
- MongoDB Atlas is used for database (external service)

## Step 1: Build the Frontend

Before deploying, build the React frontend:

```bash
./deploy.sh
```

Or manually:

```bash
cd frontend
npm install
npm run build
cd ..
```

This creates `frontend/dist/` with optimized production files.

## Step 2: Create Azure Resources

### Option A: Using Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** → **Web App**
3. Configure:
   - **Name**: `storyos-app` (or your choice)
   - **Runtime stack**: Python 3.11
   - **Region**: Choose closest to your users
   - **Pricing plan**: B1 or higher (Basic tier minimum)
4. Click **Review + create**

### Option B: Using Azure CLI

```bash
# Login to Azure
az login

# Create resource group
az group create --name storyos-rg --location eastus

# Create App Service plan
az appservice plan create \
  --name storyos-plan \
  --resource-group storyos-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group storyos-rg \
  --plan storyos-plan \
  --name storyos-app \
  --runtime "PYTHON:3.11"
```

## Step 3: Configure Environment Variables

Set these in Azure Portal → Your App Service → Configuration → Application settings:

### Required Settings

```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
MONGODB_DATABASE_NAME=storyos

XAI_API_KEY=your_xai_api_key

KLING_ACCESS_KEY=your_kling_access_key
KLING_SECRET_KEY=your_kling_secret_key
KLING_JWT_TTL=3600

JWT_SECRET_KEY=your_random_jwt_secret_here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=43200

ALLOWED_ORIGINS=https://storyos-app.azurewebsites.net,https://your-custom-domain.com

STORYOS_LOG_LEVEL=INFO
STORYOS_LOG_TO_FILE=true
STORYOS_LOG_MAX_SIZE_MB=10
STORYOS_LOG_BACKUP_COUNT=3
STORYOS_LOG_ROTATION_TYPE=size

ENABLE_DEBUG_FILE_LOGGING=false
```

### Or using Azure CLI:

```bash
az webapp config appsettings set \
  --resource-group storyos-rg \
  --name storyos-app \
  --settings \
    MONGODB_URI="mongodb+srv://..." \
    XAI_API_KEY="your_key" \
    KLING_ACCESS_KEY="your_key" \
    KLING_SECRET_KEY="your_secret" \
    JWT_SECRET_KEY="$(openssl rand -hex 32)" \
    ALLOWED_ORIGINS="https://storyos-app.azurewebsites.net"
```

## Step 4: Configure Startup Command

In Azure Portal → Your App Service → Configuration → General settings:

**Startup Command:**
```
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

Or using Azure CLI:

```bash
az webapp config set \
  --resource-group storyos-rg \
  --name storyos-app \
  --startup-file "python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000"
```

## Step 5: Deploy the Application

### Option A: Using Azure CLI (Recommended)

```bash
# Deploy using zip deployment
cd /path/to/storyos2
zip -r deploy.zip . -x "*.git*" "*.venv*" "*node_modules*" "*__pycache__*" "*.pytest_cache*"

az webapp deployment source config-zip \
  --resource-group storyos-rg \
  --name storyos-app \
  --src deploy.zip
```

### Option B: Using GitHub Actions

Create `.github/workflows/azure-deploy.yml`:

```yaml
name: Deploy to Azure App Service

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Build frontend
        run: |
          cd frontend
          npm install
          npm run build

      - name: Deploy to Azure
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'storyos-app'
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

### Option C: Using Git Deployment

```bash
# Enable local git deployment
az webapp deployment source config-local-git \
  --resource-group storyos-rg \
  --name storyos-app

# Get deployment URL
az webapp deployment list-publishing-credentials \
  --resource-group storyos-rg \
  --name storyos-app \
  --query scmUri -o tsv

# Add as git remote and push
git remote add azure <deployment-url>
git push azure main
```

## Step 6: Configure WebSocket Support

Azure App Service supports WebSockets by default on B1 tier and above. Ensure it's enabled:

```bash
az webapp config set \
  --resource-group storyos-rg \
  --name storyos-app \
  --web-sockets-enabled true
```

## Step 7: Test the Deployment

1. Visit: `https://storyos-app.azurewebsites.net`
2. Check health: `https://storyos-app.azurewebsites.net/api/health`
3. Test login and game functionality

## Step 8: Monitor and Scale

### View Logs

```bash
# Stream logs
az webapp log tail \
  --resource-group storyos-rg \
  --name storyos-app

# Or in Azure Portal → Your App Service → Log stream
```

### Scale Up/Out

```bash
# Scale up to S1 tier for better performance
az appservice plan update \
  --resource-group storyos-rg \
  --name storyos-plan \
  --sku S1

# Scale out to 2 instances
az appservice plan update \
  --resource-group storyos-rg \
  --name storyos-plan \
  --number-of-workers 2
```

## Troubleshooting

### App won't start

1. Check logs: Azure Portal → Log stream
2. Verify startup command is correct
3. Check environment variables are set
4. Ensure `frontend/dist` exists

### WebSocket connection fails

1. Verify WebSockets are enabled
2. Check ALLOWED_ORIGINS includes your domain
3. Ensure you're using wss:// (not ws://)

### Static files not loading

1. Verify `frontend/dist` directory exists in deployment
2. Check CORS settings
3. Look for 404 errors in browser console

## Cost Optimization

- **Development**: Use B1 tier (~$13/month)
- **Production**: Use S1 tier with auto-scaling (~$70/month + scaling costs)
- **Database**: MongoDB Atlas M0 (free tier) for development

## Custom Domain Setup

1. Azure Portal → Your App Service → Custom domains
2. Add your domain
3. Configure DNS CNAME record
4. Enable HTTPS (free with Azure)

```bash
az webapp config hostname add \
  --resource-group storyos-rg \
  --webapp-name storyos-app \
  --hostname yourdomain.com
```

## Continuous Deployment

For automated deployments:

1. Connect to GitHub in Azure Portal
2. Select repository and branch
3. Azure will auto-deploy on every push

## Security Checklist

- [ ] Change default JWT_SECRET_KEY
- [ ] Set strong MongoDB password
- [ ] Enable HTTPS only
- [ ] Configure ALLOWED_ORIGINS properly
- [ ] Set ENABLE_DEBUG_FILE_LOGGING=false in production
- [ ] Review MongoDB network access rules
- [ ] Enable Azure App Service authentication (optional)

## Support

For issues, check:
- Azure Portal logs
- MongoDB Atlas monitoring
- Application Insights (if enabled)

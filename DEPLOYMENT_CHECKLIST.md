# Azure Deployment Checklist

## Pre-Deployment

- [ ] Build frontend: `./deploy.sh`
- [ ] Test locally with built frontend
- [ ] Update environment variables in `.env`
- [ ] Commit all changes to git

## Azure Setup

- [ ] Create Azure resource group
- [ ] Create App Service with Python 3.11 runtime
- [ ] Configure environment variables in Azure
- [ ] Set startup command: `python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000`
- [ ] Enable WebSockets
- [ ] Configure MongoDB Atlas connection

## Deploy

- [ ] Run build script: `./deploy.sh`
- [ ] Deploy to Azure (choose one method):
  - [ ] Azure CLI zip deployment
  - [ ] GitHub Actions
  - [ ] Git deployment

## Post-Deployment

- [ ] Test health endpoint: `https://your-app.azurewebsites.net/api/health`
- [ ] Test frontend loads: `https://your-app.azurewebsites.net`
- [ ] Test user registration and login
- [ ] Test game session creation
- [ ] Test WebSocket connection
- [ ] Monitor logs for errors

## Environment Variables to Set in Azure

```
MONGODB_URI
MONGODB_USERNAME
MONGODB_PASSWORD
MONGODB_DATABASE_NAME
XAI_API_KEY
KLING_ACCESS_KEY
KLING_SECRET_KEY
JWT_SECRET_KEY
ALLOWED_ORIGINS
ENABLE_DEBUG_FILE_LOGGING=false
```

## Quick Deploy Commands

```bash
# Build
./deploy.sh

# Deploy with Azure CLI
az webapp deployment source config-zip \
  --resource-group storyos-rg \
  --name storyos-app \
  --src deploy.zip
```

See `AZURE_DEPLOYMENT.md` for detailed instructions.

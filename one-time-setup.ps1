   # Azure WebSocket Configuration Script for StoryOS
# This script enables WebSockets for the StoryOS Azure Web App

Write-Host "Azure WebSocket Configuration for StoryOS" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Prompt for Azure resource details
Write-Host ""
Write-Host "Please provide your Azure resource details:" -ForegroundColor Cyan

# Get App Name
do {
    $appName = Read-Host "Enter your Azure Web App name"
    if ([string]::IsNullOrWhiteSpace($appName)) {
        Write-Host "App name cannot be empty. Please try again." -ForegroundColor Red
    }
} while ([string]::IsNullOrWhiteSpace($appName))

# Get Resource Group Name
do {
    $resourceGroupName = Read-Host "Enter your Azure Resource Group name"
    if ([string]::IsNullOrWhiteSpace($resourceGroupName)) {
        Write-Host "Resource group name cannot be empty. Please try again." -ForegroundColor Red
    }
} while ([string]::IsNullOrWhiteSpace($resourceGroupName))

Write-Host ""
Write-Host "Configuration Summary:" -ForegroundColor Yellow
Write-Host "  App Name: $appName" -ForegroundColor White
Write-Host "  Resource Group: $resourceGroupName" -ForegroundColor White
Write-Host ""

# Confirm before proceeding
$confirm = Read-Host "Do you want to continue with these settings? (y/N)"
if ($confirm -notmatch '^[Yy]$') {
    Write-Host "Operation cancelled by user." -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# Check if Azure CLI is installed
Write-Host "Checking Azure CLI installation..." -ForegroundColor Yellow
try {
    $azVersion = az version --output json 2>$null | ConvertFrom-Json
    if ($azVersion) {
        Write-Host "✓ Azure CLI is installed (version: $($azVersion.'azure-cli'))" -ForegroundColor Green
    } else {
        throw "Azure CLI not found"
    }
} catch {
    Write-Host "✗ Azure CLI is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Azure CLI from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    exit 1
}

# Check if logged into Azure
Write-Host "Checking Azure login status..." -ForegroundColor Yellow
try {
    $account = az account show --output json 2>$null | ConvertFrom-Json
    if ($account) {
        Write-Host "✓ Logged into Azure as: $($account.user.name)" -ForegroundColor Green
        Write-Host "  Subscription: $($account.name) ($($account.id))" -ForegroundColor Cyan
    } else {
        throw "Not logged in"
    }
} catch {
    Write-Host "✗ Not logged into Azure" -ForegroundColor Red
    Write-Host "Please run 'az login' to authenticate with Azure" -ForegroundColor Yellow
    exit 1
}

# Check if resource group exists
Write-Host "Checking if resource group '$resourceGroupName' exists..." -ForegroundColor Yellow
try {
    $resourceGroup = az group show --name $resourceGroupName --output json 2>$null | ConvertFrom-Json
    if ($resourceGroup) {
        Write-Host "✓ Resource group '$resourceGroupName' found in location: $($resourceGroup.location)" -ForegroundColor Green
    } else {
        throw "Resource group not found"
    }
} catch {
    Write-Host "✗ Resource group '$resourceGroupName' not found" -ForegroundColor Red
    Write-Host "Please create the resource group or verify the name is correct" -ForegroundColor Yellow
    exit 1
}

# Check if web app exists
Write-Host "Checking if web app '$appName' exists..." -ForegroundColor Yellow
try {
    $webApp = az webapp show --name $appName --resource-group $resourceGroupName --output json 2>$null | ConvertFrom-Json
    if ($webApp) {
        Write-Host "✓ Web app '$appName' found" -ForegroundColor Green
        Write-Host "  URL: $($webApp.defaultHostName)" -ForegroundColor Cyan
        Write-Host "  State: $($webApp.state)" -ForegroundColor Cyan
    } else {
        throw "Web app not found"
    }
} catch {
    Write-Host "✗ Web app '$appName' not found in resource group '$resourceGroupName'" -ForegroundColor Red
    Write-Host "Please create the web app or verify the name is correct" -ForegroundColor Yellow
    exit 1
}

# Enable WebSockets
Write-Host "Enabling WebSockets for '$appName'..." -ForegroundColor Yellow
try {
    $result = az webapp config set --name $appName --resource-group $resourceGroupName --web-sockets-enabled true --output json | ConvertFrom-Json
    if ($result) {
        Write-Host "✓ WebSockets successfully enabled for '$appName'" -ForegroundColor Green

        # Verify the setting
        Write-Host "Verifying WebSocket configuration..." -ForegroundColor Yellow
        $config = az webapp config show --name $appName --resource-group $resourceGroupName --output json | ConvertFrom-Json
        if ($config.webSocketsEnabled -eq $true) {
            Write-Host "✓ WebSockets configuration verified: ENABLED" -ForegroundColor Green
        } else {
            Write-Host "⚠ WebSockets may not be properly configured" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "✗ Failed to enable WebSockets" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Set startup command
Write-Host ""
Write-Host "Setting startup command for '$appName'..." -ForegroundColor Yellow
$startupCommand = "python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000"
try {
    az webapp config set --name $appName --resource-group $resourceGroupName --startup-file $startupCommand --output none
    Write-Host "✓ Startup command configured successfully" -ForegroundColor Green
    Write-Host "  Command: $startupCommand" -ForegroundColor Cyan
} catch {
    Write-Host "✗ Failed to set startup command" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "You may need to set it manually in Azure Portal under Configuration > General settings" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Restarting the web app to apply WebSocket configuration..." -ForegroundColor Yellow
try {
    az webapp restart --name $appName --resource-group $resourceGroupName --output none
    Write-Host "✓ Web app '$appName' restarted successfully" -ForegroundColor Green
    
    # Wait a moment for the restart to take effect
    Write-Host "Waiting for app to come back online..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Check app status after restart
    $webAppStatus = az webapp show --name $appName --resource-group $resourceGroupName --query "state" --output tsv
    if ($webAppStatus -eq "Running") {
        Write-Host "✓ Web app is running and ready" -ForegroundColor Green
    } else {
        Write-Host "⚠ Web app status: $webAppStatus" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Failed to restart web app, but WebSocket configuration was applied" -ForegroundColor Yellow
    Write-Host "You may need to restart the app manually from the Azure portal" -ForegroundColor Yellow
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Configuration completed successfully!" -ForegroundColor Green
Write-Host "Your StoryOS app now supports WebSocket connections for real-time features." -ForegroundColor Cyan
Write-Host "App URL: https://$appName.azurewebsites.net" -ForegroundColor Cyan
   
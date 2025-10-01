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

# Ask about uploading environment variables
Write-Host ""
Write-Host "Environment Variable Upload" -ForegroundColor Yellow
Write-Host "=============================" -ForegroundColor Yellow
$uploadEnv = Read-Host "Do you want to upload environment variables from .env file to Azure? (y/N)"
if ($uploadEnv -match '^[Yy]$') {
    # Check if .env file exists
    $envFilePath = Join-Path $PSScriptRoot ".env"
    if (Test-Path $envFilePath) {
        # Parse .env file
        Write-Host ""
        Write-Host "Reading .env file..." -ForegroundColor Yellow
        $envVars = @{}
        $envVarsToUpload = @()
        $skippedVars = @()

        Get-Content $envFilePath | ForEach-Object {
            $line = $_.Trim()
            # Skip empty lines and comments
            if ($line -and -not $line.StartsWith("#")) {
                # Parse KEY=VALUE format
                if ($line -match '^([^=]+)=(.*)$') {
                    $key = $matches[1].Trim()
                    $value = $matches[2].Trim()

                    # Remove quotes if present
                    if ($value -match '^"(.*)"$' -or $value -match "^'(.*)'$") {
                        $value = $matches[1]
                    }

                    # Skip ALLOWED_ORIGINS (not needed in production)
                    if ($key -eq "ALLOWED_ORIGINS") {
                        $skippedVars += $key
                    } else {
                        $envVars[$key] = $value
                        $envVarsToUpload += $key
                    }
                }
            }
        }

        Write-Host "✓ Found $($envVarsToUpload.Count) environment variables to upload" -ForegroundColor Green

        if ($skippedVars.Count -gt 0) {
            Write-Host "ℹ Skipping: $($skippedVars -join ', ') (not needed in production)" -ForegroundColor Cyan
        }

        Write-Host ""
        Write-Host "Variables to upload:" -ForegroundColor Cyan
        foreach ($key in $envVarsToUpload) {
            $displayValue = $envVars[$key]
            # Mask sensitive values
            if ($key -match "KEY|SECRET|PASSWORD|TOKEN") {
                if ($displayValue.Length -gt 8) {
                    $displayValue = $displayValue.Substring(0, 4) + "***" + $displayValue.Substring($displayValue.Length - 4)
                } else {
                    $displayValue = "***"
                }
            }
            Write-Host "  $key = $displayValue" -ForegroundColor White
        }

        Write-Host ""
        Write-Host "WARNING: This will add/update these environment variables in Azure." -ForegroundColor Red
        Write-Host "Existing variables will be preserved. Only these variables will be added or updated." -ForegroundColor Red
        $confirmUpload = Read-Host "Are you sure you want to proceed? (y/N)"

        if ($confirmUpload -match '^[Yy]$') {
            Write-Host ""
            Write-Host "Uploading environment variables to Azure..." -ForegroundColor Yellow

            # Build settings array for Azure CLI
            $settingsArgs = @()
            foreach ($key in $envVarsToUpload) {
                $value = $envVars[$key]
                $settingsArgs += "$key=$value"
            }

            try {
                # Build a JSON object with all environment variables
                # This avoids shell escaping issues with special characters like &, ?, =
                $appSettings = @{}
                foreach ($key in $envVarsToUpload) {
                    $appSettings[$key] = $envVars[$key]
                }

                # Write to a temporary JSON file
                $tmp = Join-Path $env:TEMP "appsettings.$([guid]::NewGuid()).json"
                $appSettings | ConvertTo-Json -Compress | Set-Content -Path $tmp -Encoding UTF8

                # Upload all settings in one go using the JSON file
                az webapp config appsettings set `
                    --name $appName `
                    --resource-group $resourceGroupName `
                    --settings "@$tmp" `
                    --output none

                # Clean up temp file
                Remove-Item $tmp -ErrorAction Ignore

                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✓ All environment variables uploaded successfully" -ForegroundColor Green
                    Write-Host "  Uploaded: $($envVarsToUpload.Count) variables" -ForegroundColor Cyan
                } else {
                    throw "Azure CLI returned exit code $LASTEXITCODE"
                }
            } catch {
                Write-Host "✗ Failed to upload environment variables" -ForegroundColor Red
                Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
                Write-Host "You may need to set them manually in Azure Portal" -ForegroundColor Yellow
            }
        } else {
            Write-Host "Environment variable upload cancelled." -ForegroundColor Yellow
        }
    } else {
        Write-Host "✗ .env file not found at: $envFilePath" -ForegroundColor Red
        Write-Host "Please create a .env file in the project root directory" -ForegroundColor Yellow
    }
} else {
    Write-Host "Skipping environment variable upload." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Restarting the web app to apply configuration..." -ForegroundColor Yellow
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
   
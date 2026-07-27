# ============================================
# Fulda Nexus - Pulumi Environment Setup Script
# Run this once per PowerShell session:
#   .\setup-env.ps1
# ============================================

# Pulumi passphrase (to decrypt secrets)
$env:PULUMI_CONFIG_PASSPHRASE = "Fulda2025"

# OpenStack Keystone credentials
$env:OS_AUTH_URL              = "https://private-cloud.informatik.hs-fulda.de:5000/v3"
$env:OS_USERNAME              = "CloudComp13"
$env:OS_PASSWORD              = "Hulk@3000"
$env:OS_PROJECT_NAME          = "CloudComp13"
$env:OS_USER_DOMAIN_NAME      = "Default"
$env:OS_PROJECT_DOMAIN_NAME   = "Default"
$env:OS_IDENTITY_API_VERSION  = "3"
$env:OS_INSECURE              = "true"

Write-Host "✅ Environment variables set!" -ForegroundColor Green
Write-Host "You can now run: pulumi up / pulumi destroy / pulumi stack output" -ForegroundColor Cyan

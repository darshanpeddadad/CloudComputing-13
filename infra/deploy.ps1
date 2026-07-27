# ============================================================
# deploy.ps1  —  Full one-click deploy for Fulda Nexus
# Usage:
#   .\deploy.ps1            → create infra + setup VM + run app
#   .\deploy.ps1 destroy    → tear down all infrastructure
#   .\deploy.ps1 vm-setup   → only run VM setup (infra already up)
# ============================================================

param(
    [string]$Action = "up"
)

$KEY = Join-Path $PSScriptRoot "fulda-key-new.pem"
$GITHUB_REPO = "https://github.com/darshanpeddadad/CloudComputing-13.git"
$DB_USER     = "fulda_user"
$DB_PASS     = "Hulk@3000"
$DB_PASS_URL = "Hulk%403000"   # URL-encoded @ → %40
$DB_NAME     = "fulda_app"

# ── Helper: run a command on the VM via SSH ──────────────────
function SSH-Run {
    param([string]$IP, [string]$Command)
    ssh -i $KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 ubuntu@$IP $Command
}

# ── Load env vars ────────────────────────────────────────────
Write-Host ""
Write-Host ">>> Loading environment variables..." -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "setup-env.ps1")

# ── Activate venv ────────────────────────────────────────────
$venvActivate = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
}

# ════════════════════════════════════════════════════════════
# DESTROY
# ════════════════════════════════════════════════════════════
if ($Action -eq "destroy") {
    Write-Host ""
    Write-Host ">>> Destroying infrastructure..." -ForegroundColor Red

    # Auto-fix stuck FloatingIpAssociate resource
    $fipUrn = "urn:pulumi:dev::fuldanexus-infra::openstack:networking/floatingIpAssociate:FloatingIpAssociate::web-server-fip-assoc"
    Write-Host ">>> Removing stuck floating IP from state (if any)..." -ForegroundColor Yellow
    pulumi state delete $fipUrn --force 2>$null

    # Also remove stuck VMs from state (if any)
    $webUrn = "urn:pulumi:dev::fuldanexus-infra::openstack:compute/instance:Instance::web-server-0"
    $dbUrn  = "urn:pulumi:dev::fuldanexus-infra::openstack:compute/instance:Instance::db-server"
    pulumi state delete $webUrn --force 2>$null
    pulumi state delete $dbUrn  --force 2>$null

    pulumi destroy --yes
    Write-Host ""
    Write-Host "All infrastructure destroyed." -ForegroundColor Red
    exit 0
}

# ════════════════════════════════════════════════════════════
# VM-SETUP (skip pulumi, just configure an already-running VM)
# ════════════════════════════════════════════════════════════
if ($Action -eq "vm-setup") {
    $WEB_IP = pulumi stack output Web_Primary_Public_IP
    $DB_IP  = pulumi stack output DB_Private_IP
    Write-Host ""
    Write-Host ">>> VM setup only. Web=$WEB_IP  DB=$DB_IP" -ForegroundColor Cyan
}

# ════════════════════════════════════════════════════════════
# FULL DEPLOY (default: pulumi up + VM setup)
# ════════════════════════════════════════════════════════════
if ($Action -eq "up") {
    Write-Host ">>> Ensuring Pulumi config secrets are set..." -ForegroundColor Cyan
    pulumi config set --secret fuldanexus-infra:db_password "Hulk@3000" 2>$null
    pulumi config set fuldanexus-infra:key_name "fulda-key-new" 2>$null

    Write-Host ""
    Write-Host ">>> Running: pulumi up --yes" -ForegroundColor Green
    pulumi up --yes

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: pulumi up failed." -ForegroundColor Red
        exit 1
    }

    # Get new IPs
    $WEB_IP = pulumi stack output Web_Primary_Public_IP
    $DB_IP  = pulumi stack output DB_Private_IP

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  Infrastructure ready!" -ForegroundColor Green
    Write-Host "  Web IP : $WEB_IP" -ForegroundColor Yellow
    Write-Host "  DB IP  : $DB_IP" -ForegroundColor Yellow
    Write-Host "============================================" -ForegroundColor Green
}

# ════════════════════════════════════════════════════════════
# VM SETUP — runs for both "up" and "vm-setup"
# ════════════════════════════════════════════════════════════

# Build the .env file content
$ENV_CONTENT = @"
DATABASE_HOST=$DB_IP
DATABASE_PORT=3306
DATABASE_NAME=$DB_NAME
DATABASE_USER=$DB_USER
DATABASE_PASSWORD=$DB_PASS
DATABASE_URL=mysql+asyncmy://${DB_USER}:${DB_PASS_URL}@${DB_IP}:3306/$DB_NAME
SECRET_KEY=fulda-super-secret-key-change-in-prod
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_V1_STR=/api/v1
PROJECT_NAME=Fulda Nexus API
BACKEND_CORS_ORIGINS=["http://$WEB_IP"]
ADMIN_EMAIL=admin@informatik.hs-fulda.de
ADMIN_PASSWORD=ChangeMe123!
ADMIN_FIRST_NAMES=Fulda
ADMIN_LAST_NAME=Admin
ADMIN_DOB=1990-01-01
"@

Write-Host ""
Write-Host ">>> Waiting for VM cloud-init to finish (Docker + git clone)..." -ForegroundColor Yellow
$dockerReady = $false
for ($d = 1; $d -le 15; $d++) {
    $check = SSH-Run $WEB_IP "test -f /home/ubuntu/app/docker-compose.yml && which docker && echo READY 2>/dev/null"
    if ($check -match "READY") {
        $dockerReady = $true
        Write-Host "    VM is ready! (took ~$d min)" -ForegroundColor Green
        break
    }
    Write-Host "    VM still setting up... ($d/15 min)" -ForegroundColor DarkGray
    Start-Sleep -Seconds 60
}

if (-not $dockerReady) {
    Write-Host "ERROR: VM setup timed out. SSH in and check: sudo cat /var/log/cloud-init-output.log" -ForegroundColor Red
    exit 1
}

# Write .env file via SSH heredoc
Write-Host ">>> Writing .env file on VM..." -ForegroundColor Cyan
$envCmd = "cat > ~/app/Backend/.env << 'ENVEOF'" + "`n" + $ENV_CONTENT + "`nENVEOF"
SSH-Run $WEB_IP $envCmd

# Start Docker Compose
Write-Host ">>> Starting Docker Compose (build + start containers)..." -ForegroundColor Cyan
SSH-Run $WEB_IP "cd ~/app && sudo docker compose up --build -d"

# Poll for DB connectivity (no fixed wait — check every 30s, up to 15 min)
Write-Host ""
Write-Host ">>> Waiting for MySQL DB to be ready..." -ForegroundColor Yellow

# Try DB connectivity
Write-Host ">>> Checking DB connectivity..." -ForegroundColor Cyan
$dbReady = $false
for ($attempt = 1; $attempt -le 20; $attempt++) {
    $result = SSH-Run $WEB_IP "nc -zv $DB_IP 3306 2>&1"
    if ($result -match "succeeded") {
        $dbReady = $true
        Write-Host "    DB is reachable! (attempt $attempt)" -ForegroundColor Green
        break
    }
    Write-Host "    DB not ready yet... ($attempt/20, waiting 30s)" -ForegroundColor DarkGray
    Start-Sleep -Seconds 30
}

if (-not $dbReady) {
    Write-Host "WARNING: DB may not be ready. Try migrations manually." -ForegroundColor Red
} else {
    # Run migrations
    Write-Host ">>> Running database migrations..." -ForegroundColor Cyan
    SSH-Run $WEB_IP "sudo docker exec -e PYTHONPATH=/app fastapi-backend alembic upgrade head"

    # Seed data
    Write-Host ">>> Seeding database..." -ForegroundColor Cyan
    SSH-Run $WEB_IP "sudo docker exec -e PYTHONPATH=/app fastapi-backend python scripts/seed_events.py"
}

# ── Final summary ────────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host "  App URL  : http://$WEB_IP" -ForegroundColor Yellow
Write-Host "  SSH      : ssh -i fulda-key-new.pem ubuntu@$WEB_IP" -ForegroundColor Yellow
Write-Host "  DB IP    : $DB_IP (private)" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

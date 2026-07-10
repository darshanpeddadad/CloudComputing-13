# Fulda Nexus Cloud Infrastructure & Deployment (OpenStack + Pulumi)

Our application runs on a fully automated, secure, multi-tier environment on the **Fulda University OpenStack Cloud** provisioned using **Pulumi Infrastructure as Code (IaC)**.

---

## 🌐 Architecture Layout

The infrastructure is designed with security and scalability using the following layout:
1. **Private Subnet**: Replicates a secure VPC environment (`10.0.1.0/24`) with isolated network routing.
2. **Nginx & Docker Web Server Host**: Ubuntu VM (`10.0.1.71`) mapped to a Public Floating IP (`10.32.6.178`). Runs frontend (React) and backend (FastAPI) containers. Includes **2GB swap space** allocation to guarantee successful static asset compilation.
3. **Private MySQL Database Server VM**: Completely isolated from public access. Security groups permit connection **only** from the Web Server VM on port `3306`.
4. **Swift Object Container**: Stores user-uploaded media files.

---

## 🚀 Quick-Start Deployment Checklist

### 1. Configure Local Environment (PowerShell)
Install Pulumi, select the stack, and export your credentials:
```powershell
# Set local state backend
pulumi login --local

# Set environment authentication for Keystone API
$env:PULUMI_CONFIG_PASSPHRASE="Fulda2025"
$env:OS_AUTH_URL="https://private-cloud.informatik.hs-fulda.de:5000/v3"
$env:OS_USERNAME="CloudComp13"
$env:OS_PASSWORD="Hulk@3000"
$env:OS_PROJECT_NAME="CloudComp13"
$env:OS_USER_DOMAIN_NAME="Default"
$env:OS_PROJECT_DOMAIN_NAME="Default"
$env:OS_IDENTITY_API_VERSION="3"
$env:OS_INSECURE="true"

# Install dependencies inside a virtualenv
cd infra
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Stack Keys
```powershell
pulumi config set db_username fulda_user
pulumi config set db_name fulda_app
pulumi config set --secret db_password "Hulk@3000"
pulumi config set key_name fulda-key-new
```

### 3. Provision Infrastructure
```powershell
pulumi up
```

---

## 🚢 Application Deployment on the Instance

1. **SSH into the VM**:
   ```powershell
   ssh -i fulda-key-new.pem ubuntu@10.32.6.178
   ```
2. **Clone & Setup `.env`**:
   ```bash
   git clone https://github.com/darshanpeddadad/CloudComputing-13.git app
   cd app
   nano Backend/.env
   ```
   *(Note: The database password in `DATABASE_URL` must be URL-encoded, replacing `@` with `%40`, resulting in `mysql+asyncmy://fulda_user:Hulk%403000@10.0.1.123:3306/fulda_app`)*
3. **Boot Up & Seed Database**:
   ```bash
   docker-compose up --build -d
   docker exec -e PYTHONPATH=/app fastapi-backend alembic upgrade head
   docker exec -e PYTHONPATH=/app fastapi-backend python scripts/seed_events.py
   ```

---

## 🌐 Verified Live Endpoints
Once deployed, the app is reachable on the university intranet/VPN at:
* **Frontend Portal**: [http://10.32.6.178](http://10.32.6.178)
* **Backend Docs (Swagger)**: [http://10.32.6.178/api/docs](http://10.32.6.178/api/docs)
* **Health Endpoint**: [http://10.32.6.178/api/health](http://10.32.6.178/api/health)
